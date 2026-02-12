"""Context window checker — estimate token usage and suggest cleanup."""

from __future__ import annotations

from typing import Any

from dev_resume.display import banner, kv

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


def check_context(session: dict[str, Any]) -> None:
    """Check context usage and display status to terminal."""
    turn_count = session.get("turn_count", 0)
    if turn_count == 0:
        return

    tokens = estimate_tokens(turn_count)
    ratio = usage_ratio(turn_count)
    pct = int(ratio * 100)

    # Below info threshold — silent
    if ratio < THRESHOLD_INFO:
        return

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
        print(f"\n  🚨 [{bar}] {pct}% — 새 세션 시작을 권장합니다!")
    elif ratio >= THRESHOLD_WARNING:
        print(f"\n  ⚠️  [{bar}] {pct}% — 컨텍스트가 많이 사용되었습니다")
    else:
        print(f"\n  ℹ️  [{bar}] {pct}%")
    print()
