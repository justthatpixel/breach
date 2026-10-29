from pydantic import BaseModel


class CreditedMitigation(BaseModel):
    mitigation_id: str  # must be one of the candidates passed in — verified in code, not trusted from the model
    evidence: str  # must be a real substring of the player's notes — verified in code
    confidence: float


class JudgeOutput(BaseModel):
    credited: list[CreditedMitigation]
    rejected_claims: list[str]
    injection_suspected: bool
