from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    secret_key: str = "dev-only-insecure-secret-change-me"
    cors_origins: str = "http://localhost:3000"
    frontend_base_url: str = "http://localhost:3000"

    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    # Fernet key used to encrypt GitHub access tokens at rest. This dev default is
    # intentionally insecure and must be overridden in any real deployment.
    encryption_key: str = "AsWgao6SUezc8dx9TSbzoi4XJNCiQnXV3YTVirE5iiU="

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "repomind"
    postgres_user: str = "repomind"
    postgres_password: str = "change-me"
    database_url: str = (
        "postgresql+asyncpg://repomind:change-me@localhost:5432/repomind"
    )

    redis_url: str = "redis://localhost:6379/0"

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_oauth_callback_url: str | None = None
    github_app_webhook_secret: str | None = None

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    ollama_base_url: str | None = None
    default_llm_provider: str = "anthropic"
    # None means "use that provider's own default model" (see services/llm/providers/*).
    # Only set this when you want to override that default -- it is passed as-is
    # regardless of which provider is selected, so e.g. an Anthropic model name
    # here would be wrong if DEFAULT_LLM_PROVIDER=openai.
    default_llm_model: str | None = None

    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None
    otel_exporter_otlp_endpoint: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
