from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class RetrievedReference:
    source_identifier: str
    source_file: str | None = None
    score: float = 0.0

    @property
    def keys(self) -> set[str]:
        keys = {f"id:{self.source_identifier}"}
        if self.source_file:
            keys.add(f"file:{self.source_file}")
        return keys


def precision_at_k(retrieved: list[RetrievedReference], expected_keys: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero.")
    if not expected_keys:
        return 0.0
    top_items = retrieved[:k]
    relevant_count = sum(1 for item in top_items if item.keys & expected_keys)
    return relevant_count / k


def recall_at_k(retrieved: list[RetrievedReference], expected_keys: set[str], k: int) -> float:
    if k <= 0:
        raise ValueError("k must be greater than zero.")
    if not expected_keys:
        return 0.0
    matched_keys: set[str] = set()
    for item in retrieved[:k]:
        matched_keys.update(item.keys & expected_keys)
    return min(1.0, len(matched_keys) / len(expected_keys))


def reciprocal_rank(retrieved: list[RetrievedReference], expected_keys: set[str]) -> float:
    if not expected_keys:
        return 0.0
    for index, item in enumerate(retrieved, start=1):
        if item.keys & expected_keys:
            return 1.0 / index
    return 0.0


def first_relevant_rank(retrieved: list[RetrievedReference], expected_keys: set[str]) -> int | None:
    if not expected_keys:
        return None
    for index, item in enumerate(retrieved, start=1):
        if item.keys & expected_keys:
            return index
    return None


def average(values: list[float]) -> float:
    return mean(values) if values else 0.0
