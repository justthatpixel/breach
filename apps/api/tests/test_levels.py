import pytest
import yaml

from breach.levels import LevelValidationError, load_game_map, load_level

from .conftest import GAME_MAP_PATH, LEVELS_DIR


@pytest.fixture(scope="session")
def game_map(attack_data):
    return load_game_map(GAME_MAP_PATH, attack_data)


def test_game_map_loads_and_cross_validates(game_map):
    assert "waf" in game_map.cards
    assert game_map.cards["waf"].mitigations == ["M1050", "M1037"]
    assert "api_gateway" in game_map.component_types


def test_level_03_payments_loads(game_map):
    level = load_level(LEVELS_DIR / "03-payments.yaml", game_map)
    assert level.id == "03-payments"
    assert level.budget == 6
    assert level.entry_points == ["internet"]
    asset_ids = [c.id for c in level.components if c.asset]
    assert asset_ids == ["postgres"]


def test_every_card_mitigation_exists_in_attack_data(game_map, attack_data):
    for card in game_map.cards.values():
        for mitigation_id in card.mitigations:
            assert mitigation_id in attack_data.mitigations


def test_every_component_type_technique_exists_in_attack_data(game_map, attack_data):
    for type_def in game_map.component_types.values():
        for technique_id in type_def.techniques:
            assert technique_id in attack_data.techniques


def _write_level(tmp_path, data: dict):
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def _valid_level_dict():
    return {
        "id": "test",
        "title": "Test",
        "brief": "Test level",
        "threat_level": "low",
        "budget": 3,
        "components": [
            {"id": "internet", "type": "internet", "label": "Internet"},
            {"id": "gateway", "type": "api_gateway", "label": "Gateway", "public": True},
            {"id": "db", "type": "database", "label": "DB", "asset": True},
        ],
        "edges": [["internet", "gateway"], ["gateway", "db"]],
        "entry_points": ["internet"],
        "cards_available": ["waf"],
    }


def test_rejects_unknown_component_type(tmp_path, game_map):
    data = _valid_level_dict()
    data["components"][1]["type"] = "not_a_real_type"
    with pytest.raises(LevelValidationError):
        load_level(_write_level(tmp_path, data), game_map)


def test_rejects_edge_to_unknown_component(tmp_path, game_map):
    data = _valid_level_dict()
    data["edges"].append(["gateway", "nonexistent"])
    with pytest.raises(LevelValidationError):
        load_level(_write_level(tmp_path, data), game_map)


def test_rejects_unknown_card(tmp_path, game_map):
    data = _valid_level_dict()
    data["cards_available"].append("not_a_real_card")
    with pytest.raises(LevelValidationError):
        load_level(_write_level(tmp_path, data), game_map)


def test_rejects_unknown_entry_point(tmp_path, game_map):
    data = _valid_level_dict()
    data["entry_points"] = ["nope"]
    with pytest.raises(LevelValidationError):
        load_level(_write_level(tmp_path, data), game_map)


def test_rejects_level_with_no_asset(tmp_path, game_map):
    data = _valid_level_dict()
    data["components"][2]["asset"] = False
    with pytest.raises(LevelValidationError):
        load_level(_write_level(tmp_path, data), game_map)


def test_rejects_duplicate_component_ids(tmp_path, game_map):
    data = _valid_level_dict()
    data["components"].append({"id": "gateway", "type": "database", "label": "Dup"})
    with pytest.raises(LevelValidationError):
        load_level(_write_level(tmp_path, data), game_map)


def test_game_map_rejects_card_with_unknown_mitigation(tmp_path, attack_data):
    bad_map = {
        "component_types": {"api_gateway": {"techniques": ["T1190"]}},
        "cards": {"bogus": {"cost": 1, "mitigations": ["M9999"]}},
    }
    path = tmp_path / "game_map.yaml"
    path.write_text(yaml.safe_dump(bad_map))
    with pytest.raises(LevelValidationError):
        load_game_map(path, attack_data)
