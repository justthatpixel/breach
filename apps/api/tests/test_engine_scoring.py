import pytest

from breach.engine.config import grade_for
from breach.engine.models import AttackPath, AttackStep
from breach.engine.scoring import compute_score


def step(blocked: bool) -> AttackStep:
    return AttackStep(step=1, **{"from": "a", "to": "b"}, technique_id="T1", blocked=blocked)


def test_fully_blocked_scores_perfect_defence_plus_unused_budget_bonus():
    paths = [AttackPath(steps=[step(True)]), AttackPath(steps=[step(True)])]
    result = compute_score(paths, budget_used=2, budget_total=6)
    assert result.paths_blocked == 2
    assert result.techniques_stopped == 2
    assert result.score == pytest.approx(0.9 * 1.0 + 0.1 * (4 / 6))
    assert result.grade == "A"


def test_fully_blocked_with_zero_leftover_budget_has_no_bonus():
    paths = [AttackPath(steps=[step(True)])]
    result = compute_score(paths, budget_used=6, budget_total=6)
    assert result.score == pytest.approx(0.9)
    assert result.grade == "B"


def test_fully_breached_scores_zero():
    paths = [AttackPath(steps=[step(False)])]
    result = compute_score(paths, budget_used=0, budget_total=6)
    assert result.score == 0.0
    assert result.grade == "F"


def test_no_paths_is_vacuously_perfect():
    result = compute_score([], budget_used=0, budget_total=6)
    assert result.paths_total == 0
    assert result.score == 1.0
    assert result.grade == "A"


def test_budget_bonus_only_applies_when_fully_defended():
    blocked = compute_score([AttackPath(steps=[step(True)])], budget_used=0, budget_total=6)
    breached = compute_score([AttackPath(steps=[step(False)])], budget_used=0, budget_total=6)
    assert blocked.score > breached.score
    assert breached.score == 0.0


def test_partial_defence_scores_between_zero_and_one():
    paths = [AttackPath(steps=[step(True)]), AttackPath(steps=[step(False)])]
    result = compute_score(paths, budget_used=2, budget_total=6)
    assert 0.0 < result.score < 1.0


def test_grade_boundaries():
    assert grade_for(1.0) == "A"
    assert grade_for(0.95) == "A"
    assert grade_for(0.9499) == "B"
    assert grade_for(0.85) == "B"
    assert grade_for(0.7) == "C"
    assert grade_for(0.55) == "D"
    assert grade_for(0.0) == "F"
    assert grade_for(-1.0) == "F"  # defensive: compute_score never produces this
