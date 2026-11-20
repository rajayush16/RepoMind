import uuid

from pydantic import BaseModel


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    is_personal: bool

    model_config = {"from_attributes": True}
