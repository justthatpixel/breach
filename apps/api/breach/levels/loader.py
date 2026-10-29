from pathlib import Path

import yaml

from ..attack.models import AttackData
from .models import GameMap, Level


class LevelValidationError(ValueError):
    """A level or game map fails validation against the ATT&CK data or itself."""


def load_game_map(path: Path, attack_data: AttackData) -> GameMap:
    raw = yaml.safe_load(path.read_text())
    game_map = GameMap.model_validate(raw)

    for component_type, type_def in game_map.component_types.items():
        for technique_id in type_def.techniques:
            if technique_id not in attack_data.techniques:
                raise LevelValidationError(
                    f"game_map component type {component_type!r} references "
                    f"unknown technique {technique_id!r}"
                )

    for card_id, card in game_map.cards.items():
        for mitigation_id in card.mitigations:
            if mitigation_id not in attack_data.mitigations:
                raise LevelValidationError(
                    f"game_map card {card_id!r} references unknown mitigation "
                    f"{mitigation_id!r}"
                )

    return game_map


def load_level(path: Path, game_map: GameMap) -> Level:
    raw = yaml.safe_load(path.read_text())
    level = Level.model_validate(raw)

    known_types = game_map.known_component_types()
    for component in level.components:
        if component.type not in known_types:
            raise LevelValidationError(
                f"level {level.id!r} component {component.id!r} has unknown "
                f"type {component.type!r}"
            )

    component_ids = level.component_ids()
    if len(component_ids) != len(level.components):
        raise LevelValidationError(f"level {level.id!r} has duplicate component ids")

    for from_id, to_id in level.edges:
        for endpoint in (from_id, to_id):
            if endpoint not in component_ids:
                raise LevelValidationError(
                    f"level {level.id!r} edge references unknown component "
                    f"{endpoint!r}"
                )

    for entry_point in level.entry_points:
        if entry_point not in component_ids:
            raise LevelValidationError(
                f"level {level.id!r} entry point {entry_point!r} is not a "
                f"known component"
            )

    for card_id in level.cards_available:
        if card_id not in game_map.cards:
            raise LevelValidationError(
                f"level {level.id!r} offers unknown card {card_id!r}"
            )

    if not any(c.asset for c in level.components):
        raise LevelValidationError(f"level {level.id!r} has no asset component")

    return level
