from __future__ import annotations

from collections.abc import Iterable

from app.application.services.retrieval.models import RetrievalCandidate
from app.application.services.retrieval.query_analyzer import extract_query_terms, normalize_query


def _metadata_text(candidate: RetrievalCandidate) -> str:
    metadata = candidate.chunk.chunk_metadata or {}
    values: list[str] = [candidate.source.title or "", candidate.source.category or ""]
    for key in ("module", "category", "title", "keywords", "tags", "source", "file"):
        value = metadata.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value is not None:
            values.append(str(value))
    return " ".join(values)


class LightweightReranker:
    """Deterministic and fast reranker for Sprint 2.

    This is not an LLM reranker. It combines vector similarity, lexical match and
    metadata quality with transparent weights so it is stable in tests and safe for
    local execution.
    """

    def __init__(
        self,
        *,
        vector_weight: float,
        lexical_weight: float,
        metadata_weight: float,
        enable_reranking: bool = True,
    ) -> None:
        self.vector_weight = max(0.0, vector_weight)
        self.lexical_weight = max(0.0, lexical_weight)
        self.metadata_weight = max(0.0, metadata_weight)
        self.enable_reranking = enable_reranking

    def rerank(self, query: str, candidates: Iterable[RetrievalCandidate]) -> list[RetrievalCandidate]:
        query_terms = extract_query_terms(query)
        normalized_query = normalize_query(query)

        ranked: list[RetrievalCandidate] = []
        for candidate in candidates:
            candidate.metadata_score = self._metadata_score(candidate, query_terms)
            candidate.rerank_score = self._content_overlap_score(candidate, query_terms, normalized_query)
            candidate.final_score = self._final_score(candidate)
            candidate.rank_reasons = self._rank_reasons(candidate)
            ranked.append(candidate)

        if not self.enable_reranking:
            return sorted(
                ranked,
                key=lambda item: (item.vector_score, item.lexical_score, item.metadata_score),
                reverse=True,
            )

        return sorted(ranked, key=lambda item: item.final_score, reverse=True)

    def _content_overlap_score(
        self,
        candidate: RetrievalCandidate,
        query_terms: list[str],
        normalized_query: str,
    ) -> float:
        if not query_terms:
            return 0.0
        content = normalize_query(f"{candidate.source.title} {candidate.source.category} {candidate.chunk.content}")
        matches = sum(1 for term in query_terms if term in content)
        score = matches / max(len(query_terms), 1)
        if normalized_query and normalized_query in content:
            score += 0.20
        return min(1.0, score)

    def _metadata_score(self, candidate: RetrievalCandidate, query_terms: list[str]) -> float:
        if not query_terms:
            return 0.0
        text = normalize_query(_metadata_text(candidate))
        matches = sum(1 for term in query_terms if term in text)
        return min(1.0, matches / max(len(query_terms), 1))

    def _final_score(self, candidate: RetrievalCandidate) -> float:
        weighted = (
            candidate.vector_score * self.vector_weight
            + candidate.lexical_score * self.lexical_weight
            + candidate.metadata_score * self.metadata_weight
        )
        # Small deterministic boost for direct text overlap. It helps exact process names
        # without overpowering embeddings.
        weighted += candidate.rerank_score * 0.10
        return max(0.0, min(1.0, weighted))

    def _rank_reasons(self, candidate: RetrievalCandidate) -> list[str]:
        reasons: list[str] = []
        if candidate.vector_score > 0:
            reasons.append("similaridade_vetorial")
        if candidate.lexical_score > 0:
            reasons.append("correspondencia_lexical")
        if candidate.metadata_score > 0:
            reasons.append("metadados_relevantes")
        if candidate.rerank_score >= 0.75:
            reasons.append("alta_sobreposicao_com_a_pergunta")
        return reasons
