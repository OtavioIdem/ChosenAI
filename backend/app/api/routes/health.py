from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.schemas import HealthResponse
from app.infra.db.session import SessionLocal

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/liveness", response_model=HealthResponse)
def liveness() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/readiness", response_model=HealthResponse)
def readiness() -> HealthResponse:
    with SessionLocal() as session:
        _ensure_db(session)
    return HealthResponse(status="ok")


def _ensure_db(session: Session) -> None:
    session.execute(text("SELECT 1"))
