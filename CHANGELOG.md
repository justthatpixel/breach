# Changelog

## M4: Retrieval

- `docker-compose.yml` — a `db` service (`pgvector/pgvector:pg16`) on
  port 5433, healthchecked.
- `breach/retrieval/`: `schema.sql` + `migrate.py` (techniques,
  mitigations, technique_mitigations, mitigation_embeddings, runs — the
  HANDOFF §4.4 tables), `seed.py` (idempotent upsert of
  `data/attack/*.json` into Postgres), `embed_mitigations.py`,
  `retrieve.py` (the hybrid retrieval function).
- **Embedding provider changed from OpenAI to MiniMax** (`embo-01` via
  `api.minimax.io/v1/embeddings`) — the user supplied a MiniMax key
  instead of the OpenAI one decided in M1's open questions, so this
  supersedes that decision. The provider sits behind
  `breach/retrieval/embeddings.py`'s `EmbeddingProvider` interface
  (HANDOFF §3: "keep behind an interface"), so swapping again later is a
  one-file change.
- Real MiniMax embeddings could not actually be generated in this
  environment: two different MiniMax keys both got an immediate,
  persistent `rate limit exceeded(RPM)` from `api.minimax.io`, even after
  waiting — consistent with this sandbox's outbound IP being throttled by
  MiniMax rather than a per-key quota issue. `MiniMaxEmbeddingProvider` is
  fully implemented and does the right thing when it gets a real error
  back (raises with the API's own message) — it just hasn't been run
  successfully end to end yet. `mitigation_embeddings` is currently
  populated by `DeterministicTestEmbedder`, a local bag-of-words embedder
  with no network dependency, picked for the four retrieval test cases
  below. Re-run `embed_mitigations.py` with a working key from an
  unthrottled network to get real semantic embeddings.
- Hybrid retrieval (HANDOFF §6.1): structured filter first (mitigations
  relevant to the component's own techniques, via
  `technique_mitigations`), then vector rank that filtered set by cosine
  distance to the notes embedding (pgvector `<=>`). Never surfaces a
  mitigation that isn't structurally relevant, however it scores on
  embeddings.
- Tests: `tests/test_retrieval.py` migrates, seeds and embeds (with the
  deterministic embedder) against a real Postgres, and skips itself
  cleanly if Docker/Postgres isn't up. Four known-notes cases each land
  the expected mitigation in the top 3; plus a structured-filter-excludes
  case and an empty-candidates case for a pass-through component type.
  51 tests pass repo-wide with the DB up, 45 pass (6 skipped) without it.

## M3: Frontend with mocked backend

- `apps/web/` — Next.js (App Router) + TypeScript, React Flow for the
  architecture canvas, Framer Motion for the attack-replay pacing, Zustand
  for client state. Fonts, colours, shadows and layout copied from
  `design/game-screen.dc.html` and `design/debrief.dc.html`'s inline
  styles, rebuilt as real components (not the template syntax).
- Three screens: level select (`/`), the game screen
  (`/levels/03-payments`), and the debrief (`/levels/03-payments/debrief`).
  Only Level 3 is playable — the rest of the campaign is lock/done fixture
  state, per HANDOFF §11's milestone ordering.
- `src/fixtures/level3.ts` transcribes the mockups' own `renderVals()`
  sample data (HANDOFF §9) — mission text, the card hand, the attack
  replay log, the debrief grade/stats/through/held/for-an-A/share card.
  Two small adaptations are called out in that file's header comment: the
  mockup sample imagines a component ("admin console") that isn't in the
  authored `data/levels/03-payments.yaml`, so the MFA card and one debrief
  "held" item were re-pointed at components that actually exist on this
  canvas.
- The backend is mocked, as the milestone name says: "Run attack" always
  returns the same canned replay from the fixture rather than calling the
  real engine (M2) or an API — that wiring is M5. The game screen itself is
  fully interactive: select a component, play a card against budget,
  write notes, watch the replay stage in, reach the debrief.
- `prefers-reduced-motion` is respected in two places: CSS
  (`globals.css`, the marching-dash/pulse/bob keyframes) and JS (the
  staged step-by-step reveal in `GameScreen.tsx` is skipped in favour of
  showing the final result immediately).
- Tests: 13 Vitest unit tests on the game store (budget limits, card
  placement, reset, attack-phase sequencing), 4 Playwright e2e tests
  covering the full Level 3 flow end to end plus a dedicated
  reduced-motion run. `next build` and `eslint` are clean.

## M2: Deterministic engine

- `breach/engine/` — pure, I/O-free attack engine: simple-path enumeration
  (`graph.py`), blocking rules (`blocking.py`), scoring and grading
  (`scoring.py`, `config.py`), and the `run_engine()` orchestrator
  (`run.py`). 100% statement coverage, 45 tests passing across the repo.
- Scoring formula and grade table (`engine/config.py`) are not in HANDOFF.md
  §5 — they're a documented placeholder I designed, not a locked decision.
- **Found and flagged a contradiction** between HANDOFF.md §5's described
  Level 3 golden test and real MITRE ATT&CK data: the literal card
  placement (WAF@gateway, private_subnet@secrets, encryption+MFA@postgres)
  does not produce the claimed breach path. WAF genuinely blocks T1190 in
  real data (so Brute Force/T1110 is what actually gets through instead),
  and MFA genuinely stops T1078.004 rather than letting it slide — so that
  loadout is not breached at all, let alone via the stated path.
  Found an alternate loadout — mfa@gateway, least_privilege@payments,
  encryption@postgres, private_subnet@secrets (unused, off-path) — that
  reproduces the exact stated path (T1190 → T1552.005 → T1078.004) *and*
  the "4 cards used / 2 coins left" detail visible in the game-screen
  mockup. Confirmed with the user and locked in as `test_engine_golden.py`.

## M1: Data foundations

- `scripts/ingest_attack.py` downloads the MITRE Enterprise ATT&CK STIX
  bundle and writes a curated subset (`data/attack/{techniques,mitigations,relationships}.json`),
  validating every technique/mitigation ID and name in the spec against the
  real data. Caught and fixed one validation nuance: sub-technique STIX
  objects store only their own name (e.g. "Cloud Accounts"), not the full
  display name ("Valid Accounts: Cloud Accounts") — the script now resolves
  that via the `subtechnique-of` relationship.
- Confirmed against real ATT&CK data: `M1041` (Encrypt Sensitive Information)
  mitigates `T1530` but not `T1078.004` — the Level 3 "encryption doesn't
  stop stolen credentials" teaching moment holds.
- Added `data/attack/game_map.yaml` (component types → techniques, cards →
  mitigations) and `data/levels/03-payments.yaml`, both from HANDOFF.md §4.
- Added Pydantic loaders (`breach/attack/`, `breach/levels/`) that
  cross-validate levels and the game map against the curated ATT&CK data —
  unknown component types, edges, cards, entry points, or mitigation/
  technique IDs all fail loudly.
- 16 tests passing: ATT&CK data loads correctly, the teaching-moment
  relationship holds, Level 3 loads, and seven ways of constructing a bad
  level/game-map are all rejected.

Note: the dev venv uses Python 3.13 (3.12, per HANDOFF.md §3, wasn't
installed on this machine); nothing in the code is version-specific.
