from app.algorithms.vehicle_selector import select_vehicle
from app.domain.models import Vehicle


def make_vehicle(code: str, length: float, width: float, height: float, max_weight: float) -> Vehicle:
    return Vehicle(
        id=None,
        code=code,
        name=code,
        inner_length_cm=length,
        inner_width_cm=width,
        inner_height_cm=height,
        max_load_weight_kg=max_weight,
    )


def test_select_vehicle_prefers_minimum_vehicle_count() -> None:
    small = make_vehicle("SMALL", 100, 100, 100, 200)
    large = make_vehicle("LARGE", 300, 200, 200, 1000)

    selection = select_vehicle([small, large], shipment_volume_cm3=3_000_000, shipment_weight_kg=500)

    assert selection is not None
    assert selection.vehicle.code == "LARGE"
    assert selection.vehicle_count == 1


def test_select_vehicle_scales_count_by_weight() -> None:
    vehicle = make_vehicle("VAN", 300, 200, 200, 1000)

    selection = select_vehicle([vehicle], shipment_volume_cm3=1_000_000, shipment_weight_kg=2500)

    assert selection is not None
    assert selection.vehicle_count == 3

