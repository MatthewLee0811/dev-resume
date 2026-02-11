"""Environment detection and config persistence (~/.dev-resume/config.json)."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

CONFIG_DIR = Path.home() / ".dev-resume"
CONFIG_PATH = CONFIG_DIR / "config.json"


# ── config load / save ───────────────────────────────────────────────


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict) -> None:
    _ensure_dir()
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── auto-detection ───────────────────────────────────────────────────


def _has_ssh_connection() -> bool:
    return bool(os.environ.get("SSH_CONNECTION"))


def _is_narrow_terminal(threshold: int = 100) -> bool:
    size = shutil.get_terminal_size(fallback=(120, 24))
    return size.columns < threshold


def detect_environment() -> str:
    """Heuristic: 'mobile' if SSH + narrow terminal, else 'pc'."""
    if _has_ssh_connection() and _is_narrow_terminal():
        return "mobile"
    return "pc"


# ── public API ───────────────────────────────────────────────────────


def get_environment() -> str:
    """Return environment with priority: config.json > auto-detect."""
    config = load_config()
    env = config.get("environment")
    if env in ("mobile", "pc"):
        return env
    return detect_environment()


def set_environment(env: str) -> None:
    """Persist environment choice to config.json."""
    config = load_config()
    config["environment"] = env
    save_config(config)
