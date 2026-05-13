from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from inspect import isawaitable
from pathlib import Path
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.application.services.embeddings import (
    EmbeddingDimensionError,
    EmbeddingProviderError,
    build_embedding_provider,
)
from app.application.services.embeddings.fallback_provider import FallbackEmbeddingProvider
from app.config.settings import get_settings
from app.core.chunking import chunk_text
from app.core.json_ingestion import normalize_json_file
from app.infra.repositories.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)
ReindexProgressCallback = Callable[[dict[str, Any]], None | Awaitable[None]]


class KnowledgeService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.repository = KnowledgeRepository(session)
        self.embedding_provider = build_embedding_provider(self.settings)

    async def reindex(self, progress_callback: ReindexProgressCallback | None = None) -> dict:
        started_at = perf_counter()
        knowledge_dir = Path(self.settings.knowledge_dir)
        json_dir = knowledge_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)
        json_files = sorted(json_dir.rglob("*.json"))

        indexed_files: list[str] = []
        errors: list[dict] = []
        sources_total = 0
        sources_processed = 0
        sources_failed = 0
        chunks_indexed = 0
        chunks_failed = 0
        chunks_ignored = 0

        logger.info(
            "knowledge_reindex_started",
            extra={
                "provider": self.embedding_provider.name,
                "model": self.embedding_provider.model,
                "dimensions": self.embedding_provider.dimensions,
                "json_dir": str(json_dir),
            },
        )

        await self._emit_progress(
            progress_callback,
            {
                "event": "started",
                "sources_total": sources_total,
                "sources_processed": sources_processed,
                "sources_failed": sources_failed,
                "chunks_indexed": chunks_indexed,
                "chunks_failed": chunks_failed,
                "chunks_ignored": chunks_ignored,
                "files_total": len(json_files),
            },
        )

        for file_path in json_files:
            relative_file = file_path.relative_to(knowledge_dir).as_posix()
            await self._emit_progress(
                progress_callback,
                {
                    "event": "file_started",
                    "current_file": relative_file,
                    "sources_total": sources_total,
                    "sources_processed": sources_processed,
                    "sources_failed": sources_failed,
                    "chunks_indexed": chunks_indexed,
                    "chunks_failed": chunks_failed,
                    "chunks_ignored": chunks_ignored,
                },
            )
            try:
                normalized_items = normalize_json_file(file_path=file_path, root_dir=knowledge_dir)
                sources_total += len(normalized_items)
                await self._emit_progress(
                    progress_callback,
                    {
                        "event": "file_normalized",
                        "current_file": relative_file,
                        "sources_total": sources_total,
                        "sources_processed": sources_processed,
                        "sources_failed": sources_failed,
                        "chunks_indexed": chunks_indexed,
                        "chunks_failed": chunks_failed,
                        "chunks_ignored": chunks_ignored,
                    },
                )
            except Exception as exc:
                sources_failed += 1
                errors.append({"file": relative_file, "message": "JSON inválido ou não normalizável."})
                logger.exception(
                    "knowledge_file_normalization_failed",
                    extra={"file": relative_file, "error_type": type(exc).__name__},
                )
                await self._emit_progress(
                    progress_callback,
                    {
                        "event": "file_failed",
                        "current_file": relative_file,
                        "sources_total": sources_total,
                        "sources_processed": sources_processed,
                        "sources_failed": sources_failed,
                        "chunks_indexed": chunks_indexed,
                        "chunks_failed": chunks_failed,
                        "chunks_ignored": chunks_ignored,
                    },
                )
                continue

            file_had_success = False
            for item in normalized_items:
                try:
                    content = (item.get("content") or "").strip()
                    if not content:
                        chunks_ignored += 1
                        await self._emit_progress(
                            progress_callback,
                            {
                                "event": "source_ignored",
                                "current_file": relative_file,
                                "sources_total": sources_total,
                                "sources_processed": sources_processed,
                                "sources_failed": sources_failed,
                                "chunks_indexed": chunks_indexed,
                                "chunks_failed": chunks_failed,
                                "chunks_ignored": chunks_ignored,
                            },
                        )
                        continue

                    source = self.repository.upsert_source(
                        source_identifier=item["source_identifier"],
                        title=item["title"],
                        category=item["category"],
                        metadata=item["metadata"],
                    )
                    chunks = chunk_text(
                        text=content,
                        max_chunk_size=self.settings.max_chunk_size,
                        chunk_overlap=self.settings.chunk_overlap,
                    )
                    if not chunks:
                        chunks_ignored += 1
                        await self._emit_progress(
                            progress_callback,
                            {
                                "event": "source_ignored",
                                "current_file": relative_file,
                                "sources_total": sources_total,
                                "sources_processed": sources_processed,
                                "sources_failed": sources_failed,
                                "chunks_indexed": chunks_indexed,
                                "chunks_failed": chunks_failed,
                                "chunks_ignored": chunks_ignored,
                            },
                        )
                        continue

                    batch_started_at = perf_counter()
                    embeddings = await self.embedding_provider.embed_batch(chunks)
                    batch_duration_ms = int((perf_counter() - batch_started_at) * 1000)

                    for chunk_index, (chunk_content, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
                        self.repository.add_chunk(
                            source=source,
                            chunk_index=chunk_index,
                            content=chunk_content,
                            embedding=embedding,
                            metadata=item["metadata"],
                        )
                        chunks_indexed += 1

                    sources_processed += 1
                    file_had_success = True
                    await self._emit_progress(
                        progress_callback,
                        {
                            "event": "source_indexed",
                            "current_file": relative_file,
                            "sources_total": sources_total,
                            "sources_processed": sources_processed,
                            "sources_failed": sources_failed,
                            "chunks_indexed": chunks_indexed,
                            "chunks_failed": chunks_failed,
                            "chunks_ignored": chunks_ignored,
                        },
                    )
                    logger.info(
                        "knowledge_source_indexed",
                        extra={
                            "source_identifier": item["source_identifier"],
                            "chunks": len(chunks),
                            "duration_ms": batch_duration_ms,
                            "provider": self._actual_provider_name(),
                        },
                    )
                except EmbeddingDimensionError as exc:
                    self.session.rollback()
                    sources_failed += 1
                    chunks_failed += 1
                    errors.append(
                        {
                            "file": relative_file,
                            "source_identifier": item.get("source_identifier"),
                            "message": str(exc),
                        }
                    )
                    logger.warning(
                        "knowledge_source_embedding_dimension_failed",
                        extra={"file": relative_file, "source_identifier": item.get("source_identifier")},
                    )
                    await self._emit_progress(
                        progress_callback,
                        {
                            "event": "source_failed",
                            "current_file": relative_file,
                            "sources_total": sources_total,
                            "sources_processed": sources_processed,
                            "sources_failed": sources_failed,
                            "chunks_indexed": chunks_indexed,
                            "chunks_failed": chunks_failed,
                            "chunks_ignored": chunks_ignored,
                        },
                    )
                    continue
                except EmbeddingProviderError as exc:
                    self.session.rollback()
                    sources_failed += 1
                    chunks_failed += 1
                    errors.append(
                        {
                            "file": relative_file,
                            "source_identifier": item.get("source_identifier"),
                            "message": "Não foi possível gerar embeddings para esta fonte.",
                        }
                    )
                    logger.warning(
                        "knowledge_source_embedding_failed",
                        extra={
                            "file": relative_file,
                            "source_identifier": item.get("source_identifier"),
                            "error_type": type(exc).__name__,
                        },
                    )
                    await self._emit_progress(
                        progress_callback,
                        {
                            "event": "source_failed",
                            "current_file": relative_file,
                            "sources_total": sources_total,
                            "sources_processed": sources_processed,
                            "sources_failed": sources_failed,
                            "chunks_indexed": chunks_indexed,
                            "chunks_failed": chunks_failed,
                            "chunks_ignored": chunks_ignored,
                        },
                    )
                    continue
                except Exception as exc:
                    self.session.rollback()
                    sources_failed += 1
                    errors.append(
                        {
                            "file": relative_file,
                            "source_identifier": item.get("source_identifier"),
                            "message": "Falha controlada ao indexar fonte.",
                        }
                    )
                    logger.exception(
                        "knowledge_source_indexing_failed",
                        extra={"file": relative_file, "source_identifier": item.get("source_identifier")},
                    )
                    await self._emit_progress(
                        progress_callback,
                        {
                            "event": "source_failed",
                            "current_file": relative_file,
                            "sources_total": sources_total,
                            "sources_processed": sources_processed,
                            "sources_failed": sources_failed,
                            "chunks_indexed": chunks_indexed,
                            "chunks_failed": chunks_failed,
                            "chunks_ignored": chunks_ignored,
                        },
                    )
                    continue

            if file_had_success:
                indexed_files.append(relative_file)

        if chunks_indexed:
            self.session.commit()
        else:
            self.session.rollback()

        duration_ms = int((perf_counter() - started_at) * 1000)
        status = "success"
        if errors and chunks_indexed:
            status = "partial_success"
        elif errors and not chunks_indexed:
            status = "error"

        result = {
            "status": status,
            "provider": self.embedding_provider.name,
            "actual_provider": self._actual_provider_name(),
            "model": self.embedding_provider.model,
            "sources_total": sources_total,
            "sources_processed": sources_processed,
            "sources_failed": sources_failed,
            "sources_indexed": sources_processed,
            "chunks_indexed": chunks_indexed,
            "chunks_failed": chunks_failed,
            "chunks_ignored": chunks_ignored,
            "duration_ms": duration_ms,
            "indexed_files": indexed_files,
            "errors": errors,
        }
        logger.info(
            "knowledge_reindex_finished",
            extra={
                "status": status,
                "provider": self.embedding_provider.name,
                "actual_provider": result["actual_provider"],
                "sources_processed": sources_processed,
                "sources_failed": sources_failed,
                "chunks_indexed": chunks_indexed,
                "chunks_failed": chunks_failed,
                "duration_ms": duration_ms,
            },
        )
        await self._emit_progress(
            progress_callback,
            {
                "event": "finished",
                "current_file": None,
                "sources_total": sources_total,
                "sources_processed": sources_processed,
                "sources_failed": sources_failed,
                "chunks_indexed": chunks_indexed,
                "chunks_failed": chunks_failed,
                "chunks_ignored": chunks_ignored,
                "duration_ms": duration_ms,
                "status": status,
            },
        )
        return result

    def stats(self) -> dict:
        return self.repository.stats()

    def _actual_provider_name(self) -> str:
        if isinstance(self.embedding_provider, FallbackEmbeddingProvider):
            return self.embedding_provider.last_provider_name
        return self.embedding_provider.name

    async def _emit_progress(
        self,
        progress_callback: ReindexProgressCallback | None,
        payload: dict[str, Any],
    ) -> None:
        if progress_callback is None:
            return
        maybe_awaitable = progress_callback(payload)
        if isawaitable(maybe_awaitable):
            await maybe_awaitable
