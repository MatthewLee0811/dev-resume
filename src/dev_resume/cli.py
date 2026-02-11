"""CLI entry point for dev-resume."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from dev_resume.display import banner, kv, show_session_summary, success, warn
from dev_resume.project import detect_project_root, project_hash, project_name
from dev_resume.session import create_session, load_session, save_session


# ── helpers ──────────────────────────────────────────────────────────


def _prompt(label: str) -> str:
    """Interactive input — empty string on EOF / interrupt."""
    try:
        return input(f"  {label}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def _first_run(phash: str, pname: str, ppath: str) -> dict:
    """First-run: greet and create session."""
    banner("새 프로젝트 감지!")
    kv("  경로", ppath)
    kv("  이름", pname)
    print()

    task = _prompt("지금 하려는 작업")
    create_session(
        phash,
        project_name=pname,
        project_path=ppath,
        initial_task=task,
    )
    success("세션 생성 완료")
    return load_session(phash)  # type: ignore[return-value]


def _post_exit_prompt(phash: str, pname: str, ppath: str) -> None:
    """After claude-code exits, ask what was done and what's next."""
    banner("세션 저장")
    done = _prompt("오늘 한 일 (빈칸 → 스킵)")
    next_todo = _prompt("다음 할 일 (빈칸 → 스킵)")

    if not done and not next_todo:
        warn("입력 없음 — 세션 변경 없이 종료합니다.")
        return

    save_session(
        phash,
        project_name=pname,
        project_path=ppath,
        done=done,
        next_todo=next_todo,
    )
    success("세션 저장 완료")


def _launch_claude(project_root: str, session: dict) -> int:
    """Launch claude-code subprocess and return its exit code."""
    claude_bin = shutil.which("claude")
    if claude_bin is None:
        warn("'claude' 명령어를 찾을 수 없습니다. claude-code를 설치해 주세요.")
        return 1

    # Build resume prompt from session
    parts: list[str] = []
    last_next = session.get("last_next_todo", "")
    if last_next:
        parts.append(f"이전 세션에서 다음 할 일: {last_next}")

    last_done = session.get("last_done", "")
    if last_done:
        parts.append(f"지난 작업 내용: {last_done}")

    cmd: list[str] = [claude_bin]
    if parts:
        cmd += ["--resume-prompt", " | ".join(parts)]

    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        return 130


# ── subcommands ──────────────────────────────────────────────────────


def cmd_run(args: argparse.Namespace) -> int:
    """Default command — show summary → launch claude → post-exit save."""
    root = detect_project_root(getattr(args, "path", None))
    phash = project_hash(root)
    pname = project_name(root)
    ppath = str(root)

    session = load_session(phash)

    # First run
    if session is None:
        session = _first_run(phash, pname, ppath)

    # Show summary
    show_session_summary(session)

    # Launch claude-code
    exit_code = _launch_claude(ppath, session)

    # Post-exit prompt (only on clean exit)
    if exit_code == 0:
        _post_exit_prompt(phash, pname, ppath)
    else:
        warn(f"claude-code가 exit code {exit_code}(으)로 종료되었습니다.")

    return exit_code


def cmd_save(args: argparse.Namespace) -> int:
    """'dev-resume save' — manual session save."""
    root = detect_project_root(getattr(args, "path", None))
    phash = project_hash(root)
    pname = project_name(root)
    ppath = str(root)

    # Ensure session exists
    session = load_session(phash)
    if session is None:
        create_session(phash, project_name=pname, project_path=ppath)

    # Positional args or interactive
    done = args.done if args.done else ""
    next_todo = args.next_todo if args.next_todo else ""

    if not done and not next_todo:
        banner("세션 저장")
        done = _prompt("오늘 한 일 (빈칸 → 스킵)")
        next_todo = _prompt("다음 할 일 (빈칸 → 스킵)")

    if not done and not next_todo:
        warn("입력 없음 — 세션 변경 없이 종료합니다.")
        return 0

    save_session(
        phash,
        project_name=pname,
        project_path=ppath,
        done=done,
        next_todo=next_todo,
    )
    success("세션 저장 완료")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """'dev-resume status' — show current session without launching claude."""
    root = detect_project_root(getattr(args, "path", None))
    phash = project_hash(root)

    session = load_session(phash)
    if session is None:
        warn("이 프로젝트에 저장된 세션이 없습니다.")
        return 1

    show_session_summary(session)

    history = session.get("history", [])
    if history:
        banner("히스토리")
        for i, entry in enumerate(history[-5:], 1):
            ts = entry.get("timestamp", "?")[:10]
            done = entry.get("done", "")
            nxt = entry.get("next_todo", "")
            line = f"  {i}. [{ts}]"
            if done:
                line += f"  한 일: {done}"
            if nxt:
                line += f"  → 다음: {nxt}"
            print(line)
        print()

    return 0


# ── argument parser ──────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev-resume",
        description="Resume your dev session where you left off.",
    )
    parser.add_argument(
        "--path",
        help="프로젝트 경로 수동 지정 (기본: 자동 감지)",
        default=None,
    )

    sub = parser.add_subparsers(dest="command")

    # save
    save_parser = sub.add_parser("save", help="세션 저장 (수동)")
    save_parser.add_argument("done", nargs="?", default=None, help="오늘 한 일")
    save_parser.add_argument("next_todo", nargs="?", default=None, help="다음 할 일")

    # status
    sub.add_parser("status", help="현재 세션 상태 확인")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "save":
        code = cmd_save(args)
    elif args.command == "status":
        code = cmd_status(args)
    else:
        code = cmd_run(args)

    sys.exit(code)


if __name__ == "__main__":
    main()
