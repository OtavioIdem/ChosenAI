from __future__ import annotations

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings
from app.infra.db.base import Base


logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def init_db() -> None:
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        ensure_pgvector_schema()


def ensure_pgvector_schema() -> None:
    """Idempotent lightweight migration for projects without Alembic yet."""

    dimensions = int(settings.embeddings_vector_dimensions)
    with engine.begin() as connection:
        connection.execute(
            text(f"ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS embedding_v2 vector({dimensions})")
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_id "
                "ON knowledge_chunks (source_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_sources_category "
                "ON knowledge_sources (category)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_sources_created_at "
                "ON knowledge_sources (created_at)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_created_at "
                "ON knowledge_chunks (created_at)"
            )
        )
        try:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_v2_hnsw "
                    "ON knowledge_chunks USING hnsw (embedding_v2 vector_cosine_ops)"
                )
            )
        except Exception as exc:  # pragma: no cover - depends on pgvector/Postgres version.
            logger.warning(
                "pgvector_hnsw_index_creation_failed",
                extra={"error_type": type(exc).__name__, "dimensions": dimensions},
            )
        try:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_content_tsv_pt "
                    "ON knowledge_chunks USING gin "
                    "(to_tsvector('portuguese', coalesce(content, '') || ' ' || coalesce(metadata::text, '')))"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_knowledge_sources_title_category_tsv_pt "
                    "ON knowledge_sources USING gin "
                    "(to_tsvector('portuguese', coalesce(title, '') || ' ' || coalesce(category, '') || ' ' || coalesce(metadata::text, '')))"
                )
            )
        except Exception as exc:  # pragma: no cover - depends on PostgreSQL language configuration.
            logger.warning(
                "full_text_index_creation_failed",
                extra={"error_type": type(exc).__name__},
            )


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
