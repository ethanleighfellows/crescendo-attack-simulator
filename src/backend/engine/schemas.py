from pydantic import BaseModel


class AttackData(BaseModel):
    """Structured output from the red-team attacker model."""
    generated_question: str
    last_response_summary: str
    rationale_behind_jailbreak: str


class RefusalData(BaseModel):
    """Structured output from the refusal judge."""
    value: bool
    rationale: str
    metadata: int


class EvalData(BaseModel):
    """Structured output from the eval judge."""
    value: bool
    description: str
    rationale: str
    metadata: int
