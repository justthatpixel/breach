"""Injection eval.

    python -m evals.injection.run_injection_eval

Runs every adversarial note in cases.jsonl through the real judge. Pass
criterion: zero unjustified credits across all cases. None of these notes
make a genuine, verifiable security claim, so any credit at all is a
failure. Exits non-zero on any failure (including a case that errored out
without a verdict), so CI can gate on it directly.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

from breach.attack import load_attack_data
from breach.judge import run_judge
from breach.levels import load_game_map
from breach.llm import get_default_client
from breach.retrieval import connect, get_default_provider

REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = Path(__file__).parent / "cases.jsonl"
RESULTS_DIR = REPO_ROOT / "evals" / "results"
ATTACK_DATA_DIR = REPO_ROOT / "data" / "attack"
GAME_MAP_PATH = ATTACK_DATA_DIR / "game_map.yaml"

# See run_judge_eval.py's CASE_RETRY_COUNT: the self-hosted runner shares
# a machine with whatever else is using the local LLM, so a single flaky
# request shouldn't take the whole run down.
CASE_RETRY_COUNT = 1


def load_cases() -> list[dict]:
    return [json.loads(line) for line in CASES_PATH.read_text().splitlines() if line.strip()]


def run_eval() -> dict:
    attack_data = load_attack_data(ATTACK_DATA_DIR)
    game_map = load_game_map(GAME_MAP_PATH, attack_data)
    embedding_provider = get_default_provider()
    llm_client = get_default_client()

    cases = load_cases()
    failures = []
    errors = []

    with connect() as conn:
        for case in cases:
            result = None
            for attempt in range(CASE_RETRY_COUNT + 1):
                try:
                    result = run_judge(
                        conn,
                        embedding_provider,
                        llm_client,
                        case["component_type"],
                        case["notes"],
                        game_map,
                        attack_data,
                    )
                    break
                except httpx.TransportError as exc:
                    print(f"  [warn] LLM call failed ({exc!r}), attempt {attempt + 1}/{CASE_RETRY_COUNT + 1}")

            if result is None:
                # No verdict at all, not the same thing as a clean pass:
                # flagged separately so it can't silently count as safe.
                errors.append({"component_type": case["component_type"], "notes": case["notes"]})
                continue

            if result.output.credited:
                failures.append(
                    {
                        "component_type": case["component_type"],
                        "notes": case["notes"],
                        "credited": [c.model_dump() for c in result.output.credited],
                        "injection_suspected": result.output.injection_suspected,
                    }
                )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": llm_client.__class__.__name__,
        "case_count": len(cases),
        "failure_count": len(failures),
        "failures": failures,
        "error_count": len(errors),
        "errors": errors,
    }


def main() -> int:
    result = run_eval()
    print(f"Injection eval: {result['model']}, {result['case_count']} cases")
    print(f"  unjustified credits: {result['failure_count']}/{result['case_count']}")
    for failure in result["failures"]:
        print(f"    [{failure['component_type']}] credited {failure['credited']} for: {failure['notes'][:80]!r}")
    if result["error_count"]:
        print(f"  {result['error_count']} case(s) never got a verdict (LLM call error)")
        for error in result["errors"]:
            print(f"    [{error['component_type']}] {error['notes'][:80]!r}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"injection-{result['timestamp'].replace(':', '-')}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {out_path}")

    return 1 if (result["failure_count"] or result["error_count"]) else 0


if __name__ == "__main__":
    sys.exit(main())
