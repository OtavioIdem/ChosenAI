from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.application.services.hash_embeddings import HashEmbeddingService
from app.config.settings import get_settings
from app.core.prompt_loader import load_system_prompt
from app.infra.llm.base import ChatMessage, RetrievedContext
from app.infra.llm.factory import build_llm_provider
from app.infra.repositories.knowledge_repository import KnowledgeRepository
from app.infra.repositories.learning_repository import LearningRepository


class ChatService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.repository = KnowledgeRepository(session)
        self.learning_repository = LearningRepository(session)
        self.embedding_service = HashEmbeddingService(self.settings.vector_dimensions)
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

        query_embedding = self.embedding_service.embed_text(clean_question)
        search_results = self.repository.search_chunks(query_embedding, effective_top_k)

        contexts: list[RetrievedContext] = []
        for chunk, source, distance in search_results:
            score = max(0.0, min(1.0, 1.0 - distance))
            contexts.append(
                RetrievedContext(
                    title=source.title,
                    source_identifier=source.source_identifier,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=score,
                    metadata=chunk.chunk_metadata,
                )
            )

        confidence_score = max([context.score for context in contexts], default=0.0)
        confidence_status = self._confidence_status(confidence_score)

        warnings: list[str] = []
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
                "sources": [
                    {
                        "title": context.title,
                        "source_identifier": context.source_identifier,
                        "chunk_index": context.chunk_index,
                        "score": round(context.score, 4),
                    }
                    for context in contexts
                ],
                "warnings": warnings,
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
            "sources": [
                {
                    "title": context.title,
                    "source_identifier": context.source_identifier,
                    "chunk_index": context.chunk_index,
                    "score": round(context.score, 4),
                    "excerpt": context.content[:400],
                    "metadata": context.metadata,
                }
                for context in contexts
            ],
        }
