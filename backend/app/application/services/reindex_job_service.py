from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.application.services.knowledge_service import KnowledgeService
from app.infra.db.models import ReindexJob
from app.infra.db.session import SessionLocal

logger = logging.getLogger(__name__)


TERMINAL_STATUSES = {"success", "partial_success", "failed", "cancelled"}


class ReindexJobService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(self, *, requested_by: str | None = None) -> ReindexJob:
        job = ReindexJob(status="pending", requested_by=requested_by, job_metadata={})
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_job(self, job_id: uuid.UUID) -> ReindexJob | None:
        return self.session.get(ReindexJob, job_id)

    @staticmethod
    async def run_job(job_id: uuid.UUID) -> None:
        if not ReindexJobService._mark_running(job_id):
            return

        try:
            async def progress_callback(payload: dict[str, Any]) -> None:
                ReindexJobService._update_progress(job_id, payload)

            with SessionLocal() as session:
                result = await KnowledgeService(session).reindex(progress_callback=progress_callback)
                ReindexJobService._mark_finished(job_id, result)
        except Exception as exc:  # pragma: no cover - protects background task boundary.
            logger.exception("reindex_job_failed", extra={"job_id": str(job_id), "error_type": type(exc).__name__})
            ReindexJobService._mark_failed(job_id, str(exc))

    @staticmethod
    def to_response(job: ReindexJob) -> dict[str, Any]:
        return {
            "id": job.id,
            "status": job.status,
            "requested_by": job.requested_by,
            "sources_total": job.sources_total,
            "sources_processed": job.sources_processed,
            "sources_failed": job.sources_failed,
            "chunks_indexed": job.chunks_indexed,
            "chunks_failed": job.chunks_failed,
            "chunks_ignored": job.chunks_ignored,
            "current_file": job.current_file,
            "error_message": job.error_message,
            "metadata": job.job_metadata or {},
            "started_at": job.started_at,
            "finished_at": job.finished_at,
            "duration_ms": job.duration_ms,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }

    @staticmethod
    def _mark_running(job_id: uuid.UUID) -> bool:
        with SessionLocal() as session:
            job = session.get(ReindexJob, job_id)
            if job is None:
                logger.warning("reindex_job_not_found", extra={"job_id": str(job_id)})
                return False
            if job.status != "pending":
                logger.warning(
                    "reindex_job_not_pending",
                    extra={"job_id": str(job_id), "status": job.status},
                )
                return False

            now = datetime.now(timezone.utc)
            job.status = "running"
            job.started_at = now
            job.updated_at = now
            session.commit()
            return True

    @staticmethod
    def _update_progress(job_id: uuid.UUID, payload: dict[str, Any]) -> None:
        with SessionLocal() as session:
            job = session.get(ReindexJob, job_id)
            if job is None or job.status in TERMINAL_STATUSES:
                return

            _apply_progress(job, payload)
            metadata = dict(job.job_metadata or {})
            metadata["last_event"] = payload.get("event")
            if "files_total" in payload:
                metadata["files_total"] = payload["files_total"]
            job.job_metadata = metadata
            job.updated_at = datetime.now(timezone.utc)
            session.commit()

    @staticmethod
    def _mark_finished(job_id: uuid.UUID, result: dict[str, Any]) -> None:
        with SessionLocal() as session:
            job = session.get(ReindexJob, job_id)
            if job is None:
                return

            now = datetime.now(timezone.utc)
            result_status = result.get("status")
            job.status = "failed" if result_status == "error" else str(result_status or "failed")
            job.finished_at = now
            job.updated_at = now
            job.current_file = None
            job.duration_ms = int(result.get("duration_ms") or 0)
            job.sources_total = int(result.get("sources_total") or result.get("sources_processed") or 0)
            job.sources_processed = int(result.get("sources_processed") or 0)
            job.sources_failed = int(result.get("sources_failed") or 0)
            job.chunks_indexed = int(result.get("chunks_indexed") or 0)
            job.chunks_failed = int(result.get("chunks_failed") or 0)
            job.chunks_ignored = int(result.get("chunks_ignored") or 0)
            job.error_message = _result_error_message(result)
            job.job_metadata = {
                "provider": result.get("provider"),
                "actual_provider": result.get("actual_provider"),
                "model": result.get("model"),
                "indexed_files": result.get("indexed_files", []),
                "errors": result.get("errors", []),
            }
            session.commit()

    @staticmethod
    def _mark_failed(job_id: uuid.UUID, message: str) -> None:
        with SessionLocal() as session:
            job = session.get(ReindexJob, job_id)
            if job is None:
                return

            now = datetime.now(timezone.utc)
            job.status = "failed"
            job.finished_at = now
            job.updated_at = now
            job.error_message = message[:2000]
            metadata = dict(job.job_metadata or {})
            metadata["last_event"] = "failed"
            job.job_metadata = metadata
            session.commit()


def _apply_progress(job: ReindexJob, payload: dict[str, Any]) -> None:
    if "current_file" in payload:
        job.current_file = payload["current_file"]
    for field in (
        "sources_total",
        "sources_processed",
        "sources_failed",
        "chunks_indexed",
        "chunks_failed",
        "chunks_ignored",
        "duration_ms",
    ):
        if field in payload and payload[field] is not None:
            setattr(job, field, int(payload[field]))


def _result_error_message(result: dict[str, Any]) -> str | None:
    errors = result.get("errors") or []
    if not errors:
        return None
    first = errors[0]
    if isinstance(first, dict):
        return str(first.get("message") or "Reindex job finished with errors.")
    return str(first)
