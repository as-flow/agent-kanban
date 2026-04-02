import os
import shutil
import signal
import subprocess
import logging

import config

log = logging.getLogger(__name__)

SUPPORTED_TERMINALS = ("ghostty", "kitty", "alacritty", "wezterm", "iterm2", "terminal")

DEFAULT_PATHS = {
    "ghostty": "/Applications/Ghostty.app/Contents/MacOS/ghostty",
    "kitty": "kitty",
    "alacritty": "alacritty",
    "wezterm": "wezterm",
}


def _resolve_binary(app: str) -> str:
    if config.TERMINAL_PATH:
        return config.TERMINAL_PATH
    default = DEFAULT_PATHS.get(app, "")
    if default and (os.path.isabs(default) and os.path.exists(default)):
        return default
    return shutil.which(app) or default


def _get_app_pid(bundle_id: str) -> int:
    """Return the PID of a running macOS app by bundle ID, or 0."""
    try:
        out = subprocess.check_output(
            ["osascript", "-e", f'tell application "System Events" to unix id of process "{bundle_id}"'],
            stderr=subprocess.DEVNULL, text=True,
        )
        return int(out.strip())
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# CLI-based launchers (Ghostty, Kitty, Alacritty, WezTerm)
# ---------------------------------------------------------------------------

def _ghostty_launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("ghostty")
    cmd = [
        binary,
        f"--title={title}",
        f"--background={color_bg}",
        f"--foreground={color_fg}",
        "-e", "tmux", "attach-session", "-t", tmux_session,
    ]
    log.info("Launching Ghostty: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


def _ghostty_launch_shell(working_dir: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("ghostty")
    cmd = [
        binary,
        f"--title={title}",
        f"--background={color_bg}",
        f"--foreground={color_fg}",
        f"--working-directory={working_dir}",
    ]
    log.info("Launching Ghostty shell: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


def _kitty_launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("kitty")
    cmd = [
        binary,
        "--title", title,
        "--override", f"background={color_bg}",
        "--override", f"foreground={color_fg}",
        "-e", "tmux", "attach-session", "-t", tmux_session,
    ]
    log.info("Launching Kitty: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


def _kitty_launch_shell(working_dir: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("kitty")
    cmd = [
        binary,
        "--title", title,
        "--override", f"background={color_bg}",
        "--override", f"foreground={color_fg}",
        "--directory", working_dir,
    ]
    log.info("Launching Kitty shell: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


def _alacritty_launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("alacritty")
    cmd = [
        binary,
        "-T", title,
        "-e", "tmux", "attach-session", "-t", tmux_session,
    ]
    log.info("Launching Alacritty: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


def _alacritty_launch_shell(working_dir: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("alacritty")
    cmd = [
        binary,
        "-T", title,
        "--working-directory", working_dir,
    ]
    log.info("Launching Alacritty shell: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


def _wezterm_launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("wezterm")
    cmd = [
        binary, "start",
        "--", "tmux", "attach-session", "-t", tmux_session,
    ]
    log.info("Launching WezTerm: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


def _wezterm_launch_shell(working_dir: str, title: str, color_fg: str, color_bg: str) -> int:
    binary = _resolve_binary("wezterm")
    cmd = [
        binary, "start",
        "--cwd", working_dir,
    ]
    log.info("Launching WezTerm shell: %s", " ".join(cmd))
    return subprocess.Popen(cmd, start_new_session=True).pid


# ---------------------------------------------------------------------------
# AppleScript-based launchers (iTerm2, Terminal.app)
# ---------------------------------------------------------------------------

def _iterm2_launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    shell_cmd = f"tmux attach-session -t {tmux_session}"
    script = f'''
    tell application "iTerm"
        activate
        set newWindow to (create window with default profile)
        tell current session of newWindow
            set name to "{title}"
            write text "{shell_cmd}"
        end tell
    end tell
    '''
    log.info("Launching iTerm2 for tmux session: %s", tmux_session)
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    return _get_app_pid("iTerm2")


def _iterm2_launch_shell(working_dir: str, title: str, color_fg: str, color_bg: str) -> int:
    script = f'''
    tell application "iTerm"
        activate
        set newWindow to (create window with default profile)
        tell current session of newWindow
            set name to "{title}"
            write text "cd {working_dir}"
        end tell
    end tell
    '''
    log.info("Launching iTerm2 shell in: %s", working_dir)
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    return _get_app_pid("iTerm2")


def _terminal_app_launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    shell_cmd = f"tmux attach-session -t {tmux_session}"
    script = f'''
    tell application "Terminal"
        activate
        do script "{shell_cmd}"
        set custom title of front window to "{title}"
    end tell
    '''
    log.info("Launching Terminal.app for tmux session: %s", tmux_session)
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    return _get_app_pid("Terminal")


def _terminal_app_launch_shell(working_dir: str, title: str, color_fg: str, color_bg: str) -> int:
    script = f'''
    tell application "Terminal"
        activate
        do script "cd {working_dir}"
        set custom title of front window to "{title}"
    end tell
    '''
    log.info("Launching Terminal.app shell in: %s", working_dir)
    subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    return _get_app_pid("Terminal")


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_LAUNCHERS = {
    "ghostty":   (_ghostty_launch,       _ghostty_launch_shell),
    "kitty":     (_kitty_launch,         _kitty_launch_shell),
    "alacritty": (_alacritty_launch,     _alacritty_launch_shell),
    "wezterm":   (_wezterm_launch,       _wezterm_launch_shell),
    "iterm2":    (_iterm2_launch,        _iterm2_launch_shell),
    "terminal":  (_terminal_app_launch,  _terminal_app_launch_shell),
}


def _get_launchers():
    pair = _LAUNCHERS.get(config.TERMINAL_APP)
    if not pair:
        raise ValueError(
            f"Unsupported TERMINAL_APP={config.TERMINAL_APP!r}. "
            f"Supported: {', '.join(SUPPORTED_TERMINALS)}"
        )
    return pair


# ---------------------------------------------------------------------------
# Public API (unchanged contract)
# ---------------------------------------------------------------------------

def launch(tmux_session: str, title: str, color_fg: str, color_bg: str) -> int:
    """Launch a terminal window attached to a tmux session. Returns PID."""
    fn, _ = _get_launchers()
    return fn(tmux_session, title, color_fg, color_bg)


def launch_shell(working_dir: str, title: str, color_fg: str, color_bg: str) -> int:
    """Launch a standalone terminal window in a directory. Returns PID."""
    _, fn = _get_launchers()
    return fn(working_dir, title, color_fg, color_bg)


def is_alive(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def focus_by_pid(pid: int):
    """Bring the terminal window for the given PID to the front via AppKit."""
    from AppKit import NSRunningApplication, NSApplicationActivateAllWindows
    app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
    if app:
        app.activateWithOptions_(NSApplicationActivateAllWindows)
    else:
        log.warning("No running application found for PID %d", pid)


def kill(pid: int):
    """Kill a terminal process by PID."""
    if pid is None:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        pass
