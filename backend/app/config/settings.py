from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
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

    # Legacy embedding dimension kept for the old knowledge_chunks.embedding column.
    # New retrieval/indexing code writes real embeddings to knowledge_chunks.embedding_v2.
    vector_dimensions: int = 256

    embeddings_provider: str = "hash"
    embeddings_model: str = "embeddinggemma"
    embeddings_base_url: str = "http://host.docker.internal:11434"
    embeddings_timeout_seconds: int = 120
    embeddings_vector_dimensions: int = Field(default=256)
    embeddings_batch_size: int = 16
    embeddings_fallback_provider: str = "hash"
    embeddings_enable_fallback: bool = True

    retrieval_top_k: int = 5
    retrieval_strategy: str = "hybrid"
    retrieval_candidate_multiplier: int = 4
    retrieval_vector_weight: float = 0.65
    retrieval_lexical_weight: float = 0.25
    retrieval_metadata_weight: float = 0.10
    retrieval_min_score: float = 0.12
    retrieval_enable_reranking: bool = True
    retrieval_lexical_language: str = "portuguese"
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

    @field_validator("vector_dimensions", "embeddings_vector_dimensions")
    @classmethod
    def validate_vector_dimensions(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Embedding dimensions must be greater than 0")
        return value

    @field_validator("embeddings_timeout_seconds")
    @classmethod
    def validate_embeddings_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("EMBEDDINGS_TIMEOUT_SECONDS must be greater than 0")
        return value

    @field_validator("embeddings_batch_size", "retrieval_candidate_multiplier")
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Configured integer values must be greater than 0")
        return value

    @field_validator("retrieval_vector_weight", "retrieval_lexical_weight", "retrieval_metadata_weight", "retrieval_min_score")
    @classmethod
    def validate_retrieval_float(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Retrieval float settings cannot be negative")
        return value

    @field_validator("retrieval_strategy")
    @classmethod
    def validate_retrieval_strategy(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"vector", "lexical", "hybrid"}:
            raise ValueError("RETRIEVAL_STRATEGY must be vector, lexical or hybrid")
        return normalized

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
