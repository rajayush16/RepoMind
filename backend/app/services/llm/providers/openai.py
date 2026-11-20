import json
from collections.abc import AsyncIterator

import httpx

from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError

API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL, transport: httpx.BaseTransport | None = None
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._transport = transport

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def _payload(self, messages: list[ChatMessage], max_tokens: int, stream: bool) -> dict:
        return {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "stream": stream,
        }

    async def generate(self, messages: list[ChatMessage], *, max_tokens: int = 1024) -> str:
        async with httpx.AsyncClient(timeout=60.0, transport=self._transport) as client:
            response = await client.post(
                API_URL, headers=self._headers(), json=self._payload(messages, max_tokens, stream=False)
            )
        if response.status_code != 200:
            raise LLMProviderError(f"OpenAI API error ({response.status_code}): {response.text}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def generate_stream(
        self, messages: list[ChatMessage], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=60.0, transport=self._transport) as client:
            async with client.stream(
                "POST", API_URL, headers=self._headers(), json=self._payload(messages, max_tokens, stream=True)
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise LLMProviderError(f"OpenAI API error ({response.status_code}): {body.decode()}")

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line.removeprefix("data: ").strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0]["delta"].get("content")
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    if delta:
                        yield delta
