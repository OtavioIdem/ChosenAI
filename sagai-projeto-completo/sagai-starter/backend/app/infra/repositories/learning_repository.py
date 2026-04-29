from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infra.db.models import (
    ChatMessageModel,
    ChatSession,
    Feedback,
    KnowledgeGap,
    TrainingCandidate,
)


class LearningRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create_session(self, session_id: uuid.UUID | None, user_identifier: str | None, title: str | None) -> ChatSession:
        if session_id:
            existing = self.session.get(ChatSession, session_id)
            if existing:
                return existing

        chat_session = ChatSession(
            user_identifier=user_identifier,
            title=title,
            session_metadata={"source": "chat"},
        )
        self.session.add(chat_session)
        self.session.flush()
        return chat_session

    def add_message(
        self,
        *,
        session_id: uuid.UUID,
        role: str,
        content: str,
        confidence_score: float | None = None,
        confidence_status: str | None = None,
        mode: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessageModel:
        message = ChatMessageModel(
            session_id=session_id,
            role=role,
            content=content,
            confidence_score=confidence_score,
            confidence_status=confidence_status,
            mode=mode,
            message_metadata=metadata or {},
        )
        self.session.add(message)
        self.session.flush()
        return message

    def create_gap(
        self,
        *,
        question: str,
        reason: str,
        session_id: uuid.UUID | None,
        message_id: uuid.UUID | None,
        module: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeGap:
        gap = KnowledgeGap(
            question=question,
            module=module,
            reason=reason,
            session_id=session_id,
            message_id=message_id,
            gap_metadata=metadata or {},
        )
        self.session.add(gap)
        self.session.flush()
        return gap

    def list_gaps(self, status: str | None = None, limit: int = 100) -> list[KnowledgeGap]:
        stmt = select(KnowledgeGap).order_by(KnowledgeGap.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(KnowledgeGap.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def resolve_gap(self, gap_id: uuid.UUID, status: str) -> KnowledgeGap | None:
        gap = self.session.get(KnowledgeGap, gap_id)
        if not gap:
            return None
        gap.status = status
        gap.resolved_at = datetime.now(timezone.utc) if status in {"resolved", "ignored"} else None
        self.session.flush()
        return gap

    def add_feedback(
        self,
        *,
        message_id: uuid.UUID,
        rating: str,
        comment: str | None,
        created_by: str | None,
    ) -> Feedback:
        feedback = Feedback(
            message_id=message_id,
            rating=rating,
            comment=comment,
            created_by=created_by,
        )
        self.session.add(feedback)
        self.session.flush()
        return feedback

    def get_message(self, message_id: uuid.UUID) -> ChatMessageModel | None:
        return self.session.get(ChatMessageModel, message_id)

    def get_session_question_for_assistant_message(self, assistant_message: ChatMessageModel) -> str:
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == assistant_message.session_id)
            .where(ChatMessageModel.role == "user")
            .where(ChatMessageModel.created_at <= assistant_message.created_at)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(1)
        )
        user_message = self.session.execute(stmt).scalar_one_or_none()
        return user_message.content if user_message else ""

    def create_training_candidate(
        self,
        *,
        question: str,
        generated_answer: str,
        message_id: uuid.UUID | None,
        source_type: str = "internal_feedback",
        source_title: str | None = None,
        source_content: str | None = None,
        source_url: str | None = None,
        suggested_module: str | None = None,
        suggested_keywords: list[str] | None = None,
        confidence_score: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TrainingCandidate:
        candidate = TrainingCandidate(
            question=question,
            generated_answer=generated_answer,
            message_id=message_id,
            source_type=source_type,
            source_title=source_title,
            source_content=source_content,
            source_url=source_url,
            suggested_module=suggested_module,
            suggested_keywords=suggested_keywords or [],
            confidence_score=confidence_score,
            candidate_metadata=metadata or {},
        )
        self.session.add(candidate)
        self.session.flush()
        return candidate

    def list_training_candidates(self, status: str | None = None, limit: int = 100) -> list[TrainingCandidate]:
        stmt = select(TrainingCandidate).order_by(TrainingCandidate.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(TrainingCandidate.status == status)
        return list(self.session.execute(stmt).scalars().all())

    def list_auto_approvable_candidates(
        self,
        *,
        min_confidence: float,
        limit: int = 100,
        statuses: tuple[str, ...] = ("pending", "edited"),
    ) -> list[TrainingCandidate]:
        stmt = (
            select(TrainingCandidate)
            .where(TrainingCandidate.status.in_(statuses))
            .where(TrainingCandidate.confidence_score.isnot(None))
            .where(TrainingCandidate.confidence_score >= min_confidence)
            .order_by(TrainingCandidate.confidence_score.desc(), TrainingCandidate.created_at.asc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def update_training_candidate(self, candidate_id: uuid.UUID, data: dict[str, Any]) -> TrainingCandidate | None:
        candidate = self.session.get(TrainingCandidate, candidate_id)
        if not candidate:
            return None

        for key, value in data.items():
            if value is not None and hasattr(candidate, key):
                setattr(candidate, key, value)

        if data:
            candidate.status = data.get("status") or "edited"
        self.session.flush()
        return candidate

    def review_training_candidate(self, candidate_id: uuid.UUID, status: str, reviewed_by: str | None) -> TrainingCandidate | None:
        candidate = self.session.get(TrainingCandidate, candidate_id)
        if not candidate:
            return None
        candidate.status = status
        candidate.reviewed_by = reviewed_by
        candidate.reviewed_at = datetime.now(timezone.utc)
        self.session.flush()
        return candidate

    def mark_training_candidate_indexed(self, candidate: TrainingCandidate, metadata: dict[str, Any]) -> TrainingCandidate:
        merged_metadata = dict(candidate.candidate_metadata or {})
        merged_metadata.update(metadata)
        candidate.candidate_metadata = merged_metadata
        candidate.status = "indexed"
        candidate.reviewed_at = candidate.reviewed_at or datetime.now(timezone.utc)
        self.session.flush()
        return candidate
