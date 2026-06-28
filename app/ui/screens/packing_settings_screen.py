from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.domain.models import Vehicle
from app.services.application_settings_service import ApplicationSettings
from app.services.packing_service import PackingSettings


class PackingSettingsScreen(QWidget):
    back_requested = Signal()
    continue_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.vehicles: list[Vehicle] = []
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        title = QLabel("Paketleme Ayarları")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Hesaplamadan önce araç seçimi ve operasyon tercihlerini kontrol edin.")
        subtitle.setObjectName("screenSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        settings_frame = QFrame()
        settings_frame.setObjectName("settingsFrame")
        settings_layout = QGridLayout(settings_frame)
        settings_layout.setContentsMargins(18, 16, 18, 18)
        settings_layout.setHorizontalSpacing(18)
        settings_layout.setVerticalSpacing(14)

        vehicle_title = QLabel("Araç Seçimi")
        vehicle_title.setObjectName("sectionTitle")
        settings_layout.addWidget(vehicle_title, 0, 0, 1, 2)

        self.auto_vehicle_radio = QRadioButton("En uygun aracı otomatik seç")
        self.manual_vehicle_radio = QRadioButton("Belirli bir araç tipi kullan")
        self.auto_vehicle_radio.setChecked(True)
        self.vehicle_group = QButtonGroup(self)
        self.vehicle_group.addButton(self.auto_vehicle_radio)
        self.vehicle_group.addButton(self.manual_vehicle_radio)

        self.vehicle_combo = QComboBox()
        self.vehicle_combo.setEnabled(False)
        self.manual_vehicle_radio.toggled.connect(self.vehicle_combo.setEnabled)

        settings_layout.addWidget(self.auto_vehicle_radio, 1, 0)
        settings_layout.addWidget(self.manual_vehicle_radio, 2, 0)
        settings_layout.addWidget(self.vehicle_combo, 2, 1)

        packing_title = QLabel("Operasyon Tercihleri")
        packing_title.setObjectName("sectionTitle")
        settings_layout.addWidget(packing_title, 3, 0, 1, 2)

        self.mixed_boxes_combo = QComboBox()
        self.mixed_boxes_combo.addItems(["Şirket varsayılanı", "Evet", "Hayır"])
        self.packaging_mode_combo = QComboBox()
        self.packaging_mode_combo.addItems(["Otomatik", "Sadece kutulu plan", "Rulo için direkt yüklemeye izin ver"])

        settings_layout.addWidget(QLabel("Karma kutu kullanımı"), 4, 0)
        settings_layout.addWidget(self.mixed_boxes_combo, 4, 1)
        settings_layout.addWidget(QLabel("Paketleme tercihi"), 5, 0)
        settings_layout.addWidget(self.packaging_mode_combo, 5, 1)

        self.allow_partial_boxes_input = QCheckBox("Son kutu yarım dolu olabilir")
        self.allow_partial_boxes_input.setChecked(True)
        self.prefer_small_final_box_input = QCheckBox("Son kutuda mümkünse küçük kutu tercih et")
        self.prefer_small_final_box_input.setChecked(True)
        self.merge_duplicate_lines_input = QCheckBox("Aynı ürün satırlarını hesaplamada birleştir")
        self.merge_duplicate_lines_input.setChecked(True)
        self.allow_direct_load_fabric_rolls_input = QCheckBox("Kumaş rulosunda direkt yükleme opsiyonunu açık tut")

        settings_layout.addWidget(self.allow_partial_boxes_input, 6, 0, 1, 2)
        settings_layout.addWidget(self.prefer_small_final_box_input, 7, 0, 1, 2)
        settings_layout.addWidget(self.merge_duplicate_lines_input, 8, 0, 1, 2)
        settings_layout.addWidget(self.allow_direct_load_fabric_rolls_input, 9, 0, 1, 2)

        root.addWidget(settings_frame)
        root.addStretch(1)

        action_row = QHBoxLayout()
        back_button = QPushButton("Ön İzlemeye Dön")
        back_button.setObjectName("secondaryAction")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        continue_button = QPushButton("Hesaplamayı Başlat")
        continue_button.setObjectName("primaryAction")
        continue_button.setCursor(Qt.PointingHandCursor)
        continue_button.clicked.connect(self._emit_continue)
        action_row.addWidget(back_button)
        action_row.addStretch(1)
        action_row.addWidget(continue_button)
        root.addLayout(action_row)

    def set_vehicles(self, vehicles: list[Vehicle]) -> None:
        self.vehicles = vehicles
        self.vehicle_combo.clear()
        for vehicle in vehicles:
            self.vehicle_combo.addItem(
                f"{vehicle.code} - {vehicle.name} ({vehicle.volume_m3:.2f} m³ / {vehicle.max_load_weight_kg:g} kg)",
                vehicle.code,
            )
        self.manual_vehicle_radio.setEnabled(bool(vehicles))
        self.vehicle_combo.setEnabled(self.manual_vehicle_radio.isChecked() and bool(vehicles))

    def set_application_defaults(self, settings: ApplicationSettings) -> None:
        self.allow_partial_boxes_input.setChecked(settings.default_allow_partial_boxes)
        self.prefer_small_final_box_input.setChecked(settings.default_prefer_small_final_box)
        self.merge_duplicate_lines_input.setChecked(settings.default_merge_duplicate_lines)
        self.allow_direct_load_fabric_rolls_input.setChecked(settings.default_allow_direct_load_fabric_rolls)
        if settings.default_allow_direct_load_fabric_rolls:
            self.packaging_mode_combo.setCurrentIndex(2)
        else:
            self.packaging_mode_combo.setCurrentIndex(0)

    def current_settings(self) -> PackingSettings:
        selected_vehicle_code = None
        if self.manual_vehicle_radio.isChecked() and self.vehicle_combo.currentIndex() >= 0:
            selected_vehicle_code = str(self.vehicle_combo.currentData())

        return PackingSettings(
            allow_mixed_boxes=self._mixed_boxes_value(),
            packaging_mode=self._packaging_mode_value(),
            selected_vehicle_code=selected_vehicle_code,
            allow_partial_boxes=self.allow_partial_boxes_input.isChecked(),
            prefer_small_final_box=self.prefer_small_final_box_input.isChecked(),
            merge_duplicate_lines=self.merge_duplicate_lines_input.isChecked(),
            allow_direct_load_fabric_rolls=self.allow_direct_load_fabric_rolls_input.isChecked(),
        )

    def _mixed_boxes_value(self) -> bool | None:
        index = self.mixed_boxes_combo.currentIndex()
        if index == 1:
            return True
        if index == 2:
            return False
        return None

    def _packaging_mode_value(self) -> str:
        return ["automatic", "boxed_only", "direct_load_allowed"][self.packaging_mode_combo.currentIndex()]

    def _emit_continue(self) -> None:
        self.continue_requested.emit(self.current_settings())

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle { font-size: 30px; font-weight: 700; color: #172033; }
            #screenSubtitle { font-size: 15px; color: #526174; }
            #sectionTitle { font-size: 16px; font-weight: 700; color: #172033; }
            #settingsFrame {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            QComboBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 14px;
                padding: 8px;
            }
            QRadioButton, QCheckBox, QLabel {
                font-size: 14px;
                color: #334155;
            }
            QPushButton#primaryAction {
                background: #1769c2;
                border: 0;
                border-radius: 6px;
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
                padding: 11px 18px;
            }
            QPushButton#secondaryAction {
                background: #e8eef6;
                border: 0;
                border-radius: 6px;
                color: #172033;
                font-size: 15px;
                padding: 11px 18px;
            }
            """
        )
