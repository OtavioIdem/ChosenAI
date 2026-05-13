from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RagEvalCase:
    id: str
    question: str
    expected_source_identifiers: tuple[str, ...] = ()
    expected_source_files: tuple[str, ...] = ()
    expected_no_context: bool = False
    notes: str | None = None

    @property
    def expected_keys(self) -> set[str]:
        keys = {f"id:{value}" for value in self.expected_source_identifiers}
        keys.update(f"file:{value}" for value in self.expected_source_files)
        return keys


@dataclass(frozen=True)
class RagEvalDataset:
    name: str
    version: str
    top_k: int = 5
    questions: tuple[RagEvalCase, ...] = field(default_factory=tuple)


def load_rag_eval_dataset(path: str | Path) -> RagEvalDataset:
    dataset_path = Path(path)
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("RAG evaluation dataset must be a JSON object.")

    questions = payload.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("RAG evaluation dataset must contain a non-empty questions list.")

    cases = tuple(_parse_case(item, index) for index, item in enumerate(questions))
    top_k = int(payload.get("top_k", 5))
    if top_k <= 0:
        raise ValueError("RAG evaluation dataset top_k must be greater than zero.")

    return RagEvalDataset(
        name=str(payload.get("name") or dataset_path.stem),
        version=str(payload.get("version") or "1.0"),
        top_k=top_k,
        questions=cases,
    )


def _parse_case(item: Any, index: int) -> RagEvalCase:
    if not isinstance(item, dict):
        raise ValueError(f"RAG evaluation question at index {index} must be an object.")

    case_id = str(item.get("id") or f"question_{index + 1}").strip()
    question = str(item.get("question") or "").strip()
    if not question:
        raise ValueError(f"RAG evaluation question {case_id!r} must include question text.")

    identifiers = _string_tuple(item.get("expected_source_identifiers", ()))
    files = _string_tuple(item.get("expected_source_files", ()))
    expected_no_context = bool(item.get("expected_no_context", False))
    if not expected_no_context and not identifiers and not files:
        raise ValueError(
            f"RAG evaluation question {case_id!r} must include expected sources or expected_no_context=true."
        )

    return RagEvalCase(
        id=case_id,
        question=question,
        expected_source_identifiers=identifiers,
        expected_source_files=files,
        expected_no_context=expected_no_context,
        notes=item.get("notes"),
    )


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError("Expected source fields must be lists of strings.")
    return tuple(str(item).strip() for item in value if str(item).strip())
