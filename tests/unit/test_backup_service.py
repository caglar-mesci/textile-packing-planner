from pathlib import Path
from zipfile import ZipFile

import pytest

from app.repositories.database import Database
from app.services.backup_service import BackupError, BackupService


def test_backup_service_creates_zip_with_database_and_manifest(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    service = BackupService(database, tmp_path / "backups")

    backup_path = service.create_backup(tmp_path / "backups" / "backup.zip")

    assert backup_path.exists()
    with ZipFile(backup_path) as archive:
        assert set(archive.namelist()) == {"planner.sqlite3", "manifest.json"}


def test_backup_service_restores_database_snapshot(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    service = BackupService(database, tmp_path / "backups")
    backup_path = service.create_backup(tmp_path / "backups" / "backup.zip")

    with database.transaction() as connection:
        connection.execute("DELETE FROM vehicles")
    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] == 0

    service.restore_backup(backup_path)

    with database.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] > 0


def test_backup_service_rejects_invalid_backup_file(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    invalid_backup = tmp_path / "invalid.zip"
    with ZipFile(invalid_backup, "w") as archive:
        archive.writestr("notes.txt", "not a planner backup")

    with pytest.raises(BackupError):
        BackupService(database, tmp_path / "backups").restore_backup(invalid_backup)
