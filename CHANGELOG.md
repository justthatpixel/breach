# Changelog

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
