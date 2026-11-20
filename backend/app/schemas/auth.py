import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    github_username: str | None
    github_avatar_url: str | None
    github_connected: bool

    model_config = {"from_attributes": True}
