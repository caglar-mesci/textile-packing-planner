from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


BLOCKING_STATUSES = {"Ürün kodu eksik", "Tip eksik", "Tip tanımsız", "Miktar hatalı", "Rulo bilgisi eksik"}
ERROR_BACKGROUND = QColor("#fff1f2")
ERROR_FOREGROUND = QColor("#b42318")
NORMAL_FOREGROUND = QColor("#172033")


class OrderPreviewScreen(QWidget):
    back_requested = Signal()
    continue_requested = Signal()
    complete_products_requested = Signal()
    order_lines_changed = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.order_lines: list[dict[str, object]] = []
        self.product_types: list[str] = []
        self.selected_line_index: int | None = None
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Sipariş Ön İzleme")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Satırları kontrol edin. Eksik bilgi varsa alttaki nottan hangi satırda kaldığını görebilirsiniz.")
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

        self.summary_grid = QGridLayout()
        self.summary_grid.setSpacing(12)
        self.total_rows_card = self._summary_card("Toplam Satır", "0")
        self.unique_products_card = self._summary_card("Farklı Ürün", "0")
        self.total_quantity_card = self._summary_card("Toplam Miktar", "0")
        self.ready_rows_card = self._summary_card("Hazır Satır", "0")
        self.summary_grid.addWidget(self.total_rows_card, 0, 0)
        self.summary_grid.addWidget(self.unique_products_card, 0, 1)
        self.summary_grid.addWidget(self.total_quantity_card, 0, 2)
        self.summary_grid.addWidget(self.ready_rows_card, 0, 3)
        root.addLayout(self.summary_grid)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Ürün Kodu", "Ürün Adı", "Tip", "Miktar", "Rulo Bilgisi", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._load_selected_line)
        root.addWidget(self.table, 1)

        root.addWidget(self._build_edit_form())

        footer = QHBoxLayout()
        self.note = QLabel("Bu aşamada ürünler ortalama profillerle hesaplanacaktır.")
        self.note.setObjectName("summaryLabel")
        self.note.setWordWrap(True)
        self.complete_button = QPushButton("Eksik Ürünleri Tamamla")
        self.complete_button.setObjectName("secondaryAction")
        self.complete_button.setCursor(Qt.PointingHandCursor)
        self.complete_button.clicked.connect(self.focus_first_problem_or_first_row)
        continue_button = QPushButton("Paketleme Ayarlarına Geç")
        continue_button.setObjectName("primaryAction")
        continue_button.setCursor(Qt.PointingHandCursor)
        continue_button.clicked.connect(self.continue_requested.emit)
        footer.addWidget(self.note, 1)
        footer.addWidget(self.complete_button)
        footer.addWidget(continue_button)
        root.addLayout(footer)

    def set_order_lines(self, lines: list[dict[str, object]]) -> None:
        self.order_lines = lines
        self.selected_line_index = None
        self.table.setRowCount(0)
        for line in lines:
            self._append_line(line)
        self._update_summary()
        self._apply_edit_field_styles(None)

    def set_product_types(self, product_types: list[str]) -> None:
        current = self.type_input.currentText() if hasattr(self, "type_input") else ""
        self.product_types = product_types
        self.type_input.clear()
        self.type_input.addItem("")
        self.type_input.addItems(product_types)
        if current and (index := self.type_input.findText(current)) >= 0:
            self.type_input.setCurrentIndex(index)

    def blocking_issue_messages(self) -> list[str]:
        messages: list[str] = []
        for index, line in enumerate(self.order_lines, start=1):
            status = self._status_for_line(line)
            if status in BLOCKING_STATUSES:
                product_code = str(line.get("product_code") or f"{index}. satır")
                if status == "Rulo bilgisi eksik":
                    messages.append(f"{product_code}: rulo uzunluğu ve rulo ağırlığı girilmeli.")
                elif status == "Tip eksik":
                    messages.append(f"{product_code}: ürün tipi/profil tamamlanmalı.")
                elif status == "Tip tanımsız":
                    messages.append(f"{product_code}: ürün tipi sistemde tanımlı değil, geçerli bir tip seçilmeli.")
                elif status == "Miktar hatalı":
                    messages.append(f"{product_code}: miktar pozitif tam sayı olmalı.")
                else:
                    messages.append(f"{product_code}: ürün kodu eksik.")
        return messages

    def has_blocking_issues(self) -> bool:
        return bool(self.blocking_issue_messages())

    def _append_line(self, line: dict[str, object]) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)

        roll_length = line.get("roll_length_cm")
        roll_weight = line.get("roll_weight_kg")
        roll_info = "-"
        if roll_length and roll_weight:
            roll_info = f"{roll_length} cm / {roll_weight} kg"

        status = self._status_for_line(line)
        values = [
            str(line.get("product_code") or ""),
            str(line.get("product_name") or ""),
            str(line.get("product_type") or ""),
            str(line.get("quantity") or 0),
            roll_info,
            status,
        ]

        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setForeground(QBrush(ERROR_FOREGROUND if status in BLOCKING_STATUSES else NORMAL_FOREGROUND))
            if self._is_missing_cell(line, column):
                item.setBackground(QBrush(ERROR_BACKGROUND))
                item.setForeground(QBrush(ERROR_FOREGROUND))
                item.setToolTip("Bu alan tamamlanmalı.")
            item.setTextAlignment(Qt.AlignCenter if column >= 3 else Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, column, item)

    def _build_edit_form(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editForm")
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(0, 1_000_000)
        self.roll_length_input = QDoubleSpinBox()
        self.roll_length_input.setRange(0, 1_000_000)
        self.roll_length_input.setDecimals(2)
        self.roll_weight_input = QDoubleSpinBox()
        self.roll_weight_input.setRange(0, 1_000_000)
        self.roll_weight_input.setDecimals(2)

        fields = [
            ("Ürün Kodu", self.code_input),
            ("Ürün Adı", self.name_input),
            ("Ürün Tipi", self.type_input),
            ("Miktar", self.quantity_input),
            ("Rulo Uzunluğu", self.roll_length_input),
            ("Rulo Ağırlığı", self.roll_weight_input),
        ]
        for column, (label_text, widget) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            layout.addWidget(label, 0, column)
            layout.addWidget(widget, 1, column)

        button_row = QHBoxLayout()
        help_label = QLabel("Eksik satırı tablodan seçip burada düzeltebilirsiniz.")
        help_label.setObjectName("summaryLabel")
        save_button = QPushButton("Satırı Güncelle")
        save_button.setObjectName("primaryAction")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self._apply_selected_line_edits)
        button_row.addWidget(help_label, 1)
        button_row.addWidget(save_button)
        layout.addLayout(button_row, 2, 0, 1, len(fields))
        return frame

    def _load_selected_line(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        if row < 0 or row >= len(self.order_lines):
            return
        self.selected_line_index = row
        line = self.order_lines[row]
        self.code_input.setText(str(line.get("product_code") or ""))
        self.name_input.setText(str(line.get("product_name") or ""))
        self.type_input.setCurrentText(str(line.get("product_type") or ""))
        self.quantity_input.setValue(int(line.get("quantity") or 0))
        self.roll_length_input.setValue(float(line.get("roll_length_cm") or 0))
        self.roll_weight_input.setValue(float(line.get("roll_weight_kg") or 0))
        self._apply_edit_field_styles(line)

    def _apply_selected_line_edits(self) -> None:
        if self.selected_line_index is None:
            QMessageBox.information(self, "Satır Seçilmedi", "Önce tablodan düzenlenecek satırı seçin.")
            return
        updated_lines = [dict(line) for line in self.order_lines]
        line = updated_lines[self.selected_line_index]
        line["product_code"] = self.code_input.text().strip()
        line["product_name"] = self.name_input.text().strip() or None
        line["product_type"] = self.type_input.currentText() or None
        line["quantity"] = self.quantity_input.value()
        line["roll_length_cm"] = self.roll_length_input.value() or None
        line["roll_weight_kg"] = self.roll_weight_input.value() or None
        self.order_lines_changed.emit(updated_lines)

    def focus_first_problem_or_first_row(self) -> None:
        if not self.order_lines:
            return
        target_row = next(
            (index for index, line in enumerate(self.order_lines) if self._status_for_line(line) in BLOCKING_STATUSES),
            0,
        )
        self.table.selectRow(target_row)
        self.table.scrollToItem(self.table.item(target_row, 0))
        line = self.order_lines[target_row]
        if not line.get("product_code"):
            self.code_input.setFocus()
        elif not line.get("product_type") or self._has_unknown_product_type(line):
            self.type_input.setFocus()
        elif not line.get("quantity") or int(line["quantity"]) <= 0:
            self.quantity_input.setFocus()
        elif line.get("product_type") == "Fabric Roll" and not line.get("roll_length_cm"):
            self.roll_length_input.setFocus()
        elif line.get("product_type") == "Fabric Roll" and not line.get("roll_weight_kg"):
            self.roll_weight_input.setFocus()
        else:
            self.code_input.setFocus()

    def _status_for_line(self, line: dict[str, object]) -> str:
        if not line.get("product_code"):
            return "Ürün kodu eksik"
        if not line.get("product_type"):
            return "Tip eksik"
        if self._has_unknown_product_type(line):
            return "Tip tanımsız"
        if not line.get("quantity") or int(line["quantity"]) <= 0:
            return "Miktar hatalı"
        if line.get("product_type") == "Fabric Roll" and (
            not line.get("roll_length_cm") or not line.get("roll_weight_kg")
        ):
            return "Rulo bilgisi eksik"
        return str(line.get("match_status") or "Hazır")

    def _is_ready_line(self, line: dict[str, object]) -> bool:
        return self._status_for_line(line) not in BLOCKING_STATUSES

    def _is_missing_cell(self, line: dict[str, object], column: int) -> bool:
        if column == 0:
            return not bool(line.get("product_code"))
        if column == 2:
            return not bool(line.get("product_type")) or self._has_unknown_product_type(line)
        if column == 3:
            return not line.get("quantity") or int(line["quantity"]) <= 0
        if column == 4:
            return line.get("product_type") == "Fabric Roll" and (
                not line.get("roll_length_cm") or not line.get("roll_weight_kg")
            )
        if column == 5:
            return self._status_for_line(line) in BLOCKING_STATUSES
        return False

    def _apply_edit_field_styles(self, line: dict[str, object] | None) -> None:
        missing = {
            self.code_input: bool(line is not None and not line.get("product_code")),
            self.type_input: bool(
                line is not None and (not line.get("product_type") or self._has_unknown_product_type(line))
            ),
            self.quantity_input: bool(
                line is not None and (not line.get("quantity") or int(line["quantity"]) <= 0)
            ),
            self.roll_length_input: bool(
                line is not None and line.get("product_type") == "Fabric Roll" and not line.get("roll_length_cm")
            ),
            self.roll_weight_input: bool(
                line is not None and line.get("product_type") == "Fabric Roll" and not line.get("roll_weight_kg")
            ),
        }
        for widget, is_missing in missing.items():
            if is_missing:
                widget.setStyleSheet(
                    "background: #fff1f2; border: 2px solid #dc2626; border-radius: 6px; padding: 7px;"
                )
            else:
                widget.setStyleSheet("")

    def _has_unknown_product_type(self, line: dict[str, object]) -> bool:
        product_type = str(line.get("product_type") or "").strip()
        return bool(product_type and self.product_types and product_type not in self.product_types)

    def _update_summary(self) -> None:
        total_rows = len(self.order_lines)
        unique_products = len({line.get("product_code") for line in self.order_lines if line.get("product_code")})
        total_quantity = sum(int(line.get("quantity") or 0) for line in self.order_lines)
        ready_rows = sum(1 for line in self.order_lines if self._is_ready_line(line))
        issues = self.blocking_issue_messages()

        self.total_rows_value.setText(str(total_rows))
        self.unique_products_value.setText(str(unique_products))
        self.total_quantity_value.setText(str(total_quantity))
        self.ready_rows_value.setText(str(ready_rows))
        if issues:
            preview = "\n".join(issues[:4])
            suffix = f"\n... ve {len(issues) - 4} eksik daha" if len(issues) > 4 else ""
            self.note.setText(f"Devam etmeden önce şu eksikler tamamlanmalı:\n{preview}{suffix}")
            self.complete_button.setText("Eksikleri Tamamla")
        else:
            self.note.setText("Tüm satırlar hazır. Paketleme ayarlarına geçebilirsiniz.")
            self.complete_button.setText("Veriyi Düzenle")

    def _summary_card(self, title: str, value: str) -> QWidget:
        card = QFrame()
        card.setObjectName("summaryCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("summaryTitle")
        value_label = QLabel(value)
        value_label.setObjectName("summaryValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)

        attribute_name = {
            "Toplam Satır": "total_rows_value",
            "Farklı Ürün": "unique_products_value",
            "Toplam Miktar": "total_quantity_value",
            "Hazır Satır": "ready_rows_value",
        }[title]
        setattr(self, attribute_name, value_label)
        return card

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle { font-size: 30px; font-weight: 700; color: #172033; }
            #screenSubtitle, #summaryLabel { font-size: 15px; color: #526174; }
            #summaryCard {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            #summaryTitle { color: #64748b; font-size: 13px; font-weight: 600; }
            #summaryValue { color: #172033; font-size: 26px; font-weight: 700; }
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
                color: #172033;
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
