from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from app.repositories.profile_repository import ProfileListItem


class ProfilesScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.profiles: list[ProfileListItem] = []
        self.selected_profile_id = 0
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Ürün Profilleri")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Ortalama ölçü, ağırlık ve rulo çapı değerlerini şirket verilerine göre güncelleyin.")
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

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Profil", "Ürün Tipi", "Ortalama Ölçü", "Ağırlık", "Rulo Çapı", "Yön", "Paketleme", "Karışık Kutu"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._load_selected_profile)
        root.addWidget(self.table, 1)
        root.addWidget(self._build_form())

    def _build_form(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editForm")
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.name_input = QLineEdit()
        self.product_type_input = QComboBox()
        self.length_input = self._number_input()
        self.width_input = self._number_input()
        self.height_input = self._number_input()
        self.weight_input = self._number_input(decimals=3, maximum=10_000)
        self.diameter_input = self._number_input()
        self.orientation_input = QComboBox()
        self.orientation_input.addItems(["", "HORIZONTAL", "VERTICAL", "BOTH"])
        self.packaging_rule_input = QComboBox()
        self.packaging_rule_input.addItems(["BOXED", "DIRECT_LOAD", "PALLETIZED", "BOXED_OR_DIRECT"])
        self.mixed_box_input = QCheckBox("Karışık kutuya izin ver")
        self.active_input = QCheckBox("Aktif")
        self.active_input.setChecked(True)

        fields = [
            ("Profil Adı", self.name_input),
            ("Ürün Tipi", self.product_type_input),
            ("Uzunluk (cm)", self.length_input),
            ("Genişlik (cm)", self.width_input),
            ("Yükseklik (cm)", self.height_input),
            ("Ağırlık (kg)", self.weight_input),
            ("Rulo Çapı (cm)", self.diameter_input),
            ("Rulo Yönü", self.orientation_input),
            ("Paketleme", self.packaging_rule_input),
        ]
        for index, (label_text, widget) in enumerate(fields):
            row = index // 5 * 2
            column = index % 5
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            layout.addWidget(label, row, column)
            layout.addWidget(widget, row + 1, column)

        button_row = QHBoxLayout()
        new_button = QPushButton("Yeni")
        new_button.setObjectName("secondaryAction")
        new_button.clicked.connect(self.clear_form)
        save_button = QPushButton("Kaydet")
        save_button.setObjectName("primaryAction")
        save_button.clicked.connect(self._emit_save)
        button_row.addWidget(self.mixed_box_input)
        button_row.addWidget(self.active_input)
        button_row.addStretch(1)
        button_row.addWidget(new_button)
        button_row.addWidget(save_button)
        layout.addLayout(button_row, 4, 0, 1, 5)
        return frame

    def _number_input(self, decimals: int = 2, maximum: float = 1_000_000) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(0, maximum)
        box.setDecimals(decimals)
        return box

    def set_product_types(self, product_types: list[str]) -> None:
        current = self.product_type_input.currentText()
        self.product_type_input.clear()
        self.product_type_input.addItems(product_types)
        if current:
            index = self.product_type_input.findText(current)
            if index >= 0:
                self.product_type_input.setCurrentIndex(index)

    def set_profiles(self, profiles: list[ProfileListItem]) -> None:
        self.profiles = profiles
        self.table.setRowCount(0)
        for profile in profiles:
            row = self.table.rowCount()
            self.table.insertRow(row)
            dimensions = "-"
            if profile.average_length_cm and profile.average_width_cm and profile.average_height_cm:
                dimensions = (
                    f"{profile.average_length_cm:g} x {profile.average_width_cm:g} x "
                    f"{profile.average_height_cm:g} cm"
                )
            values = [
                profile.name,
                profile.product_type,
                dimensions,
                f"{profile.average_weight_kg:g} kg" if profile.average_weight_kg else "-",
                f"{profile.average_diameter_cm:g} cm" if profile.average_diameter_cm else "-",
                profile.allowed_orientation or "-",
                profile.default_packaging_rule,
                "Evet" if profile.default_mixed_box_allowed else "Hayır",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, profile.id)
                item.setTextAlignment(Qt.AlignCenter if column >= 2 else Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)

    def clear_form(self) -> None:
        self.selected_profile_id = 0
        self.name_input.clear()
        for widget in [self.length_input, self.width_input, self.height_input, self.weight_input, self.diameter_input]:
            widget.setValue(0)
        self.orientation_input.setCurrentIndex(0)
        self.packaging_rule_input.setCurrentText("BOXED")
        self.mixed_box_input.setChecked(False)
        self.active_input.setChecked(True)

    def _load_selected_profile(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        profile_id = selected_items[0].data(Qt.UserRole)
        profile = next((item for item in self.profiles if item.id == profile_id), None)
        if profile is None:
            return
        self.selected_profile_id = profile.id
        self.name_input.setText(profile.name)
        type_index = self.product_type_input.findText(profile.product_type)
        if type_index >= 0:
            self.product_type_input.setCurrentIndex(type_index)
        self.length_input.setValue(profile.average_length_cm or 0)
        self.width_input.setValue(profile.average_width_cm or 0)
        self.height_input.setValue(profile.average_height_cm or 0)
        self.weight_input.setValue(profile.average_weight_kg or 0)
        self.diameter_input.setValue(profile.average_diameter_cm or 0)
        self.orientation_input.setCurrentText(profile.allowed_orientation or "")
        self.packaging_rule_input.setCurrentText(profile.default_packaging_rule)
        self.mixed_box_input.setChecked(profile.default_mixed_box_allowed)
        self.active_input.setChecked(profile.active)

    def _emit_save(self) -> None:
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Profil adı zorunludur.")
            return
        profile = ProfileListItem(
            id=self.selected_profile_id,
            name=self.name_input.text().strip(),
            product_type=self.product_type_input.currentText(),
            average_length_cm=self._none_if_zero(self.length_input.value()),
            average_width_cm=self._none_if_zero(self.width_input.value()),
            average_height_cm=self._none_if_zero(self.height_input.value()),
            average_weight_kg=self._none_if_zero(self.weight_input.value()),
            average_diameter_cm=self._none_if_zero(self.diameter_input.value()),
            allowed_orientation=self.orientation_input.currentText() or None,
            default_packaging_rule=self.packaging_rule_input.currentText(),
            default_mixed_box_allowed=self.mixed_box_input.isChecked(),
            active=self.active_input.isChecked(),
        )
        self.save_requested.emit(profile)

    def _none_if_zero(self, value: float) -> float | None:
        return value if value > 0 else None

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
            QLineEdit, QDoubleSpinBox, QComboBox {
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

