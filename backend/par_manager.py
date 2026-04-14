import json
import subprocess
import logging
from pathlib import Path
from typing import Any

from config import REPOS_DIRECTORY

log = logging.getLogger(__name__)


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    log.info("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def _par_state_path() -> Path:
    return Path.home() / ".local" / "share" / "par" / "global_state.json"


def _load_par_state() -> dict[str, Any]:
    state_path = _par_state_path()
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text() or "{}")
    except (OSError, json.JSONDecodeError):
        return {}


def get_workspace_session(label: str) -> dict[str, Any] | None:
    """Return persisted par metadata for a workspace label, if present."""
    state = _load_par_state()
    sessions = state.get("sessions", {})
    session = sessions.get(label)
    if session and session.get("session_type") == "workspace":
        return session
    workspaces = state.get("workspaces", {})
    workspace = workspaces.get(label)
    if workspace:
        return workspace
    return None


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


def get_workspace_path(label: str) -> str:
    """Resolve the par workspace directory for a label."""
    session = get_workspace_session(label)
    if session:
        workspace_path = session.get("worktree_path") or session.get("repository_path")
        if workspace_path and Path(workspace_path).is_dir():
            return str(workspace_path)
    base = Path.home() / ".local" / "share" / "par" / "workspaces"
    if base.is_dir():
        for hash_dir in base.iterdir():
            candidate = hash_dir / label
            if candidate.is_dir():
                return str(candidate)
    return ""


def is_tmux_session_alive(session_name: str) -> bool:
    result = _run(["tmux", "has-session", "-t", session_name], check=False)
    return result.returncode == 0


def ensure_tmux_session(label: str, tmux_session: str | None = None, create: bool = False) -> str:
    """Return a live tmux session for a workspace, recreating it when requested."""
    session = get_workspace_session(label)
    candidates: list[str] = []
    persisted_session = ""
    if session and session.get("tmux_session_name"):
        persisted_session = str(session["tmux_session_name"])
    if tmux_session:
        candidates.append(tmux_session)
    if persisted_session and persisted_session not in candidates:
        candidates.append(persisted_session)
    discovered = discover_tmux_session(label)
    if discovered and discovered not in candidates:
        candidates.append(discovered)

    for candidate in candidates:
        if candidate and is_tmux_session_alive(candidate):
            return candidate

    canonical = persisted_session or tmux_session or discovered
    if not create:
        return canonical

    workspace_path = get_workspace_path(label)
    if not workspace_path:
        raise FileNotFoundError("Workspace directory not found")

    _run(["tmux", "new-session", "-d", "-s", canonical, "-c", workspace_path])
    return canonical


def get_pane_command(session_name: str) -> str:
    """Return the current command running in the first pane of a tmux session."""
    result = _run(
        ["tmux", "list-panes", "-t", session_name, "-F", "#{pane_current_command}"],
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
