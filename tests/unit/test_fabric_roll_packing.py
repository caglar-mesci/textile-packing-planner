from app.algorithms.fabric_roll_packing import (
    FabricRollProfile,
    calculate_fabric_roll_capacity,
    choose_best_fabric_roll_box,
)
from app.domain.models import Box


def make_box(code: str, length: float, width: float, height: float, max_weight: float = 35) -> Box:
    return Box(
        id=None,
        code=code,
        name=code,
        inner_length_cm=length,
        inner_width_cm=width,
        inner_height_cm=height,
        outer_length_cm=length + 2,
        outer_width_cm=width + 2,
        outer_height_cm=height + 2,
        empty_weight_kg=1,
        max_gross_weight_kg=max_weight,
    )


def test_fabric_roll_capacity_uses_length_diameter_and_weight() -> None:
    box = make_box("BOX-L", 100, 60, 60)
    profile = FabricRollProfile(roll_length_cm=80, roll_weight_kg=10, average_diameter_cm=30)

    capacity = calculate_fabric_roll_capacity(box, profile)

    assert capacity is not None
    assert capacity.final_capacity == 3
    assert capacity.weight_capacity == 3


def test_choose_best_fabric_roll_box_returns_valid_result() -> None:
    small = make_box("BOX-S", 50, 40, 40)
    large = make_box("BOX-L", 100, 60, 60)
    profile = FabricRollProfile(roll_length_cm=80, roll_weight_kg=10, average_diameter_cm=30)

    result = choose_best_fabric_roll_box([small, large], profile, roll_count=5)

    assert result is not None
    assert result.box.code == "BOX-L"
    assert result.box_count == 2
