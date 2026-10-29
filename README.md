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
