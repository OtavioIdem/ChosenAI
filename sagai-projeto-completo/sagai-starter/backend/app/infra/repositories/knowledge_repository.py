from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infra.db.models import KnowledgeChunk, KnowledgeSource


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_source(
        self,
        source_identifier: str,
        title: str,
        category: str,
        metadata: dict,
    ) -> KnowledgeSource:
        source = self.session.execute(
            select(KnowledgeSource).where(KnowledgeSource.source_identifier == source_identifier)
        ).scalar_one_or_none()

        if source is None:
            source = KnowledgeSource(
                source_identifier=source_identifier,
                title=title,
                category=category,
                source_metadata=metadata,
            )
            self.session.add(source)
            self.session.flush()
            return source

        source.title = title
        source.category = category
        source.source_metadata = metadata
        self.session.flush()

        self.session.query(KnowledgeChunk).filter(KnowledgeChunk.source_id == source.id).delete()
        self.session.flush()
        return source

    def add_chunk(
        self,
        source: KnowledgeSource,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata: dict,
    ) -> KnowledgeChunk:
        preview = content[:300].replace("\n", " ").strip()
        chunk = KnowledgeChunk(
            source_id=source.id,
            chunk_index=chunk_index,
            content=content,
            content_preview=preview,
            embedding=embedding,
            chunk_metadata=metadata,
            token_estimate=max(1, len(content.split())),
        )
        self.session.add(chunk)
        return chunk

    def search_chunks(self, query_embedding: list[float], limit: int) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)

        rows: Sequence[tuple[KnowledgeChunk, KnowledgeSource, float]] = self.session.execute(
            select(KnowledgeChunk, KnowledgeSource, distance.label("distance"))
            .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
            .order_by(distance.asc())
            .limit(limit)
        ).all()

        return [(chunk, source, float(distance_value)) for chunk, source, distance_value in rows]

    def stats(self) -> dict:
        sources_count = self.session.query(func.count(KnowledgeSource.id)).scalar() or 0
        chunks_count = self.session.query(func.count(KnowledgeChunk.id)).scalar() or 0

        files = self.session.execute(
            select(KnowledgeSource.source_metadata["file"].astext).distinct()
        ).scalars().all()

        return {
            "sources_count": int(sources_count),
            "chunks_count": int(chunks_count),
            "indexed_files": sorted([file_name for file_name in files if file_name]),
        }
