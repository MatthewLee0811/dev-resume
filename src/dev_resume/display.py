"""Terminal display helpers — keeps cli.py clean."""

from __future__ import annotations

import sys
from typing import Any

# ANSI helpers
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    return f"{code}{text}{RESET}" if _supports_color() else text


def banner(title: str) -> None:
    print(f"\n  {_c(BOLD + CYAN, title)}")
    print(f"  {_c(DIM, '─' * 40)}")


def kv(key: str, value: str) -> None:
    print(f"  {_c(DIM, key + ':')} {value}")


def success(msg: str) -> None:
    print(f"\n  {_c(GREEN, '✓')} {msg}")


def warn(msg: str) -> None:
    print(f"\n  {_c(YELLOW, '!')} {msg}")


def show_session_summary(session: dict[str, Any]) -> None:
    """Print the last session state before launching claude."""
    banner(f"프로젝트: {session['project_name']}")
    kv("  경로", session["project_path"])

    last_done = session.get("last_done", "")
    last_next = session.get("last_next_todo", "")

    if last_done:
        kv("  지난 작업", last_done)
    if last_next:
        kv("  다음 할 일", last_next)

    history = session.get("history", [])
    if history:
        kv("  세션 횟수", str(len(history)))

    print()
