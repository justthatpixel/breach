# Changelog

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
