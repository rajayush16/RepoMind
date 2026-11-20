import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.services.parsing.languages import language_for_path

EXCLUDED_DIR_NAMES = {
    ".git",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "out",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".next",
    ".turbo",
    "target",
    "bin",
    "obj",
    ".idea",
    ".vscode",
}

EXCLUDED_FILENAMES = {
    ".env",
    ".env.local",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
}

EXCLUDED_FILE_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".lock")

MAX_FILE_SIZE_BYTES = 1_000_000  # 1 MB


@dataclass(frozen=True)
class IndexableFile:
    relative_path: str
    language: str


def _is_excluded_path(relative_path: str) -> bool:
    parts = Path(relative_path).parts
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    name = parts[-1] if parts else relative_path
    if name in EXCLUDED_FILENAMES or name.startswith(".env"):
        return True
    if name.endswith(EXCLUDED_FILE_SUFFIXES):
        return True
    return False


def list_tracked_files(repo_dir: Path) -> list[str]:
    """Files tracked by git in the clone -- already excludes anything .gitignore hides."""
    result = subprocess.run(
        ["git", "-C", str(repo_dir), "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    raw = result.stdout.decode("utf-8", errors="replace")
    return [p for p in raw.split("\0") if p]


def list_indexable_files(repo_dir: Path) -> list[IndexableFile]:
    indexable: list[IndexableFile] = []

    for relative_path in list_tracked_files(repo_dir):
        if _is_excluded_path(relative_path):
            continue

        language = language_for_path(relative_path)
        if language is None:
            continue

        full_path = repo_dir / relative_path
        try:
            if not full_path.is_file() or full_path.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
        except OSError:
            continue

        indexable.append(IndexableFile(relative_path=relative_path, language=language))

    return indexable
