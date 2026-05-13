-- New environments get the same pgvector index prepared automatically.
-- Existing environments are also protected by app.infra.db.session.ensure_pgvector_schema().
CREATE EXTENSION IF NOT EXISTS vector;
