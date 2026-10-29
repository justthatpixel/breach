from pathlib import Path

import pytest

from breach.attack import AttackData, load_attack_data

REPO_ROOT = Path(__file__).resolve().parents[3]
ATTACK_DATA_DIR = REPO_ROOT / "data" / "attack"
GAME_MAP_PATH = ATTACK_DATA_DIR / "game_map.yaml"
LEVELS_DIR = REPO_ROOT / "data" / "levels"


@pytest.fixture(scope="session")
def attack_data() -> AttackData:
    return load_attack_data(ATTACK_DATA_DIR)
