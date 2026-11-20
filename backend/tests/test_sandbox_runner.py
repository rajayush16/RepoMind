from app.services.sandbox.docker_runner import run_tests_in_sandbox


def test_sandbox_reports_unavailable_without_docker() -> None:
    """Docker genuinely isn't installed in this environment, so this is a real
    (not mocked) check that we report the honest status rather than claiming
    tests passed when nothing actually ran."""
    result = run_tests_in_sandbox("pytest", "def test_x():\n    assert True\n")
    assert result.status == "sandbox_unavailable"
    assert result.duration_ms is None
    assert "Docker" in result.output


def test_sandbox_reports_unsupported_framework() -> None:
    result = run_tests_in_sandbox("junit", "class FooTest {}")
    assert result.status == "unsupported_framework"
