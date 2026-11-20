import pytest

from app.services.graph import queries as graph_queries
from tests.conftest import get_test_settings


class _FakeResult:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __aiter__(self):
        return self._iter()

    async def _iter(self):
        for row in self._rows:
            yield _FakeRecord(row)


class _FakeRecord:
    def __init__(self, row: dict) -> None:
        self._row = row

    def data(self) -> dict:
        return self._row


class _FakeSession:
    def __init__(self, responses: dict[str, list[dict]]) -> None:
        self._responses = responses
        self._call_index = 0

    async def run(self, query: str, **kwargs):
        # Dispatch by a distinguishing keyword in the query text, in call order
        # matching get_repository_graph's four sequential queries.
        if "RETURN f.path AS path, f.language" in query:
            return _FakeResult(self._responses["files"])
        if "DEFINES]->(s:Symbol)" in query and "RETURN s.name AS name" in query:
            return _FakeResult(self._responses["symbols"])
        if "CALLS]->(callee:Symbol)" in query:
            return _FakeResult(self._responses["calls"])
        if "IMPORTS]->(m:Module)" in query:
            return _FakeResult(self._responses["imports"])
        raise AssertionError(f"Unexpected query: {query}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeDriver:
    def __init__(self, responses: dict[str, list[dict]]) -> None:
        self._responses = responses

    def session(self):
        return _FakeSession(self._responses)

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_repository_graph_produces_consistent_node_and_edge_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = {
        "files": [{"path": "app.py", "language": "python"}],
        "symbols": [
            {"name": "helper", "type": "function", "file_path": "app.py"},
            {"name": "run", "type": "method", "file_path": "app.py"},
        ],
        "calls": [
            {"caller": "run", "caller_file": "app.py", "callee": "helper", "callee_file": "app.py"},
            # Unresolved callee (no defining file) -- must be dropped, not linked
            # to a node id that doesn't exist.
            {"caller": "run", "caller_file": "app.py", "callee": "print", "callee_file": None},
        ],
        "imports": [{"file_path": "app.py", "module": "os"}],
    }

    monkeypatch.setattr(graph_queries, "_driver", lambda settings: _FakeDriver(responses))

    graph = await graph_queries.get_repository_graph(get_test_settings(), "repo-123")

    assert graph["available"] is True
    node_ids = {n["id"] for n in graph["nodes"]}
    assert "file:app.py" in node_ids
    assert "symbol:app.py:helper" in node_ids
    assert "symbol:app.py:run" in node_ids
    assert "module:os" in node_ids

    edge_pairs = {(e["source"], e["target"], e["type"]) for e in graph["edges"]}
    assert ("file:app.py", "symbol:app.py:helper", "DEFINES") in edge_pairs
    assert ("file:app.py", "symbol:app.py:run", "DEFINES") in edge_pairs
    assert ("file:app.py", "module:os", "IMPORTS") in edge_pairs
    assert ("symbol:app.py:run", "symbol:app.py:helper", "CALLS") in edge_pairs

    # Every edge endpoint must reference a node that actually exists in the
    # response -- this is exactly the bug this test guards against.
    for source, target, _ in edge_pairs:
        assert source in node_ids
        assert target in node_ids


class _RecordingSession:
    """Mirrors neo4j.AsyncSession.run's real signature -- its first positional
    parameter is itself named `query` -- so a caller that also passes a `query=`
    keyword (a real bug caught in find_symbols_by_name) raises here exactly as it
    would against the real driver."""

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows
        self.calls: list[dict] = []

    async def run(self, query: str, **kwargs):
        self.calls.append(kwargs)
        return _FakeResult(self._rows)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _RecordingDriver:
    def __init__(self, session: _RecordingSession) -> None:
        self._session = session

    def session(self):
        return self._session

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_find_symbols_by_name_does_not_collide_with_run_s_own_query_kwarg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _RecordingSession([{"name": "authenticate", "type": "function", "start_line": 1, "end_line": 2, "file_path": "auth.py"}])
    monkeypatch.setattr(graph_queries, "_driver", lambda settings: _RecordingDriver(session))

    results = await graph_queries.find_symbols_by_name(get_test_settings(), "repo-123", "auth")

    assert results[0]["name"] == "authenticate"
    assert session.calls[0]["search_term"] == "auth"
    assert "query" not in session.calls[0]
