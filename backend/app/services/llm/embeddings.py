from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings

OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS = 1536


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str = OPENAI_EMBEDDING_MODEL) -> None:
        self._api_key = api_key
        self._model = model

    @property
    def dimensions(self) -> int:
        return OPENAI_EMBEDDING_DIMENSIONS

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"input": texts, "model": self._model},
            )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]


def get_embedding_provider(settings: Settings) -> EmbeddingProvider | None:
    """Returns None (gracefully) when no embedding-capable provider is configured.

    Only OpenAI is wired up for embeddings right now since neither Anthropic nor
    Gemini expose an embeddings endpoint comparable to OpenAI's, and Ollama support
    is deferred to Phase 6 alongside the rest of the LLM provider abstraction.
    """
    if settings.openai_api_key:
        return OpenAIEmbeddingProvider(settings.openai_api_key)
    return None
