# Breach

A threat-modelling game: secure a given system architecture, then an AI red
team attacks it using real MITRE ATT&CK techniques, and you get a graded
debrief. See [HANDOFF.md](HANDOFF.md) for the full spec.

Deterministic attack engine, LLM used only as a judge (grading player notes)
and narrator (flavour text) — both schema-validated. See HANDOFF.md §2 for
the design decisions this is built around.

## Backend dev setup

```bash
cd apps/api
python3.12 -m venv ../../.venv   # 3.13 also works; 3.12 wasn't installed on the build machine
source ../../.venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Regenerating the ATT&CK data

```bash
source .venv/bin/activate
python scripts/ingest_attack.py
```

Downloads the current MITRE Enterprise ATT&CK STIX bundle and writes a
curated subset to `data/attack/`, restricted to the IDs in
`data/attack/wanted_ids.yaml`. Fails loudly if any ID is missing or its name
no longer matches what the spec expects, rather than guessing.

## Retrieval (Postgres + pgvector)

```bash
docker compose up -d db
cd apps/api && cp .env.example .env   # fill in MINIMAX_API_KEY for real embeddings
source ../../.venv/bin/activate
python -m breach.retrieval.migrate
python -m breach.retrieval.seed
python -m breach.retrieval.embed_mitigations   # needs MINIMAX_API_KEY
```

Without a working `MINIMAX_API_KEY`, run `embed_mitigations` with
`EMBEDDING_PROVIDER=test` (or pass `provider=DeterministicTestEmbedder()`
directly) — a local bag-of-words embedder, no network needed. It's what
`pytest` uses: `tests/test_retrieval.py` seeds and embeds with it
automatically and skips itself if Postgres isn't reachable, so the rest of
the suite doesn't need Docker running.

Embeddings are behind an interface (`breach/retrieval/embeddings.py`) —
`MiniMaxEmbeddingProvider` is the real one (MiniMax's `embo-01`, called at
`api.minimax.io`), `DeterministicTestEmbedder` is the test one. Swap via
`EMBEDDING_PROVIDER` in `.env`.
