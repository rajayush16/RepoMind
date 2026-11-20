from app.core.config import Settings
from app.services.llm.base import LLMProvider
from app.services.llm.providers.anthropic import AnthropicProvider
from app.services.llm.providers.gemini import GeminiProvider
from app.services.llm.providers.ollama import OllamaProvider
from app.services.llm.providers.openai import OpenAIProvider


class NoProviderConfiguredError(Exception):
    pass


def get_llm_provider(settings: Settings) -> LLMProvider:
    """Resolve the configured provider+model. Never silently falls back to a
    different provider than the one requested -- if the preferred provider's API
    key is missing, this raises rather than guessing another one."""
    provider = settings.default_llm_provider
    model_kwargs = {"model": settings.default_llm_model} if settings.default_llm_model else {}

    if provider == "openai":
        if not settings.openai_api_key:
            raise NoProviderConfiguredError("OPENAI_API_KEY is not set.")
        return OpenAIProvider(settings.openai_api_key, **model_kwargs)

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise NoProviderConfiguredError("ANTHROPIC_API_KEY is not set.")
        return AnthropicProvider(settings.anthropic_api_key, **model_kwargs)

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise NoProviderConfiguredError("GEMINI_API_KEY is not set.")
        return GeminiProvider(settings.gemini_api_key, **model_kwargs)

    if provider == "ollama":
        if not settings.ollama_base_url:
            raise NoProviderConfiguredError("OLLAMA_BASE_URL is not set.")
        return OllamaProvider(settings.ollama_base_url, **model_kwargs)

    raise NoProviderConfiguredError(f"Unknown DEFAULT_LLM_PROVIDER: {provider!r}")
