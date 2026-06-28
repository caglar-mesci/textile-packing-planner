from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import ConfidenceLevel, PackagingRule, ProductCategory


@dataclass(frozen=True)
class ProductType:
    id: int | None
    name: str
    category: ProductCategory
    active: bool = True


@dataclass(frozen=True)
class ProductProfile:
    id: int | None
    name: str
    product_type_id: int
    average_length_cm: float | None = None
    average_width_cm: float | None = None
    average_height_cm: float | None = None
    average_weight_kg: float | None = None
    average_diameter_cm: float | None = None
    allowed_orientation: str | None = None
    stackable: bool = True
    default_packaging_rule: PackagingRule = PackagingRule.BOXED
    default_mixed_box_allowed: bool = True
    active: bool = True


@dataclass(frozen=True)
class Product:
    id: int | None
    product_code: str
    product_name: str | None
    product_type_id: int
    profile_id: int
    packaging_rule: PackagingRule
    mixed_box_allowed: bool
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Box:
    id: int | None
    code: str
    name: str
    inner_length_cm: float
    inner_width_cm: float
    inner_height_cm: float
    outer_length_cm: float
    outer_width_cm: float
    outer_height_cm: float
    empty_weight_kg: float
    max_gross_weight_kg: float
    active: bool = True

    @property
    def inner_volume_cm3(self) -> float:
        return self.inner_length_cm * self.inner_width_cm * self.inner_height_cm

    @property
    def outer_volume_cm3(self) -> float:
        return self.outer_length_cm * self.outer_width_cm * self.outer_height_cm


@dataclass(frozen=True)
class Vehicle:
    id: int | None
    code: str
    name: str
    inner_length_cm: float
    inner_width_cm: float
    inner_height_cm: float
    max_load_weight_kg: float
    active: bool = True

    @property
    def volume_cm3(self) -> float:
        return self.inner_length_cm * self.inner_width_cm * self.inner_height_cm

    @property
    def volume_m3(self) -> float:
        return self.volume_cm3 / 1_000_000


@dataclass(frozen=True)
class Order:
    id: int | None
    order_number: str | None
    customer_name: str | None
    shipment_date: date | None
    source_type: str
    source_file: str | None
    status: str


@dataclass(frozen=True)
class OrderItem:
    id: int | None
    order_id: int
    product_code: str
    product_name: str | None
    product_type_id: int | None
    profile_id: int | None
    quantity: float
    unit: str | None
    roll_length_cm: float | None
    roll_weight_kg: float | None
    packaging_rule: PackagingRule
    mixed_box_allowed: bool
    source_row: int | None = None


@dataclass(frozen=True)
class ValidationMessage:
    severity: str
    code: str
    message: str
    related_entity: str | None = None


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: list[ValidationMessage]
    warnings: list[ValidationMessage]


@dataclass(frozen=True)
class PackingPlanSummary:
    confidence_level: ConfidenceLevel
    total_product_quantity: float
    total_box_count: int
    total_weight_kg: float
    average_box_fullness: float
    vehicle_count: int
    vehicle_volume_utilization: float
    vehicle_weight_utilization: float
    is_valid: bool

