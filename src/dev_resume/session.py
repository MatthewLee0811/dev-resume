"""Session persistence — load / save JSON session files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".dev-resume"
SESSIONS_DIR = CONFIG_DIR / "sessions"


def _ensure_dirs() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def session_path(project_hash: str) -> Path:
    _ensure_dirs()
    return SESSIONS_DIR / f"{project_hash}.json"


def load_session(project_hash: str) -> dict[str, Any] | None:
    """Load existing session, or None if first run."""
    path = session_path(project_hash)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_session(
    project_hash: str,
    *,
    project_name: str,
    project_path: str,
    done: str = "",
    next_todo: str = "",
    history: list[dict[str, str]] | None = None,
) -> Path:
    """Save (or update) session file. Returns the path written."""
    path = session_path(project_hash)
    now = datetime.now(timezone.utc).isoformat()

    existing = load_session(project_hash)
    if existing is None:
        existing = {
            "project_name": project_name,
            "project_path": project_path,
            "created_at": now,
            "history": [],
        }

    # Append to history only when there is content
    if done or next_todo:
        entry: dict[str, str] = {"timestamp": now}
        if done:
            entry["done"] = done
        if next_todo:
            entry["next_todo"] = next_todo
        existing.setdefault("history", []).append(entry)

    existing["updated_at"] = now
    existing["last_done"] = done
    existing["last_next_todo"] = next_todo

    if history is not None:
        existing["history"] = history

    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def create_session(
    project_hash: str,
    *,
    project_name: str,
    project_path: str,
    initial_task: str = "",
) -> Path:
    """Create a brand-new session for first run."""
    return save_session(
        project_hash,
        project_name=project_name,
        project_path=project_path,
        next_todo=initial_task,
    )
