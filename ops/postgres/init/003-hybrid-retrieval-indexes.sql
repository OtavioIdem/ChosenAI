-- New environments are also protected by app.infra.db.session.ensure_pgvector_schema().
-- Docker init may run before SQLAlchemy creates tables, so guard table existence.
DO $$
BEGIN
  IF to_regclass('public.knowledge_chunks') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_content_tsv_pt
      ON knowledge_chunks
      USING gin (to_tsvector('portuguese', coalesce(content, '') || ' ' || coalesce(metadata::text, '')));
  END IF;

  IF to_regclass('public.knowledge_sources') IS NOT NULL THEN
    CREATE INDEX IF NOT EXISTS idx_knowledge_sources_title_category_tsv_pt
      ON knowledge_sources
      USING gin (to_tsvector('portuguese', coalesce(title, '') || ' ' || coalesce(category, '') || ' ' || coalesce(metadata::text, '')));
  END IF;
END $$;
