from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.services.knowledge_service import KnowledgeService
from app.application.services.reindex_job_service import ReindexJobService
from app.core.security import validate_admin_key
from app.domain.schemas import (
    KnowledgeStatsResponse,
    ReindexJobCreateRequest,
    ReindexJobResponse,
    ReindexResponse,
)
from app.infra.db.session import get_db_session

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/stats", response_model=KnowledgeStatsResponse)
def stats(session: Session = Depends(get_db_session)) -> KnowledgeStatsResponse:
    service = KnowledgeService(session)
    result = service.stats()
    return KnowledgeStatsResponse(**result)


@router.post("/reindex", response_model=ReindexResponse, dependencies=[Depends(validate_admin_key)])
async def reindex(session: Session = Depends(get_db_session)) -> ReindexResponse:
    service = KnowledgeService(session)
    result = await service.reindex()
    return ReindexResponse(**result)


@router.post(
    "/reindex-jobs",
    response_model=ReindexJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(validate_admin_key)],
)
async def create_reindex_job(
    background_tasks: BackgroundTasks,
    payload: ReindexJobCreateRequest | None = Body(default=None),
    session: Session = Depends(get_db_session),
) -> ReindexJobResponse:
    service = ReindexJobService(session)
    job = service.create_job(requested_by=payload.requested_by if payload else None)
    background_tasks.add_task(ReindexJobService.run_job, job.id)
    return ReindexJobResponse(**ReindexJobService.to_response(job))


@router.get("/reindex-jobs/{job_id}", response_model=ReindexJobResponse)
def get_reindex_job(job_id: uuid.UUID, session: Session = Depends(get_db_session)) -> ReindexJobResponse:
    service = ReindexJobService(session)
    job = service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reindex job not found.")
    return ReindexJobResponse(**ReindexJobService.to_response(job))
