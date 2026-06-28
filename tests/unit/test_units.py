import pytest

from app.domain.exceptions import UnknownUnitError
from app.utils.units import cm3_to_m3, normalize_length, normalize_weight


def test_normalize_length_to_cm() -> None:
    assert normalize_length(10, "mm") == 1
    assert normalize_length(2, "m") == 200
    assert normalize_length(15, "cm") == 15


def test_normalize_weight_to_kg() -> None:
    assert normalize_weight(500, "g") == 0.5
    assert normalize_weight(3, "kg") == 3


def test_unknown_unit_raises_user_presentable_error() -> None:
    with pytest.raises(UnknownUnitError, match="Desteklenmeyen"):
        normalize_length(1, "inch")


def test_cm3_to_m3() -> None:
    assert cm3_to_m3(1_000_000) == 1

