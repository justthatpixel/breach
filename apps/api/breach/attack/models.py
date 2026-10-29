from pydantic import BaseModel, ConfigDict


class Technique(BaseModel):
    id: str
    name: str
    description: str
    platforms: list[str]
    tactics: list[str]


class Mitigation(BaseModel):
    id: str
    name: str
    description: str


class AttackData(BaseModel):
    """Curated MITRE ATT&CK subset: techniques, mitigations, and which
    mitigations actually mitigate which techniques."""

    techniques: dict[str, Technique]
    mitigations: dict[str, Mitigation]
    mitigates: dict[str, frozenset[str]]  # mitigation_id -> technique_ids it mitigates

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def mitigates_technique(self, mitigation_id: str, technique_id: str) -> bool:
        return technique_id in self.mitigates.get(mitigation_id, frozenset())
