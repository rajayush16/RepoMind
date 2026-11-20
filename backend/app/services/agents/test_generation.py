import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.indexing import CodeSymbol, IndexedFile
from app.services.llm.base import ChatMessage, LLMProvider

FRAMEWORK_INSTRUCTIONS = {
    "pytest": "Write pytest-style tests (plain `assert` statements, `def test_*` functions).",
    "jest": "Write Jest-style tests (`describe`/`it`/`expect`), using CommonJS or ESM imports matching the source file.",
}


class SymbolNotFoundError(Exception):
    pass


def _extract_snippet(content: str, start_line: int, end_line: int) -> str:
    lines = content.splitlines()
    return "\n".join(lines[max(0, start_line - 1) : end_line])


async def generate_test_code(
    db: AsyncSession,
    provider: LLMProvider,
    repository_id: uuid.UUID,
    symbol_name: str,
    file_path: str,
    framework: str,
) -> str:
    """Generates test code for a real, already-indexed symbol -- never for a
    symbol that doesn't actually exist in this repository's index."""
    result = await db.execute(
        select(CodeSymbol, IndexedFile)
        .join(IndexedFile, CodeSymbol.indexed_file_id == IndexedFile.id)
        .where(
            CodeSymbol.repository_id == repository_id,
            CodeSymbol.name == symbol_name,
            IndexedFile.relative_path == file_path,
        )
    )
    row = result.first()
    if row is None:
        raise SymbolNotFoundError(f"Symbol {symbol_name!r} not found in {file_path!r} for this repository.")

    symbol, indexed_file = row
    snippet = _extract_snippet(indexed_file.content or "", symbol.start_line, symbol.end_line)
    instructions = FRAMEWORK_INSTRUCTIONS.get(framework, "Write idiomatic tests for this language.")

    messages = [
        ChatMessage(
            role="system",
            content=(
                "You generate test code for a real function/method from a real codebase. "
                "Cover the normal case and at least one edge case. Output ONLY the test "
                "file's code, no explanation, no markdown fences."
            ),
        ),
        ChatMessage(
            role="user",
            content=(
                f"File: {file_path} ({indexed_file.language})\n"
                f"Symbol: {symbol.name} ({symbol.symbol_type})\n\n"
                f"Source:\n{snippet}\n\n"
                f"{instructions}"
            ),
        ),
    ]

    raw = await provider.generate(messages, max_tokens=1500)
    return raw.strip().removeprefix("```python").removeprefix("```javascript").removeprefix("```").removesuffix("```").strip()
