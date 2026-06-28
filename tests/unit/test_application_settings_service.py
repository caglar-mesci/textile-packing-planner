from pathlib import Path

from app.services.application_settings_service import ApplicationSettings, ApplicationSettingsService
from app.repositories.database import Database


def test_application_settings_service_loads_defaults(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    service = ApplicationSettingsService(database)

    settings = service.load()

    assert settings.default_export_dir
    assert settings.default_backup_dir
    assert settings.default_allow_partial_boxes
    assert settings.default_merge_duplicate_lines


def test_application_settings_service_saves_and_loads_values(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    service = ApplicationSettingsService(database)
    expected = ApplicationSettings(
        default_export_dir=str(tmp_path / "exports"),
        default_backup_dir=str(tmp_path / "backups"),
        default_allow_partial_boxes=False,
        default_prefer_small_final_box=False,
        default_merge_duplicate_lines=False,
        default_allow_direct_load_fabric_rolls=True,
    )

    service.save(expected)
    loaded = service.load()

    assert loaded == expected


def test_application_settings_service_creates_configured_directories(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    service = ApplicationSettingsService(database)
    settings = ApplicationSettings(
        default_export_dir=str(tmp_path / "exports"),
        default_backup_dir=str(tmp_path / "backups"),
    )

    service.ensure_directories(settings)

    assert (tmp_path / "exports").is_dir()
    assert (tmp_path / "backups").is_dir()
