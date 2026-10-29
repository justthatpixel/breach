from ..attack.models import AttackData
from ..levels.models import GameMap, Level
from .blocking import effective_mitigations, resolve_hop
from .graph import enumerate_simple_paths
from .models import AttackPath, AttackStep, ComponentDefence, Defences, EngineResult
from .scoring import compute_score


def run_engine(
    level: Level,
    game_map: GameMap,
    attack_data: AttackData,
    defences: Defences,
) -> EngineResult:
    """Pure function: given a level, the game map, the ATT&CK data and what
    the player did, compute every attack path and the resulting score. No
    I/O, no LLM calls (HANDOFF §5)."""
    components_by_id = {c.id: c for c in level.components}
    raw_paths = enumerate_simple_paths(level)

    attack_paths: list[AttackPath] = []
    for raw_path in raw_paths:
        steps: list[AttackStep] = []
        step_number = 1
        for from_component, to_component in zip(raw_path, raw_path[1:]):
            component = components_by_id[to_component]
            techniques = game_map.techniques_for(component.type)
            if not techniques:
                # A pass-through node (no attack surface): the attacker
                # transits through it for free.
                continue
            defence = defences.get(to_component, ComponentDefence())
            mitigations = effective_mitigations(defence, game_map)
            steps.append(
                resolve_hop(
                    step_number, from_component, to_component, techniques, mitigations, attack_data
                )
            )
            step_number += 1
        attack_paths.append(AttackPath(steps=steps))

    budget_used = sum(
        game_map.cards[card_id].cost
        for defence in defences.values()
        for card_id in defence.cards
    )

    return compute_score(attack_paths, budget_used, level.budget)
