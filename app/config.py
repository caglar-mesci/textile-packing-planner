import os
import sys
from pathlib import Path


APP_NAME = "Tekstil Paketleme Planlayıcı"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _default_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "TekstilPaketlemePlanlayici"
        return Path.home() / ".tekstil_paketleme_planlayici"
    return PROJECT_ROOT / "data"


DATA_DIR = _default_data_dir()
DATABASE_PATH = DATA_DIR / "planner.sqlite3"
