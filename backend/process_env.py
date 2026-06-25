import os
import shutil

GHOSTTY_TERMINFO = "/Applications/Ghostty.app/Contents/Resources/terminfo"
_GH_PATH = shutil.which("gh")

_STRIP_ENV_KEYS = frozenset({
    "NO_COLOR",
    "FORCE_COLOR",
    "CLICOLOR",
    "CLICOLOR_FORCE",
    "CI",
})


def cleaned_child_env() -> dict[str, str]:
    """Environment for terminal/par children launched from Cursor-hosted kanban."""
    env = os.environ.copy()
    for key in list(env.keys()):
        if key in _STRIP_ENV_KEYS or key.startswith("CURSOR_"):
            del env[key]
    if env.get("TERM") in ("dumb", ""):
        env.pop("TERM", None)
    existing = env.get("TERMINFO_DIRS", "")
    if GHOSTTY_TERMINFO not in existing.split(":"):
        env["TERMINFO_DIRS"] = (
            f"{GHOSTTY_TERMINFO}:{existing}" if existing else GHOSTTY_TERMINFO
        )
    return env


def git_subprocess_env() -> dict[str, str]:
    """Environment for non-interactive git subprocesses from the kanban backend."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def git_pull_argv() -> list[str]:
    """git pull argv; uses gh for HTTPS credentials when the gh CLI is available."""
    cmd = ["git"]
    if _GH_PATH:
        cmd.extend([
            "-c", "credential.helper=",
            "-c", "credential.helper=!gh auth git-credential",
        ])
    cmd.append("pull")
    return cmd
