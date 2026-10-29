CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS techniques (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    platforms TEXT[] NOT NULL,
    tactics TEXT[] NOT NULL
);

CREATE TABLE IF NOT EXISTS mitigations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS technique_mitigations (
    mitigation_id TEXT NOT NULL REFERENCES mitigations (id),
    technique_id TEXT NOT NULL REFERENCES techniques (id),
    PRIMARY KEY (mitigation_id, technique_id)
);

-- {embedding_dim} is substituted by migrate.py from config.EMBEDDING_DIM —
-- pgvector requires a fixed dimension in the column type itself.
CREATE TABLE IF NOT EXISTS mitigation_embeddings (
    mitigation_id TEXT PRIMARY KEY REFERENCES mitigations (id),
    chunk_text TEXT NOT NULL,
    embedding VECTOR({embedding_dim}) NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level_id TEXT NOT NULL,
    defences JSONB NOT NULL,
    judge_output JSONB,
    engine_output JSONB,
    narrator_output JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ADD COLUMN IF NOT EXISTS so this stays idempotent against a database
-- that was migrated before narrator_output existed (M5).
ALTER TABLE runs ADD COLUMN IF NOT EXISTS narrator_output JSONB;
