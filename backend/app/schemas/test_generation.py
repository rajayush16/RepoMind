import uuid
from datetime import datetime

from pydantic import BaseModel


class GenerateTestRequest(BaseModel):
    symbol_name: str
    file_path: str
    framework: str  # pytest | jest


class GeneratedTestOut(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    symbol_name: str
    file_path: str
    framework: str
    code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TestExecutionOut(BaseModel):
    # Not a pytest test class -- pytest's discovery heuristic matches on the
    # "Test" name prefix alone.
    __test__ = False

    id: uuid.UUID
    generated_test_id: uuid.UUID
    status: str
    output: str | None
    duration_ms: int | None
    created_at: datetime

    model_config = {"from_attributes": True}
