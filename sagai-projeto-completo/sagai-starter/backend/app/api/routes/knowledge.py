from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.services.knowledge_service import KnowledgeService
from app.core.security import validate_admin_key
from app.domain.schemas import KnowledgeStatsResponse, ReindexResponse
from app.infra.db.session import get_db_session

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/stats", response_model=KnowledgeStatsResponse)
def stats(session: Session = Depends(get_db_session)) -> KnowledgeStatsResponse:
    service = KnowledgeService(session)
    result = service.stats()
    return KnowledgeStatsResponse(**result)


@router.post("/reindex", response_model=ReindexResponse, dependencies=[Depends(validate_admin_key)])
def reindex(session: Session = Depends(get_db_session)) -> ReindexResponse:
    service = KnowledgeService(session)
    result = service.reindex()
    return ReindexResponse(**result)
