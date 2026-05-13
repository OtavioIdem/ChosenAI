from __future__ import annotations

import logging
import uuid
from time import perf_counter

from sqlalchemy.orm import Session

from app.application.services.embeddings import EmbeddingProviderError, build_embedding_provider
from app.config.settings import get_settings
from app.application.services.retrieval.hybrid_retriever import HybridRetriever
from app.core.prompt_loader import load_system_prompt
from app.infra.llm.base import ChatMessage, RetrievedContext
from app.infra.llm.factory import build_llm_provider
from app.infra.repositories.knowledge_repository import KnowledgeRepository
from app.infra.repositories.learning_repository import LearningRepository

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.repository = KnowledgeRepository(session)
        self.retriever = HybridRetriever(self.repository, self.settings)
        self.learning_repository = LearningRepository(session)
        self.embedding_provider = build_embedding_provider(self.settings)
        self.llm_provider = build_llm_provider()

    def _confidence_status(self, score: float) -> str:
        if score >= self.settings.confidence_threshold_high:
            return "high"
        if score >= self.settings.confidence_threshold_medium:
            return "medium"
        return "low"

    async def answer(
        self,
        question: str,
        top_k: int | None = None,
        session_id: uuid.UUID | None = None,
        user_identifier: str | None = None,
    ) -> dict:
        effective_top_k = top_k or self.settings.retrieval_top_k
        clean_question = question.strip()

        chat_session = self.learning_repository.get_or_create_session(
            session_id=session_id,
            user_identifier=user_identifier,
            title=clean_question[:120],
        )

        user_message = self.learning_repository.add_message(
            session_id=chat_session.id,
            role="user",
            content=clean_question,
            metadata={"top_k": effective_top_k},
        )

        contexts: list[RetrievedContext] = []
        embedding_warning: str | None = None
        try:
            embedding_started_at = perf_counter()
            query_embedding = await self.embedding_provider.embed_text(clean_question)
            embedding_duration_ms = int((perf_counter() - embedding_started_at) * 1000)
            logger.info(
                "query_embedding_completed",
                extra={
                    "provider": self.embedding_provider.name,
                    "model": self.embedding_provider.model,
                    "dimensions": self.embedding_provider.dimensions,
                    "duration_ms": embedding_duration_ms,
                    "question_length": len(clean_question),
                },
            )
            contexts = self.retriever.retrieve(
                query=clean_question,
                query_embedding=query_embedding,
                top_k=effective_top_k,
            )
        except EmbeddingProviderError as exc:
            embedding_warning = (
                "Não foi possível gerar embedding da pergunta; "
                "a recuperação textual será usada quando a estratégia permitir."
            )
            logger.warning(
                "query_embedding_failed_using_lexical_when_available",
                extra={"provider": self.embedding_provider.name, "error_type": type(exc).__name__},
            )
            contexts = self.retriever.retrieve(
                query=clean_question,
                query_embedding=None,
                top_k=effective_top_k,
            )

        confidence_score = max([context.score for context in contexts], default=0.0)
        confidence_status = self._confidence_status(confidence_score)

        warnings: list[str] = []
        if embedding_warning:
            warnings.append(embedding_warning)
        if not contexts:
            warnings.append("Nenhum trecho relevante foi encontrado na base documental indexada.")
        elif confidence_status == "medium":
            warnings.append("A resposta foi gerada com confiança moderada. Valide a fonte antes de usar em produção.")
        elif confidence_status == "low":
            warnings.append("A resposta foi gerada com baixa confiança. Uma lacuna de conhecimento foi registrada para auditoria.")

        context_block = "\n\n".join(
            [
                (
                    f"[Fonte {index + 1}] {context.title}\n"
                    f"Identificador: {context.source_identifier}\n"
                    f"Trecho: {context.chunk_index + 1}\n"
                    f"Score: {context.score:.4f}\n"
                    f"Conteúdo: {context.content}"
                )
                for index, context in enumerate(contexts)
            ]
        )

        system_prompt = load_system_prompt()
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(
                role="system",
                content=(
                    "Use somente o contexto abaixo para responder. "
                    "Se o contexto não for suficiente, informe essa limitação de forma clara.\n\n"
                    f"{context_block if context_block else 'Nenhum contexto recuperado.'}"
                ),
            ),
            ChatMessage(role="user", content=clean_question),
        ]

        answer = await self.llm_provider.generate(messages=messages, contexts=contexts)

        assistant_message = self.learning_repository.add_message(
            session_id=chat_session.id,
            role="assistant",
            content=answer,
            confidence_score=confidence_score,
            confidence_status=confidence_status,
            mode=self.settings.llm_provider,
            metadata={
                "embedding_provider": self.embedding_provider.name,
                "embedding_model": self.embedding_provider.model,
                "sources": [
                    {
                        "title": context.title,
                        "source_identifier": context.source_identifier,
                        "chunk_index": context.chunk_index,
                        "score": round(context.score, 4),
                        "retrieval": (context.metadata or {}).get("retrieval", {}),
                    }
                    for context in contexts
                ],
                "warnings": warnings,
                "retrieval_telemetry": self._retrieval_telemetry(),
                "user_message_id": str(user_message.id),
            },
        )

        knowledge_gap_id = None
        if confidence_status == "low":
            gap = self.learning_repository.create_gap(
                question=clean_question,
                reason="confidence_below_threshold" if contexts else "no_context_found",
                session_id=chat_session.id,
                message_id=assistant_message.id,
                metadata={
                    "confidence_score": confidence_score,
                    "confidence_status": confidence_status,
                    "top_k": effective_top_k,
                    "embedding_provider": self.embedding_provider.name,
                    "retrieval_strategy": self.settings.retrieval_strategy,
                },
            )
            knowledge_gap_id = gap.id

        self.session.commit()

        return {
            "answer": answer,
            "warnings": warnings,
            "mode": self.settings.llm_provider,
            "session_id": chat_session.id,
            "user_message_id": user_message.id,
            "assistant_message_id": assistant_message.id,
            "confidence_score": round(confidence_score, 4),
            "confidence_status": confidence_status,
            "knowledge_gap_id": knowledge_gap_id,
            "retrieval": self._retrieval_telemetry(),
            "sources": [
                {
                    "title": context.title,
                    "source_identifier": context.source_identifier,
                    "chunk_index": context.chunk_index,
                    "score": round(context.score, 4),
                    "excerpt": context.content[:400],
                    "metadata": context.metadata,
                    "retrieval": (context.metadata or {}).get("retrieval", {}),
                }
                for context in contexts
            ],
        }

    def _retrieval_telemetry(self) -> dict:
        telemetry = self.retriever.last_telemetry
        if telemetry is None:
            return {"strategy": self.settings.retrieval_strategy, "returned_contexts": 0}
        return {
            "strategy": telemetry.strategy,
            "vector_candidates": telemetry.vector_candidates,
            "lexical_candidates": telemetry.lexical_candidates,
            "merged_candidates": telemetry.merged_candidates,
            "returned_contexts": telemetry.returned_contexts,
            "duration_ms": telemetry.duration_ms,
            "score_min": round(telemetry.score_min, 4) if telemetry.score_min is not None else None,
            "score_max": round(telemetry.score_max, 4) if telemetry.score_max is not None else None,
            "score_avg": round(telemetry.score_avg, 4) if telemetry.score_avg is not None else None,
        }
