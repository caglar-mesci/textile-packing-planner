from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
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

from app.domain.exceptions import ExcelImportError, MissingRequiredColumnError
from app.importers.column_detector import normalize_product_type
from app.importers.excel_reader import ExcelOrderReader
from app.importers.import_models import ImportPreview, InvalidImportRow


class ExcelImportScreen(QWidget):
    back_requested = Signal()
    preview_requested = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.reader = ExcelOrderReader()
        self.selected_file: Path | None = None
        self.current_preview: ImportPreview | None = None
        self.current_lines: list[dict[str, object]] = []
        self.invalid_rows: list[InvalidImportRow] = []
        self.selected_invalid_row_number: int | None = None
        self.review_sheet_names: list[str] = []
        self.approved_lines_by_sheet: dict[str, list[dict[str, object]]] = {}
        self.setAcceptDrops(True)
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Excel'den Sipariş Yükle")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Dosyayı seçin, her sipariş sayfasını kontrol edip onaylayın.")
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

        pick_frame = QFrame()
        pick_frame.setObjectName("dropArea")
        pick_layout = QVBoxLayout(pick_frame)
        pick_layout.setContentsMargins(22, 20, 22, 20)
        pick_layout.setSpacing(12)

        self.file_label = QLabel(
            "Henüz dosya seçilmedi. .xlsx dosyasını buraya sürükleyebilir veya dosya seçebilirsiniz."
        )
        self.file_label.setObjectName("dropText")
        self.file_label.setWordWrap(True)
        pick_button = QPushButton("Dosya Seç")
        pick_button.setObjectName("primaryAction")
        pick_button.setCursor(Qt.PointingHandCursor)
        pick_button.clicked.connect(self.pick_file)

        sheet_row = QHBoxLayout()
        sheet_label = QLabel("Sayfa")
        sheet_label.setObjectName("fieldLabel")
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentTextChanged.connect(self.read_selected_sheet)
        sheet_row.addWidget(sheet_label)
        sheet_row.addWidget(self.sheet_combo, 1)

        pick_layout.addWidget(self.file_label)
        pick_layout.addWidget(pick_button, 0, Qt.AlignLeft)
        pick_layout.addLayout(sheet_row)
        root.addWidget(pick_frame)

        self.summary_label = QLabel("Dosya seçildiğinde sipariş sayfaları burada kontrol edilecek.")
        self.summary_label.setObjectName("summaryLabel")
        self.summary_label.setWordWrap(True)
        root.addWidget(self.summary_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Ürün Kodu", "Ürün Adı", "Tip", "Miktar", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemSelectionChanged.connect(self._load_selected_error_row)
        root.addWidget(self.table, 1)

        root.addWidget(self._build_correction_form())

        footer = QHBoxLayout()
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        self.continue_button = QPushButton("Bu Sayfayı Onayla")
        self.continue_button.setObjectName("primaryAction")
        self.continue_button.setCursor(Qt.PointingHandCursor)
        self.continue_button.clicked.connect(self.emit_preview)
        footer.addWidget(self.error_label, 1)
        footer.addWidget(self.continue_button)
        root.addLayout(footer)

    def dragEnterEvent(self, event: object) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: object) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        self.load_file(Path(urls[0].toLocalFile()))

    def pick_file(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Excel dosyası seç",
            "",
            "Excel Dosyaları (*.xlsx *.xls)",
        )
        if file_name:
            self.load_file(Path(file_name))

    def load_file(self, file_path: Path) -> None:
        self.selected_file = file_path
        self.current_preview = None
        self.current_lines = []
        self.invalid_rows = []
        self.selected_invalid_row_number = None
        self.review_sheet_names = []
        self.approved_lines_by_sheet = {}
        self.error_label.setText("")
        self._clear_correction_form()
        self.file_label.setText(str(file_path))
        self.sheet_combo.blockSignals(True)
        self.sheet_combo.clear()
        try:
            sheets = self.reader.list_sheets(file_path)
        except ExcelImportError as exc:
            self._show_error(str(exc))
            self.sheet_combo.blockSignals(False)
            return

        self.review_sheet_names = self._detect_order_sheets(file_path, sheets)
        if not self.review_sheet_names:
            self._show_error("Sipariş tablosu içeren sayfa bulunamadı.")
            self.sheet_combo.blockSignals(False)
            return

        self.sheet_combo.addItems(self.review_sheet_names)
        self.sheet_combo.blockSignals(False)
        self.read_selected_sheet(self.review_sheet_names[0])

    def read_selected_sheet(self, sheet_name: str) -> None:
        if not self.selected_file or not sheet_name:
            return
        try:
            self.current_preview = self.reader.read(self.selected_file, sheet_name)
        except (ExcelImportError, MissingRequiredColumnError) as exc:
            self.current_preview = None
            self._show_error(str(exc))
            return
        self.current_lines = [line.to_preview_dict() for line in self.current_preview.lines]
        self.invalid_rows = list(self.current_preview.invalid_rows)
        self.selected_invalid_row_number = None
        self._clear_correction_form()
        self._render_preview()

    def emit_preview(self) -> None:
        if self.current_preview is None:
            QMessageBox.information(self, "Dosya Hazır Değil", "Önce geçerli bir Excel dosyası seçin.")
            return
        if self.invalid_rows:
            QMessageBox.warning(
                self,
                "Hatalı Satırlar Var",
                "Bu sayfadaki hatalı satırlar alttaki düzeltme alanında tamamlanmadan devam edilemez.",
            )
            return
        if not self.current_lines:
            QMessageBox.information(self, "Satır Bulunamadı", "Bu sayfada içe aktarılacak sipariş satırı bulunamadı.")
            return

        self.approved_lines_by_sheet[self.current_preview.sheet_name] = list(self.current_lines)
        next_sheet = self._next_unapproved_sheet()
        if next_sheet:
            approved_sheet = self.current_preview.sheet_name
            self.sheet_combo.setCurrentText(next_sheet)
            QMessageBox.information(
                self,
                "Sayfa Onaylandı",
                f"{approved_sheet} onaylandı. Şimdi {next_sheet} sayfasını kontrol edin.",
            )
            return

        merged_lines: list[dict[str, object]] = []
        for sheet_name in self.review_sheet_names:
            merged_lines.extend(self.approved_lines_by_sheet.get(sheet_name, []))
        self.preview_requested.emit(merged_lines)

    def _render_preview(self) -> None:
        if self.current_preview is None:
            return
        self.error_label.setText("")
        self.table.setRowCount(0)
        for line in self.current_lines:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(line.get("product_code") or ""),
                str(line.get("product_name") or ""),
                str(line.get("product_type") or ""),
                str(line.get("quantity") or ""),
                "Hazır" if line.get("product_type") else "Tip eksik",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setForeground(QBrush(QColor("#172033")))
                item.setTextAlignment(Qt.AlignCenter if column >= 3 else Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)

        for invalid_row in self.invalid_rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                invalid_row.product_code or "",
                invalid_row.product_name or "",
                invalid_row.product_type or "",
                str(invalid_row.quantity or ""),
                " / ".join(invalid_row.messages),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, invalid_row.row_number)
                item.setForeground(QBrush(QColor("#b42318")))
                item.setBackground(QBrush(QColor("#fff1f2")))
                item.setToolTip("Bu satır alttaki düzeltme alanında tamamlanmalı.")
                item.setTextAlignment(Qt.AlignCenter if column >= 3 else Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)

        mapped_columns = ", ".join(self.current_preview.column_mapping.values())
        self.summary_label.setText(
            f"Sayfa {self._current_sheet_number()} / {len(self.review_sheet_names)}. "
            f"{len(self.approved_lines_by_sheet)} sayfa onaylandı. "
            f"{len(self.current_lines)} geçerli satır, {len(self.invalid_rows)} hatalı satır bulundu. "
            f"Toplam miktar: {sum(int(line.get('quantity') or 0) for line in self.current_lines)}. "
            f"Bulunan sütunlar: {mapped_columns}."
        )
        if self.invalid_rows:
            first_errors = "\n".join(
                f"Satır {row.row_number}: {' / '.join(row.messages)}" for row in self.invalid_rows[:5]
            )
            self.error_label.setText(first_errors)
        if not self.invalid_rows:
            self.error_label.setText("")
        self._update_continue_button_text()

    def _detect_order_sheets(self, file_path: Path, sheets: list[str]) -> list[str]:
        order_sheets: list[str] = []
        for sheet in sheets:
            try:
                self.reader.read(file_path, sheet)
            except MissingRequiredColumnError:
                continue
            except ExcelImportError:
                continue
            order_sheets.append(sheet)
        return order_sheets

    def _build_correction_form(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("correctionForm")
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.correction_title = QLabel("Hatalı satırı seçip burada düzeltin.")
        self.correction_title.setObjectName("summaryLabel")
        layout.addWidget(self.correction_title, 0, 0, 1, 6)

        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.type_input = QLineEdit()
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
            layout.addWidget(label, 1, column)
            layout.addWidget(widget, 2, column)

        fix_button = QPushButton("Hatalı Satırı Düzelt")
        fix_button.setObjectName("primaryAction")
        fix_button.setCursor(Qt.PointingHandCursor)
        fix_button.clicked.connect(self.apply_error_row_correction)
        layout.addWidget(fix_button, 3, 5)
        return frame

    def _load_selected_error_row(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            self.selected_invalid_row_number = None
            self._clear_correction_form()
            return
        row_number = selected_items[0].data(Qt.UserRole)
        if row_number is None:
            self.selected_invalid_row_number = None
            self._clear_correction_form()
            return
        invalid_row = next((row for row in self.invalid_rows if row.row_number == row_number), None)
        if invalid_row is None:
            self.selected_invalid_row_number = None
            self._clear_correction_form()
            return
        self.selected_invalid_row_number = invalid_row.row_number
        self.code_input.setText(invalid_row.product_code or "")
        self.name_input.setText(invalid_row.product_name or "")
        self.type_input.setText(invalid_row.product_type or "")
        self.quantity_input.setValue(self._safe_int(invalid_row.quantity))
        self.roll_length_input.setValue(float(invalid_row.roll_length_cm or 0))
        self.roll_weight_input.setValue(float(invalid_row.roll_weight_kg or 0))
        self._style_correction_fields()

    def apply_error_row_correction(self) -> None:
        if self.selected_invalid_row_number is None:
            QMessageBox.information(self, "Satır Seçilmedi", "Önce tablodan kırmızı hatalı satırı seçin.")
            return
        product_code = self.code_input.text().strip()
        quantity = self.quantity_input.value()
        if not product_code or quantity <= 0:
            self._style_correction_fields()
            QMessageBox.warning(self, "Eksik Bilgi", "Ürün kodu ve pozitif miktar zorunludur.")
            return

        corrected_line = {
            "product_code": product_code,
            "product_name": self.name_input.text().strip() or None,
            "product_type": normalize_product_type(self.type_input.text().strip()) if self.type_input.text().strip() else None,
            "quantity": quantity,
            "roll_length_cm": self.roll_length_input.value() or None,
            "roll_weight_kg": self.roll_weight_input.value() or None,
            "source_row": self.selected_invalid_row_number,
        }
        self.current_lines.append(corrected_line)
        self.invalid_rows = [row for row in self.invalid_rows if row.row_number != self.selected_invalid_row_number]
        self.selected_invalid_row_number = None
        self._clear_correction_form()
        self._render_preview()

    def _safe_int(self, value: object) -> int:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return 0
        if parsed <= 0:
            return 0
        return int(parsed)

    def _clear_correction_form(self) -> None:
        self.code_input.clear()
        self.name_input.clear()
        self.type_input.clear()
        self.quantity_input.setValue(0)
        self.roll_length_input.setValue(0)
        self.roll_weight_input.setValue(0)
        self._clear_correction_styles()

    def _style_correction_fields(self) -> None:
        missing_code = not self.code_input.text().strip()
        missing_quantity = self.quantity_input.value() <= 0
        for widget, missing in [(self.code_input, missing_code), (self.quantity_input, missing_quantity)]:
            if missing:
                widget.setStyleSheet("background: #fff1f2; border: 2px solid #dc2626; border-radius: 6px; padding: 7px;")
            else:
                widget.setStyleSheet("")

    def _clear_correction_styles(self) -> None:
        for widget in [self.code_input, self.name_input, self.type_input, self.quantity_input]:
            widget.setStyleSheet("")

    def _current_sheet_number(self) -> int:
        if not self.current_preview or self.current_preview.sheet_name not in self.review_sheet_names:
            return 0
        return self.review_sheet_names.index(self.current_preview.sheet_name) + 1

    def _next_unapproved_sheet(self) -> str | None:
        for sheet_name in self.review_sheet_names:
            if sheet_name not in self.approved_lines_by_sheet:
                return sheet_name
        return None

    def _update_continue_button_text(self) -> None:
        if not self.current_preview:
            self.continue_button.setText("Bu Sayfayı Onayla")
            return
        remaining_after_current = [
            sheet_name
            for sheet_name in self.review_sheet_names
            if sheet_name != self.current_preview.sheet_name and sheet_name not in self.approved_lines_by_sheet
        ]
        if remaining_after_current:
            self.continue_button.setText("Bu Sayfayı Onayla ve Sonrakine Geç")
        else:
            self.continue_button.setText("Son Sayfayı Onayla ve Ön İzlemeye Geç")

    def _show_error(self, message: str) -> None:
        self.table.setRowCount(0)
        self.summary_label.setText("Dosya okunamadı.")
        self.error_label.setText(message)

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
            #dropArea {
                background: #ffffff;
                border: 1px dashed #9db7d4;
                border-radius: 8px;
            }
            #correctionForm {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            #dropText {
                color: #334155;
                font-size: 15px;
            }
            #fieldLabel {
                font-size: 13px;
                font-weight: 600;
                color: #334155;
            }
            #errorLabel {
                color: #b42318;
                font-size: 13px;
            }
            QComboBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                color: #172033;
                font-size: 14px;
                padding: 8px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                color: #172033;
                font-size: 13px;
                padding: 7px;
            }
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
                color: #172033;
                gridline-color: #e2e8f0;
                font-size: 13px;
            }
            QTableWidget::item {
                color: #172033;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #172033;
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
