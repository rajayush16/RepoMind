from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProviderError(Exception):
    pass


class LLMProvider(ABC):
    """Common interface every provider adapter implements.

    `generate_structured` is deliberately implemented once here (not per-provider):
    it asks the model for JSON matching a schema via the prompt and validates the
    response with Pydantic, rather than relying on provider-specific structured-
    output features that differ across OpenAI/Anthropic/Gemini/Ollama.
    """

    name: str
    model: str

    @abstractmethod
    async def generate(self, messages: list[ChatMessage], *, max_tokens: int = 1024) -> str: ...

    @abstractmethod
    def generate_stream(
        self, messages: list[ChatMessage], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]: ...

    def count_tokens(self, text: str) -> int:
        """Approximate token count (~4 chars/token). Not model-exact -- each
        provider tokenizes differently, and this project doesn't bundle every
        provider's real tokenizer. Good enough for cost estimation, not billing."""
        return max(1, len(text) // 4)

    async def generate_structured(self, messages: list[ChatMessage], *, schema, max_tokens: int = 1024):
        import json

        schema_messages = [
            *messages,
            ChatMessage(
                role="system",
                content=(
                    "Respond with ONLY a single JSON object matching this schema, no "
                    f"prose, no markdown fences: {schema.model_json_schema()}"
                ),
            ),
        ]
        raw = await self.generate(schema_messages, max_tokens=max_tokens)
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return schema.model_validate(json.loads(cleaned))
