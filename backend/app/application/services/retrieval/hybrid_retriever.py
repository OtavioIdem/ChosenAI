from __future__ import annotations

import logging
from time import perf_counter

from app.application.services.retrieval.models import RetrievalCandidate, RetrievalTelemetry
from app.application.services.retrieval.reranker import LightweightReranker
from app.config.settings import Settings
from app.infra.llm.base import RetrievedContext
from app.infra.repositories.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Coordinates vector, lexical and hybrid retrieval for SAGAI."""

    def __init__(self, repository: KnowledgeRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings
        self.reranker = LightweightReranker(
            vector_weight=settings.retrieval_vector_weight,
            lexical_weight=settings.retrieval_lexical_weight,
            metadata_weight=settings.retrieval_metadata_weight,
            enable_reranking=settings.retrieval_enable_reranking,
        )
        self.last_telemetry: RetrievalTelemetry | None = None

    def retrieve(
        self,
        *,
        query: str,
        query_embedding: list[float] | None,
        top_k: int,
    ) -> list[RetrievedContext]:
        started_at = perf_counter()
        strategy = self.settings.retrieval_strategy.lower().strip()
        candidate_limit = max(top_k, top_k * self.settings.retrieval_candidate_multiplier)
        merged: dict[str, RetrievalCandidate] = {}
        vector_candidates = 0
        lexical_candidates = 0

        if strategy not in {"vector", "lexical", "hybrid"}:
            logger.warning("invalid_retrieval_strategy_fallback", extra={"strategy": strategy})
            strategy = "hybrid"

        if strategy in {"vector", "hybrid"} and query_embedding is not None:
            for chunk, source, distance in self.repository.search_chunks_vector(query_embedding, candidate_limit):
                score = max(0.0, min(1.0, 1.0 - distance))
                candidate = merged.setdefault(str(chunk.id), RetrievalCandidate(chunk=chunk, source=source))
                candidate.vector_score = max(candidate.vector_score, score)
                candidate.match_types.add("vector")
                vector_candidates += 1

        if strategy in {"lexical", "hybrid"}:
            lexical_rows = self.repository.search_chunks_lexical(
                query_text=query,
                limit=candidate_limit,
                language=self.settings.retrieval_lexical_language,
            )
            max_rank = max((rank for _, _, rank in lexical_rows), default=0.0)
            for chunk, source, rank in lexical_rows:
                normalized_rank = (rank / max_rank) if max_rank > 0 else rank
                candidate = merged.setdefault(str(chunk.id), RetrievalCandidate(chunk=chunk, source=source))
                candidate.lexical_score = max(candidate.lexical_score, max(0.0, min(1.0, normalized_rank)))
                candidate.match_types.add("lexical")
                lexical_candidates += 1

        ranked = self.reranker.rerank(query, merged.values())
        min_score = self.settings.retrieval_min_score
        selected = [candidate for candidate in ranked if candidate.final_score >= min_score][:top_k]
        scores = [candidate.final_score for candidate in selected]
        duration_ms = int((perf_counter() - started_at) * 1000)
        self.last_telemetry = RetrievalTelemetry(
            strategy=strategy,
            vector_candidates=vector_candidates,
            lexical_candidates=lexical_candidates,
            merged_candidates=len(merged),
            returned_contexts=len(selected),
            duration_ms=duration_ms,
            score_min=min(scores) if scores else None,
            score_max=max(scores) if scores else None,
            score_avg=(sum(scores) / len(scores)) if scores else None,
        )
        logger.info(
            "hybrid_retrieval_completed",
            extra={
                "strategy": strategy,
                "duration_ms": duration_ms,
                "top_k": top_k,
                "candidate_limit": candidate_limit,
                "vector_candidates": vector_candidates,
                "lexical_candidates": lexical_candidates,
                "merged_candidates": len(merged),
                "returned_contexts": len(selected),
                "score_min": self.last_telemetry.score_min,
                "score_max": self.last_telemetry.score_max,
                "score_avg": self.last_telemetry.score_avg,
            },
        )
        return [self._to_context(candidate) for candidate in selected]

    def _to_context(self, candidate: RetrievalCandidate) -> RetrievedContext:
        metadata = dict(candidate.chunk.chunk_metadata or {})
        metadata["retrieval"] = {
            "strategy": self.settings.retrieval_strategy,
            **candidate.score_details(),
        }
        return RetrievedContext(
            title=candidate.source.title,
            source_identifier=candidate.source.source_identifier,
            chunk_index=candidate.chunk.chunk_index,
            content=candidate.chunk.content,
            score=candidate.final_score,
            metadata=metadata,
        )
