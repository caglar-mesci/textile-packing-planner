from dataclasses import dataclass
from math import ceil, floor, pi

from app.domain.models import Box


@dataclass(frozen=True)
class FabricRollProfile:
    roll_length_cm: float
    roll_weight_kg: float
    average_diameter_cm: float
    allowed_orientation: str | None = "HORIZONTAL"

    @property
    def volume_cm3(self) -> float:
        return pi * (self.average_diameter_cm / 2) ** 2 * self.roll_length_cm


@dataclass(frozen=True)
class FabricRollBoxCapacity:
    box: Box
    orientation: str
    geometric_capacity: int
    weight_capacity: int
    final_capacity: int
    fullness_percent_at_capacity: float


@dataclass(frozen=True)
class FabricRollPackingResult:
    box: Box
    capacity: FabricRollBoxCapacity
    roll_count: int
    box_count: int
    partial_box_count: int
    average_fullness_percent: float
    estimated_total_gross_weight_kg: float
    score: float


def calculate_fabric_roll_capacity(
    box: Box,
    profile: FabricRollProfile,
    operational_maximum: int | None = None,
) -> FabricRollBoxCapacity | None:
    candidates: list[FabricRollBoxCapacity] = []
    allowed_orientation = (profile.allowed_orientation or "HORIZONTAL").upper()

    if allowed_orientation in {"HORIZONTAL", "BOTH"}:
        candidates.extend(_horizontal_capacities(box, profile, operational_maximum))
    if allowed_orientation in {"VERTICAL", "BOTH"}:
        vertical = _vertical_capacity(box, profile, operational_maximum)
        if vertical is not None:
            candidates.append(vertical)

    if not candidates:
        return None

    return max(candidates, key=lambda candidate: (candidate.final_capacity, candidate.fullness_percent_at_capacity))


def rank_fabric_roll_box(
    box: Box,
    profile: FabricRollProfile,
    roll_count: int,
    operational_maximum: int | None = None,
) -> FabricRollPackingResult | None:
    if roll_count <= 0:
        return None

    capacity = calculate_fabric_roll_capacity(box, profile, operational_maximum)
    if capacity is None:
        return None

    box_count = ceil(roll_count / capacity.final_capacity)
    used_volume = roll_count * profile.volume_cm3
    total_inner_volume = box_count * box.inner_volume_cm3
    average_fullness = used_volume / total_inner_volume * 100
    estimated_weight = roll_count * profile.roll_weight_kg + box_count * box.empty_weight_kg
    total_unused_volume = total_inner_volume - used_volume
    partial_box_count = 1 if roll_count % capacity.final_capacity else 0
    score = box_count * 1_000_000 + partial_box_count * 100_000 + total_unused_volume

    return FabricRollPackingResult(
        box=box,
        capacity=capacity,
        roll_count=roll_count,
        box_count=box_count,
        partial_box_count=partial_box_count,
        average_fullness_percent=average_fullness,
        estimated_total_gross_weight_kg=estimated_weight,
        score=score,
    )


def choose_best_fabric_roll_box(
    boxes: list[Box],
    profile: FabricRollProfile,
    roll_count: int,
    operational_maximum_by_box_code: dict[str, int] | None = None,
    allow_partial_boxes: bool = True,
    prefer_small_final_box: bool = True,
) -> FabricRollPackingResult | None:
    operational_maximum_by_box_code = operational_maximum_by_box_code or {}
    results = [
        result
        for box in boxes
        if (
            result := rank_fabric_roll_box(
                box,
                profile,
                roll_count,
                operational_maximum_by_box_code.get(box.code),
            )
        )
        is not None
    ]
    if not allow_partial_boxes:
        results = [result for result in results if not result.partial_box_count]
    if not results:
        return None
    return min(
        results,
        key=lambda result: (
            result.score,
            -result.average_fullness_percent,
            result.box.outer_volume_cm3 if prefer_small_final_box else 0,
        ),
    )


def _horizontal_capacities(
    box: Box,
    profile: FabricRollProfile,
    operational_maximum: int | None,
) -> list[FabricRollBoxCapacity]:
    dimensions = [
        (box.inner_length_cm, box.inner_width_cm, box.inner_height_cm, "yatay-uzunluk"),
        (box.inner_width_cm, box.inner_length_cm, box.inner_height_cm, "yatay-genişlik"),
        (box.inner_height_cm, box.inner_length_cm, box.inner_width_cm, "yatay-yükseklik"),
    ]
    capacities: list[FabricRollBoxCapacity] = []
    for axis, side_a, side_b, label in dimensions:
        if profile.roll_length_cm > axis:
            continue
        geometric_capacity = (
            floor(axis / profile.roll_length_cm)
            * floor(side_a / profile.average_diameter_cm)
            * floor(side_b / profile.average_diameter_cm)
        )
        capacity = _capacity_from_geometric(box, profile, geometric_capacity, operational_maximum, label)
        if capacity is not None:
            capacities.append(capacity)
    return capacities


def _vertical_capacity(
    box: Box,
    profile: FabricRollProfile,
    operational_maximum: int | None,
) -> FabricRollBoxCapacity | None:
    if profile.roll_length_cm > box.inner_height_cm:
        return None
    geometric_capacity = floor(box.inner_length_cm / profile.average_diameter_cm) * floor(
        box.inner_width_cm / profile.average_diameter_cm
    )
    return _capacity_from_geometric(box, profile, geometric_capacity, operational_maximum, "dikey")


def _capacity_from_geometric(
    box: Box,
    profile: FabricRollProfile,
    geometric_capacity: int,
    operational_maximum: int | None,
    orientation: str,
) -> FabricRollBoxCapacity | None:
    available_weight = max(box.max_gross_weight_kg - box.empty_weight_kg, 0)
    weight_capacity = floor(available_weight / profile.roll_weight_kg) if profile.roll_weight_kg > 0 else 0
    final_capacity = min(geometric_capacity, weight_capacity)
    if operational_maximum is not None:
        final_capacity = min(final_capacity, operational_maximum)
    if final_capacity <= 0:
        return None

    fullness = final_capacity * profile.volume_cm3 / box.inner_volume_cm3 * 100
    return FabricRollBoxCapacity(
        box=box,
        orientation=orientation,
        geometric_capacity=geometric_capacity,
        weight_capacity=weight_capacity,
        final_capacity=final_capacity,
        fullness_percent_at_capacity=fullness,
    )
