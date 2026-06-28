from pathlib import Path

from app.repositories.database import Database
from app.repositories.packing_plan_repository import PackingPlanRepository
from app.services.packing_service import PackingService


def test_packing_plan_repository_saves_calculated_plan(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 80}]
    )

    plan_id = PackingPlanRepository(database).save_calculated_plan(result)

    with database.connect() as connection:
        plan = connection.execute("SELECT * FROM packing_plans WHERE id = ?", (plan_id,)).fetchone()
        box_count = connection.execute(
            "SELECT COUNT(*) FROM packing_plan_boxes WHERE packing_plan_id = ?",
            (plan_id,),
        ).fetchone()[0]

    assert plan is not None
    assert plan["total_product_quantity"] == 80
    assert box_count == result.total_box_count


def test_packing_plan_repository_lists_recent_plans(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 80}]
    )
    repository = PackingPlanRepository(database)
    plan_id = repository.save_calculated_plan(result)

    plans = repository.list_recent_plans()
    plan = repository.get_plan_summary(plan_id)

    assert plans
    assert plans[0].id == plan_id
    assert plan is not None
    assert plan.total_box_count == result.total_box_count


def test_packing_plan_repository_returns_plan_detail(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 80}]
    )
    repository = PackingPlanRepository(database)
    plan_id = repository.save_calculated_plan(result)

    detail = repository.get_plan_detail(plan_id)

    assert detail is not None
    assert detail.summary.id == plan_id
    assert len(detail.boxes) == result.total_box_count
    assert detail.boxes[0].box_code
