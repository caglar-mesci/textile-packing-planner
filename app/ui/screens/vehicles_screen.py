from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.domain.models import Vehicle


class VehiclesScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.vehicles: list[Vehicle] = []
        self.selected_vehicle_id: int | None = None
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Araçlar")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Araç kapasite bilgilerini buradan ekleyip güncelleyebilirsiniz.")
        subtitle.setObjectName("screenSubtitle")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        back_button = QPushButton("Yeni Plana Dön")
        back_button.setObjectName("secondaryAction")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        header.addLayout(title_block, 1)
        header.addWidget(back_button, 0, Qt.AlignTop)
        root.addLayout(header)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Kod", "Ad", "Uzunluk", "Genişlik", "Yükseklik", "Hacim", "Azami Yük"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._load_selected_vehicle)
        root.addWidget(self.table, 1)
        root.addWidget(self._build_form())

    def _build_form(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editForm")
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.length_input = self._number_input()
        self.width_input = self._number_input()
        self.height_input = self._number_input()
        self.max_weight_input = self._number_input(decimals=2, maximum=1_000_000)
        self.active_input = QCheckBox("Aktif")
        self.active_input.setChecked(True)

        fields = [
            ("Kod", self.code_input),
            ("Ad", self.name_input),
            ("İç Uzunluk (cm)", self.length_input),
            ("İç Genişlik (cm)", self.width_input),
            ("İç Yükseklik (cm)", self.height_input),
            ("Azami Yük (kg)", self.max_weight_input),
        ]
        for index, (label_text, widget) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            layout.addWidget(label, 0, index)
            layout.addWidget(widget, 1, index)

        button_row = QHBoxLayout()
        new_button = QPushButton("Yeni")
        new_button.setObjectName("secondaryAction")
        new_button.clicked.connect(self.clear_form)
        save_button = QPushButton("Kaydet")
        save_button.setObjectName("primaryAction")
        save_button.clicked.connect(self._emit_save)
        button_row.addWidget(self.active_input)
        button_row.addStretch(1)
        button_row.addWidget(new_button)
        button_row.addWidget(save_button)
        layout.addLayout(button_row, 2, 0, 1, 6)
        return frame

    def _number_input(self, decimals: int = 2, maximum: float = 1_000_000) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(0, maximum)
        box.setDecimals(decimals)
        return box

    def set_vehicles(self, vehicles: list[Vehicle]) -> None:
        self.vehicles = vehicles
        self.table.setRowCount(0)
        for vehicle in vehicles:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                vehicle.code,
                vehicle.name,
                f"{vehicle.inner_length_cm:g} cm",
                f"{vehicle.inner_width_cm:g} cm",
                f"{vehicle.inner_height_cm:g} cm",
                f"{vehicle.volume_m3:.2f} m³",
                f"{vehicle.max_load_weight_kg:g} kg",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, vehicle.id)
                item.setTextAlignment(Qt.AlignCenter if column >= 2 else Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)

    def clear_form(self) -> None:
        self.selected_vehicle_id = None
        self.code_input.clear()
        self.name_input.clear()
        self.length_input.setValue(0)
        self.width_input.setValue(0)
        self.height_input.setValue(0)
        self.max_weight_input.setValue(0)
        self.active_input.setChecked(True)

    def _load_selected_vehicle(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        vehicle_id = selected_items[0].data(Qt.UserRole)
        vehicle = next((item for item in self.vehicles if item.id == vehicle_id), None)
        if vehicle is None:
            return
        self.selected_vehicle_id = vehicle.id
        self.code_input.setText(vehicle.code)
        self.name_input.setText(vehicle.name)
        self.length_input.setValue(vehicle.inner_length_cm)
        self.width_input.setValue(vehicle.inner_width_cm)
        self.height_input.setValue(vehicle.inner_height_cm)
        self.max_weight_input.setValue(vehicle.max_load_weight_kg)
        self.active_input.setChecked(vehicle.active)

    def _emit_save(self) -> None:
        if not self.code_input.text().strip() or not self.name_input.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Kod ve ad alanları zorunludur.")
            return
        vehicle = Vehicle(
            id=self.selected_vehicle_id,
            code=self.code_input.text().strip(),
            name=self.name_input.text().strip(),
            inner_length_cm=self.length_input.value(),
            inner_width_cm=self.width_input.value(),
            inner_height_cm=self.height_input.value(),
            max_load_weight_kg=self.max_weight_input.value(),
            active=self.active_input.isChecked(),
        )
        self.save_requested.emit(vehicle)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle { font-size: 30px; font-weight: 700; color: #172033; }
            #screenSubtitle { font-size: 15px; color: #526174; }
            #editForm {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            #fieldLabel { font-size: 13px; font-weight: 600; color: #334155; }
            QLineEdit, QDoubleSpinBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 13px;
                padding: 7px;
            }
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
                gridline-color: #e2e8f0;
                font-size: 13px;
            }
            QHeaderView::section {
                background: #eef5ff;
                border: 0;
                border-right: 1px solid #d5e3f5;
                color: #172033;
                font-weight: 700;
                padding: 8px;
            }
            QPushButton#primaryAction {
                background: #1769c2;
                border: 0;
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 16px;
            }
            QPushButton#secondaryAction {
                background: #e8eef6;
                border: 0;
                border-radius: 6px;
                color: #172033;
                font-size: 14px;
                padding: 10px 14px;
            }
            """
        )

