"""Git sync — fetch, pull primary, optionally merge secondary branch."""

from __future__ import annotations

import subprocess

from dev_resume.display import banner, kv, success, warn

# ── environment config (hardcoded for now, later from config.json) ───

is_mobile = False  # TODO: read from ~/.dev-resume/config.json

if is_mobile:
    PRIMARY = "mobile"
    SECONDARY = "main"
else:
    PRIMARY = "main"
    SECONDARY = "mobile"


# ── helpers ──────────────────────────────────────────────────────────


def _git(args: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _has_git(cwd: str) -> bool:
    r = _git(["rev-parse", "--is-inside-work-tree"], cwd)
    return r.returncode == 0


def _remote_branch_exists(branch: str, cwd: str) -> bool:
    r = _git(["rev-parse", "--verify", f"origin/{branch}"], cwd)
    return r.returncode == 0


def _local_branch_exists(branch: str, cwd: str) -> bool:
    r = _git(["rev-parse", "--verify", branch], cwd)
    return r.returncode == 0


def _current_branch(cwd: str) -> str:
    r = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    return r.stdout.strip()


def _commits_behind(branch: str, cwd: str) -> int:
    """How many commits local branch is behind origin/{branch}."""
    r = _git(["rev-list", "--count", f"{branch}..origin/{branch}"], cwd)
    if r.returncode != 0:
        return 0
    return int(r.stdout.strip())


def _commits_ahead(remote_branch: str, local_branch: str, cwd: str) -> int:
    """How many commits origin/{remote_branch} is ahead of local_branch."""
    r = _git(
        ["rev-list", "--count", f"{local_branch}..origin/{remote_branch}"],
        cwd,
    )
    if r.returncode != 0:
        return 0
    return int(r.stdout.strip())


def _latest_commits(ref: str, count: int, cwd: str) -> list[str]:
    r = _git(
        ["log", ref, f"-{count}", "--oneline", "--no-decorate"],
        cwd,
    )
    if r.returncode != 0:
        return []
    return [line for line in r.stdout.strip().splitlines() if line]


def _prompt_yn(label: str) -> bool:
    try:
        answer = input(f"  {label} [y/N]: ").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def _prompt_choice(label: str) -> str:
    try:
        return input(f"  {label} [1/2/3]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "3"


# ── primary branch sync ─────────────────────────────────────────────


def _sync_primary(cwd: str) -> None:
    branch = PRIMARY
    banner(f"Primary: {branch}")

    if not _remote_branch_exists(branch, cwd):
        kv("  상태", f"origin/{branch} 없음 — 스킵")
        return

    behind = _commits_behind(branch, cwd)

    if behind == 0:
        success(f"{branch} 최신 상태")
        return

    # Show recent commits from remote
    kv("  상태", f"{behind}개 커밋 뒤처짐")
    commits = _latest_commits(f"origin/{branch}", min(behind, 3), cwd)
    for c in commits:
        print(f"    {c}")

    if not _prompt_yn("Pull?"):
        warn("스킵")
        return

    r = _git(["pull", "origin", branch], cwd)
    if r.returncode == 0:
        success(f"git pull origin {branch} 완료")
    else:
        warn(f"pull 실패: {r.stderr.strip()}")


# ── secondary branch merge ───────────────────────────────────────────


def _sync_secondary(cwd: str) -> None:
    branch = SECONDARY
    banner(f"Secondary: {branch}")

    if not _remote_branch_exists(branch, cwd):
        kv("  상태", f"origin/{branch} 없음 — 스킵")
        return

    current = _current_branch(cwd)
    ahead = _commits_ahead(branch, current, cwd)

    if ahead == 0:
        success(f"{branch} 변경사항 없음")
        return

    kv("  상태", f"{ahead}개 새 커밋")
    commits = _latest_commits(f"origin/{branch}", min(ahead, 3), cwd)
    for c in commits:
        print(f"    {c}")

    print()
    print("  [1] 머지 실행  [2] 나중에  [3] 스킵")
    choice = _prompt_choice("선택")

    if choice != "1":
        warn("스킵")
        return

    r = _git(["merge", f"origin/{branch}"], cwd)
    if r.returncode == 0:
        success(f"git merge origin/{branch} 완료")
    else:
        # Merge conflict or other failure
        stderr = r.stderr.strip()
        if "CONFLICT" in r.stdout or "CONFLICT" in stderr:
            warn("머지 충돌 발생! 수동으로 해결해 주세요:")
            conflict_lines = [
                l
                for l in (r.stdout + r.stderr).splitlines()
                if "CONFLICT" in l
            ]
            for l in conflict_lines:
                print(f"    {l}")
        else:
            warn(f"머지 실패: {stderr}")


# ── public API ───────────────────────────────────────────────────────


def run_git_sync(project_path: str) -> None:
    """Run the full git sync flow. Safe to call — skips silently on errors."""
    if not _has_git(project_path):
        return

    # fetch all remotes first
    banner("Git Sync")
    r = _git(["fetch", "origin"], project_path)
    if r.returncode != 0:
        warn(f"git fetch 실패: {r.stderr.strip()}")
        return

    success("git fetch origin 완료")

    _sync_primary(project_path)
    _sync_secondary(project_path)
    print()
