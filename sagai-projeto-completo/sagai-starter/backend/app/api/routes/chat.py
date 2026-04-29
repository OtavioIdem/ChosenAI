from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.chat_service import ChatService
from app.domain.schemas import ChatRequest, ChatResponse
from app.infra.db.session import get_db_session

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    payload: ChatRequest,
    session: Session = Depends(get_db_session),
) -> ChatResponse:
    service = ChatService(session)
    result = await service.answer(
        question=payload.question,
        top_k=payload.top_k,
        session_id=payload.session_id,
        user_identifier=payload.user_identifier,
    )
    return ChatResponse(**result)
