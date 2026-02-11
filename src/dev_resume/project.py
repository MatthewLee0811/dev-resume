"""Project auto-detection: git root priority, cwd fallback."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def detect_project_root(override: str | None = None) -> Path:
    """Detect project root directory.

    Priority:
      1. --path override (if given)
      2. git rev-parse --show-toplevel
      3. current working directory
    """
    if override:
        return Path(override).resolve()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def project_hash(project_root: Path) -> str:
    """Stable hash from absolute path — used as session filename."""
    return hashlib.sha256(str(project_root).encode()).hexdigest()[:12]


def project_name(project_root: Path) -> str:
    """Human-readable name extracted from directory name."""
    return project_root.name
