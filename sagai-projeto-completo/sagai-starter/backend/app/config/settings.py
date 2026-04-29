from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SAGAI API"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+psycopg://sagai:change_this_password@postgres:5432/sagai"
    cors_allowed_origins: str = "http://localhost:3000"

    knowledge_dir: Path = Path("/app/knowledge")
    prompt_file: Path = Path("/app/knowledge/prompt/system_prompt.md")

    embeddings_provider: str = "hash"
    vector_dimensions: int = 256
    retrieval_top_k: int = 5
    confidence_threshold_high: float = 0.85
    confidence_threshold_medium: float = 0.70
    training_auto_approve_min_confidence: float = 0.60
    max_chunk_size: int = 1000
    chunk_overlap: int = 150

    llm_provider: str = "mock"
    llm_model: str = "qwen2.5:7b-instruct"
    llm_base_url: str = "http://host.docker.internal:11434"
    llm_api_key: str | None = None
    llm_timeout_seconds: int = 60

    admin_api_key: str = "change_this_admin_key"

    @field_validator("vector_dimensions")
    @classmethod
    def validate_vector_dimensions(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("VECTOR_DIMENSIONS must be greater than 0")
        return value

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, value: int) -> int:
        if value < 0:
            raise ValueError("CHUNK_OVERLAP cannot be negative")
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
