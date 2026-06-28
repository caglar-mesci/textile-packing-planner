import json
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from app.config import DATA_DIR
from app.repositories.database import Database


BACKUP_DATABASE_NAME = "planner.sqlite3"
BACKUP_MANIFEST_NAME = "manifest.json"


@dataclass(frozen=True)
class BackupInfo:
    path: Path
    created_at: datetime
    size_bytes: int

    @property
    def file_name(self) -> str:
        return self.path.name

    @property
    def size_mb(self) -> float:
        return self.size_bytes / 1024 / 1024


class BackupError(Exception):
    pass


class BackupService:
    def __init__(self, database: Database | None = None, backup_dir: Path | None = None) -> None:
        self.database = database or Database()
        self.backup_dir = backup_dir or DATA_DIR / "backups"

    def create_backup(self, destination: Path | None = None) -> Path:
        self.database.initialize()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        destination = destination or self._default_backup_path()
        destination.parent.mkdir(parents=True, exist_ok=True)

        temp_database = destination.with_suffix(".tmp.sqlite3")
        try:
            self._copy_database_snapshot(temp_database)
            manifest = {
                "app": "textile-packing-planner",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "database_file": BACKUP_DATABASE_NAME,
            }
            with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
                archive.write(temp_database, BACKUP_DATABASE_NAME)
                archive.writestr(BACKUP_MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
        except Exception as exc:
            if destination.exists():
                destination.unlink()
            raise BackupError("Yedek dosyası oluşturulamadı.") from exc
        finally:
            if temp_database.exists():
                temp_database.unlink()

        return destination

    def restore_backup(self, source: Path) -> None:
        if not source.exists():
            raise BackupError("Yedek dosyası bulunamadı.")

        restore_temp = self.database.path.with_suffix(".restore.sqlite3")
        try:
            with ZipFile(source, "r") as archive:
                names = set(archive.namelist())
                if BACKUP_DATABASE_NAME not in names or BACKUP_MANIFEST_NAME not in names:
                    raise BackupError("Seçilen dosya geçerli bir uygulama yedeği değil.")
                with archive.open(BACKUP_DATABASE_NAME) as archived_database, restore_temp.open("wb") as output:
                    shutil.copyfileobj(archived_database, output)

            self._validate_database(restore_temp)
            self.database.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(restore_temp), str(self.database.path))
        except BackupError:
            raise
        except (BadZipFile, OSError, sqlite3.Error) as exc:
            raise BackupError("Yedek geri yüklenemedi.") from exc
        finally:
            if restore_temp.exists():
                restore_temp.unlink()

    def list_backups(self) -> list[BackupInfo]:
        if not self.backup_dir.exists():
            return []
        backups = []
        for path in self.backup_dir.glob("*.zip"):
            stat = path.stat()
            backups.append(
                BackupInfo(
                    path=path,
                    created_at=datetime.fromtimestamp(stat.st_mtime),
                    size_bytes=stat.st_size,
                )
            )
        return sorted(backups, key=lambda backup: backup.created_at, reverse=True)

    def database_status(self) -> dict[str, object]:
        exists = self.database.path.exists()
        size_bytes = self.database.path.stat().st_size if exists else 0
        modified_at = datetime.fromtimestamp(self.database.path.stat().st_mtime) if exists else None
        return {
            "path": self.database.path,
            "exists": exists,
            "size_bytes": size_bytes,
            "modified_at": modified_at,
        }

    def _default_backup_path(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.backup_dir / f"paketleme_yedek_{timestamp}.zip"

    def _copy_database_snapshot(self, destination: Path) -> None:
        source = sqlite3.connect(self.database.path)
        try:
            target = sqlite3.connect(destination)
            try:
                source.backup(target)
            finally:
                target.close()
        finally:
            source.close()

    def _validate_database(self, path: Path) -> None:
        connection = sqlite3.connect(path)
        try:
            required_tables = {"boxes", "vehicles", "product_profiles", "packing_plans", "application_settings"}
            rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            table_names = {row[0] for row in rows}
            if not required_tables.issubset(table_names):
                raise BackupError("Yedek dosyasında gerekli uygulama tabloları bulunamadı.")
        finally:
            connection.close()
