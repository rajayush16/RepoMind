import json
from collections.abc import AsyncIterator

import httpx

from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError

DEFAULT_MODEL = "llama3.1"


class OllamaProvider(LLMProvider):
    """Local-model adapter -- no API key required, talks to a running Ollama server."""

    name = "ollama"

    def __init__(
        self, base_url: str, model: str = DEFAULT_MODEL, transport: httpx.BaseTransport | None = None
    ) -> None:
        self.model = model
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    def _payload(self, messages: list[ChatMessage], stream: bool) -> dict:
        return {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
        }

    async def generate(self, messages: list[ChatMessage], *, max_tokens: int = 1024) -> str:
        async with httpx.AsyncClient(timeout=120.0, transport=self._transport) as client:
            response = await client.post(
                f"{self._base_url}/api/chat", json=self._payload(messages, stream=False)
            )
        if response.status_code != 200:
            raise LLMProviderError(f"Ollama error ({response.status_code}): {response.text}")
        return response.json()["message"]["content"]

    async def generate_stream(
        self, messages: list[ChatMessage], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120.0, transport=self._transport) as client:
            async with client.stream(
                "POST", f"{self._base_url}/api/chat", json=self._payload(messages, stream=True)
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise LLMProviderError(f"Ollama error ({response.status_code}): {body.decode()}")

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = chunk.get("message", {}).get("content")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break
