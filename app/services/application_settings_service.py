from dataclasses import dataclass
from pathlib import Path

from app.config import DATA_DIR
from app.repositories.database import Database


@dataclass(frozen=True)
class ApplicationSettings:
    default_export_dir: str
    default_backup_dir: str
    default_allow_partial_boxes: bool = True
    default_prefer_small_final_box: bool = True
    default_merge_duplicate_lines: bool = True
    default_allow_direct_load_fabric_rolls: bool = False


class ApplicationSettingsService:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def load(self) -> ApplicationSettings:
        self.database.initialize()
        values = self._load_values()
        return ApplicationSettings(
            default_export_dir=values.get("default_export_dir", str(DATA_DIR / "exports")),
            default_backup_dir=values.get("default_backup_dir", str(DATA_DIR / "backups")),
            default_allow_partial_boxes=self._bool_value(values.get("default_allow_partial_boxes"), True),
            default_prefer_small_final_box=self._bool_value(values.get("default_prefer_small_final_box"), True),
            default_merge_duplicate_lines=self._bool_value(values.get("default_merge_duplicate_lines"), True),
            default_allow_direct_load_fabric_rolls=self._bool_value(
                values.get("default_allow_direct_load_fabric_rolls"),
                False,
            ),
        )

    def save(self, settings: ApplicationSettings) -> None:
        self.database.initialize()
        values = {
            "default_export_dir": settings.default_export_dir,
            "default_backup_dir": settings.default_backup_dir,
            "default_allow_partial_boxes": self._serialize_bool(settings.default_allow_partial_boxes),
            "default_prefer_small_final_box": self._serialize_bool(settings.default_prefer_small_final_box),
            "default_merge_duplicate_lines": self._serialize_bool(settings.default_merge_duplicate_lines),
            "default_allow_direct_load_fabric_rolls": self._serialize_bool(
                settings.default_allow_direct_load_fabric_rolls
            ),
        }
        with self.database.transaction() as connection:
            for key, value in values.items():
                connection.execute(
                    """
                    INSERT INTO application_settings (key, value)
                    VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, value),
                )

    def _load_values(self) -> dict[str, str]:
        with self.database.connect() as connection:
            rows = connection.execute("SELECT key, value FROM application_settings").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def _bool_value(self, value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "evet"}

    def _serialize_bool(self, value: bool) -> str:
        return "1" if value else "0"

    def ensure_directories(self, settings: ApplicationSettings) -> None:
        Path(settings.default_export_dir).mkdir(parents=True, exist_ok=True)
        Path(settings.default_backup_dir).mkdir(parents=True, exist_ok=True)
