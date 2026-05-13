from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.infra.db.models import KnowledgeChunk, KnowledgeSource


@dataclass(slots=True)
class RetrievalCandidate:
    """Internal candidate used before producing LLM context."""

    chunk: KnowledgeChunk
    source: KnowledgeSource
    vector_score: float = 0.0
    lexical_score: float = 0.0
    metadata_score: float = 0.0
    rerank_score: float = 0.0
    final_score: float = 0.0
    match_types: set[str] = field(default_factory=set)
    rank_reasons: list[str] = field(default_factory=list)

    @property
    def chunk_id(self) -> str:
        return str(self.chunk.id)

    def score_details(self) -> dict[str, Any]:
        return {
            "vector_score": round(self.vector_score, 4),
            "lexical_score": round(self.lexical_score, 4),
            "metadata_score": round(self.metadata_score, 4),
            "rerank_score": round(self.rerank_score, 4),
            "final_score": round(self.final_score, 4),
            "match_types": sorted(self.match_types),
            "rank_reasons": self.rank_reasons,
        }


@dataclass(frozen=True, slots=True)
class RetrievalTelemetry:
    strategy: str
    vector_candidates: int
    lexical_candidates: int
    merged_candidates: int
    returned_contexts: int
    duration_ms: int
    score_min: float | None
    score_max: float | None
    score_avg: float | None
