from pathlib import Path

import pytest

from breach.attack import AttackData, load_attack_data
from breach.levels import GameMap, Level, load_game_map, load_level

REPO_ROOT = Path(__file__).resolve().parents[3]
ATTACK_DATA_DIR = REPO_ROOT / "data" / "attack"
GAME_MAP_PATH = ATTACK_DATA_DIR / "game_map.yaml"
LEVELS_DIR = REPO_ROOT / "data" / "levels"


@pytest.fixture(scope="session")
def attack_data() -> AttackData:
    return load_attack_data(ATTACK_DATA_DIR)


@pytest.fixture(scope="session")
def game_map(attack_data: AttackData) -> GameMap:
    return load_game_map(GAME_MAP_PATH, attack_data)


@pytest.fixture(scope="session")
def level3(game_map: GameMap) -> Level:
    return load_level(LEVELS_DIR / "03-payments.yaml", game_map)
