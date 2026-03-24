import subprocess
import logging

from config import REPOS_DIRECTORY

log = logging.getLogger(__name__)


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    log.info("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def workspace_start(label: str, repos: list[str]) -> str:
    """Create a par workspace. Returns the tmux session name."""
    repos_csv = ",".join(repos)
    _run([
        "par", "workspace", "start", label,
        "--path", REPOS_DIRECTORY,
        "--repos", repos_csv,
    ])
    return discover_tmux_session(label)


def workspace_rm(label: str):
    """Remove a par workspace (worktrees, branches, tmux session)."""
    _run(["par", "rm", label], check=False)


def send_command(label: str, command: str):
    """Send a command to a par session's tmux pane."""
    _run(["par", "send", label, command])


def discover_tmux_session(label: str) -> str:
    """Find the tmux session name for a par label by listing sessions."""
    result = _run(["tmux", "list-sessions", "-F", "#{session_name}"], check=False)
    if result.returncode != 0:
        return f"par-ws-{label}"
    for line in result.stdout.strip().splitlines():
        if label in line:
            return line.strip()
    return f"par-ws-{label}"


def is_tmux_session_alive(session_name: str) -> bool:
    result = _run(["tmux", "has-session", "-t", session_name], check=False)
    return result.returncode == 0


def get_pane_command(session_name: str) -> str:
    """Return the current command running in the first pane of a tmux session."""
    result = _run(
        ["tmux", "list-panes", "-t", session_name, "-F", "#{pane_current_command}"],
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
