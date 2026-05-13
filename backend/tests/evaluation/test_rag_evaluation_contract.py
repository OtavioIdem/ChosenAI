from pathlib import Path
from types import SimpleNamespace

import pytest

from app.application.services.evaluation.dataset_loader import RagEvalCase, RagEvalDataset, load_rag_eval_dataset
from app.application.services.evaluation.metrics import (
    RetrievedReference,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.application.services.evaluation.rag_evaluator import RagEvaluator
from app.infra.llm.base import RetrievedContext


def test_load_rag_eval_dataset_fixture():
    dataset = load_rag_eval_dataset(Path(__file__).parents[1] / "fixtures" / "rag_eval_dataset.json")

    assert dataset.name == "sagai_sprint_3_seed"
    assert dataset.version == "1.0"
    assert dataset.top_k == 5
    assert len(dataset.questions) == 4
    assert dataset.questions[-1].expected_no_context is True


def test_metrics_use_expected_source_keys():
    retrieved = [
        RetrievedReference(source_identifier="json/a.sagai.json::0", source_file="json/a.sagai.json", score=0.9),
        RetrievedReference(source_identifier="json/b.sagai.json::0", source_file="json/b.sagai.json", score=0.8),
    ]
    expected = {"file:json/a.sagai.json"}

    assert precision_at_k(retrieved, expected, 1) == 1.0
    assert precision_at_k(retrieved, expected, 3) == pytest.approx(1 / 3)
    assert recall_at_k(retrieved, expected, 5) == 1.0
    assert reciprocal_rank(retrieved, expected) == 1.0


@pytest.mark.asyncio
async def test_rag_evaluator_returns_report_contract():
    dataset = RagEvalDataset(
        name="contract",
        version="1.0",
        top_k=3,
        questions=(
            RagEvalCase(
                id="alpha",
                question="Como concluir ALFA?",
                expected_source_files=("json/alpha.sagai.json",),
            ),
            RagEvalCase(
                id="negative",
                question="Pergunta sem contexto",
                expected_no_context=True,
            ),
        ),
    )
    evaluator = RagEvaluator(
        retriever=FakeRetriever(),
        embedding_provider=FakeEmbeddingProvider(),
        settings=SimpleNamespace(),
    )

    report = await evaluator.evaluate_dataset(dataset)

    assert report.metrics["total_questions"] == 2
    assert report.metrics["precision_at_1"] == 0.5
    assert report.metrics["recall_at_5"] == 0.5
    assert report.metrics["expected_no_context_accuracy"] == 1.0
    assert report.cases[0].first_relevant_rank == 1
    assert report.cases[1].no_relevant_context is True
    assert "RAG Evaluation - contract" in report.to_markdown()


class FakeEmbeddingProvider:
    async def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeRetriever:
    def __init__(self) -> None:
        self.last_telemetry = None

    def retrieve(self, *, query: str, query_embedding: list[float] | None, top_k: int) -> list[RetrievedContext]:
        self.last_telemetry = SimpleNamespace(
            strategy="hybrid",
            vector_candidates=1,
            lexical_candidates=1,
            merged_candidates=1,
            returned_contexts=1,
            duration_ms=3,
            score_min=0.9,
            score_max=0.9,
            score_avg=0.9,
        )
        if "ALFA" not in query:
            self.last_telemetry.returned_contexts = 0
            return []
        return [
            RetrievedContext(
                title="ALFA",
                source_identifier="json/alpha.sagai.json::0",
                chunk_index=0,
                content="Para concluir ALFA, use a rotina documentada.",
                score=0.9,
                metadata={"file": "json/alpha.sagai.json"},
            )
        ]
