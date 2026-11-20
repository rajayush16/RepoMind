import uuid
from datetime import datetime

from pydantic import BaseModel


class RootCauseAnalysis(BaseModel):
    root_cause: str
    confidence_explanation: str
    suggested_fix: str
    potential_side_effects: str


class StartInvestigationRequest(BaseModel):
    bug_description: str
    error_message: str | None = None
    stack_trace: str | None = None


class InvestigationStepOut(BaseModel):
    id: uuid.UUID
    stage: str
    summary: str
    evidence: list | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvestigationOut(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    bug_description: str
    error_message: str | None
    stack_trace: str | None
    status: str
    root_cause: str | None
    confidence_explanation: str | None
    suggested_fix: str | None
    potential_side_effects: str | None
    error_detail: str | None
    created_at: datetime
    steps: list[InvestigationStepOut] = []

    model_config = {"from_attributes": True}
