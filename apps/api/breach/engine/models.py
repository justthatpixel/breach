from pydantic import BaseModel, ConfigDict, Field


class ComponentDefence(BaseModel):
    """What the player did to one component: cards they played, plus
    mitigations the judge (§6) credited from their notes. Until M5 exists,
    callers pass credited_mitigations=[] directly."""

    cards: list[str] = Field(default_factory=list)
    credited_mitigations: list[str] = Field(default_factory=list)


# component_id -> what the player did there. Components with no entry get
# no cards and no credited mitigations.
Defences = dict[str, ComponentDefence]


class AttackStep(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    step: int
    from_component: str = Field(alias="from")
    to_component: str = Field(alias="to")
    technique_id: str
    blocked: bool
    blocked_by: str | None = None


class AttackPath(BaseModel):
    steps: list[AttackStep]

    @property
    def breached(self) -> bool:
        """A path is breached if every hop on it succeeded (HANDOFF §5.6).
        A path with zero steps (every component on it is a pass-through
        with no attack surface) is vacuously breached."""
        return all(not step.blocked for step in self.steps)


class EngineResult(BaseModel):
    paths: list[AttackPath]
    paths_total: int
    paths_blocked: int
    techniques_attempted: int
    techniques_stopped: int
    budget_used: int
    budget_total: int
    score: float
    grade: str
