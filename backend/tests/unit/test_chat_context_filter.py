from types import SimpleNamespace

from app.application.services.chat_service import ChatService
from app.infra.llm.base import RetrievedContext


def _service() -> ChatService:
    service = object.__new__(ChatService)
    service.settings = SimpleNamespace(confidence_threshold_medium=0.70)
    return service


def _context(score: float, retrieval: dict) -> RetrievedContext:
    return RetrievedContext(
        title="Fonte",
        source_identifier="test/source.json",
        chunk_index=0,
        content="Conteudo de teste",
        score=score,
        metadata={"retrieval": retrieval},
    )


def test_filter_discards_weak_vector_only_contexts():
    contexts = [
        _context(0.28, {"vector_score": 0.43, "lexical_score": 0.0, "metadata_score": 0.0, "rerank_score": 0.0})
    ]

    filtered, was_filtered = _service()._filter_contexts_for_answer(contexts)

    assert filtered == []
    assert was_filtered is True


def test_filter_keeps_low_contexts_with_lexical_signal():
    contexts = [
        _context(0.53, {"vector_score": 0.35, "lexical_score": 1.0, "metadata_score": 0.0, "rerank_score": 0.5})
    ]

    filtered, was_filtered = _service()._filter_contexts_for_answer(contexts)

    assert filtered == contexts
    assert was_filtered is False


def test_filter_keeps_high_score_vector_contexts():
    contexts = [
        _context(0.78, {"vector_score": 0.78, "lexical_score": 0.0, "metadata_score": 0.0, "rerank_score": 0.0})
    ]

    filtered, was_filtered = _service()._filter_contexts_for_answer(contexts)

    assert filtered == contexts
    assert was_filtered is False
