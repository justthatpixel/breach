from breach.attack.models import AttackData, Mitigation, Technique
from breach.engine.blocking import blocking_mitigation, effective_mitigations, resolve_hop
from breach.engine.models import ComponentDefence
from breach.levels.models import CardDef, GameMap


def make_attack_data(mitigates: dict[str, frozenset[str]]) -> AttackData:
    technique_ids = {t for ts in mitigates.values() for t in ts}
    mitigation_ids = set(mitigates)
    return AttackData(
        techniques={t: Technique(id=t, name=t, description="", platforms=[], tactics=[]) for t in technique_ids},
        mitigations={m: Mitigation(id=m, name=m, description="") for m in mitigation_ids},
        mitigates=mitigates,
    )


def make_game_map(cards: dict[str, tuple[int, list[str]]]) -> GameMap:
    return GameMap(
        component_types={},
        cards={cid: CardDef(cost=cost, mitigations=mits) for cid, (cost, mits) in cards.items()},
    )


def test_effective_mitigations_combines_cards_and_credits():
    game_map = make_game_map({"c1": (1, ["M1"]), "c2": (1, ["M2"])})
    defence = ComponentDefence(cards=["c1", "c2"], credited_mitigations=["M3"])
    assert effective_mitigations(defence, game_map) == frozenset({"M1", "M2", "M3"})


def test_effective_mitigations_empty_by_default():
    game_map = make_game_map({})
    assert effective_mitigations(ComponentDefence(), game_map) == frozenset()


def test_blocking_mitigation_returns_none_when_nothing_blocks():
    attack_data = make_attack_data({"M1": frozenset({"T1"})})
    assert blocking_mitigation("T2", frozenset({"M1"}), attack_data) is None


def test_blocking_mitigation_picks_first_alphabetically_when_several_block():
    attack_data = make_attack_data({"M2": frozenset({"T1"}), "M1": frozenset({"T1"})})
    assert blocking_mitigation("T1", frozenset({"M1", "M2"}), attack_data) == "M1"


def test_resolve_hop_picks_first_unblocked_by_id_order():
    attack_data = make_attack_data({"M1": frozenset({"T1"})})
    step = resolve_hop(1, "a", "b", ["T2", "T1"], frozenset({"M1"}), attack_data)
    assert step.technique_id == "T2"
    assert step.blocked is False
    assert step.blocked_by is None
    assert step.from_component == "a"
    assert step.to_component == "b"


def test_resolve_hop_all_blocked_records_first_candidate_as_blocked():
    attack_data = make_attack_data({"M1": frozenset({"T1"}), "M2": frozenset({"T2"})})
    step = resolve_hop(1, "a", "b", ["T2", "T1"], frozenset({"M1", "M2"}), attack_data)
    assert step.technique_id == "T1"
    assert step.blocked is True
    assert step.blocked_by == "M1"
