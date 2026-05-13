from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from time import perf_counter

from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.application.services.embeddings.hash_provider import HashEmbeddingProvider
from app.application.services.retrieval.query_analyzer import extract_query_terms
from app.config.settings import get_settings
from app.infra.db.models import KnowledgeChunk, KnowledgeSource

logger = logging.getLogger(__name__)


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self._legacy_hash_provider = HashEmbeddingProvider(dimensions=self.settings.vector_dimensions)

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
        legacy_embedding: list[float] | None = None,
    ) -> KnowledgeChunk:
        preview = content[:300].replace("\n", " ").strip()
        chunk = KnowledgeChunk(
            source_id=source.id,
            chunk_index=chunk_index,
            content=content,
            content_preview=preview,
            embedding=legacy_embedding or self._legacy_hash_provider._embed_text_sync(content),
            embedding_v2=embedding,
            chunk_metadata=metadata,
            token_estimate=max(1, len(content.split())),
        )
        self.session.add(chunk)
        return chunk

    def search_chunks_vector(self, query_embedding: list[float], limit: int) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        started_at = perf_counter()
        distance = KnowledgeChunk.embedding_v2.cosine_distance(query_embedding)

        rows: Sequence[tuple[KnowledgeChunk, KnowledgeSource, float]] = self.session.execute(
            select(KnowledgeChunk, KnowledgeSource, distance.label("distance"))
            .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
            .where(KnowledgeChunk.embedding_v2.is_not(None))
            .order_by(distance.asc())
            .limit(limit)
        ).all()

        duration_ms = int((perf_counter() - started_at) * 1000)
        distances = [float(distance_value) for _, _, distance_value in rows if distance_value is not None]
        scores = [max(0.0, min(1.0, 1.0 - value)) for value in distances]
        logger.info(
            "vector_search_completed",
            extra={
                "duration_ms": duration_ms,
                "top_k": limit,
                "results_count": len(rows),
                "score_min": min(scores) if scores else None,
                "score_max": max(scores) if scores else None,
                "score_avg": (sum(scores) / len(scores)) if scores else None,
            },
        )

        return [(chunk, source, float(distance_value)) for chunk, source, distance_value in rows]

    def search_chunks(self, query_embedding: list[float], limit: int) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        # Backward compatible alias used by older tests or integrations.
        return self.search_chunks_vector(query_embedding, limit)

    def search_chunks_lexical(
        self,
        *,
        query_text: str,
        limit: int,
        language: str = "portuguese",
    ) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        terms = extract_query_terms(query_text)
        if not terms:
            return []

        started_at = perf_counter()
        try:
            rows = self._search_chunks_full_text(query_text=query_text, limit=limit, language=language)
        except Exception as exc:  # pragma: no cover - mostly used when DB is not PostgreSQL.
            logger.warning(
                "full_text_search_failed_using_ilike_fallback",
                extra={"error_type": type(exc).__name__, "terms_count": len(terms)},
            )
            rows = self._search_chunks_ilike(terms=terms, limit=limit)

        duration_ms = int((perf_counter() - started_at) * 1000)
        ranks = [rank for _, _, rank in rows]
        logger.info(
            "lexical_search_completed",
            extra={
                "duration_ms": duration_ms,
                "top_k": limit,
                "results_count": len(rows),
                "rank_min": min(ranks) if ranks else None,
                "rank_max": max(ranks) if ranks else None,
                "rank_avg": (sum(ranks) / len(ranks)) if ranks else None,
                "terms_count": len(terms),
            },
        )
        return rows

    def _search_chunks_full_text(
        self,
        *,
        query_text: str,
        limit: int,
        language: str,
    ) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        if self.session.bind is None or self.session.bind.dialect.name != "postgresql":
            raise RuntimeError("full text search is only enabled for PostgreSQL")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", language):
            language = "portuguese"

        sql = text(
            f"""
            SELECT
                kc.id AS chunk_id,
                ts_rank_cd(
                    to_tsvector('{language}',
                        coalesce(kc.content, '') || ' ' ||
                        coalesce(ks.title, '') || ' ' ||
                        coalesce(ks.category, '') || ' ' ||
                        coalesce(kc.metadata::text, '')
                    ),
                    plainto_tsquery('{language}', :query_text)
                ) AS rank
            FROM knowledge_chunks kc
            JOIN knowledge_sources ks ON ks.id = kc.source_id
            WHERE to_tsvector('{language}',
                        coalesce(kc.content, '') || ' ' ||
                        coalesce(ks.title, '') || ' ' ||
                        coalesce(ks.category, '') || ' ' ||
                        coalesce(kc.metadata::text, '')
                  ) @@ plainto_tsquery('{language}', :query_text)
            ORDER BY rank DESC, kc.created_at DESC
            LIMIT :limit
            """
        )
        raw_rows = self.session.execute(sql, {"query_text": query_text, "limit": limit}).all()
        return self._hydrate_ranked_chunk_rows([(row.chunk_id, float(row.rank or 0.0)) for row in raw_rows])

    def _search_chunks_ilike(
        self,
        *,
        terms: list[str],
        limit: int,
    ) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        clauses = []
        for term in terms[:8]:
            like = f"%{term}%"
            clauses.extend([
                KnowledgeChunk.content.ilike(like),
                KnowledgeSource.title.ilike(like),
                KnowledgeSource.category.ilike(like),
            ])

        if not clauses:
            return []

        rows: Sequence[tuple[KnowledgeChunk, KnowledgeSource]] = self.session.execute(
            select(KnowledgeChunk, KnowledgeSource)
            .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
            .where(or_(*clauses))
            .limit(limit)
        ).all()

        scored: list[tuple[KnowledgeChunk, KnowledgeSource, float]] = []
        for chunk, source in rows:
            text_value = f"{source.title} {source.category} {chunk.content}".lower()
            matches = sum(1 for term in terms if term.lower() in text_value)
            scored.append((chunk, source, matches / max(len(terms), 1)))
        return sorted(scored, key=lambda item: item[2], reverse=True)[:limit]

    def _hydrate_ranked_chunk_rows(
        self,
        ranked_rows: list[tuple[object, float]],
    ) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        if not ranked_rows:
            return []
        ids = [chunk_id for chunk_id, _ in ranked_rows]
        rank_by_id = {str(chunk_id): rank for chunk_id, rank in ranked_rows}
        entities: Sequence[tuple[KnowledgeChunk, KnowledgeSource]] = self.session.execute(
            select(KnowledgeChunk, KnowledgeSource)
            .join(KnowledgeSource, KnowledgeSource.id == KnowledgeChunk.source_id)
            .where(KnowledgeChunk.id.in_(ids))
        ).all()
        by_id = {str(chunk.id): (chunk, source) for chunk, source in entities}
        results: list[tuple[KnowledgeChunk, KnowledgeSource, float]] = []
        for chunk_id, rank in ranked_rows:
            pair = by_id.get(str(chunk_id))
            if pair is None:
                continue
            results.append((pair[0], pair[1], float(rank_by_id[str(chunk_id)])))
        return results

    def stats(self) -> dict:
        sources_count = self.session.query(func.count(KnowledgeSource.id)).scalar() or 0
        chunks_count = self.session.query(func.count(KnowledgeChunk.id)).scalar() or 0
        chunks_with_embedding_v2 = (
            self.session.query(func.count(KnowledgeChunk.id))
            .filter(KnowledgeChunk.embedding_v2.is_not(None))
            .scalar()
            or 0
        )

        files = self.session.execute(
            select(KnowledgeSource.source_metadata["file"].astext).distinct()
        ).scalars().all()

        return {
            "sources_count": int(sources_count),
            "chunks_count": int(chunks_count),
            "chunks_with_embedding_v2": int(chunks_with_embedding_v2),
            "indexed_files": sorted([file_name for file_name in files if file_name]),
        }
