import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

REPOS_DIRECTORY = os.getenv("REPOS_DIRECTORY", "")
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "kanban.db"
TERMINAL_APP = os.getenv("TERMINAL_APP", "ghostty").lower()
TERMINAL_PATH = os.getenv("TERMINAL_PATH", "")

_SETTINGS_MAP = {
    "terminal_app": "TERMINAL_APP",
    "terminal_path": "TERMINAL_PATH",
    "repos_directory": "REPOS_DIRECTORY",
}


def get_settings() -> dict:
    return {key: globals()[attr] for key, attr in _SETTINGS_MAP.items()}


def apply_settings(data: dict):
    from models import upsert_setting

    for key, attr in _SETTINGS_MAP.items():
        if key in data:
            val = str(data[key]).strip()
            if key == "terminal_app":
                val = val.lower()
            globals()[attr] = val
            upsert_setting(key, val)


def load_settings_from_db():
    from models import get_all_settings

    saved = get_all_settings()
    for key, attr in _SETTINGS_MAP.items():
        if key in saved:
            globals()[attr] = saved[key]
