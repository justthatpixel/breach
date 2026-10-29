from breach.engine import ComponentDefence, run_engine


def test_no_defences_breaches_level3(level3, game_map, attack_data):
    """With nothing played, every hop's lowest-ID technique is open, so the
    one path to the asset (postgres) breaches end to end."""
    result = run_engine(level3, game_map, attack_data, {})
    assert result.paths_total == 1
    assert result.paths_blocked == 0
    path = result.paths[0]
    assert path.breached is True
    assert [s.technique_id for s in path.steps] == ["T1110", "T1528", "T1078.004"]
    assert result.score == 0.0
    assert result.grade == "F"


def test_covering_every_candidate_technique_blocks_the_only_path(level3, game_map, attack_data):
    """Each hop has multiple candidate techniques; blocking only one still
    leaves the hop open via another. Every candidate at every hop must be
    covered to stop the path: waf+mfa at the gateway (T1190/T1498 and
    T1110), private_subnet+least_privilege at payments (T1552.005 and
    T1528), mfa at Postgres (T1078.004)."""
    defences = {
        "gateway": ComponentDefence(cards=["waf", "mfa"]),
        "payments": ComponentDefence(cards=["private_subnet", "least_privilege"]),
        "postgres": ComponentDefence(cards=["mfa"]),
    }
    result = run_engine(level3, game_map, attack_data, defences)
    assert result.paths_blocked == 1
    assert result.paths_total == 1
    assert result.paths[0].breached is False
    assert all(s.blocked for s in result.paths[0].steps)


def test_defending_the_asset_alone_is_not_enough(level3, game_map, attack_data):
    """Encryption at Postgres doesn't stop valid credentials reaching it
    (HANDOFF's teaching moment) if the earlier hops are undefended."""
    defences = {"postgres": ComponentDefence(cards=["encryption"])}
    result = run_engine(level3, game_map, attack_data, defences)
    assert result.paths[0].breached is True
    assert result.paths[0].steps[-1].technique_id == "T1078.004"
    assert result.paths[0].steps[-1].blocked is False


def test_card_mitigation_and_judge_credited_mitigation_both_count(level3, game_map, attack_data):
    """credited_mitigations (from the judge, §6) block just like a card
    does — the engine doesn't care where a mitigation came from."""
    via_card = run_engine(
        level3, game_map, attack_data, {"gateway": ComponentDefence(cards=["mfa"])}
    )
    via_credit = run_engine(
        level3,
        game_map,
        attack_data,
        {"gateway": ComponentDefence(credited_mitigations=["M1032"])},
    )
    gateway_step_card = via_card.paths[0].steps[0]
    gateway_step_credit = via_credit.paths[0].steps[0]
    assert gateway_step_card.technique_id == gateway_step_credit.technique_id
    assert gateway_step_card.blocked == gateway_step_credit.blocked == False


def test_passthrough_component_adds_no_step(attack_data):
    """A component type with no listed techniques (e.g. a queue) has no
    attack surface: the attacker transits it for free, and no step is
    recorded for that hop."""
    from breach.levels.models import CardDef, Component, ComponentTypeDef, GameMap, Level

    game_map = GameMap(
        component_types={"source": ComponentTypeDef(techniques=["T1190"])},
        cards={},
    )
    level = Level(
        id="t",
        title="t",
        brief="t",
        threat_level="low",
        budget=0,
        components=[
            Component(id="internet", type="internet", label="Internet"),
            Component(id="relay", type="queue", label="Relay"),
            Component(id="db", type="source", label="DB", asset=True),
        ],
        edges=[("internet", "relay"), ("relay", "db")],
        entry_points=["internet"],
        cards_available=[],
    )
    result = run_engine(level, game_map, attack_data, {})
    assert len(result.paths[0].steps) == 1
    assert result.paths[0].steps[0].to_component == "db"


def test_budget_used_sums_card_costs_across_components(level3, game_map, attack_data):
    defences = {
        "gateway": ComponentDefence(cards=["waf", "mfa"]),
        "postgres": ComponentDefence(cards=["encryption"]),
    }
    result = run_engine(level3, game_map, attack_data, defences)
    assert result.budget_used == 3
    assert result.budget_total == 6
