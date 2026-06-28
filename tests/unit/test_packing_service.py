from pathlib import Path

from app.repositories.database import Database
from app.services.packing_service import PackingService, PackingSettings


def test_packing_service_calculates_garment_summary(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 160}]
    )

    assert result.total_quantity == 160
    assert result.total_box_count > 0
    assert result.estimated_total_weight_kg > 0
    assert result.packed_lines[0].box_code is not None
    assert result.vehicle_selection is not None


def test_packing_service_warns_for_fabric_rolls(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [
            {
                "product_code": "ROLL-1",
                "product_name": "Kumaş",
                "product_type": "Fabric Roll",
                "quantity": 3,
                "roll_length_cm": 70,
                "roll_weight_kg": 12,
            }
        ]
    )

    assert result.total_box_count > 0
    assert result.estimated_total_weight_kg > 36
    assert result.packed_lines[0].box_code is not None
    assert result.vehicle_selection is not None
    assert result.warnings


def test_packing_service_warns_when_fabric_roll_data_is_missing(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [{"product_code": "ROLL-2", "product_type": "Fabric Roll", "quantity": 3, "roll_weight_kg": 12}]
    )

    assert result.total_box_count == 0
    assert result.packed_lines[0].status_text == "Rulo bilgisi eksik"


def test_packing_service_uses_selected_vehicle_when_provided(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 160}],
        PackingSettings(selected_vehicle_code="VAN"),
    )

    assert result.vehicle_selection is not None
    assert result.vehicle_selection.vehicle.code == "VAN"
    assert result.settings.selected_vehicle_code == "VAN"


def test_packing_service_blocks_selected_vehicle_when_one_vehicle_is_too_small(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [{"product_code": "TSH-BIG", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 5000}],
        PackingSettings(selected_vehicle_code="VAN"),
    )

    assert result.validation_result is not None
    assert not result.validation_result.is_valid
    assert any(error.code == "SELECTED_VEHICLE_TOO_SMALL" for error in result.validation_result.errors)
    assert any("otomatik araç seçimine dönün" in error.message for error in result.validation_result.errors)


def test_packing_service_warns_when_selected_vehicle_is_missing(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 160}],
        PackingSettings(selected_vehicle_code="UNKNOWN"),
    )

    assert result.vehicle_selection is None
    assert "Seçilen araç bulunamadı: UNKNOWN" in result.warnings


def test_packing_service_merges_duplicate_lines_by_default(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [
            {"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 80},
            {"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 20},
        ]
    )

    assert len(result.packed_lines) == 1
    assert result.packed_lines[0].quantity == 100


def test_packing_service_can_keep_duplicate_lines_separate(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [
            {"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 80},
            {"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 20},
        ],
        PackingSettings(merge_duplicate_lines=False),
    )

    assert len(result.packed_lines) == 2
    assert [line.quantity for line in result.packed_lines] == [80, 20]


def test_packing_service_can_reject_partial_boxes(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 30}],
        PackingSettings(allow_partial_boxes=False),
    )

    assert result.total_box_count == 0
    assert result.packed_lines[0].status_text == "Uygun kutu yok"


def test_packing_service_does_not_direct_load_unboxed_garments(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [{"product_code": "TSH-1", "product_name": "T-Shirt", "product_type": "T-Shirt", "quantity": 30}],
        PackingSettings(allow_partial_boxes=False, packaging_mode="direct_load_allowed"),
    )

    assert result.total_box_count == 0
    assert result.packed_lines[0].box_code is None
    assert result.packed_lines[0].status_text == "Uygun kutu yok"


def test_packing_service_allows_direct_load_for_unboxed_fabric_rolls(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [
            {
                "product_code": "ROLL-LONG",
                "product_name": "Uzun Kumaş",
                "product_type": "Fabric Roll",
                "quantity": 2,
                "roll_length_cm": 900,
                "roll_weight_kg": 12,
            }
        ],
        PackingSettings(packaging_mode="direct_load_allowed"),
    )

    assert result.packed_lines[0].box_code == "DIREKT"
    assert result.packed_lines[0].status_text == "Direkt yükleme"
    assert result.validation_result is not None
    assert result.validation_result.is_valid


def test_packing_service_explains_unboxed_fabric_roll_action(tmp_path: Path) -> None:
    database = Database(tmp_path / "planner.sqlite3")
    database.initialize()

    result = PackingService(database).calculate(
        [
            {
                "product_code": "ROLL-TOO-LONG",
                "product_name": "Uzun Kumaş",
                "product_type": "Fabric Roll",
                "quantity": 1,
                "roll_length_cm": 900,
                "roll_weight_kg": 12,
            }
        ],
        PackingSettings(packaging_mode="boxed_only"),
    )

    assert result.validation_result is not None
    assert not result.validation_result.is_valid
    assert any("Rulo için direkt yüklemeyi açın" in error.message for error in result.validation_result.errors)
