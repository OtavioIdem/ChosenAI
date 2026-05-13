from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.services.learning_service import LearningService
from app.domain.schemas import (
    AutoApproveTrainingCandidatesRequest,
    AutoApproveTrainingCandidatesResponse,
    FeedbackRequest,
    FeedbackResponse,
    KnowledgeGapItem,
    ResolveKnowledgeGapRequest,
    ReviewTrainingCandidateRequest,
    TrainingCandidateItem,
    TrainingCandidateUpdateRequest,
)
from app.infra.db.session import get_db_session

router = APIRouter(prefix="/api/v1", tags=["learning"])


@router.post("/feedback", response_model=FeedbackResponse)
def create_feedback(
    payload: FeedbackRequest,
    session: Session = Depends(get_db_session),
) -> FeedbackResponse:
    service = LearningService(session)
    result = service.create_feedback(
        message_id=payload.message_id,
        rating=payload.rating,
        comment=payload.comment,
        created_by=payload.created_by,
        create_training_candidate=payload.create_training_candidate,
    )
    return FeedbackResponse(**result)


@router.get("/knowledge/gaps", response_model=list[KnowledgeGapItem])
def list_knowledge_gaps(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db_session),
) -> list[KnowledgeGapItem]:
    service = LearningService(session)
    return [KnowledgeGapItem(**item) for item in service.list_gaps(status=status, limit=limit)]


@router.post("/knowledge/gaps/{gap_id}/resolve", response_model=KnowledgeGapItem)
def resolve_knowledge_gap(
    gap_id: uuid.UUID,
    payload: ResolveKnowledgeGapRequest,
    session: Session = Depends(get_db_session),
) -> KnowledgeGapItem:
    service = LearningService(session)
    return KnowledgeGapItem(**service.resolve_gap(gap_id, payload.status))


@router.get("/training/candidates", response_model=list[TrainingCandidateItem])
def list_training_candidates(
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db_session),
) -> list[TrainingCandidateItem]:
    service = LearningService(session)
    return [TrainingCandidateItem(**item) for item in service.list_training_candidates(status=status, limit=limit)]


@router.post("/training/candidates/auto-approve", response_model=AutoApproveTrainingCandidatesResponse)
def auto_approve_training_candidates(
    payload: AutoApproveTrainingCandidatesRequest,
    session: Session = Depends(get_db_session),
) -> AutoApproveTrainingCandidatesResponse:
    service = LearningService(session)
    result = service.auto_approve_training_candidates(
        min_confidence=payload.min_confidence,
        reviewed_by=payload.reviewed_by,
        limit=payload.limit,
    )
    return AutoApproveTrainingCandidatesResponse(**result)


@router.put("/training/candidates/{candidate_id}", response_model=TrainingCandidateItem)
def update_training_candidate(
    candidate_id: uuid.UUID,
    payload: TrainingCandidateUpdateRequest,
    session: Session = Depends(get_db_session),
) -> TrainingCandidateItem:
    service = LearningService(session)
    data = payload.model_dump(exclude_unset=True)
    return TrainingCandidateItem(**service.update_training_candidate(candidate_id, data))


@router.post("/training/candidates/{candidate_id}/approve", response_model=TrainingCandidateItem)
def approve_training_candidate(
    candidate_id: uuid.UUID,
    payload: ReviewTrainingCandidateRequest,
    session: Session = Depends(get_db_session),
) -> TrainingCandidateItem:
    service = LearningService(session)
    return TrainingCandidateItem(**service.review_training_candidate(candidate_id, "approved", payload.reviewed_by))


@router.post("/training/candidates/{candidate_id}/reject", response_model=TrainingCandidateItem)
def reject_training_candidate(
    candidate_id: uuid.UUID,
    payload: ReviewTrainingCandidateRequest,
    session: Session = Depends(get_db_session),
) -> TrainingCandidateItem:
    service = LearningService(session)
    return TrainingCandidateItem(**service.review_training_candidate(candidate_id, "rejected", payload.reviewed_by))
