import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.security import decrypt_secret
from app.models.pull_request import PullRequestReview, ReviewFinding
from app.models.repository import Repository
from app.models.user import User
from app.schemas.pull_request import PRReviewAnalysisSchema
from app.services.github.client import get_pull_request, get_pull_request_files
from app.services.llm.base import ChatMessage, LLMProvider

MAX_PATCH_CHARS = 4000
MAX_FILES_IN_PROMPT = 15

REVIEW_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Review ONLY the diff provided -- do not "
    "invent file paths, line numbers, or code that isn't in the diff. For each "
    "finding, classify it into exactly one category: correctness, security, "
    "performance, maintainability, testing, or architecture. Rate severity as "
    "high, medium, or low. Flag missing tests for new logic as a 'testing' "
    "finding. Be specific and reference the real file path and, where possible, "
    "a real line number from the diff."
)


def _format_diff(files: list[dict]) -> str:
    blocks = []
    for f in files[:MAX_FILES_IN_PROMPT]:
        patch = (f.get("patch") or "(no textual diff -- binary or too large)")[:MAX_PATCH_CHARS]
        blocks.append(f"--- {f['filename']} ({f['status']}, +{f['additions']}/-{f['deletions']}) ---\n{patch}")
    return "\n\n".join(blocks)


class PRReviewError(Exception):
    pass


async def run_pr_review(
    review_id: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    provider: LLMProvider,
) -> None:
    async with session_factory() as db:
        review = await db.get(PullRequestReview, review_id)
        if review is None:
            return

        try:
            repository = await db.get(Repository, review.repository_id)
            access_token = None
            if repository and repository.connected_by_user_id:
                user = await db.get(User, repository.connected_by_user_id)
                if user and user.github_access_token_encrypted:
                    access_token = decrypt_secret(user.github_access_token_encrypted, settings)

            if not access_token:
                raise PRReviewError("No connected GitHub account with a stored access token.")

            pr = await get_pull_request(access_token, repository.owner, repository.name, review.pr_number)
            files = await get_pull_request_files(access_token, repository.owner, repository.name, review.pr_number)

            review.pr_title = pr.get("title", review.pr_title)
            review.pr_url = pr.get("html_url", review.pr_url)

            diff_text = _format_diff(files)
            messages = [
                ChatMessage(role="system", content=REVIEW_SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=f"Pull request: {pr.get('title')}\n\nChanged files diff:\n\n{diff_text}",
                ),
            ]

            analysis = await provider.generate_structured(messages, schema=PRReviewAnalysisSchema)

            review.summary = analysis.summary
            for finding in analysis.findings:
                db.add(
                    ReviewFinding(
                        pull_request_review_id=review.id,
                        file_path=finding.file_path,
                        line=finding.line,
                        severity=finding.severity,
                        category=finding.category,
                        summary=finding.summary,
                        explanation=finding.explanation,
                        suggestion=finding.suggestion,
                    )
                )

            review.status = "complete"
            await db.commit()
        except Exception as exc:  # noqa: BLE001
            review.status = "failed"
            review.error_detail = f"{type(exc).__name__}: {exc}"
            await db.commit()
