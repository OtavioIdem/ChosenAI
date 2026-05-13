CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS reindex_jobs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    status varchar(40) NOT NULL DEFAULT 'pending',
    requested_by varchar(120),
    sources_total integer NOT NULL DEFAULT 0,
    sources_processed integer NOT NULL DEFAULT 0,
    sources_failed integer NOT NULL DEFAULT 0,
    chunks_indexed integer NOT NULL DEFAULT 0,
    chunks_failed integer NOT NULL DEFAULT 0,
    chunks_ignored integer NOT NULL DEFAULT 0,
    current_file varchar(1000),
    error_message text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at timestamptz,
    finished_at timestamptz,
    duration_ms integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reindex_jobs_status ON reindex_jobs (status);
CREATE INDEX IF NOT EXISTS idx_reindex_jobs_created_at ON reindex_jobs (created_at);
