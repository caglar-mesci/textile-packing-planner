from datetime import datetime
from dataclasses import dataclass
import sqlite3

from app.repositories.database import Database
from app.services.packing_service import PackingCalculationResult


@dataclass(frozen=True)
class SavedPlanSummary:
    id: int
    created_at: str
    status: str
    total_product_quantity: float
    total_box_count: int
    total_weight_kg: float
    average_box_fullness: float
    vehicle_name: str | None
    vehicle_count: int
    is_valid: bool


@dataclass(frozen=True)
class SavedPlanBox:
    sequence_number: int
    box_code: str
    box_name: str
    estimated_gross_weight_kg: float
    fullness_percent: float
    is_valid: bool


@dataclass(frozen=True)
class SavedPlanDetail:
    summary: SavedPlanSummary
    boxes: list[SavedPlanBox]


class PackingPlanRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def save_calculated_plan(self, result: PackingCalculationResult, source_type: str = "MANUAL") -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with self.database.transaction() as connection:
            order_id = self._insert_order(connection, source_type, now)
            plan_id = self._insert_plan(connection, result, order_id, now)
            self._insert_plan_boxes(connection, result, plan_id)
            return plan_id

    def _insert_order(self, connection: sqlite3.Connection, source_type: str, now: str) -> int:
        cursor = connection.execute(
            """
            INSERT INTO orders (
                order_number,
                customer_name,
                shipment_date,
                source_type,
                source_file,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (None, None, None, source_type, None, "CALCULATED", now, now),
        )
        return int(cursor.lastrowid)

    def _insert_plan(
        self,
        connection: sqlite3.Connection,
        result: PackingCalculationResult,
        order_id: int,
        now: str,
    ) -> int:
        is_valid = 1 if result.validation_result and result.validation_result.is_valid else 0
        cursor = connection.execute(
            """
            INSERT INTO packing_plans (
                order_id,
                status,
                confidence_level,
                total_product_quantity,
                total_box_count,
                total_weight_kg,
                average_box_fullness,
                vehicle_id_nullable,
                vehicle_count,
                vehicle_volume_utilization,
                vehicle_weight_utilization,
                is_valid,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                "VALID" if is_valid else "INVALID",
                "MEDIUM",
                result.total_quantity,
                result.total_box_count,
                result.estimated_total_weight_kg,
                result.average_fullness_percent,
                result.vehicle_selection.vehicle.id if result.vehicle_selection else None,
                result.vehicle_selection.vehicle_count if result.vehicle_selection else 0,
                result.vehicle_selection.volume_utilization_percent if result.vehicle_selection else 0,
                result.vehicle_selection.weight_utilization_percent if result.vehicle_selection else 0,
                is_valid,
                now,
                now,
            ),
        )
        return int(cursor.lastrowid)

    def _insert_plan_boxes(
        self,
        connection: sqlite3.Connection,
        result: PackingCalculationResult,
        plan_id: int,
    ) -> None:
        for line in result.packed_lines:
            if not line.box_code or line.box_count <= 0:
                continue
            box_row = connection.execute("SELECT id FROM boxes WHERE code = ?", (line.box_code,)).fetchone()
            if box_row is None:
                continue
            for sequence in range(line.box_count):
                connection.execute(
                    """
                    INSERT INTO packing_plan_boxes (
                        packing_plan_id,
                        box_id,
                        sequence_number,
                        estimated_gross_weight_kg,
                        fullness_percent,
                        is_valid
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        plan_id,
                        box_row["id"],
                        sequence + 1,
                        line.estimated_weight_kg / line.box_count,
                        line.average_fullness_percent,
                        1,
                    ),
                )

    def list_recent_plans(self, limit: int = 25) -> list[SavedPlanSummary]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    packing_plans.id,
                    packing_plans.created_at,
                    packing_plans.status,
                    packing_plans.total_product_quantity,
                    packing_plans.total_box_count,
                    packing_plans.total_weight_kg,
                    packing_plans.average_box_fullness,
                    packing_plans.vehicle_count,
                    packing_plans.is_valid,
                    vehicles.name AS vehicle_name
                FROM packing_plans
                LEFT JOIN vehicles ON vehicles.id = packing_plans.vehicle_id_nullable
                ORDER BY packing_plans.created_at DESC, packing_plans.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._summary_from_row(row) for row in rows]

    def get_plan_summary(self, plan_id: int) -> SavedPlanSummary | None:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    packing_plans.id,
                    packing_plans.created_at,
                    packing_plans.status,
                    packing_plans.total_product_quantity,
                    packing_plans.total_box_count,
                    packing_plans.total_weight_kg,
                    packing_plans.average_box_fullness,
                    packing_plans.vehicle_count,
                    packing_plans.is_valid,
                    vehicles.name AS vehicle_name
                FROM packing_plans
                LEFT JOIN vehicles ON vehicles.id = packing_plans.vehicle_id_nullable
                WHERE packing_plans.id = ?
                """,
                (plan_id,),
            ).fetchone()
        if row is None:
            return None
        return self._summary_from_row(row)

    def get_plan_detail(self, plan_id: int) -> SavedPlanDetail | None:
        summary = self.get_plan_summary(plan_id)
        if summary is None:
            return None

        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    packing_plan_boxes.sequence_number,
                    boxes.code AS box_code,
                    boxes.name AS box_name,
                    packing_plan_boxes.estimated_gross_weight_kg,
                    packing_plan_boxes.fullness_percent,
                    packing_plan_boxes.is_valid
                FROM packing_plan_boxes
                JOIN boxes ON boxes.id = packing_plan_boxes.box_id
                WHERE packing_plan_boxes.packing_plan_id = ?
                ORDER BY packing_plan_boxes.sequence_number ASC, packing_plan_boxes.id ASC
                """,
                (plan_id,),
            ).fetchall()

        return SavedPlanDetail(
            summary=summary,
            boxes=[
                SavedPlanBox(
                    sequence_number=row["sequence_number"],
                    box_code=row["box_code"],
                    box_name=row["box_name"],
                    estimated_gross_weight_kg=row["estimated_gross_weight_kg"],
                    fullness_percent=row["fullness_percent"],
                    is_valid=bool(row["is_valid"]),
                )
                for row in rows
            ],
        )

    def _summary_from_row(self, row: object) -> SavedPlanSummary:
        return SavedPlanSummary(
            id=row["id"],
            created_at=row["created_at"],
            status=row["status"],
            total_product_quantity=row["total_product_quantity"],
            total_box_count=row["total_box_count"],
            total_weight_kg=row["total_weight_kg"],
            average_box_fullness=row["average_box_fullness"],
            vehicle_name=row["vehicle_name"],
            vehicle_count=row["vehicle_count"],
            is_valid=bool(row["is_valid"]),
        )
