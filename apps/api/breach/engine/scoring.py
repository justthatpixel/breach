from .config import BUDGET_BONUS_WEIGHT, DEFENCE_SCORE_WEIGHT, grade_for
from .models import AttackPath, EngineResult


def compute_score(paths: list[AttackPath], budget_used: int, budget_total: int) -> EngineResult:
    paths_total = len(paths)
    paths_blocked = sum(1 for p in paths if not p.breached)

    all_steps = [step for path in paths for step in path.steps]
    techniques_attempted = len(all_steps)
    techniques_stopped = sum(1 for step in all_steps if step.blocked)

    path_ratio = paths_blocked / paths_total if paths_total else 1.0
    technique_ratio = (
        techniques_stopped / techniques_attempted if techniques_attempted else 1.0
    )
    defence_score = (path_ratio + technique_ratio) / 2

    fully_defended = paths_blocked == paths_total
    unused_ratio = (budget_total - budget_used) / budget_total if budget_total else 0.0
    budget_bonus = unused_ratio if fully_defended else 0.0

    score = DEFENCE_SCORE_WEIGHT * defence_score + BUDGET_BONUS_WEIGHT * budget_bonus
    score = max(0.0, min(1.0, score))

    return EngineResult(
        paths=paths,
        paths_total=paths_total,
        paths_blocked=paths_blocked,
        techniques_attempted=techniques_attempted,
        techniques_stopped=techniques_stopped,
        budget_used=budget_used,
        budget_total=budget_total,
        score=score,
        grade=grade_for(score),
    )
