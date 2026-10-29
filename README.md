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

## Running the API (judge + narrator + engine)

```bash
docker compose up -d db
cd apps/api && cp .env.example .env   # fill in ANTHROPIC_API_KEY for the real judge/narrator
source ../../.venv/bin/activate
python -m breach.retrieval.migrate
python -m breach.retrieval.seed
python -m breach.retrieval.embed_mitigations   # or EMBEDDING_PROVIDER=test, see above
uvicorn breach.app:app --reload
```

`POST /runs` is the whole loop (HANDOFF §10): the judge credits the
player's notes from retrieval candidates, the deterministic engine (M2)
decides what actually breaches, and the narrator turns that into replay
and debrief text. Every LLM boundary is schema-validated — the judge can
only credit mitigations from the candidate list with evidence that's a
real substring of the notes, and the narrator can only mention technique
IDs the engine actually produced.

The LLM is behind the same kind of interface as embeddings
(`breach/llm.py`): `AnthropicLLMClient` is the real one (needs
`ANTHROPIC_API_KEY`), `DeterministicTestLLMClient` is a no-network stand-in
used when `LLM_PROVIDER=test` — what the test suite and `npm run
test:e2e` use, so neither needs a key.

Player notes are untrusted input (HANDOFF §7): control characters are
stripped and length-capped before they reach a prompt
(`breach/security/injection.py`), a heuristic flags common injection
phrasing alongside the judge's own `injection_suspected` field, and
either one zeroes that component's credit. `POST /runs` is rate-limited
per client IP (`RUN_RATE_LIMIT_PER_MINUTE`, in-memory — fine for a single
process, not for a multi-instance deploy).

## Evals (HANDOFF §8)

See [evals/README.md](evals/README.md) for how to run them. Measured
against the real judge (real retrieval + a real LLM call, not the LLM in
isolation), on `qwen3:8b` via a self-hosted Ollama runner:

- **Judge accuracy** (70 hand-labelled cases): precision=0.746,
  recall=0.733, f1=0.739, 50/70 exact match. Most of the misses are
  confusions between closely-related mitigations the judge (and the
  crude bag-of-words test embedder used for retrieval here) genuinely
  struggles to tell apart from a short note — M1018/M1026/M1036 (all
  account-management variants) and M1030/M1035 (both about network
  reachability). See `evals/results/` for the full per-case diffs.
- **Injection** (31 adversarial notes): 0/31 unjustified credits.

CI (`.github/workflows/evals.yml`) runs both on every PR touching
`judge/`, `narrator/`, `retrieval/`, `security/`, `llm.py`,
`data/attack/`, or `evals/`, and fails if judge F1 drops more than 3
points below the committed baseline or any injection case credits
something unjustified.
