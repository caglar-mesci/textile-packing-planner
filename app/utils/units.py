from app.domain.exceptions import UnknownUnitError


LENGTH_UNITS_TO_CM = {
    "mm": 0.1,
    "cm": 1.0,
    "m": 100.0,
}

WEIGHT_UNITS_TO_KG = {
    "g": 0.001,
    "kg": 1.0,
}


def normalize_length(value: float, unit: str) -> float:
    normalized_unit = unit.strip().lower()
    if normalized_unit not in LENGTH_UNITS_TO_CM:
        raise UnknownUnitError(f"Desteklenmeyen uzunluk birimi: {unit}")
    return value * LENGTH_UNITS_TO_CM[normalized_unit]


def normalize_weight(value: float, unit: str) -> float:
    normalized_unit = unit.strip().lower()
    if normalized_unit not in WEIGHT_UNITS_TO_KG:
        raise UnknownUnitError(f"Desteklenmeyen ağırlık birimi: {unit}")
    return value * WEIGHT_UNITS_TO_KG[normalized_unit]


def cm3_to_m3(value: float) -> float:
    return value / 1_000_000

