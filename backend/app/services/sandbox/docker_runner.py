import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import docker
from docker.errors import DockerException

DEFAULT_TIMEOUT_SECONDS = 60
MAX_OUTPUT_CHARS = 8000

FRAMEWORK_CONFIG = {
    "pytest": {
        "image": "repomind-sandbox-python:latest",
        "filename": "test_generated.py",
        "command": ["pytest", "test_generated.py", "-v"],
    },
    "jest": {
        "image": "repomind-sandbox-node:latest",
        "filename": "generated.test.js",
        "command": ["npx", "jest", "generated.test.js"],
    },
}


@dataclass
class SandboxResult:
    # passed | failed | sandbox_unavailable | unsupported_framework
    status: str
    output: str
    duration_ms: int | None


def run_tests_in_sandbox(
    framework: str, test_code: str, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> SandboxResult:
    """Runs generated test code in an ephemeral, isolated Docker container.

    Never reports "passed" unless a real container actually ran the test and
    exited 0. If Docker isn't reachable, this returns "sandbox_unavailable" with
    a clear reason -- it never fakes a result.

    Only pytest and Jest are supported; JUnit (full compile step) is not
    implemented yet (see IMPLEMENTATION_PLAN.md).
    """
    config = FRAMEWORK_CONFIG.get(framework)
    if config is None:
        return SandboxResult(
            status="unsupported_framework",
            output=f"Sandbox execution for framework '{framework}' is not implemented.",
            duration_ms=None,
        )

    try:
        client = docker.from_env()
        client.ping()
    except DockerException as exc:
        return SandboxResult(status="sandbox_unavailable", output=f"Docker is not available: {exc}", duration_ms=None)

    with tempfile.TemporaryDirectory(prefix="repomind-sandbox-") as tmp:
        workdir = Path(tmp)
        (workdir / config["filename"]).write_text(test_code, encoding="utf-8")

        start = time.monotonic()
        container = None
        try:
            container = client.containers.run(
                config["image"],
                command=config["command"],
                working_dir="/workspace",
                volumes={str(workdir): {"bind": "/workspace", "mode": "rw"}},
                network_disabled=True,
                mem_limit="256m",
                nano_cpus=1_000_000_000,  # 1 CPU
                read_only=True,
                tmpfs={"/tmp": "size=64m"},
                detach=True,
            )
            wait_result = container.wait(timeout=timeout_seconds)
            exit_code = wait_result.get("StatusCode", 1)
            output = container.logs().decode("utf-8", errors="replace")
        except DockerException as exc:
            return SandboxResult(
                status="sandbox_unavailable", output=f"Sandbox execution failed: {exc}", duration_ms=None
            )
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except DockerException:
                    pass

        duration_ms = int((time.monotonic() - start) * 1000)
        status = "passed" if exit_code == 0 else "failed"
        return SandboxResult(status=status, output=output[-MAX_OUTPUT_CHARS:], duration_ms=duration_ms)
