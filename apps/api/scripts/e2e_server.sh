#!/usr/bin/env bash
# Starts the API for Playwright e2e (apps/web/playwright.config.ts), using
# the deterministic test LLM and embedding providers — no network, no
# API keys. Tries to migrate/seed/embed against Postgres (docker compose
# up -d db), but tolerates it being unreachable: /healthz and /levels
# don't need the DB, and the e2e spec skips itself if /runs does.
set -uo pipefail
cd "$(dirname "$0")/.."
# CI installs breach into the runner's own Python, with no venv to activate.
if [ -f ../../.venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source ../../.venv/bin/activate
fi

export LLM_PROVIDER=test
export EMBEDDING_PROVIDER=test

python -c "
from breach.retrieval.migrate import migrate
from breach.retrieval.seed import seed
from breach.retrieval.embed_mitigations import embed_mitigations
from breach.retrieval import DeterministicTestEmbedder

migrate()
seed()
embed_mitigations(provider=DeterministicTestEmbedder())
" || echo "e2e_server.sh: retrieval bootstrap failed (Postgres down?) — starting the API anyway" >&2

exec uvicorn breach.app:app --host 127.0.0.1 --port 8000
