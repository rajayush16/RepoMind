import json

import httpx
import pytest

from app.core.config import Settings
from app.services.llm.base import ChatMessage, LLMProviderError
from app.services.llm.providers.anthropic import AnthropicProvider
from app.services.llm.providers.gemini import GeminiProvider
from app.services.llm.providers.ollama import OllamaProvider
from app.services.llm.providers.openai import OpenAIProvider
from app.services.llm.registry import NoProviderConfiguredError, get_llm_provider


def _sse(lines: list[str]) -> bytes:
    return ("".join(f"data: {line}\n\n" for line in lines)).encode()


@pytest.mark.asyncio
async def test_openai_generate_parses_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.openai.com/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["messages"] == [{"role": "user", "content": "hi"}]
        assert body["stream"] is False
        return httpx.Response(200, json={"choices": [{"message": {"content": "hello there"}}]})

    provider = OpenAIProvider("test-key", transport=httpx.MockTransport(handler))
    result = await provider.generate([ChatMessage(role="user", content="hi")])
    assert result == "hello there"


@pytest.mark.asyncio
async def test_openai_generate_stream_yields_deltas() -> None:
    chunks = _sse(
        [
            json.dumps({"choices": [{"delta": {"content": "Hel"}}]}),
            json.dumps({"choices": [{"delta": {"content": "lo"}}]}),
            "[DONE]",
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=chunks, headers={"content-type": "text/event-stream"})

    provider = OpenAIProvider("test-key", transport=httpx.MockTransport(handler))
    deltas = [d async for d in provider.generate_stream([ChatMessage(role="user", content="hi")])]
    assert "".join(deltas) == "Hello"


@pytest.mark.asyncio
async def test_openai_generate_raises_on_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    provider = OpenAIProvider("bad-key", transport=httpx.MockTransport(handler))
    with pytest.raises(LLMProviderError):
        await provider.generate([ChatMessage(role="user", content="hi")])


@pytest.mark.asyncio
async def test_anthropic_generate_splits_system_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        body = json.loads(request.content)
        assert body["system"] == "be nice"
        assert body["messages"] == [{"role": "user", "content": "hi"}]
        return httpx.Response(200, json={"content": [{"type": "text", "text": "hello"}]})

    provider = AnthropicProvider("test-key", transport=httpx.MockTransport(handler))
    result = await provider.generate(
        [ChatMessage(role="system", content="be nice"), ChatMessage(role="user", content="hi")]
    )
    assert result == "hello"


@pytest.mark.asyncio
async def test_anthropic_generate_stream_yields_text_deltas() -> None:
    events = _sse(
        [
            json.dumps({"type": "message_start"}),
            json.dumps({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hel"}}),
            json.dumps({"type": "content_block_delta", "delta": {"type": "text_delta", "text": "lo"}}),
            json.dumps({"type": "message_stop"}),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=events, headers={"content-type": "text/event-stream"})

    provider = AnthropicProvider("test-key", transport=httpx.MockTransport(handler))
    deltas = [d async for d in provider.generate_stream([ChatMessage(role="user", content="hi")])]
    assert "".join(deltas) == "Hello"


@pytest.mark.asyncio
async def test_gemini_generate_parses_candidate_parts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "key=test-key" in str(request.url)
        return httpx.Response(
            200, json={"candidates": [{"content": {"parts": [{"text": "hello"}]}}]}
        )

    provider = GeminiProvider("test-key", transport=httpx.MockTransport(handler))
    result = await provider.generate([ChatMessage(role="user", content="hi")])
    assert result == "hello"


@pytest.mark.asyncio
async def test_ollama_generate_parses_message_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://localhost:11434/api/chat"
        return httpx.Response(200, json={"message": {"content": "hello"}, "done": True})

    provider = OllamaProvider("http://localhost:11434", transport=httpx.MockTransport(handler))
    result = await provider.generate([ChatMessage(role="user", content="hi")])
    assert result == "hello"


@pytest.mark.asyncio
async def test_ollama_generate_stream_parses_ndjson() -> None:
    body = (
        json.dumps({"message": {"content": "Hel"}, "done": False})
        + "\n"
        + json.dumps({"message": {"content": "lo"}, "done": False})
        + "\n"
        + json.dumps({"message": {"content": ""}, "done": True})
        + "\n"
    ).encode()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    provider = OllamaProvider("http://localhost:11434", transport=httpx.MockTransport(handler))
    deltas = [d async for d in provider.generate_stream([ChatMessage(role="user", content="hi")])]
    assert "".join(deltas) == "Hello"


def test_registry_never_silently_falls_back_to_another_provider() -> None:
    settings = Settings(default_llm_provider="openai", openai_api_key=None, anthropic_api_key="has-a-key")
    with pytest.raises(NoProviderConfiguredError):
        get_llm_provider(settings)


def test_registry_resolves_configured_provider() -> None:
    settings = Settings(default_llm_provider="openai", openai_api_key="sk-test")
    provider = get_llm_provider(settings)
    assert provider.name == "openai"
