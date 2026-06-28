import sqlite3
from dataclasses import dataclass, field

from app.algorithms.fabric_roll_packing import FabricRollProfile, choose_best_fabric_roll_box
from app.algorithms.garment_packing import GarmentProfileDimensions, choose_best_box
from app.algorithms.vehicle_selector import VehicleSelection, select_vehicle
from app.domain.models import ValidationMessage, ValidationResult
from app.domain.models import Box, Vehicle
from app.repositories.database import Database


@dataclass(frozen=True)
class PackingSettings:
    allow_mixed_boxes: bool | None = None
    packaging_mode: str = "automatic"
    selected_vehicle_code: str | None = None
    allow_partial_boxes: bool = True
    prefer_small_final_box: bool = True
    merge_duplicate_lines: bool = True
    allow_direct_load_fabric_rolls: bool = False


@dataclass(frozen=True)
class PackedLine:
    product_code: str
    product_name: str | None
    product_type: str | None
    quantity: int
    box_code: str | None
    box_name: str | None
    box_count: int
    average_fullness_percent: float
    estimated_weight_kg: float
    shipment_volume_cm3: float
    status_text: str


@dataclass(frozen=True)
class PackingCalculationResult:
    packed_lines: list[PackedLine] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    vehicle_selection: VehicleSelection | None = None
    validation_result: ValidationResult | None = None
    settings: PackingSettings = field(default_factory=PackingSettings)

    @property
    def total_quantity(self) -> int:
        return sum(line.quantity for line in self.packed_lines)

    @property
    def total_box_count(self) -> int:
        return sum(line.box_count for line in self.packed_lines)

    @property
    def estimated_total_weight_kg(self) -> float:
        return sum(line.estimated_weight_kg for line in self.packed_lines)

    @property
    def shipment_volume_cm3(self) -> float:
        return sum(line.shipment_volume_cm3 for line in self.packed_lines)

    @property
    def average_fullness_percent(self) -> float:
        boxed_lines = [line for line in self.packed_lines if line.box_count > 0]
        if not boxed_lines:
            return 0
        total_boxes = sum(line.box_count for line in boxed_lines)
        weighted_fullness = sum(line.average_fullness_percent * line.box_count for line in boxed_lines)
        return weighted_fullness / total_boxes


class PackingService:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()

    def calculate(
        self,
        lines: list[dict[str, object]],
        settings: PackingSettings | None = None,
    ) -> PackingCalculationResult:
        settings = settings or PackingSettings()
        packed_lines: list[PackedLine] = []
        warnings: list[str] = []
        calculation_lines = self._prepare_lines(lines, settings)

        # Packing is calculated per product line first; vehicle validation runs after
        # all box volumes and estimated weights are known.
        with self.database.connect() as connection:
            boxes = self._load_active_boxes(connection)
            vehicles = self._load_active_vehicles(connection)
            for line in calculation_lines:
                packed_line, line_warnings = self._pack_line(connection, boxes, line, settings)
                packed_lines.append(packed_line)
                warnings.extend(line_warnings)

        selected_vehicles = self._filter_vehicles_for_settings(vehicles, settings, warnings)
        vehicle_selection = select_vehicle(
            selected_vehicles,
            shipment_volume_cm3=sum(line.shipment_volume_cm3 for line in packed_lines),
            shipment_weight_kg=sum(line.estimated_weight_kg for line in packed_lines),
        )
        if vehicle_selection is None:
            if settings.selected_vehicle_code:
                warnings.append(f"Seçilen araç bu sipariş için uygun değil: {settings.selected_vehicle_code}")
            else:
                warnings.append("Aktif araç bulunamadı.")

        validation_result = self._validate_result(packed_lines, warnings, vehicle_selection, settings)

        return PackingCalculationResult(
            packed_lines=packed_lines,
            warnings=warnings,
            vehicle_selection=vehicle_selection,
            validation_result=validation_result,
            settings=settings,
        )

    def _prepare_lines(
        self,
        lines: list[dict[str, object]],
        settings: PackingSettings,
    ) -> list[dict[str, object]]:
        if not settings.merge_duplicate_lines:
            return lines

        # Merge only lines that share the same packing-relevant attributes.
        # Roll dimensions are part of the key because they change box fit.
        merged_lines: dict[tuple[object, ...], dict[str, object]] = {}
        ordered_keys: list[tuple[object, ...]] = []
        for line in lines:
            key = (
                line.get("product_code") or "",
                line.get("product_type") or "",
                line.get("profile_id") or "",
                line.get("roll_length_cm") or "",
                line.get("roll_weight_kg") or "",
            )
            if key not in merged_lines:
                merged_lines[key] = dict(line)
                ordered_keys.append(key)
                continue
            merged_lines[key]["quantity"] = int(merged_lines[key].get("quantity") or 0) + int(line.get("quantity") or 0)

        return [merged_lines[key] for key in ordered_keys]

    def _filter_vehicles_for_settings(
        self,
        vehicles: list[Vehicle],
        settings: PackingSettings,
        warnings: list[str],
    ) -> list[Vehicle]:
        if not settings.selected_vehicle_code:
            return vehicles

        selected = [vehicle for vehicle in vehicles if vehicle.code == settings.selected_vehicle_code]
        if selected:
            return selected

        warnings.append(f"Seçilen araç bulunamadı: {settings.selected_vehicle_code}")
        return []

    def _validate_result(
        self,
        packed_lines: list[PackedLine],
        warnings: list[str],
        vehicle_selection: VehicleSelection | None,
        settings: PackingSettings,
    ) -> ValidationResult:
        errors: list[ValidationMessage] = []
        validation_warnings = [
            ValidationMessage("warning", "ASSUMPTION", warning)
            for warning in warnings
        ]

        if not packed_lines:
            errors.append(ValidationMessage("error", "EMPTY_PLAN", "Paketleme planında ürün bulunmuyor."))

        for line in packed_lines:
            if line.quantity <= 0:
                errors.append(
                    ValidationMessage("error", "INVALID_QUANTITY", f"{line.product_code}: Miktar pozitif olmalıdır.")
                )
            if line.box_count == 0 and line.box_code != "DIREKT":
                errors.append(
                    ValidationMessage(
                        "error",
                        "UNPACKED_LINE",
                        self._unpacked_line_message(line, settings),
                    )
                )

        if vehicle_selection is None:
            if settings.selected_vehicle_code:
                errors.append(
                    ValidationMessage(
                        "error",
                        "SELECTED_VEHICLE_NOT_AVAILABLE",
                        f"Seçilen araç bu sipariş için uygun değil: {settings.selected_vehicle_code}. "
                        "Daha büyük bir araç seçin veya otomatik araç seçimine dönün.",
                    )
                )
            else:
                errors.append(ValidationMessage("error", "NO_VEHICLE", "Uygun aktif araç bulunamadı."))

        if settings.selected_vehicle_code and vehicle_selection is not None and vehicle_selection.vehicle_count > 1:
            errors.append(
                ValidationMessage(
                    "error",
                    "SELECTED_VEHICLE_TOO_SMALL",
                    f"Seçilen araç ({vehicle_selection.vehicle.code}) bu sipariş için küçük kalıyor. "
                    f"Bu yük için aynı araçtan {vehicle_selection.vehicle_count} adet gerekir. "
                    "Daha büyük bir araç seçin veya otomatik araç seçimine dönün.",
                )
            )

        return ValidationResult(is_valid=not errors, errors=errors, warnings=validation_warnings)

    def _unpacked_line_message(self, line: PackedLine, settings: PackingSettings) -> str:
        if line.status_text == "Rulo bilgisi eksik":
            return f"{line.product_code}: Rulo uzunluğu ve birim rulo ağırlığı girilmelidir."
        if line.status_text in {"Profil bulunamadı", "Rulo profili bulunamadı"}:
            return f"{line.product_code}: Ürün profili bulunamadı. Ürün/profil tanımını tamamlayın."
        if line.product_type == "Fabric Roll":
            if not self._allows_direct_load_for_fabric_rolls(settings):
                return (
                    f"{line.product_code}: Mevcut kutularla paketlenemiyor. "
                    "Rulo için direkt yüklemeyi açın veya kutu/rulo bilgisini güncelleyin."
                )
            return f"{line.product_code}: Mevcut araç ve kutu ayarlarıyla paketlenemiyor."
        return f"{line.product_code}: Mevcut kutularla paketlenemiyor. Kutu veya ürün profilini güncelleyin."

    def _pack_line(
        self,
        connection: sqlite3.Connection,
        boxes: list[Box],
        line: dict[str, object],
        settings: PackingSettings,
    ) -> tuple[PackedLine, list[str]]:
        product_type = str(line.get("product_type") or "") or None
        if product_type == "Fabric Roll":
            return self._pack_fabric_roll_line(connection, boxes, line, settings)
        return self._pack_garment_line(connection, boxes, line, settings)

    def _pack_garment_line(
        self,
        connection: sqlite3.Connection,
        boxes: list[Box],
        line: dict[str, object],
        settings: PackingSettings,
    ) -> tuple[PackedLine, list[str]]:
        product_code = str(line.get("product_code") or "")
        product_name = str(line.get("product_name") or "") or None
        product_type = str(line.get("product_type") or "") or None
        quantity = int(line.get("quantity") or 0)

        profile_row = self._find_profile(connection, line)
        if profile_row is None:
            return self._empty_line(
                product_code,
                product_name,
                product_type,
                quantity,
                "Profil bulunamadı",
                [f"{product_code}: Ürün profili bulunamadı."],
            )

        profile = GarmentProfileDimensions(
            length_cm=float(profile_row["average_length_cm"]),
            width_cm=float(profile_row["average_width_cm"]),
            height_cm=float(profile_row["average_height_cm"]),
            unit_weight_kg=float(profile_row["average_weight_kg"]),
        )
        best = choose_best_box(
            boxes,
            profile,
            quantity,
            allow_partial_boxes=settings.allow_partial_boxes,
            prefer_small_final_box=settings.prefer_small_final_box,
        )
        if best is None:
            return self._empty_line(
                product_code,
                product_name,
                product_type,
                quantity,
                "Uygun kutu yok",
                [f"{product_code}: Uygun kutu bulunamadı."],
                estimated_weight_kg=quantity * profile.unit_weight_kg,
            )

        return (
            PackedLine(
                product_code=product_code,
                product_name=product_name,
                product_type=product_type,
                quantity=quantity,
                box_code=best.box.code,
                box_name=best.box.name,
                box_count=best.box_count,
                average_fullness_percent=best.average_fullness_percent,
                estimated_weight_kg=best.estimated_total_gross_weight_kg,
                shipment_volume_cm3=best.box_count * best.box.outer_volume_cm3,
                status_text="Hazır",
            ),
            [],
        )

    def _pack_fabric_roll_line(
        self,
        connection: sqlite3.Connection,
        boxes: list[Box],
        line: dict[str, object],
        settings: PackingSettings,
    ) -> tuple[PackedLine, list[str]]:
        product_code = str(line.get("product_code") or "")
        product_name = str(line.get("product_name") or "") or None
        quantity = int(line.get("quantity") or 0)
        roll_length = float(line.get("roll_length_cm") or 0)
        roll_weight = float(line.get("roll_weight_kg") or 0)

        if roll_length <= 0 or roll_weight <= 0:
            return self._empty_line(
                product_code,
                product_name,
                "Fabric Roll",
                quantity,
                "Rulo bilgisi eksik",
                [f"{product_code}: Rulo uzunluğu ve birim rulo ağırlığı girilmelidir."],
                estimated_weight_kg=roll_weight * quantity,
            )

        profile_row = self._find_profile(connection, line)
        if profile_row is None or profile_row["average_diameter_cm"] is None:
            return self._empty_line(
                product_code,
                product_name,
                "Fabric Roll",
                quantity,
                "Rulo profili bulunamadı",
                [f"{product_code}: Kumaş rulosu için ortalama çap profili bulunamadı."],
                estimated_weight_kg=roll_weight * quantity,
            )

        profile = FabricRollProfile(
            roll_length_cm=roll_length,
            roll_weight_kg=roll_weight,
            average_diameter_cm=float(profile_row["average_diameter_cm"]),
            allowed_orientation=profile_row["allowed_orientation"],
        )
        best = choose_best_fabric_roll_box(
            boxes,
            profile,
            quantity,
            allow_partial_boxes=settings.allow_partial_boxes,
            prefer_small_final_box=settings.prefer_small_final_box,
        )
        if best is None:
            if self._allows_direct_load_for_fabric_rolls(settings):
                return self._direct_load_line(
                    product_code,
                    product_name,
                    "Fabric Roll",
                    quantity,
                    roll_weight * quantity,
                    [f"{product_code}: Uygun kutu bulunamadı; direkt yükleme olarak planlandı."],
                )
            return self._empty_line(
                product_code,
                product_name,
                "Fabric Roll",
                quantity,
                "Uygun kutu yok",
                [f"{product_code}: Rulo uzunluğu veya ağırlığı nedeniyle uygun kutu bulunamadı."],
                estimated_weight_kg=roll_weight * quantity,
            )

        return (
            PackedLine(
                product_code=product_code,
                product_name=product_name,
                product_type="Fabric Roll",
                quantity=quantity,
                box_code=best.box.code,
                box_name=best.box.name,
                box_count=best.box_count,
                average_fullness_percent=best.average_fullness_percent,
                estimated_weight_kg=best.estimated_total_gross_weight_kg,
                shipment_volume_cm3=best.box_count * best.box.outer_volume_cm3,
                status_text="Ortalama çap profiliyle hesaplandı",
            ),
            [f"{product_code}: Kumaş rulosu hesaplaması ortalama çap profiliyle tahmini yapılmıştır."],
        )

    def _allows_direct_load_for_fabric_rolls(self, settings: PackingSettings) -> bool:
        return settings.packaging_mode == "direct_load_allowed" or settings.allow_direct_load_fabric_rolls

    def _direct_load_line(
        self,
        product_code: str,
        product_name: str | None,
        product_type: str | None,
        quantity: int,
        estimated_weight_kg: float,
        warnings: list[str],
    ) -> tuple[PackedLine, list[str]]:
        return (
            PackedLine(
                product_code=product_code,
                product_name=product_name,
                product_type=product_type,
                quantity=quantity,
                box_code="DIREKT",
                box_name="Direkt yükleme",
                box_count=0,
                average_fullness_percent=0,
                estimated_weight_kg=estimated_weight_kg,
                shipment_volume_cm3=0,
                status_text="Direkt yükleme",
            ),
            warnings,
        )

    def _empty_line(
        self,
        product_code: str,
        product_name: str | None,
        product_type: str | None,
        quantity: int,
        status_text: str,
        warnings: list[str],
        estimated_weight_kg: float = 0,
    ) -> tuple[PackedLine, list[str]]:
        return (
            PackedLine(
                product_code=product_code,
                product_name=product_name,
                product_type=product_type,
                quantity=quantity,
                box_code=None,
                box_name=None,
                box_count=0,
                average_fullness_percent=0,
                estimated_weight_kg=estimated_weight_kg,
                shipment_volume_cm3=0,
                status_text=status_text,
            ),
            warnings,
        )

    def _find_profile(self, connection: sqlite3.Connection, line: dict[str, object]) -> sqlite3.Row | None:
        profile_id = line.get("profile_id")
        if profile_id:
            row = connection.execute(
                "SELECT * FROM product_profiles WHERE id = ? AND active = 1",
                (profile_id,),
            ).fetchone()
            if row is not None:
                return row

        product_type = line.get("product_type")
        if not product_type:
            return None

        return connection.execute(
            """
            SELECT product_profiles.*
            FROM product_profiles
            JOIN product_types ON product_types.id = product_profiles.product_type_id
            WHERE product_types.name = ?
              AND product_profiles.active = 1
            ORDER BY product_profiles.id ASC
            LIMIT 1
            """,
            (product_type,),
        ).fetchone()

    def _load_active_boxes(self, connection: sqlite3.Connection) -> list[Box]:
        rows = connection.execute("SELECT * FROM boxes WHERE active = 1 ORDER BY id ASC").fetchall()
        return [
            Box(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                inner_length_cm=row["inner_length_cm"],
                inner_width_cm=row["inner_width_cm"],
                inner_height_cm=row["inner_height_cm"],
                outer_length_cm=row["outer_length_cm"],
                outer_width_cm=row["outer_width_cm"],
                outer_height_cm=row["outer_height_cm"],
                empty_weight_kg=row["empty_weight_kg"],
                max_gross_weight_kg=row["max_gross_weight_kg"],
                active=bool(row["active"]),
            )
            for row in rows
        ]

    def _load_active_vehicles(self, connection: sqlite3.Connection) -> list[Vehicle]:
        rows = connection.execute("SELECT * FROM vehicles WHERE active = 1 ORDER BY id ASC").fetchall()
        return [
            Vehicle(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                inner_length_cm=row["inner_length_cm"],
                inner_width_cm=row["inner_width_cm"],
                inner_height_cm=row["inner_height_cm"],
                max_load_weight_kg=row["max_load_weight_kg"],
                active=bool(row["active"]),
            )
            for row in rows
        ]
