import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

REPOS_DIRECTORY = os.getenv("REPOS_DIRECTORY", "")
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "kanban.db"
GHOSTTY_PATH = "/Applications/Ghostty.app/Contents/MacOS/ghostty"
