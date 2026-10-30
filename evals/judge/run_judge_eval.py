"""Judge accuracy eval.

    python -m evals.judge.run_judge_eval [--update-baseline]

Runs every case in cases.jsonl through the real judge (breach.judge),
including real retrieval against Postgres, so this measures the whole
credit pipeline, not the LLM in isolation. Reports micro-averaged
precision/recall/F1 on credited mitigations, prints a per-case diff
table, and writes the full result to evals/results/<timestamp>.json.
`--update-baseline` additionally writes baseline.json, which the CI eval
gate compares future runs against (fails if F1 drops more than 3 points
below it).
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from breach.attack import load_attack_data
from breach.judge import run_judge
from breach.levels import load_game_map
from breach.llm import get_default_client
from breach.retrieval import connect, get_default_provider

# One flaky request (the self-hosted runner shares a machine with
# whatever else is using the local LLM at the time) shouldn't take down
# a 70-case run; retry a timed-out case once before counting it as a
# miss and moving on.
CASE_RETRY_COUNT = 1

REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = Path(__file__).parent / "cases.jsonl"
BASELINE_PATH = Path(__file__).parent / "baseline.json"
RESULTS_DIR = REPO_ROOT / "evals" / "results"
ATTACK_DATA_DIR = REPO_ROOT / "data" / "attack"
GAME_MAP_PATH = ATTACK_DATA_DIR / "game_map.yaml"


def load_cases() -> list[dict]:
    return [json.loads(line) for line in CASES_PATH.read_text().splitlines() if line.strip()]


def run_eval() -> dict:
    attack_data = load_attack_data(ATTACK_DATA_DIR)
    game_map = load_game_map(GAME_MAP_PATH, attack_data)
    embedding_provider = get_default_provider()
    llm_client = get_default_client()

    cases = load_cases()
    diffs = []
    true_positives = false_positives = false_negatives = 0
    error_count = 0

    with connect() as conn:
        for case in cases:
            expected = set(case["expected_credited"])

            credited: set[str] = set()
            errored = False
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
                    credited = {c.mitigation_id for c in result.output.credited}
                    errored = False
                    break
                except httpx.TransportError as exc:
                    errored = True
                    print(f"  [warn] LLM call failed ({exc!r}), attempt {attempt + 1}/{CASE_RETRY_COUNT + 1}")

            if errored:
                error_count += 1

            tp = expected & credited
            fp = credited - expected
            fn = expected - credited
            true_positives += len(tp)
            false_positives += len(fp)
            false_negatives += len(fn)

            diffs.append(
                {
                    "component_type": case["component_type"],
                    "notes_on_label": case["notes_on_label"],
                    "expected": sorted(expected),
                    "credited": sorted(credited),
                    "correct": expected == credited,
                    "errored": errored,
                }
            )

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 1.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": llm_client.__class__.__name__,
        "case_count": len(cases),
        "exact_match_count": sum(1 for d in diffs if d["correct"]),
        "error_count": error_count,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "diffs": diffs,
    }


def print_summary(result: dict) -> None:
    print(f"Judge eval: {result['model']}, {result['case_count']} cases")
    print(
        f"  precision={result['precision']:.3f}  recall={result['recall']:.3f}  f1={result['f1']:.3f}  "
        f"exact_match={result['exact_match_count']}/{result['case_count']}"
    )
    if result["error_count"]:
        print(f"  {result['error_count']} case(s) hit an LLM call error and were scored as a miss")
    wrong = [d for d in result["diffs"] if not d["correct"]]
    if wrong:
        print(f"\n  {len(wrong)} mismatches:")
        for d in wrong:
            tag = " [errored]" if d["errored"] else ""
            print(f"    [{d['component_type']}] {d['notes_on_label']}{tag}")
            print(f"        expected={d['expected']}  credited={d['credited']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-baseline", action="store_true")
    args = parser.parse_args()

    result = run_eval()
    print_summary(result)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"judge-{result['timestamp'].replace(':', '-')}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {out_path}")

    if args.update_baseline:
        baseline = {k: result[k] for k in ("timestamp", "model", "case_count", "precision", "recall", "f1")}
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2) + "\n")
        print(f"Updated baseline: {BASELINE_PATH}")


if __name__ == "__main__":
    main()
