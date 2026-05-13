-- Idempotent Sprint 1 migration for pgvector real embeddings.
-- Adjust the vector dimension if EMBEDDINGS_VECTOR_DIMENSIONS is different from 768.

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE knowledge_chunks
  ADD COLUMN IF NOT EXISTS embedding_v2 vector(768);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_v2_hnsw
  ON knowledge_chunks
  USING hnsw (embedding_v2 vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source_id
  ON knowledge_chunks (source_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_category
  ON knowledge_sources (category);

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_created_at
  ON knowledge_sources (created_at);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_created_at
  ON knowledge_chunks (created_at);
