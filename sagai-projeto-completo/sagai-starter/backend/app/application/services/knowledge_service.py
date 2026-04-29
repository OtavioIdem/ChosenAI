from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from app.application.services.hash_embeddings import HashEmbeddingService
from app.config.settings import get_settings
from app.core.chunking import chunk_text
from app.core.json_ingestion import normalize_json_file
from app.infra.repositories.knowledge_repository import KnowledgeRepository


class KnowledgeService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.repository = KnowledgeRepository(session)
        self.embedding_service = HashEmbeddingService(self.settings.vector_dimensions)

    def reindex(self) -> dict:
        knowledge_dir = Path(self.settings.knowledge_dir)
        json_dir = knowledge_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)

        indexed_files: list[str] = []
        sources_indexed = 0
        chunks_indexed = 0

        for file_path in sorted(json_dir.rglob("*.json")):
            normalized_items = normalize_json_file(file_path=file_path, root_dir=knowledge_dir)

            for item in normalized_items:
                source = self.repository.upsert_source(
                    source_identifier=item["source_identifier"],
                    title=item["title"],
                    category=item["category"],
                    metadata=item["metadata"],
                )
                chunks = chunk_text(
                    text=item["content"],
                    max_chunk_size=self.settings.max_chunk_size,
                    chunk_overlap=self.settings.chunk_overlap,
                )

                for chunk_index, chunk_content in enumerate(chunks):
                    embedding = self.embedding_service.embed_text(chunk_content)
                    self.repository.add_chunk(
                        source=source,
                        chunk_index=chunk_index,
                        content=chunk_content,
                        embedding=embedding,
                        metadata=item["metadata"],
                    )
                    chunks_indexed += 1

                sources_indexed += 1

            indexed_files.append(file_path.relative_to(knowledge_dir).as_posix())

        self.session.commit()

        return {
            "sources_indexed": sources_indexed,
            "chunks_indexed": chunks_indexed,
            "indexed_files": indexed_files,
        }

    def stats(self) -> dict:
        return self.repository.stats()
