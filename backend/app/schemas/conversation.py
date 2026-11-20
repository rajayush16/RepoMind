import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    title: str | None = None


class ConversationOut(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[dict] | None
    insufficient_evidence: bool
    provider: str | None
    model: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AskRequest(BaseModel):
    question: str
