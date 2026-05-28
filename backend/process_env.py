import os

GHOSTTY_TERMINFO = "/Applications/Ghostty.app/Contents/Resources/terminfo"

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
