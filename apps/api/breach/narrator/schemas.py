from pydantic import BaseModel


class ReplayStep(BaseModel):
    step: int
    technique_id: str  # must exist in the engine output — verified in code
    line: str


class Debrief(BaseModel):
    through: list[str]
    held: list[str]
    tips: list[str]


class NarratorOutput(BaseModel):
    steps: list[ReplayStep]
    debrief: Debrief
