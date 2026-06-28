from app.algorithms.garment_packing import (
    GarmentProfileDimensions,
    calculate_capacity,
    choose_best_box,
)
from app.algorithms.orientations import generate_orientations
from app.domain.models import Box


def make_box(code: str, length: float, width: float, height: float, max_weight: float = 25) -> Box:
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


def test_generate_orientations_returns_unique_permutations() -> None:
    assert len(generate_orientations(30, 25, 2)) == 6
    assert len(generate_orientations(30, 30, 2)) == 3


def test_calculate_capacity_uses_geometry_weight_and_operational_maximum() -> None:
    box = make_box("BOX-L", 80, 50, 45, max_weight=35)
    profile = GarmentProfileDimensions(length_cm=30, width_cm=25, height_cm=2, unit_weight_kg=0.2)

    capacity = calculate_capacity(box, profile, operational_maximum=80)

    assert capacity is not None
    assert capacity.geometric_capacity >= 80
    assert capacity.weight_capacity > 80
    assert capacity.final_capacity == 80


def test_choose_best_box_prefers_lower_score() -> None:
    small = make_box("BOX-S", 40, 30, 25)
    large = make_box("BOX-L", 80, 50, 45, max_weight=35)
    profile = GarmentProfileDimensions(length_cm=30, width_cm=25, height_cm=2, unit_weight_kg=0.2)

    result = choose_best_box([small, large], profile, quantity=160, operational_maximum_by_box_code={"BOX-L": 80})

    assert result is not None
    assert result.box.code == "BOX-L"
    assert result.box_count == 2

