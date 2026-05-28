import json
import subprocess
import logging
from pathlib import Path
from typing import Any

from config import REPOS_DIRECTORY
from process_env import GHOSTTY_TERMINFO, cleaned_child_env

log = logging.getLogger(__name__)

_TMUX_STRIP_ENV_KEYS = (
    "NO_COLOR",
    "FORCE_COLOR",
    "CLICOLOR",
    "CLICOLOR_FORCE",
    "CI",
)

_TMUX_TERMINAL_FEATURES = (
    "xterm-ghostty:RGB",
    "xterm-ghostty:extkeys",
)


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    log.info("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=check, env=cleaned_child_env())


def _ensure_tmux_server_defaults():
    """Configure tmux before Par creates panes, so new shells inherit sane defaults."""
    _run(["tmux", "start-server"], check=False)
    # Match the only known-good strict tmux Droid runtime from historical logs:
    # Droid saw TERM=xterm-ghostty and TERM_PROGRAM=ghostty while multiplexer=tmux.
    _run(["tmux", "set-option", "-gq", "default-terminal", "xterm-ghostty"], check=False)
    _run(["tmux", "set-option", "-gq", "allow-passthrough", "on"], check=False)
    _run(["tmux", "set-option", "-sq", "extended-keys", "always"], check=False)
    _run(["tmux", "set-option", "-sq", "extended-keys-format", "csi-u"], check=False)
    for key in _TMUX_STRIP_ENV_KEYS:
        _run(["tmux", "set-environment", "-gu", key], check=False)
    _run(["tmux", "set-environment", "-g", "COLORTERM", "truecolor"], check=False)
    _run(["tmux", "set-environment", "-g", "TERMINFO_DIRS", GHOSTTY_TERMINFO], check=False)
    _run(["tmux", "set-environment", "-g", "TERM_PROGRAM", "ghostty"], check=False)
    for feature in _TMUX_TERMINAL_FEATURES:
        _append_tmux_terminal_feature(feature)


def _append_tmux_terminal_feature(feature: str):
    result = _run(["tmux", "show-options", "-sv", "terminal-features"], check=False)
    current = result.stdout.strip().split(",") if result.returncode == 0 else []
    if feature in current:
        return
    prefix = "," if current and current != [""] else ""
    _run(["tmux", "set-option", "-asq", "terminal-features", f"{prefix}{feature}"], check=False)


def configure_tmux_session(session_name: str):
    """Apply Droid-friendly tmux environment/options to a Par session."""
    if not session_name:
        return
    _ensure_tmux_server_defaults()
    for key in _TMUX_STRIP_ENV_KEYS:
        _run(["tmux", "set-environment", "-t", session_name, "-u", key], check=False)
    _run(["tmux", "set-environment", "-t", session_name, "COLORTERM", "truecolor"], check=False)
    _run(["tmux", "set-environment", "-t", session_name, "TERMINFO_DIRS", GHOSTTY_TERMINFO], check=False)
    _run(["tmux", "set-environment", "-t", session_name, "TERM_PROGRAM", "ghostty"], check=False)
    _run(["tmux", "set-option", "-t", session_name, "-q", "default-terminal", "xterm-ghostty"], check=False)
    _run(["tmux", "set-option", "-t", session_name, "-q", "allow-passthrough", "on"], check=False)


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
    _ensure_tmux_server_defaults()
    _run([
        "par", "workspace", "start", label,
        "--path", REPOS_DIRECTORY,
        "--repos", repos_csv,
    ])
    tmux_session = discover_tmux_session(label)
    return tmux_session


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

    _ensure_tmux_server_defaults()
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
