from itertools import permutations


def generate_orientations(length_cm: float, width_cm: float, height_cm: float) -> list[tuple[float, float, float]]:
    """Return unique rectangular orientations in deterministic order."""
    seen: set[tuple[float, float, float]] = set()
    orientations: list[tuple[float, float, float]] = []
    for orientation in permutations((length_cm, width_cm, height_cm), 3):
        if orientation not in seen:
            seen.add(orientation)
            orientations.append(orientation)
    return orientations

