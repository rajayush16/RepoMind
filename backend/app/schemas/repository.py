import uuid
from datetime import datetime

from pydantic import BaseModel


class AvailableGithubRepo(BaseModel):
    github_repo_id: int
    owner: str
    name: str
    full_name: str
    description: str | None
    default_branch: str
    primary_language: str | None
    is_private: bool
    already_connected: bool


class ConnectRepositoryRequest(BaseModel):
    github_repo_id: int
    owner: str
    name: str
    full_name: str
    description: str | None = None
    default_branch: str = "main"
    selected_branch: str | None = None
    primary_language: str | None = None
    is_private: bool = False


class RepositoryOut(BaseModel):
    id: uuid.UUID
    owner: str
    name: str
    full_name: str
    description: str | None
    default_branch: str
    selected_branch: str
    primary_language: str | None
    is_private: bool
    indexing_status: str
    file_count: int
    symbol_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
