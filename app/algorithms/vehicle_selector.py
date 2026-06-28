from dataclasses import dataclass
from math import ceil

from app.domain.models import Vehicle


@dataclass(frozen=True)
class VehicleSelection:
    vehicle: Vehicle
    vehicle_count: int
    volume_utilization_percent: float
    weight_utilization_percent: float
    unused_volume_cm3: float


def select_vehicle(
    vehicles: list[Vehicle],
    shipment_volume_cm3: float,
    shipment_weight_kg: float,
) -> VehicleSelection | None:
    active_vehicles = [vehicle for vehicle in vehicles if vehicle.active]
    if not active_vehicles:
        return None

    selections: list[VehicleSelection] = []
    for vehicle in active_vehicles:
        count_by_volume = ceil(shipment_volume_cm3 / vehicle.volume_cm3) if shipment_volume_cm3 > 0 else 1
        count_by_weight = ceil(shipment_weight_kg / vehicle.max_load_weight_kg) if shipment_weight_kg > 0 else 1
        vehicle_count = max(count_by_volume, count_by_weight, 1)
        total_vehicle_volume = vehicle_count * vehicle.volume_cm3
        total_vehicle_weight = vehicle_count * vehicle.max_load_weight_kg
        volume_utilization = shipment_volume_cm3 / total_vehicle_volume * 100 if total_vehicle_volume else 0
        weight_utilization = shipment_weight_kg / total_vehicle_weight * 100 if total_vehicle_weight else 0
        selections.append(
            VehicleSelection(
                vehicle=vehicle,
                vehicle_count=vehicle_count,
                volume_utilization_percent=volume_utilization,
                weight_utilization_percent=weight_utilization,
                unused_volume_cm3=total_vehicle_volume - shipment_volume_cm3,
            )
        )

    return min(
        selections,
        key=lambda selection: (
            selection.vehicle_count,
            -selection.volume_utilization_percent,
            selection.unused_volume_cm3,
        ),
    )

