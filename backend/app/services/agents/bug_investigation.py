import uuid
from datetime import datetime, timezone
from typing import TypedDict

import structlog
from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.models.investigation import Investigation, InvestigationStatus, InvestigationStep
from app.services.agents.stack_trace import extract_search_terms
from app.services.graph.queries import get_callers
from app.services.llm.base import ChatMessage, LLMProvider
from app.services.retrieval.hybrid import hybrid_search
from app.schemas.investigation import RootCauseAnalysis

logger = structlog.get_logger(__name__)

NO_EVIDENCE_ROOT_CAUSE = (
    "Not enough evidence in the indexed codebase to identify a root cause. The "
    "search terms extracted from this report didn't match any indexed file or "
    "symbol in this repository."
)


class InvestigationState(TypedDict, total=False):
    repository_id: str
    bug_description: str
    error_message: str | None
    stack_trace: str | None
    search_terms: list[str]
    evidence: list[dict]
    callers: list[dict]
    root_cause: str
    confidence_explanation: str
    suggested_fix: str
    potential_side_effects: str
    steps: list[dict]


def _add_step(state: InvestigationState, stage: str, summary: str, evidence: list | None = None) -> None:
    state.setdefault("steps", []).append({"stage": stage, "summary": summary, "evidence": evidence})


def build_investigation_graph(db: AsyncSession, settings: Settings, provider: LLMProvider):
    async def parse_issue(state: InvestigationState) -> InvestigationState:
        terms = extract_search_terms(
            state["bug_description"], state.get("error_message"), state.get("stack_trace")
        )
        state["search_terms"] = terms
        _add_step(
            state,
            "parse_issue",
            f"Extracted {len(terms)} search term(s) from the report: {', '.join(terms) or '(none)'}.",
            terms,
        )
        return state

    async def find_related_symbols(state: InvestigationState) -> InvestigationState:
        # Search terms must be queried independently, not joined into one string:
        # hybrid_search's lexical/symbol paths do substring matching, so e.g.
        # "authenticate check_password" would never match any single symbol name
        # even though "authenticate" and "check_password" individually would.
        terms = state["search_terms"][:6] or [state["bug_description"]]
        seen: set[tuple[str, str | None, int | None]] = set()
        results = []
        for term in terms:
            for result in await hybrid_search(db, settings, uuid.UUID(state["repository_id"]), term):
                key = (result.file_path, result.symbol_name, result.start_line)
                if key not in seen:
                    seen.add(key)
                    results.append(result)

        evidence = [
            {
                "file_path": r.file_path,
                "symbol_name": r.symbol_name,
                "symbol_type": r.symbol_type,
                "start_line": r.start_line,
                "end_line": r.end_line,
                "snippet": r.snippet,
            }
            for r in results
        ]
        state["evidence"] = evidence
        _add_step(
            state,
            "find_related_symbols",
            f"Found {len(evidence)} potentially related symbol(s)/file(s) in the index.",
            evidence,
        )
        return state

    async def trace_execution(state: InvestigationState) -> InvestigationState:
        callers: list[dict] = []
        for item in state.get("evidence", [])[:5]:
            if not item.get("symbol_name"):
                continue
            try:
                found = await get_callers(settings, state["repository_id"], item["symbol_name"])
            except Exception as exc:  # noqa: BLE001
                logger.info("trace_execution_skipped", reason=str(exc))
                found = []
            callers.extend(found)

        state["callers"] = callers
        _add_step(
            state,
            "trace_execution",
            f"Traced {len(callers)} caller relationship(s) via the code graph"
            + ("" if callers else " (Neo4j may be unreachable, or nothing calls this)."),
            callers,
        )
        return state

    async def evaluate_causes(state: InvestigationState) -> InvestigationState:
        if not state.get("evidence"):
            state["root_cause"] = NO_EVIDENCE_ROOT_CAUSE
            state["confidence_explanation"] = "No supporting evidence was retrieved from this repository's index."
            state["suggested_fix"] = ""
            state["potential_side_effects"] = ""
            _add_step(state, "evaluate_causes", "Skipped the model: no evidence to reason over.")
            return state

        evidence_text = "\n\n".join(
            f"[{e['file_path']}" + (f":{e['start_line']}" if e.get("start_line") else "") + f"]\n{e['snippet']}"
            for e in state["evidence"]
        )
        caller_text = "\n".join(
            f"{c.get('name')} (in {c.get('file_path')})" for c in state.get("callers", [])
        )
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a debugging assistant. Analyse the bug report using ONLY the "
                    "evidence provided. Never invent file paths or function names not in "
                    "the evidence. Be explicit about your reasoning and uncertainty."
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    f"Bug report: {state['bug_description']}\n"
                    f"Error message: {state.get('error_message') or '(none)'}\n"
                    f"Stack trace: {state.get('stack_trace') or '(none)'}\n\n"
                    f"Evidence from the repository:\n{evidence_text}\n\n"
                    f"Known callers of the evidence symbols:\n{caller_text or '(none found)'}"
                ),
            ),
        ]

        try:
            analysis = await provider.generate_structured(messages, schema=RootCauseAnalysis)
        except Exception as exc:  # noqa: BLE001
            _add_step(state, "evaluate_causes", f"Model call failed: {exc}")
            raise

        state["root_cause"] = analysis.root_cause
        state["confidence_explanation"] = analysis.confidence_explanation
        state["suggested_fix"] = analysis.suggested_fix
        state["potential_side_effects"] = analysis.potential_side_effects
        _add_step(state, "evaluate_causes", "Model produced a root-cause analysis from the retrieved evidence.")
        return state

    async def prepare_findings(state: InvestigationState) -> InvestigationState:
        _add_step(state, "prepare_findings", "Investigation complete.")
        return state

    graph = StateGraph(InvestigationState)
    graph.add_node("parse_issue", parse_issue)
    graph.add_node("find_related_symbols", find_related_symbols)
    graph.add_node("trace_execution", trace_execution)
    graph.add_node("evaluate_causes", evaluate_causes)
    graph.add_node("prepare_findings", prepare_findings)

    graph.set_entry_point("parse_issue")
    graph.add_edge("parse_issue", "find_related_symbols")
    graph.add_edge("find_related_symbols", "trace_execution")
    graph.add_edge("trace_execution", "evaluate_causes")
    graph.add_edge("evaluate_causes", "prepare_findings")
    graph.add_edge("prepare_findings", END)

    return graph.compile()


async def run_investigation(
    investigation_id: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    provider: LLMProvider,
) -> None:
    async with session_factory() as db:
        investigation = await db.get(Investigation, investigation_id)
        if investigation is None:
            return

        initial_state: InvestigationState = {
            "repository_id": str(investigation.repository_id),
            "bug_description": investigation.bug_description,
            "error_message": investigation.error_message,
            "stack_trace": investigation.stack_trace,
        }

        graph = build_investigation_graph(db, settings, provider)

        try:
            final_state = await graph.ainvoke(initial_state)
        except Exception as exc:  # noqa: BLE001
            investigation.status = InvestigationStatus.FAILED
            investigation.error_detail = f"{type(exc).__name__}: {exc}"
            await db.commit()
            return

        for step in final_state.get("steps", []):
            db.add(
                InvestigationStep(
                    investigation_id=investigation.id,
                    stage=step["stage"],
                    summary=step["summary"],
                    evidence=step.get("evidence"),
                )
            )

        investigation.status = InvestigationStatus.COMPLETE
        investigation.root_cause = final_state.get("root_cause")
        investigation.confidence_explanation = final_state.get("confidence_explanation")
        investigation.suggested_fix = final_state.get("suggested_fix")
        investigation.potential_side_effects = final_state.get("potential_side_effects")
        investigation.updated_at = datetime.now(timezone.utc)
        await db.commit()
