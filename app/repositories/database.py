import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.config import DATABASE_PATH
from app.repositories.schema import SCHEMA_SQL


PRODUCT_TYPE_SEED = [
    ("T-Shirt", "GARMENT"),
    ("Shirt", "GARMENT"),
    ("Pants", "GARMENT"),
    ("Sweatshirt", "GARMENT"),
    ("Jacket", "GARMENT"),
    ("Other Garment", "GARMENT"),
    ("Fabric Roll", "FABRIC_ROLL"),
]

PROFILE_SEED = [
    ("Standard T-Shirt", "T-Shirt", 30, 25, 2, 0.20, None, None, 1),
    ("Standard Shirt", "Shirt", 32, 26, 2.5, 0.25, None, None, 1),
    ("Standard Pants", "Pants", 35, 28, 3, 0.45, None, None, 1),
    ("Standard Sweatshirt", "Sweatshirt", 36, 30, 5, 0.65, None, None, 1),
    ("Standard Jacket", "Jacket", 45, 35, 8, 1.10, None, None, 0),
    ("General Garment", "Other Garment", 35, 28, 4, 0.50, None, None, 1),
    ("General Fabric Roll", "Fabric Roll", None, None, None, None, 30, "HORIZONTAL", 0),
    ("Cotton Fabric Roll", "Fabric Roll", None, None, None, None, 28, "HORIZONTAL", 0),
    ("Polyester Fabric Roll", "Fabric Roll", None, None, None, None, 26, "HORIZONTAL", 0),
]

BOX_SEED = [
    ("BOX-S", "Küçük Kutu", 40, 30, 25, 42, 32, 27, 0.6, 18),
    ("BOX-M", "Orta Kutu", 60, 40, 35, 62, 42, 37, 1.0, 25),
    ("BOX-L", "Büyük Kutu", 80, 50, 45, 83, 53, 48, 1.6, 35),
]

VEHICLE_SEED = [
    ("VAN", "Panelvan", 250, 160, 150, 900),
    ("TRUCK-S", "Küçük Kamyon", 420, 210, 220, 2500),
]


class Database:
    def __init__(self, path: Path = DATABASE_PATH) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.transaction() as connection:
            connection.executescript(SCHEMA_SQL)
            seed_database(connection)


def seed_database(connection: sqlite3.Connection) -> None:
    # Seed data is intentionally minimal: companies are expected to replace these
    # defaults with their real box, vehicle, and product profile values.
    _seed_product_types(connection)
    type_ids = _product_type_ids(connection)
    _seed_profiles(connection, type_ids)
    _seed_boxes(connection)
    _seed_vehicles(connection)
    _seed_application_settings(connection)


def _seed_product_types(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO product_types (name, category)
        VALUES (?, ?)
        """,
        PRODUCT_TYPE_SEED,
    )


def _product_type_ids(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        row["name"]: row["id"]
        for row in connection.execute("SELECT id, name FROM product_types")
    }


def _seed_profiles(connection: sqlite3.Connection, type_ids: dict[str, int]) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO product_profiles (
            name,
            product_type_id,
            average_length_cm,
            average_width_cm,
            average_height_cm,
            average_weight_kg,
            average_diameter_cm,
            allowed_orientation,
            stackable,
            default_packaging_rule,
            default_mixed_box_allowed
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'BOXED', 1)
        """,
        [
            (name, type_ids[type_name], length, width, height, weight, diameter, orientation, stackable)
            for name, type_name, length, width, height, weight, diameter, orientation, stackable in PROFILE_SEED
        ],
    )


def _seed_boxes(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO boxes (
            code,
            name,
            inner_length_cm,
            inner_width_cm,
            inner_height_cm,
            outer_length_cm,
            outer_width_cm,
            outer_height_cm,
            empty_weight_kg,
            max_gross_weight_kg
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        BOX_SEED,
    )


def _seed_vehicles(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT OR IGNORE INTO vehicles (
            code,
            name,
            inner_length_cm,
            inner_width_cm,
            inner_height_cm,
            max_load_weight_kg
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        VEHICLE_SEED,
    )


def _seed_application_settings(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT OR IGNORE INTO application_settings (key, value)
        VALUES ('seed_data_notice_tr', 'Bu değerler örnek veridir; şirket değerleriyle güncellenmelidir.')
        """
    )
