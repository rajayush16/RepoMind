import subprocess
from pathlib import Path

import pytest

from app.services.indexing.clone import CloneError, clone_repository
from app.services.indexing.filters import list_indexable_files


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "fixture-repo"
    repo_dir.mkdir()

    _run("git", "init", "-q", "-b", "main", cwd=repo_dir)
    _run("git", "config", "user.email", "test@example.com", cwd=repo_dir)
    _run("git", "config", "user.name", "Test", cwd=repo_dir)

    (repo_dir / "app.py").write_text("def main():\n    return 1\n")
    (repo_dir / "README.md").write_text("# fixture\n")

    (repo_dir / "node_modules").mkdir()
    (repo_dir / "node_modules" / "dep.js").write_text("module.exports = {};\n")

    (repo_dir / ".env").write_text("SECRET=should-not-be-indexed\n")

    gitignore = repo_dir / ".gitignore"
    gitignore.write_text("node_modules/\n.env\n")

    _run("git", "add", "-A", cwd=repo_dir)
    _run("git", "commit", "-q", "-m", "initial commit", cwd=repo_dir)

    return repo_dir


def test_clone_repository_shallow_clones_local_fixture(fixture_repo: Path) -> None:
    with clone_repository(str(fixture_repo), branch="main") as (workdir, commit_sha):
        assert (workdir / "app.py").exists()
        assert len(commit_sha) == 40

    assert not workdir.exists()  # cleaned up after the context manager exits


def test_clone_repository_rejects_unknown_branch(fixture_repo: Path) -> None:
    with pytest.raises(CloneError):
        with clone_repository(str(fixture_repo), branch="does-not-exist"):
            pass


def test_clone_repository_rejects_malicious_branch_name(fixture_repo: Path) -> None:
    with pytest.raises(CloneError):
        with clone_repository(str(fixture_repo), branch="--upload-pack=evil"):
            pass


def test_list_indexable_files_respects_gitignore_and_exclusions(fixture_repo: Path) -> None:
    with clone_repository(str(fixture_repo), branch="main") as (workdir, _):
        files = list_indexable_files(workdir)

    relative_paths = {f.relative_path for f in files}
    assert relative_paths == {"app.py"}
