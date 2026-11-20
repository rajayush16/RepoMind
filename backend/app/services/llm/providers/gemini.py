import json
from collections.abc import AsyncIterator

import httpx

from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-1.5-flash"


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL, transport: httpx.BaseTransport | None = None
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._transport = transport

    @staticmethod
    def _to_contents(messages: list[ChatMessage]) -> tuple[dict | None, list[dict]]:
        system_parts = [m.content for m in messages if m.role == "system"]
        system = {"parts": [{"text": "\n".join(system_parts)}]} if system_parts else None
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
            if m.role != "system"
        ]
        return system, contents

    def _payload(self, messages: list[ChatMessage], max_tokens: int) -> dict:
        system, contents = self._to_contents(messages)
        payload = {"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens}}
        if system:
            payload["systemInstruction"] = system
        return payload

    async def generate(self, messages: list[ChatMessage], *, max_tokens: int = 1024) -> str:
        url = f"{API_BASE}/{self.model}:generateContent?key={self._api_key}"
        async with httpx.AsyncClient(timeout=60.0, transport=self._transport) as client:
            response = await client.post(url, json=self._payload(messages, max_tokens))
        if response.status_code != 200:
            raise LLMProviderError(f"Gemini API error ({response.status_code}): {response.text}")
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts)

    async def generate_stream(
        self, messages: list[ChatMessage], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        url = f"{API_BASE}/{self.model}:streamGenerateContent?alt=sse&key={self._api_key}"
        async with httpx.AsyncClient(timeout=60.0, transport=self._transport) as client:
            async with client.stream("POST", url, json=self._payload(messages, max_tokens)) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise LLMProviderError(f"Gemini API error ({response.status_code}): {body.decode()}")

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        chunk = json.loads(line.removeprefix("data: ").strip())
                        parts = chunk["candidates"][0]["content"]["parts"]
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    for part in parts:
                        text = part.get("text")
                        if text:
                            yield text
