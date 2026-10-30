"""The CI quality gate: reads the judge/injection eval results this run
just wrote, compares the judge's F1 to the committed baseline
(evals/judge/baseline.json), fails on any injection case that produced an
unjustified credit, and posts a summary table as a PR comment. Exit code
is the gate's pass/fail signal for the Actions job; run_judge_eval.py and
run_injection_eval.py themselves only measure and record, they don't
decide pass/fail for CI.

    python evals/ci_gate.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "evals" / "results"
BASELINE_PATH = REPO_ROOT / "evals" / "judge" / "baseline.json"
F1_DROP_TOLERANCE = 0.03


def latest_result(prefix: str) -> dict:
    candidates = sorted(RESULTS_DIR.glob(f"{prefix}-*.json"))
    if not candidates:
        raise SystemExit(f"No {prefix}-*.json result found in {RESULTS_DIR} — run the eval first.")
    return json.loads(candidates[-1].read_text())


def post_pr_comment(body: str) -> None:
    repo = os.environ.get("GITHUB_REPOSITORY")
    pr_number = os.environ.get("PR_NUMBER")
    if not repo or not pr_number:
        print("(not running against a PR — skipping PR comment)")
        return
    subprocess.run(["gh", "pr", "comment", pr_number, "--repo", repo, "--body", body], check=True)


def main() -> int:
    judge = latest_result("judge")
    injection = latest_result("injection")
    baseline = json.loads(BASELINE_PATH.read_text()) if BASELINE_PATH.exists() else None

    f1_ok = baseline is None or judge["f1"] >= baseline["f1"] - F1_DROP_TOLERANCE
    injection_ok = injection["failure_count"] == 0

    lines = [
        "## Eval results",
        "",
        f"**Judge** ({judge['model']}, {judge['case_count']} cases): "
        f"precision={judge['precision']:.3f} recall={judge['recall']:.3f} f1={judge['f1']:.3f} "
        f"exact_match={judge['exact_match_count']}/{judge['case_count']}",
    ]
    if judge.get("error_count"):
        lines.append(f"- {judge['error_count']} case(s) hit an LLM call error and were scored as a miss")
    if baseline is not None:
        delta = judge["f1"] - baseline["f1"]
        lines.append(f"- baseline f1={baseline['f1']:.3f} (delta {delta:+.3f}, tolerance -{F1_DROP_TOLERANCE})")
    else:
        lines.append("- no committed baseline yet")
    lines.append(f"- gate: {'PASS' if f1_ok else 'FAIL'}")
    lines += [
        "",
        f"**Injection** ({injection['model']}, {injection['case_count']} cases): "
        f"{injection['failure_count']} unjustified credit(s)",
    ]
    if injection.get("error_count"):
        lines.append(f"- {injection['error_count']} case(s) never got a verdict (LLM call error)")
    lines.append(f"- gate: {'PASS' if injection_ok else 'FAIL'}")

    body = "\n".join(lines)
    print(body)
    post_pr_comment(body)

    return 0 if (f1_ok and injection_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
