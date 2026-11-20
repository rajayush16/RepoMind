from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    language: str | None = None
    symbolType: str | None = None
    file: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphOut(BaseModel):
    available: bool
    reason: str | None
    nodes: list[GraphNode]
    edges: list[GraphEdge]
