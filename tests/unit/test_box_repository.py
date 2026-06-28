from pathlib import Path

from app.repositories.box_repository import BoxRepository
from app.repositories.database import Database
from app.domain.models import Box


def test_box_repository_lists_seeded_active_boxes(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    boxes = BoxRepository(database).list_active_boxes()

    assert len(boxes) == 3
    assert boxes[0].inner_volume_cm3 > 0


def test_box_repository_saves_new_box(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()
    repository = BoxRepository(database)

    box_id = repository.save_box(
        Box(
            id=None,
            code="BOX-NEW",
            name="Yeni Kutu",
            inner_length_cm=50,
            inner_width_cm=40,
            inner_height_cm=30,
            outer_length_cm=52,
            outer_width_cm=42,
            outer_height_cm=32,
            empty_weight_kg=1,
            max_gross_weight_kg=20,
        )
    )

    boxes = repository.list_active_boxes()
    assert box_id is not None
    assert any(box.code == "BOX-NEW" for box in boxes)
