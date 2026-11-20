import uuid

from pydantic import BaseModel


class FileEntry(BaseModel):
    relative_path: str
    language: str
    symbol_count: int
    size_bytes: int


class FileContentOut(BaseModel):
    relative_path: str
    language: str
    content: str


class SymbolOut(BaseModel):
    id: uuid.UUID
    name: str
    symbol_type: str
    parent_name: str | None
    start_line: int
    end_line: int
    signature: str
    file_path: str

    model_config = {"from_attributes": True}
