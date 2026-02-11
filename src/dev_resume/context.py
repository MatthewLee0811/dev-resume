"""Context window checker — estimate token usage and suggest cleanup."""

from __future__ import annotations

from typing import Any

from dev_resume.display import banner, kv, warn

# Claude-code context window size (tokens)
MAX_TOKENS = 200_000
TOKENS_PER_TURN = 3_000

# Thresholds (fraction of MAX_TOKENS)
THRESHOLD_CRITICAL = 0.85
THRESHOLD_WARNING = 0.75
THRESHOLD_INFO = 0.50


def estimate_tokens(turn_count: int) -> int:
    return turn_count * TOKENS_PER_TURN


def usage_ratio(turn_count: int) -> float:
    return estimate_tokens(turn_count) / MAX_TOKENS


def check_context(session: dict[str, Any]) -> str | None:
    """Check context usage and display status.

    Returns the user's cleanup choice:
      "impact" / "clear" / None (skip or below threshold)
    """
    turn_count = session.get("turn_count", 0)
    if turn_count == 0:
        return None

    tokens = estimate_tokens(turn_count)
    ratio = usage_ratio(turn_count)
    pct = int(ratio * 100)

    # Below info threshold — silent
    if ratio < THRESHOLD_INFO:
        return None

    banner("컨텍스트 체크")
    kv("  턴 수", str(turn_count))
    kv("  추정 토큰", f"{tokens:,} / {MAX_TOKENS:,} ({pct}%)")

    last_cleanup = session.get("last_cleanup", "")
    if last_cleanup:
        kv("  마지막 정리", last_cleanup[:16])

    # Bar visualization
    bar_len = 20
    filled = int(bar_len * ratio)
    bar = "█" * filled + "░" * (bar_len - filled)

    if ratio >= THRESHOLD_CRITICAL:
        print(f"\n  🚨 [{bar}] {pct}% — 즉시 정리를 권장합니다!")
    elif ratio >= THRESHOLD_WARNING:
        print(f"\n  ⚠️  [{bar}] {pct}% — 정리를 제안합니다")
    else:
        print(f"\n  ℹ️  [{bar}] {pct}%")
        return None  # info only — no prompt

    # Prompt cleanup options
    print()
    print("  [1] claude --resume 실행 후 시작 (대화 요약 유지)")
    print("  [2] claude --clear 실행 후 시작 (완전 초기화)")
    print("  [3] 바로 시작")

    try:
        choice = input("  선택 [1/2/3]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        choice = "3"

    if choice == "1":
        return "resume"
    if choice == "2":
        return "clear"
    return None
