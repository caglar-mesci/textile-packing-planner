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

from app.domain.models import Box


class BoxesScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.boxes: list[Box] = []
        self.selected_box_id: int | None = None
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Kutular")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Kutu ölçülerini ve ağırlık limitlerini buradan ekleyip güncelleyebilirsiniz.")
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

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels(
            ["Kod", "Ad", "İç Ölçü", "Dış Ölçü", "İç Hacim", "Dış Hacim", "Boş Ağırlık", "Azami Brüt", "Durum"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._load_selected_box)
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
        self.inner_length_input = self._number_input()
        self.inner_width_input = self._number_input()
        self.inner_height_input = self._number_input()
        self.outer_length_input = self._number_input()
        self.outer_width_input = self._number_input()
        self.outer_height_input = self._number_input()
        self.empty_weight_input = self._number_input(decimals=3, maximum=10_000)
        self.max_weight_input = self._number_input(decimals=3, maximum=100_000)
        self.active_input = QCheckBox("Aktif")
        self.active_input.setChecked(True)

        fields = [
            ("Kod", self.code_input),
            ("Ad", self.name_input),
            ("İç Uzunluk (cm)", self.inner_length_input),
            ("İç Genişlik (cm)", self.inner_width_input),
            ("İç Yükseklik (cm)", self.inner_height_input),
            ("Dış Uzunluk (cm)", self.outer_length_input),
            ("Dış Genişlik (cm)", self.outer_width_input),
            ("Dış Yükseklik (cm)", self.outer_height_input),
            ("Boş Ağırlık (kg)", self.empty_weight_input),
            ("Azami Brüt (kg)", self.max_weight_input),
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

    def set_boxes(self, boxes: list[Box]) -> None:
        self.boxes = boxes
        self.table.setRowCount(0)
        for box in boxes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                box.code,
                box.name,
                f"{box.inner_length_cm:g} x {box.inner_width_cm:g} x {box.inner_height_cm:g} cm",
                f"{box.outer_length_cm:g} x {box.outer_width_cm:g} x {box.outer_height_cm:g} cm",
                f"{box.inner_volume_cm3 / 1_000_000:.3f} m³",
                f"{box.outer_volume_cm3 / 1_000_000:.3f} m³",
                f"{box.empty_weight_kg:g} kg",
                f"{box.max_gross_weight_kg:g} kg",
                "Aktif" if box.active else "Pasif",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, box.id)
                item.setTextAlignment(Qt.AlignCenter if column >= 2 else Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)

    def clear_form(self) -> None:
        self.selected_box_id = None
        for widget in [
            self.code_input,
            self.name_input,
        ]:
            widget.clear()
        for widget in [
            self.inner_length_input,
            self.inner_width_input,
            self.inner_height_input,
            self.outer_length_input,
            self.outer_width_input,
            self.outer_height_input,
            self.empty_weight_input,
            self.max_weight_input,
        ]:
            widget.setValue(0)
        self.active_input.setChecked(True)

    def _load_selected_box(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        box_id = selected_items[0].data(Qt.UserRole)
        box = next((item for item in self.boxes if item.id == box_id), None)
        if box is None:
            return
        self.selected_box_id = box.id
        self.code_input.setText(box.code)
        self.name_input.setText(box.name)
        self.inner_length_input.setValue(box.inner_length_cm)
        self.inner_width_input.setValue(box.inner_width_cm)
        self.inner_height_input.setValue(box.inner_height_cm)
        self.outer_length_input.setValue(box.outer_length_cm)
        self.outer_width_input.setValue(box.outer_width_cm)
        self.outer_height_input.setValue(box.outer_height_cm)
        self.empty_weight_input.setValue(box.empty_weight_kg)
        self.max_weight_input.setValue(box.max_gross_weight_kg)
        self.active_input.setChecked(box.active)

    def _emit_save(self) -> None:
        if not self.code_input.text().strip() or not self.name_input.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Kod ve ad alanları zorunludur.")
            return
        if self.max_weight_input.value() <= self.empty_weight_input.value():
            QMessageBox.warning(self, "Ağırlık Hatalı", "Azami brüt ağırlık boş ağırlıktan büyük olmalıdır.")
            return
        box = Box(
            id=self.selected_box_id,
            code=self.code_input.text().strip(),
            name=self.name_input.text().strip(),
            inner_length_cm=self.inner_length_input.value(),
            inner_width_cm=self.inner_width_input.value(),
            inner_height_cm=self.inner_height_input.value(),
            outer_length_cm=self.outer_length_input.value(),
            outer_width_cm=self.outer_width_input.value(),
            outer_height_cm=self.outer_height_input.value(),
            empty_weight_kg=self.empty_weight_input.value(),
            max_gross_weight_kg=self.max_weight_input.value(),
            active=self.active_input.isChecked(),
        )
        self.save_requested.emit(box)

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

