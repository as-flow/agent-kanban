import os
import signal
import subprocess
import logging

from config import GHOSTTY_PATH

log = logging.getLogger(__name__)


def launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    """Launch a Ghostty window attached to a tmux session. Returns the PID."""
    cmd = [
        GHOSTTY_PATH,
        f"--title={title}",
        f"--background={color_bg}",
        f"--foreground={color_fg}",
        "-e", "tmux", "attach-session", "-t", tmux_session,
    ]
    log.info("Launching Ghostty: %s", " ".join(cmd))
    proc = subprocess.Popen(cmd, start_new_session=True)
    return proc.pid


def is_alive(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def focus():
    """Bring the Ghostty app to the foreground via AppleScript."""
    subprocess.run(
        ["osascript", "-e", 'tell application "Ghostty" to activate'],
        check=False,
    )


def kill(pid: int):
    """Kill a Ghostty process by PID."""
    if pid is None:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        pass
