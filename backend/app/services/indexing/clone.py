import os
import re
import shutil
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

BRANCH_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]*$")


class CloneError(Exception):
    pass


def _authenticated_url(url: str, access_token: str | None) -> str:
    if not access_token or not url.startswith("https://"):
        return url
    return url.replace("https://", f"https://x-access-token:{access_token}@", 1)


def _redact(text: str, access_token: str | None) -> str:
    if access_token:
        text = text.replace(access_token, "***")
    return text


def _validate_branch_name(branch: str) -> None:
    if not branch or not BRANCH_NAME_PATTERN.match(branch):
        raise CloneError(f"Refusing to clone: invalid branch name {branch!r}.")


def _force_remove_readonly(func, path, _exc_info) -> None:
    """Git marks pack/object files read-only; retry after clearing that bit.

    Needed because shutil.rmtree(ignore_errors=True) would otherwise silently
    leave the clone behind on Windows instead of actually cleaning it up.
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


@contextmanager
def clone_repository(url: str, branch: str, access_token: str | None = None):
    """Shallow-clone a single branch into a temporary directory.

    Yields (workdir, commit_sha) and always removes the clone afterwards, even on
    failure. Never runs any code from the cloned repository -- only `git` itself.
    """
    _validate_branch_name(branch)
    workdir = Path(tempfile.mkdtemp(prefix="repomind-clone-"))

    try:
        clone_url = _authenticated_url(url, access_token)
        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                "--single-branch",
                "--",
                clone_url,
                str(workdir),
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise CloneError(f"git clone failed: {_redact(result.stderr.strip(), access_token)}")

        commit_result = subprocess.run(
            ["git", "-C", str(workdir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_sha = commit_result.stdout.strip()

        yield workdir, commit_sha
    finally:
        shutil.rmtree(workdir, onerror=_force_remove_readonly)
