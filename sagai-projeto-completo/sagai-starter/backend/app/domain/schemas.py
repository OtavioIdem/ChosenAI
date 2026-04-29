from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    session_id: uuid.UUID | None = None
    user_identifier: str | None = Field(default=None, max_length=120)


class SourceItem(BaseModel):
    title: str
    source_identifier: str
    chunk_index: int
    score: float
    excerpt: str
    metadata: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    warnings: list[str] = []
    mode: str
    session_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
    confidence_score: float
    confidence_status: Literal["high", "medium", "low"]
    knowledge_gap_id: uuid.UUID | None = None


class HealthResponse(BaseModel):
    status: str


class KnowledgeStatsResponse(BaseModel):
    sources_count: int
    chunks_count: int
    indexed_files: list[str]


class ReindexResponse(BaseModel):
    sources_indexed: int
    chunks_indexed: int
    indexed_files: list[str]


class FeedbackRequest(BaseModel):
    message_id: uuid.UUID
    rating: Literal["useful", "not_useful", "incomplete", "incorrect", "bad_source", "needs_adjustment"]
    comment: str | None = Field(default=None, max_length=2000)
    created_by: str | None = Field(default=None, max_length=120)
    create_training_candidate: bool = True


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    rating: str
    comment: str | None
    created_by: str | None
    training_candidate_id: uuid.UUID | None = None
    created_at: datetime


class KnowledgeGapItem(BaseModel):
    id: uuid.UUID
    question: str
    module: str | None
    reason: str
    status: str
    session_id: uuid.UUID | None
    message_id: uuid.UUID | None
    metadata: dict[str, Any]
    created_at: datetime
    resolved_at: datetime | None


class ResolveKnowledgeGapRequest(BaseModel):
    status: Literal["reviewing", "resolved", "ignored"] = "resolved"


class TrainingCandidateItem(BaseModel):
    id: uuid.UUID
    question: str
    generated_answer: str
    corrected_answer: str | None
    source_type: str
    source_url: str | None
    source_title: str | None
    source_content: str | None
    suggested_module: str | None
    suggested_keywords: list[str]
    confidence_score: float | None
    status: str
    reviewed_by: str | None
    reviewed_at: datetime | None
    message_id: uuid.UUID | None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TrainingCandidateUpdateRequest(BaseModel):
    corrected_answer: str | None = None
    suggested_module: str | None = None
    suggested_keywords: list[str] | None = None
    source_title: str | None = None
    source_content: str | None = None
    status: Literal["pending", "edited", "approved", "rejected", "indexed"] | None = None


class ReviewTrainingCandidateRequest(BaseModel):
    reviewed_by: str | None = Field(default=None, max_length=120)


class AutoApproveTrainingCandidatesRequest(BaseModel):
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reviewed_by: str | None = Field(default="auto-approve", max_length=120)
    limit: int = Field(default=100, ge=1, le=1000)


class AutoApproveTrainingCandidatesResponse(BaseModel):
    threshold: float
    approved_count: int
    skipped_count: int
    indexed_candidates: list[TrainingCandidateItem]
    skipped_candidates: list[dict[str, Any]]
