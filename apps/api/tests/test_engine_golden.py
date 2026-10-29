"""The Level 3 golden test named in HANDOFF.md §5.

The card placement in §5's prose (WAF@gateway, encryption+MFA@postgres)
does not reproduce its claimed breach path against real MITRE ATT&CK
mitigates data — WAF blocks T1190 but not Brute Force (T1110), and MFA
genuinely stops T1078.004 rather than letting it through. See the M2
CHANGELOG entry for the full analysis.

This is the corrected loadout, confirmed by the user: it reproduces the
exact stated breach path (T1190 -> T1552.005 -> T1078.004) and the 4-cards-
used / 2-coins-left budget split visible in the game-screen mockup.
"""
from breach.engine import ComponentDefence, run_engine


def test_level3_golden_breach(level3, game_map, attack_data):
    defences = {
        "gateway": ComponentDefence(cards=["mfa"]),
        "payments": ComponentDefence(cards=["least_privilege"]),
        "postgres": ComponentDefence(cards=["encryption"]),
        "secrets": ComponentDefence(cards=["private_subnet"]),
    }
    result = run_engine(level3, game_map, attack_data, defences)

    assert result.paths_total == 1
    path = result.paths[0]
    assert path.breached is True
    assert [s.technique_id for s in path.steps] == ["T1190", "T1552.005", "T1078.004"]
    assert all(not s.blocked for s in path.steps)

    assert result.budget_used == 4
    assert result.budget_total == 6
