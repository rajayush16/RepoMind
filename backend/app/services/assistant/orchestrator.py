import json
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.models.conversation import Message
from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError
from app.services.retrieval.hybrid import RetrievalResult, hybrid_search

SYSTEM_PROMPT = (
    "You are RepoMind, an assistant that explains a specific codebase. "
    "You are given retrieved evidence (real file paths, line ranges, and code "
    "signatures) from that repository. Answer ONLY using this evidence. "
    "Always cite the file path and line numbers for any factual claim about the "
    "code. Never invent a file path, function name, or line number that is not "
    "in the evidence provided. If the evidence is insufficient to answer, say so "
    "plainly instead of guessing."
)

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I couldn't find any relevant code in this repository's index to answer that "
    "question. Try rephrasing, or ask about something more specific to this "
    "codebase."
)


def build_context(results: list[RetrievalResult]) -> str:
    blocks = []
    for result in results:
        location = result.file_path
        if result.start_line is not None:
            location += f":{result.start_line}"
            if result.end_line and result.end_line != result.start_line:
                location += f"-{result.end_line}"
        header = f"{location}"
        if result.symbol_name:
            header += f" ({result.symbol_type or 'symbol'}: {result.symbol_name})"
        blocks.append(f"[{header}]\n{result.snippet}")
    return "\n\n".join(blocks)


def _citations_from_results(results: list[RetrievalResult]) -> list[dict]:
    return [
        {
            "file_path": r.file_path,
            "symbol_name": r.symbol_name,
            "symbol_type": r.symbol_type,
            "start_line": r.start_line,
            "end_line": r.end_line,
            "sources": r.sources,
        }
        for r in results
    ]


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_answer(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    provider: LLMProvider,
    repository_id: uuid.UUID,
    conversation_id: uuid.UUID,
    question: str,
) -> AsyncIterator[str]:
    """Retrieve evidence, stream the model's answer as SSE, then persist both the
    user question and the assistant answer. Citations are the real evidence that
    was actually retrieved and sent to the model -- never anything the model
    claims about itself -- so they can't be hallucinated.

    Takes a session FACTORY, not a session: this generator keeps running after a
    FastAPI route returns a StreamingResponse built from it, by which point any
    `Depends(get_db)` session from that route would already be closed. Opening the
    session here, scoped to the generator's own lifetime, avoids that.
    """
    async with session_factory() as db:
        db.add(Message(conversation_id=conversation_id, role="user", content=question))
        await db.commit()

        results = await hybrid_search(db, settings, repository_id, question)

        if not results:
            db.add(
                Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=INSUFFICIENT_EVIDENCE_MESSAGE,
                    citations=[],
                    insufficient_evidence=True,
                )
            )
            await db.commit()
            yield _sse("token", {"text": INSUFFICIENT_EVIDENCE_MESSAGE})
            yield _sse("done", {"citations": [], "insufficient_evidence": True})
            return

        context = build_context(results)
        messages = [
            ChatMessage(role="system", content=SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=f"Evidence from the repository:\n\n{context}\n\nQuestion: {question}",
            ),
        ]

        answer_parts: list[str] = []
        try:
            async for delta in provider.generate_stream(messages):
                answer_parts.append(delta)
                yield _sse("token", {"text": delta})
        except LLMProviderError as exc:
            yield _sse("error", {"detail": str(exc)})
            return

        answer = "".join(answer_parts)
        citations = _citations_from_results(results)

        db.add(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
                citations=citations,
                insufficient_evidence=False,
                provider=provider.name,
                model=provider.model,
                token_count=provider.count_tokens(answer),
            )
        )
        await db.commit()

        yield _sse("done", {"citations": citations, "insufficient_evidence": False})
