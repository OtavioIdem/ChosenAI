from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.application.services.embeddings import EmbeddingProviderError, build_embedding_provider
from app.application.services.evaluation.dataset_loader import RagEvalCase, RagEvalDataset
from app.application.services.evaluation.metrics import (
    RetrievedReference,
    average,
    first_relevant_rank,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.application.services.retrieval.hybrid_retriever import HybridRetriever
from app.config.settings import Settings, get_settings
from app.infra.llm.base import RetrievedContext
from app.infra.repositories.knowledge_repository import KnowledgeRepository


@dataclass(frozen=True)
class RagEvalCaseResult:
    id: str
    question: str
    expected_no_context: bool
    retrieved: list[RetrievedReference]
    precision_at_1: float
    precision_at_3: float
    recall_at_5: float
    reciprocal_rank: float
    first_relevant_rank: int | None
    top_score: float | None
    latency_ms: int
    telemetry: dict[str, Any]
    embedding_error: str | None = None

    @property
    def no_context(self) -> bool:
        return not self.retrieved

    @property
    def no_relevant_context(self) -> bool:
        return self.first_relevant_rank is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "expected_no_context": self.expected_no_context,
            "retrieved": [
                {
                    "source_identifier": item.source_identifier,
                    "source_file": item.source_file,
                    "score": round(item.score, 4),
                }
                for item in self.retrieved
            ],
            "precision_at_1": round(self.precision_at_1, 4),
            "precision_at_3": round(self.precision_at_3, 4),
            "recall_at_5": round(self.recall_at_5, 4),
            "reciprocal_rank": round(self.reciprocal_rank, 4),
            "first_relevant_rank": self.first_relevant_rank,
            "top_score": round(self.top_score, 4) if self.top_score is not None else None,
            "latency_ms": self.latency_ms,
            "telemetry": self.telemetry,
            "embedding_error": self.embedding_error,
        }


@dataclass(frozen=True)
class RagEvaluationReport:
    dataset_name: str
    dataset_version: str
    generated_at: datetime
    top_k: int
    cases: list[RagEvalCaseResult]

    @property
    def metrics(self) -> dict[str, float | int]:
        total = len(self.cases)
        if total == 0:
            return {
                "total_questions": 0,
                "precision_at_1": 0.0,
                "precision_at_3": 0.0,
                "recall_at_5": 0.0,
                "mean_reciprocal_rank": 0.0,
                "no_context_rate": 0.0,
                "no_relevant_context_rate": 0.0,
                "expected_no_context_accuracy": 0.0,
                "avg_retrieval_score": 0.0,
                "avg_latency_ms": 0.0,
            }

        no_context_cases = [case for case in self.cases if case.no_context]
        no_relevant_cases = [case for case in self.cases if case.no_relevant_context]
        expected_no_context_cases = [case for case in self.cases if case.expected_no_context]
        expected_no_context_hits = [
            case for case in expected_no_context_cases if case.no_relevant_context
        ]
        scores = [case.top_score for case in self.cases if case.top_score is not None]

        return {
            "total_questions": total,
            "precision_at_1": average([case.precision_at_1 for case in self.cases]),
            "precision_at_3": average([case.precision_at_3 for case in self.cases]),
            "recall_at_5": average([case.recall_at_5 for case in self.cases]),
            "mean_reciprocal_rank": average([case.reciprocal_rank for case in self.cases]),
            "no_context_rate": len(no_context_cases) / total,
            "no_relevant_context_rate": len(no_relevant_cases) / total,
            "expected_no_context_accuracy": (
                len(expected_no_context_hits) / len(expected_no_context_cases)
                if expected_no_context_cases
                else 0.0
            ),
            "avg_retrieval_score": average([float(score) for score in scores]),
            "avg_latency_ms": average([float(case.latency_ms) for case in self.cases]),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "dataset_version": self.dataset_version,
            "generated_at": self.generated_at.isoformat(),
            "top_k": self.top_k,
            "metrics": self.metrics,
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_markdown(self) -> str:
        metrics = self.metrics
        lines = [
            f"# RAG Evaluation - {self.dataset_name}",
            "",
            f"- Dataset version: `{self.dataset_version}`",
            f"- Generated at: `{self.generated_at.isoformat()}`",
            f"- Top K: `{self.top_k}`",
            "",
            "## Metrics",
            "",
        ]
        for key, value in metrics.items():
            rendered = f"{value:.4f}" if isinstance(value, float) else str(value)
            lines.append(f"- `{key}`: {rendered}")

        lines.extend(["", "## Questions", ""])
        for case in self.cases:
            lines.extend(
                [
                    f"### {case.id}",
                    "",
                    f"- Question: {case.question}",
                    f"- First relevant rank: {case.first_relevant_rank or 'not_found'}",
                    f"- Precision@1: {case.precision_at_1:.4f}",
                    f"- Precision@3: {case.precision_at_3:.4f}",
                    f"- Recall@5: {case.recall_at_5:.4f}",
                    f"- MRR contribution: {case.reciprocal_rank:.4f}",
                    f"- Top score: {case.top_score:.4f}" if case.top_score is not None else "- Top score: n/a",
                    f"- Latency ms: {case.latency_ms}",
                ]
            )
            if case.embedding_error:
                lines.append(f"- Embedding error: {case.embedding_error}")
            lines.append("- Retrieved sources:")
            if not case.retrieved:
                lines.append("  - none")
            for item in case.retrieved:
                source_file = item.source_file or "unknown_file"
                lines.append(f"  - `{item.source_identifier}` (`{source_file}`), score `{item.score:.4f}`")
            lines.append("")
        return "\n".join(lines).strip() + "\n"


class RagEvaluator:
    def __init__(
        self,
        *,
        retriever: HybridRetriever,
        embedding_provider: Any,
        settings: Settings,
    ) -> None:
        self.retriever = retriever
        self.embedding_provider = embedding_provider
        self.settings = settings

    @classmethod
    def from_session(cls, session: Session, settings: Settings | None = None) -> "RagEvaluator":
        settings = settings or get_settings()
        repository = KnowledgeRepository(session)
        return cls(
            retriever=HybridRetriever(repository, settings),
            embedding_provider=build_embedding_provider(settings),
            settings=settings,
        )

    async def evaluate_dataset(
        self,
        dataset: RagEvalDataset,
        *,
        top_k: int | None = None,
    ) -> RagEvaluationReport:
        effective_top_k = top_k or dataset.top_k
        cases = [await self.evaluate_case(case, top_k=effective_top_k) for case in dataset.questions]
        return RagEvaluationReport(
            dataset_name=dataset.name,
            dataset_version=dataset.version,
            generated_at=datetime.now(UTC),
            top_k=effective_top_k,
            cases=cases,
        )

    async def evaluate_case(self, case: RagEvalCase, *, top_k: int) -> RagEvalCaseResult:
        started_at = perf_counter()
        embedding_error = None
        query_embedding = None
        try:
            query_embedding = await self.embedding_provider.embed_text(case.question)
        except EmbeddingProviderError as exc:
            embedding_error = type(exc).__name__

        contexts = self.retriever.retrieve(
            query=case.question,
            query_embedding=query_embedding,
            top_k=top_k,
        )
        latency_ms = int((perf_counter() - started_at) * 1000)
        retrieved = [_context_to_reference(context) for context in contexts]
        expected_keys = case.expected_keys
        telemetry = _telemetry_to_dict(getattr(self.retriever, "last_telemetry", None))

        return RagEvalCaseResult(
            id=case.id,
            question=case.question,
            expected_no_context=case.expected_no_context,
            retrieved=retrieved,
            precision_at_1=precision_at_k(retrieved, expected_keys, 1),
            precision_at_3=precision_at_k(retrieved, expected_keys, 3),
            recall_at_5=recall_at_k(retrieved, expected_keys, 5),
            reciprocal_rank=reciprocal_rank(retrieved, expected_keys),
            first_relevant_rank=first_relevant_rank(retrieved, expected_keys),
            top_score=max((item.score for item in retrieved), default=None),
            latency_ms=latency_ms,
            telemetry=telemetry,
            embedding_error=embedding_error,
        )


def _context_to_reference(context: RetrievedContext) -> RetrievedReference:
    metadata = context.metadata or {}
    return RetrievedReference(
        source_identifier=context.source_identifier,
        source_file=metadata.get("file"),
        score=context.score,
    )


def _telemetry_to_dict(telemetry: Any) -> dict[str, Any]:
    if telemetry is None:
        return {}
    return {
        "strategy": getattr(telemetry, "strategy", None),
        "vector_candidates": getattr(telemetry, "vector_candidates", None),
        "lexical_candidates": getattr(telemetry, "lexical_candidates", None),
        "merged_candidates": getattr(telemetry, "merged_candidates", None),
        "returned_contexts": getattr(telemetry, "returned_contexts", None),
        "duration_ms": getattr(telemetry, "duration_ms", None),
        "score_min": getattr(telemetry, "score_min", None),
        "score_max": getattr(telemetry, "score_max", None),
        "score_avg": getattr(telemetry, "score_avg", None),
    }
