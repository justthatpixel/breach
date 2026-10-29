from ..attack.models import AttackData
from ..levels.models import GameMap
from .models import AttackStep, ComponentDefence


def effective_mitigations(defence: ComponentDefence, game_map: GameMap) -> frozenset[str]:
    """A component's effective mitigation set: card mitigations plus
    judge-credited mitigations (HANDOFF §5.4)."""
    mitigations: set[str] = set(defence.credited_mitigations)
    for card_id in defence.cards:
        mitigations.update(game_map.cards[card_id].mitigations)
    return frozenset(mitigations)


def blocking_mitigation(
    technique_id: str, mitigations: frozenset[str], attack_data: AttackData
) -> str | None:
    """The mitigation that blocks this technique, or None. When several of
    the component's mitigations would block it, the lexicographically
    first one is recorded, for determinism."""
    blockers = sorted(
        m for m in mitigations if attack_data.mitigates_technique(m, technique_id)
    )
    return blockers[0] if blockers else None


def resolve_hop(
    step_number: int,
    from_component: str,
    to_component: str,
    candidate_techniques: list[str],
    mitigations: frozenset[str],
    attack_data: AttackData,
) -> AttackStep:
    """Pick the one technique the engine records for a hop into
    `to_component`: the first (sorted by ID) candidate that isn't blocked.
    If every candidate is blocked, the hop fails; record the first (sorted)
    candidate as the blocked attempt (HANDOFF §5.5)."""
    ordered = sorted(candidate_techniques)
    blocked_by = {t: blocking_mitigation(t, mitigations, attack_data) for t in ordered}

    for technique_id in ordered:
        if blocked_by[technique_id] is None:
            return AttackStep(
                step=step_number,
                **{"from": from_component, "to": to_component},
                technique_id=technique_id,
                blocked=False,
                blocked_by=None,
            )

    first_technique = ordered[0]
    return AttackStep(
        step=step_number,
        **{"from": from_component, "to": to_component},
        technique_id=first_technique,
        blocked=True,
        blocked_by=blocked_by[first_technique],
    )
