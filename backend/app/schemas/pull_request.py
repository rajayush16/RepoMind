import uuid
from datetime import datetime

from pydantic import BaseModel


class ReviewFindingSchema(BaseModel):
    """Schema the LLM is asked to produce JSON matching (see generate_structured)."""

    file_path: str
    line: int | None = None
    severity: str  # "high" | "medium" | "low"
    category: str  # correctness | security | performance | maintainability | testing | architecture
    summary: str
    explanation: str
    suggestion: str | None = None


class PRReviewAnalysisSchema(BaseModel):
    summary: str
    findings: list[ReviewFindingSchema]


class StartReviewRequest(BaseModel):
    pr_number: int


class PublishReviewRequest(BaseModel):
    confirm: bool = False


class ReviewFindingOut(BaseModel):
    id: uuid.UUID
    file_path: str
    line: int | None
    severity: str
    category: str
    summary: str
    explanation: str
    suggestion: str | None

    model_config = {"from_attributes": True}


class PullRequestReviewOut(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    pr_number: int
    pr_title: str
    pr_url: str
    status: str
    summary: str | None
    published: bool
    published_comment_url: str | None
    error_detail: str | None
    created_at: datetime
    findings: list[ReviewFindingOut] = []

    model_config = {"from_attributes": True}
