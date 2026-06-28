from pathlib import Path

from app.repositories.database import Database
from app.repositories.vehicle_repository import VehicleRepository
from app.domain.models import Vehicle


def test_vehicle_repository_lists_seeded_active_vehicles(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    vehicles = VehicleRepository(database).list_active_vehicles()

    assert len(vehicles) == 2
    assert vehicles[0].volume_m3 > 0


def test_vehicle_repository_saves_new_vehicle(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    repository = VehicleRepository(database)

    vehicle_id = repository.save_vehicle(
        Vehicle(
            id=None,
            code="TRUCK-NEW",
            name="Yeni Araç",
            inner_length_cm=500,
            inner_width_cm=220,
            inner_height_cm=230,
            max_load_weight_kg=3000,
        )
    )

    vehicles = repository.list_active_vehicles()
    assert vehicle_id is not None
    assert any(vehicle.code == "TRUCK-NEW" for vehicle in vehicles)
