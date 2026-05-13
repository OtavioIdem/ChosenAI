-- Idempotent Sprint 2 migration for hybrid retrieval.
-- Adds PostgreSQL full-text indexes used by the lexical branch of hybrid search.

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_content_tsv_pt
  ON knowledge_chunks
  USING gin (to_tsvector('portuguese', coalesce(content, '') || ' ' || coalesce(metadata::text, '')));

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_title_category_tsv_pt
  ON knowledge_sources
  USING gin (to_tsvector('portuguese', coalesce(title, '') || ' ' || coalesce(category, '') || ' ' || coalesce(metadata::text, '')));
