from pydantic import BaseModel


class CallerOut(BaseModel):
    name: str
    file_path: str | None


class DependentFileOut(BaseModel):
    file_path: str


class ImpactAnalysisOut(BaseModel):
    symbol_name: str
    available: bool
    reason: str | None
    direct_callers: list[CallerOut]
    dependent_files: list[DependentFileOut]
    risk: str  # "low" | "medium" | "high" | "unknown"
