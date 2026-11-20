from dataclasses import dataclass

from app.core.config import Settings
from app.services.graph.queries import get_callers


@dataclass
class ImpactResult:
    symbol_name: str
    available: bool
    reason: str | None
    direct_callers: list[dict]
    dependent_files: list[str]
    risk: str


def _risk_level(caller_count: int) -> str:
    if caller_count == 0:
        return "low"
    if caller_count <= 5:
        return "medium"
    return "high"


async def analyse_change_impact(settings: Settings, repository_id: str, symbol_name: str) -> ImpactResult:
    """Change-impact analysis built entirely from the Neo4j code graph (direct
    callers of the symbol, and the distinct files those callers live in) -- no
    speculative AI commentary layered on top, so every number here is a real,
    statically discovered relationship, never a guess."""
    try:
        callers = await get_callers(settings, repository_id, symbol_name)
    except Exception as exc:  # noqa: BLE001
        return ImpactResult(
            symbol_name=symbol_name,
            available=False,
            reason=str(exc),
            direct_callers=[],
            dependent_files=[],
            risk="unknown",
        )

    dependent_files = sorted({c["file_path"] for c in callers if c.get("file_path")})

    return ImpactResult(
        symbol_name=symbol_name,
        available=True,
        reason=None,
        direct_callers=callers,
        dependent_files=dependent_files,
        risk=_risk_level(len(callers)),
    )
