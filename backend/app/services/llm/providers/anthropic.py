import json
from collections.abc import AsyncIterator

import httpx

from app.services.llm.base import ChatMessage, LLMProvider, LLMProviderError

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(
        self, api_key: str, model: str = DEFAULT_MODEL, transport: httpx.BaseTransport | None = None
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._transport = transport

    def _headers(self) -> dict:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    @staticmethod
    def _split_system(messages: list[ChatMessage]) -> tuple[str | None, list[dict]]:
        system_parts = [m.content for m in messages if m.role == "system"]
        system = "\n".join(system_parts) if system_parts else None
        turns = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        return system, turns

    def _payload(self, messages: list[ChatMessage], max_tokens: int, stream: bool) -> dict:
        system, turns = self._split_system(messages)
        payload = {"model": self.model, "max_tokens": max_tokens, "messages": turns, "stream": stream}
        if system:
            payload["system"] = system
        return payload

    async def generate(self, messages: list[ChatMessage], *, max_tokens: int = 1024) -> str:
        async with httpx.AsyncClient(timeout=60.0, transport=self._transport) as client:
            response = await client.post(
                API_URL, headers=self._headers(), json=self._payload(messages, max_tokens, stream=False)
            )
        if response.status_code != 200:
            raise LLMProviderError(f"Anthropic API error ({response.status_code}): {response.text}")
        data = response.json()
        return "".join(block["text"] for block in data["content"] if block.get("type") == "text")

    async def generate_stream(
        self, messages: list[ChatMessage], *, max_tokens: int = 1024
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=60.0, transport=self._transport) as client:
            async with client.stream(
                "POST", API_URL, headers=self._headers(), json=self._payload(messages, max_tokens, stream=True)
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    raise LLMProviderError(f"Anthropic API error ({response.status_code}): {body.decode()}")

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line.removeprefix("data: ").strip())
                    except json.JSONDecodeError:
                        continue

                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta", {})
                        if delta.get("type") == "text_delta" and delta.get("text"):
                            yield delta["text"]
