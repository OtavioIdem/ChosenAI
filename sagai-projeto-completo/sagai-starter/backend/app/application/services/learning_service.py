from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.application.services.hash_embeddings import HashEmbeddingService
from app.config.settings import get_settings
from app.core.chunking import chunk_text
from app.infra.db.models import TrainingCandidate
from app.infra.repositories.knowledge_repository import KnowledgeRepository
from app.infra.repositories.learning_repository import LearningRepository


class LearningService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.repository = LearningRepository(session)
        self.knowledge_repository = KnowledgeRepository(session)
        self.embedding_service = HashEmbeddingService(self.settings.vector_dimensions)

    def create_feedback(
        self,
        *,
        message_id: uuid.UUID,
        rating: str,
        comment: str | None,
        created_by: str | None,
        create_training_candidate: bool,
    ) -> dict[str, Any]:
        message = self.repository.get_message(message_id)
        if message is None:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada.")

        feedback = self.repository.add_feedback(
            message_id=message_id,
            rating=rating,
            comment=comment,
            created_by=created_by,
        )

        training_candidate_id = None
        if create_training_candidate and message.role == "assistant" and rating in {"useful", "incomplete", "incorrect", "needs_adjustment"}:
            question = self.repository.get_session_question_for_assistant_message(message)
            candidate = self.repository.create_training_candidate(
                question=question,
                generated_answer=message.content,
                message_id=message.id,
                source_type="internal_feedback",
                source_title="Resposta avaliada no chat interno",
                source_content=message.content,
                confidence_score=message.confidence_score,
                metadata={
                    "feedback_id": str(feedback.id),
                    "feedback_rating": rating,
                    "feedback_comment": comment,
                    "confidence_status": message.confidence_status,
                },
            )
            training_candidate_id = candidate.id

        self.session.commit()
        return {
            "id": feedback.id,
            "message_id": feedback.message_id,
            "rating": feedback.rating,
            "comment": feedback.comment,
            "created_by": feedback.created_by,
            "training_candidate_id": training_candidate_id,
            "created_at": feedback.created_at,
        }

    def list_gaps(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        gaps = self.repository.list_gaps(status=status, limit=limit)
        return [
            {
                "id": gap.id,
                "question": gap.question,
                "module": gap.module,
                "reason": gap.reason,
                "status": gap.status,
                "session_id": gap.session_id,
                "message_id": gap.message_id,
                "metadata": gap.gap_metadata,
                "created_at": gap.created_at,
                "resolved_at": gap.resolved_at,
            }
            for gap in gaps
        ]

    def resolve_gap(self, gap_id: uuid.UUID, status: str) -> dict[str, Any]:
        gap = self.repository.resolve_gap(gap_id, status)
        if gap is None:
            raise HTTPException(status_code=404, detail="Lacuna não encontrada.")
        self.session.commit()
        return {
            "id": gap.id,
            "question": gap.question,
            "module": gap.module,
            "reason": gap.reason,
            "status": gap.status,
            "session_id": gap.session_id,
            "message_id": gap.message_id,
            "metadata": gap.gap_metadata,
            "created_at": gap.created_at,
            "resolved_at": gap.resolved_at,
        }

    def list_training_candidates(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        candidates = self.repository.list_training_candidates(status=status, limit=limit)
        return [self._candidate_to_dict(candidate) for candidate in candidates]

    def update_training_candidate(self, candidate_id: uuid.UUID, data: dict[str, Any]) -> dict[str, Any]:
        candidate = self.repository.update_training_candidate(candidate_id, data)
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidato de treinamento não encontrado.")
        self.session.commit()
        return self._candidate_to_dict(candidate)

    def review_training_candidate(self, candidate_id: uuid.UUID, status: str, reviewed_by: str | None) -> dict[str, Any]:
        candidate = self.repository.review_training_candidate(candidate_id, status, reviewed_by)
        if candidate is None:
            raise HTTPException(status_code=404, detail="Candidato de treinamento não encontrado.")

        if status == "approved":
            self._index_training_candidate(candidate)

        self.session.commit()
        return self._candidate_to_dict(candidate)

    def auto_approve_training_candidates(
        self,
        *,
        min_confidence: float | None,
        reviewed_by: str | None,
        limit: int,
    ) -> dict[str, Any]:
        threshold = min_confidence if min_confidence is not None else self.settings.training_auto_approve_min_confidence
        candidates = self.repository.list_auto_approvable_candidates(
            min_confidence=threshold,
            limit=limit,
        )

        indexed: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []

        for candidate in candidates:
            try:
                candidate.status = "approved"
                candidate.reviewed_by = reviewed_by or "auto-approve"
                self._index_training_candidate(candidate)
                indexed.append(self._candidate_to_dict(candidate))
            except Exception as exc:  # mantém o lote rodando mesmo se 1 candidato estiver inválido
                skipped.append({
                    "id": candidate.id,
                    "reason": str(exc),
                })

        self.session.commit()

        return {
            "threshold": threshold,
            "approved_count": len(indexed),
            "skipped_count": len(skipped),
            "indexed_candidates": indexed,
            "skipped_candidates": skipped,
        }

    def _index_training_candidate(self, candidate: TrainingCandidate) -> None:
        content = self._build_training_content(candidate)
        if not content.strip():
            raise HTTPException(status_code=400, detail="Candidato aprovado não possui conteúdo para indexação.")

        source_identifier = f"training_candidate::{candidate.id}"
        title = self._build_training_title(candidate)
        category = candidate.suggested_module or "aprendizado_supervisionado"
        source_file = f"training/candidates/{candidate.id}.sagai.json"

        metadata = {
            "file": source_file,
            "source_type": "training_candidate",
            "candidate_id": str(candidate.id),
            "message_id": str(candidate.message_id) if candidate.message_id else None,
            "question": candidate.question,
            "source_url": candidate.source_url,
            "source_title": candidate.source_title,
            "suggested_module": candidate.suggested_module,
            "suggested_keywords": candidate.suggested_keywords or [],
            "confidence_score": candidate.confidence_score,
            "reviewed_by": candidate.reviewed_by,
        }

        source = self.knowledge_repository.upsert_source(
            source_identifier=source_identifier,
            title=title,
            category=category,
            metadata=metadata,
        )

        chunks = chunk_text(
            text=content,
            max_chunk_size=self.settings.max_chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )

        chunks_indexed = 0
        for chunk_index, chunk_content in enumerate(chunks):
            embedding = self.embedding_service.embed_text(chunk_content)
            self.knowledge_repository.add_chunk(
                source=source,
                chunk_index=chunk_index,
                content=chunk_content,
                embedding=embedding,
                metadata=metadata,
            )
            chunks_indexed += 1

        self.repository.mark_training_candidate_indexed(
            candidate,
            metadata={
                "indexed": True,
                "knowledge_source_identifier": source_identifier,
                "knowledge_source_id": str(source.id),
                "chunks_indexed": chunks_indexed,
                "index_file": source_file,
            },
        )

    @staticmethod
    def _build_training_title(candidate: TrainingCandidate) -> str:
        if candidate.source_title:
            return candidate.source_title[:255]
        question = (candidate.question or "Treinamento aprovado").strip().replace("\n", " ")
        return f"Treinamento aprovado: {question[:210]}"

    @staticmethod
    def _build_training_content(candidate: TrainingCandidate) -> str:
        approved_answer = candidate.corrected_answer or candidate.generated_answer
        parts = [
            "Tipo de conteúdo: treinamento supervisionado aprovado.",
            f"Pergunta original: {candidate.question}",
            f"Resposta aprovada: {approved_answer}",
        ]

        if candidate.source_content and candidate.source_content.strip() != approved_answer.strip():
            parts.append(f"Conteúdo de referência: {candidate.source_content}")

        if candidate.source_url:
            parts.append(f"URL da fonte: {candidate.source_url}")

        if candidate.suggested_module:
            parts.append(f"Módulo sugerido: {candidate.suggested_module}")

        if candidate.suggested_keywords:
            parts.append("Palavras-chave: " + ", ".join(candidate.suggested_keywords))

        return "\n\n".join(part for part in parts if part)

    @staticmethod
    def _candidate_to_dict(candidate) -> dict[str, Any]:
        return {
            "id": candidate.id,
            "question": candidate.question,
            "generated_answer": candidate.generated_answer,
            "corrected_answer": candidate.corrected_answer,
            "source_type": candidate.source_type,
            "source_url": candidate.source_url,
            "source_title": candidate.source_title,
            "source_content": candidate.source_content,
            "suggested_module": candidate.suggested_module,
            "suggested_keywords": candidate.suggested_keywords,
            "confidence_score": candidate.confidence_score,
            "status": candidate.status,
            "reviewed_by": candidate.reviewed_by,
            "reviewed_at": candidate.reviewed_at,
            "message_id": candidate.message_id,
            "metadata": candidate.candidate_metadata,
            "created_at": candidate.created_at,
            "updated_at": candidate.updated_at,
        }
