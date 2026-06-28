from app.domain.models import Box
from app.repositories.database import Database


class BoxRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def list_active_boxes(self) -> list[Box]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM boxes
                WHERE active = 1
                ORDER BY id ASC
                """
            ).fetchall()
        return [
            Box(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                inner_length_cm=row["inner_length_cm"],
                inner_width_cm=row["inner_width_cm"],
                inner_height_cm=row["inner_height_cm"],
                outer_length_cm=row["outer_length_cm"],
                outer_width_cm=row["outer_width_cm"],
                outer_height_cm=row["outer_height_cm"],
                empty_weight_kg=row["empty_weight_kg"],
                max_gross_weight_kg=row["max_gross_weight_kg"],
                active=bool(row["active"]),
            )
            for row in rows
        ]

    def save_box(self, box: Box) -> int:
        with self.database.transaction() as connection:
            if box.id is None:
                cursor = connection.execute(
                    """
                    INSERT INTO boxes (
                        code,
                        name,
                        inner_length_cm,
                        inner_width_cm,
                        inner_height_cm,
                        outer_length_cm,
                        outer_width_cm,
                        outer_height_cm,
                        empty_weight_kg,
                        max_gross_weight_kg,
                        active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        box.code,
                        box.name,
                        box.inner_length_cm,
                        box.inner_width_cm,
                        box.inner_height_cm,
                        box.outer_length_cm,
                        box.outer_width_cm,
                        box.outer_height_cm,
                        box.empty_weight_kg,
                        box.max_gross_weight_kg,
                        int(box.active),
                    ),
                )
                return int(cursor.lastrowid)

            connection.execute(
                """
                UPDATE boxes
                SET
                    code = ?,
                    name = ?,
                    inner_length_cm = ?,
                    inner_width_cm = ?,
                    inner_height_cm = ?,
                    outer_length_cm = ?,
                    outer_width_cm = ?,
                    outer_height_cm = ?,
                    empty_weight_kg = ?,
                    max_gross_weight_kg = ?,
                    active = ?
                WHERE id = ?
                """,
                (
                    box.code,
                    box.name,
                    box.inner_length_cm,
                    box.inner_width_cm,
                    box.inner_height_cm,
                    box.outer_length_cm,
                    box.outer_width_cm,
                    box.outer_height_cm,
                    box.empty_weight_kg,
                    box.max_gross_weight_kg,
                    int(box.active),
                    box.id,
                ),
            )
            return int(box.id)
