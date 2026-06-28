from dataclasses import dataclass
from math import ceil, floor

from app.algorithms.orientations import generate_orientations
from app.domain.models import Box


@dataclass(frozen=True)
class GarmentProfileDimensions:
    length_cm: float
    width_cm: float
    height_cm: float
    unit_weight_kg: float

    @property
    def volume_cm3(self) -> float:
        return self.length_cm * self.width_cm * self.height_cm


@dataclass(frozen=True)
class GarmentBoxCapacity:
    box: Box
    orientation: tuple[float, float, float]
    geometric_capacity: int
    weight_capacity: int
    operational_maximum: int | None
    final_capacity: int
    fullness_percent_at_capacity: float


@dataclass(frozen=True)
class GarmentPackingResult:
    box: Box
    capacity: GarmentBoxCapacity
    quantity: int
    box_count: int
    full_box_count: int
    partial_box_count: int
    average_fullness_percent: float
    estimated_total_gross_weight_kg: float
    score: float


def calculate_capacity(
    box: Box,
    profile: GarmentProfileDimensions,
    operational_maximum: int | None = None,
) -> GarmentBoxCapacity | None:
    best_capacity: GarmentBoxCapacity | None = None
    available_weight = max(box.max_gross_weight_kg - box.empty_weight_kg, 0)
    weight_capacity = floor(available_weight / profile.unit_weight_kg) if profile.unit_weight_kg > 0 else 0

    for orientation in generate_orientations(profile.length_cm, profile.width_cm, profile.height_cm):
        length, width, height = orientation
        count_x = floor(box.inner_length_cm / length)
        count_y = floor(box.inner_width_cm / width)
        count_z = floor(box.inner_height_cm / height)
        geometric_capacity = count_x * count_y * count_z
        final_capacity = min(geometric_capacity, weight_capacity)
        if operational_maximum is not None:
            final_capacity = min(final_capacity, operational_maximum)
        if final_capacity <= 0:
            continue

        fullness = final_capacity * profile.volume_cm3 / box.inner_volume_cm3 * 100
        candidate = GarmentBoxCapacity(
            box=box,
            orientation=orientation,
            geometric_capacity=geometric_capacity,
            weight_capacity=weight_capacity,
            operational_maximum=operational_maximum,
            final_capacity=final_capacity,
            fullness_percent_at_capacity=fullness,
        )
        if best_capacity is None or candidate.final_capacity > best_capacity.final_capacity:
            best_capacity = candidate
        elif best_capacity and candidate.final_capacity == best_capacity.final_capacity:
            if candidate.fullness_percent_at_capacity > best_capacity.fullness_percent_at_capacity:
                best_capacity = candidate

    return best_capacity


def rank_box_for_quantity(
    box: Box,
    profile: GarmentProfileDimensions,
    quantity: int,
    operational_maximum: int | None = None,
) -> GarmentPackingResult | None:
    if quantity <= 0:
        return None

    capacity = calculate_capacity(box, profile, operational_maximum)
    if capacity is None:
        return None

    box_count = ceil(quantity / capacity.final_capacity)
    full_box_count = quantity // capacity.final_capacity
    partial_box_count = 1 if quantity % capacity.final_capacity else 0
    used_volume = quantity * profile.volume_cm3
    total_inner_volume = box_count * box.inner_volume_cm3
    average_fullness = used_volume / total_inner_volume * 100
    estimated_total_gross_weight = quantity * profile.unit_weight_kg + box_count * box.empty_weight_kg
    total_unused_volume = total_inner_volume - used_volume
    score = box_count * 1_000_000 + partial_box_count * 100_000 + total_unused_volume

    return GarmentPackingResult(
        box=box,
        capacity=capacity,
        quantity=quantity,
        box_count=box_count,
        full_box_count=full_box_count,
        partial_box_count=partial_box_count,
        average_fullness_percent=average_fullness,
        estimated_total_gross_weight_kg=estimated_total_gross_weight,
        score=score,
    )


def choose_best_box(
    boxes: list[Box],
    profile: GarmentProfileDimensions,
    quantity: int,
    operational_maximum_by_box_code: dict[str, int] | None = None,
    allow_partial_boxes: bool = True,
    prefer_small_final_box: bool = True,
) -> GarmentPackingResult | None:
    results: list[GarmentPackingResult] = []
    operational_maximum_by_box_code = operational_maximum_by_box_code or {}

    for box in boxes:
        result = rank_box_for_quantity(
            box=box,
            profile=profile,
            quantity=quantity,
            operational_maximum=operational_maximum_by_box_code.get(box.code),
        )
        if result is not None:
            if not allow_partial_boxes and result.partial_box_count:
                continue
            results.append(result)

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
