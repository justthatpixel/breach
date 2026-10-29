from breach.engine.models import AttackPath, AttackStep


def test_breached_true_when_all_steps_unblocked():
    path = AttackPath(steps=[AttackStep(step=1, **{"from": "a", "to": "b"}, technique_id="T1", blocked=False)])
    assert path.breached is True


def test_breached_false_when_any_step_blocked():
    path = AttackPath(
        steps=[
            AttackStep(step=1, **{"from": "a", "to": "b"}, technique_id="T1", blocked=False),
            AttackStep(step=2, **{"from": "b", "to": "c"}, technique_id="T2", blocked=True, blocked_by="M1"),
        ]
    )
    assert path.breached is False


def test_breached_true_vacuously_with_no_steps():
    assert AttackPath(steps=[]).breached is True
