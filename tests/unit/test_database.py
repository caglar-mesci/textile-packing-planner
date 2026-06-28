from pathlib import Path

from app.repositories.database import Database


def test_database_initializes_schema_and_seed_data(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")

    database.initialize()

    with database.connect() as connection:
        product_type_count = connection.execute("SELECT COUNT(*) FROM product_types").fetchone()[0]
        profile_count = connection.execute("SELECT COUNT(*) FROM product_profiles").fetchone()[0]
        box_count = connection.execute("SELECT COUNT(*) FROM boxes").fetchone()[0]
        vehicle_count = connection.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]

    assert product_type_count == 7
    assert profile_count == 9
    assert box_count == 3
    assert vehicle_count == 2

