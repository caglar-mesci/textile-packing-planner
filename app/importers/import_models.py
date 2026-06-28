from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ImportErrorMessage:
    row_number: int | None
    message: str


@dataclass(frozen=True)
class InvalidImportRow:
    row_number: int
    product_code: str | None
    product_name: str | None
    product_type: str | None
    quantity: object
    roll_length_cm: float | None
    roll_weight_kg: float | None
    messages: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ImportedOrderLine:
    product_code: str
    product_name: str | None
    product_type: str | None
    quantity: int
    roll_length_cm: float | None = None
    roll_weight_kg: float | None = None
    source_row: int | None = None

    def to_preview_dict(self) -> dict[str, object]:
        return {
            "product_code": self.product_code,
            "product_name": self.product_name,
            "product_type": self.product_type,
            "quantity": self.quantity,
            "roll_length_cm": self.roll_length_cm,
            "roll_weight_kg": self.roll_weight_kg,
            "source_row": self.source_row,
        }


@dataclass(frozen=True)
class ImportPreview:
    file_path: Path
    sheet_name: str
    lines: list[ImportedOrderLine] = field(default_factory=list)
    errors: list[ImportErrorMessage] = field(default_factory=list)
    column_mapping: dict[str, str] = field(default_factory=dict)
    invalid_rows: list[InvalidImportRow] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors and bool(self.lines)

    @property
    def total_quantity(self) -> int:
        return sum(line.quantity for line in self.lines)

    @property
    def unique_product_count(self) -> int:
        return len({line.product_code for line in self.lines})
