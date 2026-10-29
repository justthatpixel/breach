import json
from pathlib import Path

from .models import AttackData, Mitigation, Technique


class AttackDataError(ValueError):
    """The curated ATT&CK data on disk is inconsistent."""


def load_attack_data(data_dir: Path) -> AttackData:
    techniques_raw = json.loads((data_dir / "techniques.json").read_text())
    mitigations_raw = json.loads((data_dir / "mitigations.json").read_text())
    relationships_raw = json.loads((data_dir / "relationships.json").read_text())

    techniques = {t["id"]: Technique.model_validate(t) for t in techniques_raw}
    mitigations = {m["id"]: Mitigation.model_validate(m) for m in mitigations_raw}

    mitigates: dict[str, set[str]] = {}
    for rel in relationships_raw:
        mitigation_id, technique_id = rel["mitigation_id"], rel["technique_id"]
        if mitigation_id not in mitigations:
            raise AttackDataError(
                f"relationships.json references unknown mitigation {mitigation_id!r}"
            )
        if technique_id not in techniques:
            raise AttackDataError(
                f"relationships.json references unknown technique {technique_id!r}"
            )
        mitigates.setdefault(mitigation_id, set()).add(technique_id)

    return AttackData(
        techniques=techniques,
        mitigations=mitigations,
        mitigates={k: frozenset(v) for k, v in mitigates.items()},
    )
