from pydantic import BaseModel


class SearchResultOut(BaseModel):
    file_path: str
    symbol_name: str | None
    symbol_type: str | None
    start_line: int | None
    end_line: int | None
    snippet: str
    sources: list[str]
    score: float
