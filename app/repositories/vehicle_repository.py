from app.domain.models import Vehicle
from app.repositories.database import Database


class VehicleRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def list_active_vehicles(self) -> list[Vehicle]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM vehicles
                WHERE active = 1
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            Vehicle(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                inner_length_cm=row["inner_length_cm"],
                inner_width_cm=row["inner_width_cm"],
                inner_height_cm=row["inner_height_cm"],
                max_load_weight_kg=row["max_load_weight_kg"],
                active=bool(row["active"]),
            )
            for row in rows
        ]

    def save_vehicle(self, vehicle: Vehicle) -> int:
        with self.database.transaction() as connection:
            if vehicle.id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO vehicles (
                        code,
                        name,
                        inner_length_cm,
                        inner_width_cm,
                        inner_height_cm,
                        max_load_weight_kg,
                        active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        vehicle.code,
                        vehicle.name,
                        vehicle.inner_length_cm,
                        vehicle.inner_width_cm,
                        vehicle.inner_height_cm,
                        vehicle.max_load_weight_kg,
                        int(vehicle.active),
                    ),
                )
                return int(cursor.lastrowid)

            connection.execute(
                """
                UPDATE vehicles
                SET
                    code = ?,
                    name = ?,
                    inner_length_cm = ?,
                    inner_width_cm = ?,
                    inner_height_cm = ?,
                    max_load_weight_kg = ?,
                    active = ?
                WHERE id = ?
                """,
                (
                    vehicle.code,
                    vehicle.name,
                    vehicle.inner_length_cm,
                    vehicle.inner_width_cm,
                    vehicle.inner_height_cm,
                    vehicle.max_load_weight_kg,
                    int(vehicle.active),
                    vehicle.id,
                ),
            )
            return int(vehicle.id)
