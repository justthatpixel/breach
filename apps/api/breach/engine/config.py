"""Scoring weights and the grade table.

HANDOFF.md §5 names these metrics but doesn't pin down a formula or grade
cutoffs — flagged as an open question. These are a documented placeholder,
not a locked decision; change freely.
"""

# score = DEFENCE_SCORE_WEIGHT * defence_score + BUDGET_BONUS_WEIGHT * budget_bonus
DEFENCE_SCORE_WEIGHT = 0.9
BUDGET_BONUS_WEIGHT = 0.1

# (minimum score, grade), checked in order, highest threshold first.
GRADE_TABLE: list[tuple[float, str]] = [
    (0.95, "A"),
    (0.85, "B"),
    (0.70, "C"),
    (0.55, "D"),
    (0.0, "F"),
]


def grade_for(score: float) -> str:
    for threshold, grade in GRADE_TABLE:
        if score >= threshold:
            return grade
    return "F"
