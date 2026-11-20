import uuid

import httpx
import pytest
from sqlalchemy import select

from app.api.routes import pull_requests as pull_requests_routes
from app.core.security import encrypt_secret
from app.models.pull_request import PullRequestReview, ReviewFinding
from app.models.user import User
from app.services.github import client as github_client

from tests.conftest import TestSessionLocal, get_test_settings


async def _register_and_connect(client: httpx.AsyncClient, email: str) -> str:
    await client.post("/api/auth/register", json={"email": email, "password": "correct-horse-battery"})
    response = await client.post(
        "/api/repositories",
        json={
            "github_repo_id": 77,
            "owner": "octocat",
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "default_branch": "main",
        },
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_start_review_enqueues_task(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_id = await _register_and_connect(client, f"revA-{uuid.uuid4().hex[:8]}@example.com")

    enqueued: list[str] = []
    monkeypatch.setattr(
        pull_requests_routes.review_pull_request_task, "delay", lambda rid: enqueued.append(rid)
    )

    response = await client.post(f"/api/repositories/{repo_id}/pull-requests", json={"pr_number": 42})
    assert response.status_code == 202
    body = response.json()
    assert enqueued == [body["id"]]
    assert body["pr_number"] == 42
    assert body["published"] is False


@pytest.mark.asyncio
async def test_list_and_get_review(client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_id = await _register_and_connect(client, f"revB-{uuid.uuid4().hex[:8]}@example.com")
    monkeypatch.setattr(pull_requests_routes.review_pull_request_task, "delay", lambda rid: None)

    create_response = await client.post(f"/api/repositories/{repo_id}/pull-requests", json={"pr_number": 5})
    review_id = create_response.json()["id"]

    list_response = await client.get(f"/api/repositories/{repo_id}/pull-requests")
    assert len(list_response.json()) == 1

    get_response = await client.get(f"/api/pull-requests/{review_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == review_id


@pytest.mark.asyncio
async def test_publish_requires_confirm_and_complete_status(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = f"revC-{uuid.uuid4().hex[:8]}@example.com"
    repo_id = await _register_and_connect(client, email)
    monkeypatch.setattr(pull_requests_routes.review_pull_request_task, "delay", lambda rid: None)

    create_response = await client.post(f"/api/repositories/{repo_id}/pull-requests", json={"pr_number": 9})
    review_id = create_response.json()["id"]

    no_confirm = await client.post(f"/api/pull-requests/{review_id}/publish", json={"confirm": False})
    assert no_confirm.status_code == 422

    still_pending = await client.post(f"/api/pull-requests/{review_id}/publish", json={"confirm": True})
    assert still_pending.status_code == 422


@pytest.mark.asyncio
async def test_publish_posts_comment_when_confirmed_and_complete(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = f"revd-{uuid.uuid4().hex[:8]}@example.com"
    repo_id = await _register_and_connect(client, email)
    monkeypatch.setattr(pull_requests_routes.review_pull_request_task, "delay", lambda rid: None)

    create_response = await client.post(f"/api/repositories/{repo_id}/pull-requests", json={"pr_number": 3})
    review_id = create_response.json()["id"]

    settings = get_test_settings()
    async with TestSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.github_access_token_encrypted = encrypt_secret("fake-token", settings)

        review_result = await db.execute(
            select(PullRequestReview).where(PullRequestReview.id == uuid.UUID(review_id))
        )
        review = review_result.scalar_one()
        review.status = "complete"
        review.summary = "Looks good overall."
        db.add(ReviewFinding(
            pull_request_review_id=review.id,
            file_path="app.py",
            line=1,
            severity="low",
            category="maintainability",
            summary="Minor naming nit",
            explanation="Variable name could be clearer.",
        ))
        await db.commit()

    async def fake_post_issue_comment(token, owner, repo, issue_number, body):
        assert token == "fake-token"
        assert "Looks good overall" in body
        return {"html_url": "https://github.com/octocat/hello-world/pull/3#issuecomment-1"}

    monkeypatch.setattr(github_client, "post_issue_comment", fake_post_issue_comment)
    monkeypatch.setattr(pull_requests_routes, "post_issue_comment", fake_post_issue_comment)

    response = await client.post(f"/api/pull-requests/{review_id}/publish", json={"confirm": True})
    assert response.status_code == 200
    body = response.json()
    assert body["published"] is True
    assert body["published_comment_url"] == "https://github.com/octocat/hello-world/pull/3#issuecomment-1"

    second_attempt = await client.post(f"/api/pull-requests/{review_id}/publish", json={"confirm": True})
    assert second_attempt.status_code == 422
