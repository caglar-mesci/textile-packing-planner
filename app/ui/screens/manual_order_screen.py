from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


PRODUCT_TYPES = [
    "T-Shirt",
    "Shirt",
    "Pants",
    "Sweatshirt",
    "Jacket",
    "Other Garment",
    "Fabric Roll",
]


class ManualOrderScreen(QWidget):
    back_requested = Signal()
    preview_requested = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Manuel Sipariş Girişi")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Ürünleri ekleyin, miktarları kontrol edin ve ön izlemeye geçin.")
        subtitle.setObjectName("screenSubtitle")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        back_button = QPushButton("Geri")
        back_button.setObjectName("secondaryAction")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        header.addLayout(title_block, 1)
        header.addWidget(back_button, 0, Qt.AlignTop)
        root.addLayout(header)

        form = self._build_entry_form()
        root.addWidget(form)

        table_label = QLabel("Sipariş Satırları")
        table_label.setObjectName("sectionTitle")
        root.addWidget(table_label)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "Ürün Kodu",
                "Ürün Adı",
                "Ürün Tipi",
                "Miktar",
                "Rulo Uzunluğu (cm)",
                "Rulo Ağırlığı (kg)",
                "Durum",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.summary_label = QLabel("Henüz ürün eklenmedi.")
        self.summary_label.setObjectName("summaryLabel")

        clear_button = QPushButton("Listeyi Temizle")
        clear_button.setObjectName("secondaryAction")
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.clear_lines)

        remove_button = QPushButton("Seçili Satırı Sil")
        remove_button.setObjectName("secondaryAction")
        remove_button.setCursor(Qt.PointingHandCursor)
        remove_button.clicked.connect(self.remove_selected_line)

        preview_button = QPushButton("Ön İzlemeye Geç")
        preview_button.setObjectName("primaryAction")
        preview_button.setCursor(Qt.PointingHandCursor)
        preview_button.clicked.connect(self.emit_preview)

        footer.addWidget(self.summary_label, 1)
        footer.addWidget(remove_button)
        footer.addWidget(clear_button)
        footer.addWidget(preview_button)
        root.addLayout(footer)

    def _build_entry_form(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("entryForm")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        first_row = QHBoxLayout()
        self.product_code_input = QLineEdit()
        self.product_code_input.setPlaceholderText("Ürün kodu")
        self.product_name_input = QLineEdit()
        self.product_name_input.setPlaceholderText("Ürün adı (isteğe bağlı)")
        self.product_type_input = QComboBox()
        self.product_type_input.addItems(PRODUCT_TYPES)
        self.product_type_input.currentTextChanged.connect(self.update_roll_fields)

        first_row.addWidget(self._labeled_widget("Ürün Kodu", self.product_code_input), 2)
        first_row.addWidget(self._labeled_widget("Ürün Adı", self.product_name_input), 2)
        first_row.addWidget(self._labeled_widget("Ürün Tipi", self.product_type_input), 1)
        layout.addLayout(first_row)

        second_row = QHBoxLayout()
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 1_000_000)
        self.quantity_input.setValue(1)

        self.roll_length_input = QDoubleSpinBox()
        self.roll_length_input.setRange(0, 1_000_000)
        self.roll_length_input.setDecimals(2)
        self.roll_length_input.setSuffix(" cm")

        self.roll_weight_input = QDoubleSpinBox()
        self.roll_weight_input.setRange(0, 100_000)
        self.roll_weight_input.setDecimals(3)
        self.roll_weight_input.setSuffix(" kg")

        add_button = QPushButton("Satır Ekle")
        add_button.setObjectName("primaryAction")
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.clicked.connect(self.add_line)

        second_row.addWidget(self._labeled_widget("Miktar / Rulo Adedi", self.quantity_input), 1)
        second_row.addWidget(self._labeled_widget("Rulo Uzunluğu", self.roll_length_input), 1)
        second_row.addWidget(self._labeled_widget("Birim Rulo Ağırlığı", self.roll_weight_input), 1)
        second_row.addWidget(add_button, 0, Qt.AlignBottom)
        layout.addLayout(second_row)

        self.update_roll_fields()
        return frame

    def _labeled_widget(self, label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        layout.addWidget(widget)
        return container

    def update_roll_fields(self) -> None:
        is_fabric_roll = self.product_type_input.currentText() == "Fabric Roll"
        self.roll_length_input.setEnabled(is_fabric_roll)
        self.roll_weight_input.setEnabled(is_fabric_roll)
        if not is_fabric_roll:
            self.roll_length_input.setValue(0)
            self.roll_weight_input.setValue(0)

    def add_line(self) -> None:
        product_code = self.product_code_input.text().strip()
        product_type = self.product_type_input.currentText()
        quantity = self.quantity_input.value()
        roll_length = self.roll_length_input.value()
        roll_weight = self.roll_weight_input.value()

        if not product_code:
            QMessageBox.warning(self, "Eksik Bilgi", "Ürün kodu zorunludur.")
            return

        if product_type == "Fabric Roll" and (roll_length <= 0 or roll_weight <= 0):
            QMessageBox.warning(
                self,
                "Eksik Rulo Bilgisi",
                "Kumaş rulosu için rulo uzunluğu ve birim rulo ağırlığı girilmelidir.",
            )
            return

        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [
            product_code,
            self.product_name_input.text().strip(),
            product_type,
            str(quantity),
            f"{roll_length:.2f}" if product_type == "Fabric Roll" else "-",
            f"{roll_weight:.3f}" if product_type == "Fabric Roll" else "-",
            "Hazır",
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignCenter if column >= 3 else Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, column, item)

        self.product_code_input.clear()
        self.product_name_input.clear()
        self.quantity_input.setValue(1)
        self.update_summary()

    def remove_selected_line(self) -> None:
        selected_rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        if not selected_rows:
            QMessageBox.information(self, "Satır Seçilmedi", "Silmek için bir satır seçin.")
            return
        for row in selected_rows:
            self.table.removeRow(row)
        self.update_summary()

    def clear_lines(self) -> None:
        if self.table.rowCount() == 0:
            return
        answer = QMessageBox.question(
            self,
            "Listeyi Temizle",
            "Tüm sipariş satırları silinsin mi?",
        )
        if answer == QMessageBox.Yes:
            self.table.setRowCount(0)
            self.update_summary()

    def emit_preview(self) -> None:
        lines = self.collect_lines()
        if not lines:
            QMessageBox.information(self, "Sipariş Boş", "Ön izleme için en az bir ürün ekleyin.")
            return
        self.preview_requested.emit(lines)

    def collect_lines(self) -> list[dict[str, object]]:
        lines: list[dict[str, object]] = []
        for row in range(self.table.rowCount()):
            product_type = self.table.item(row, 2).text()
            lines.append(
                {
                    "product_code": self.table.item(row, 0).text(),
                    "product_name": self.table.item(row, 1).text() or None,
                    "product_type": product_type,
                    "quantity": int(self.table.item(row, 3).text()),
                    "roll_length_cm": self._optional_float(row, 4),
                    "roll_weight_kg": self._optional_float(row, 5),
                }
            )
        return lines

    def _optional_float(self, row: int, column: int) -> float | None:
        value = self.table.item(row, column).text()
        if value == "-":
            return None
        return float(value)

    def update_summary(self) -> None:
        row_count = self.table.rowCount()
        total_quantity = 0
        for row in range(row_count):
            total_quantity += int(self.table.item(row, 3).text())

        if row_count == 0:
            self.summary_label.setText("Henüz ürün eklenmedi.")
        else:
            self.summary_label.setText(f"{row_count} satır, toplam {total_quantity} adet/rulo")

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle {
                font-size: 30px;
                font-weight: 700;
                color: #172033;
            }
            #screenSubtitle, #summaryLabel {
                font-size: 15px;
                color: #526174;
            }
            #sectionTitle {
                font-size: 18px;
                font-weight: 700;
                color: #172033;
            }
            #entryForm {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            #fieldLabel {
                font-size: 13px;
                font-weight: 600;
                color: #334155;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 14px;
                padding: 8px;
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
            QPushButton#primaryAction:hover {
                background: #1457a8;
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

