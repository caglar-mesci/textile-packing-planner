from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.repositories.product_repository import ProductCodeRuleListItem, ProductListItem


class ProductsScreen(QWidget):
    back_requested = Signal()
    save_product_requested = Signal(object)
    save_rule_requested = Signal(object)
    product_type_changed = Signal(str)
    rule_product_type_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.products: list[ProductListItem] = []
        self.rules: list[ProductCodeRuleListItem] = []
        self.selected_product_id = 0
        self.selected_rule_id = 0
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Ürünler")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Öğrenilmiş ürün kodları ve kod eşleştirme kuralları.")
        subtitle.setObjectName("screenSubtitle")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        self.back_button = QPushButton("Yeni Plana Dön")
        self.back_button.setObjectName("secondaryAction")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_requested.emit)
        header.addLayout(title_block, 1)
        header.addWidget(self.back_button, 0, Qt.AlignTop)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.products_tab = self._build_products_tab()
        self.rules_tab = self._build_rules_tab()
        self.tabs.addTab(self.products_tab, "Ürün Kodları")
        self.tabs.addTab(self.rules_tab, "Kod Kuralları")
        root.addWidget(self.tabs, 1)

    def _build_products_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.products_table = QTableWidget(0, 7)
        self.products_table.setHorizontalHeaderLabels(
            ["Ürün Kodu", "Ürün Adı", "Tip", "Profil", "Paketleme", "Karışık Kutu", "Durum"]
        )
        self._setup_table(self.products_table)
        self.products_table.itemSelectionChanged.connect(self._load_selected_product)
        layout.addWidget(self.products_table, 1)
        layout.addWidget(self._build_product_form())
        return tab

    def _build_rules_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.rules_table = QTableWidget(0, 6)
        self.rules_table.setHorizontalHeaderLabels(["Eşleşme", "Desen", "Tip", "Profil", "Öncelik", "Durum"])
        self._setup_table(self.rules_table)
        self.rules_table.itemSelectionChanged.connect(self._load_selected_rule)
        layout.addWidget(self.rules_table, 1)
        layout.addWidget(self._build_rule_form())
        return tab

    def _setup_table(self, table: QTableWidget) -> None:
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

    def _build_product_form(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editForm")
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.product_code_input = QLineEdit()
        self.product_name_input = QLineEdit()
        self.product_type_input = QComboBox()
        self.product_type_input.currentTextChanged.connect(self.product_type_changed.emit)
        self.product_profile_input = QComboBox()
        self.product_packaging_input = QComboBox()
        self.product_packaging_input.addItems(["BOXED", "DIRECT_LOAD", "PALLETIZED", "BOXED_OR_DIRECT"])
        self.product_mixed_input = QCheckBox("Karışık kutuya izin ver")
        self.product_active_input = QCheckBox("Aktif")
        self.product_active_input.setChecked(True)

        fields = [
            ("Ürün Kodu", self.product_code_input),
            ("Ürün Adı", self.product_name_input),
            ("Ürün Tipi", self.product_type_input),
            ("Profil", self.product_profile_input),
            ("Paketleme", self.product_packaging_input),
        ]
        for column, (label_text, widget) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            layout.addWidget(label, 0, column)
            layout.addWidget(widget, 1, column)

        button_row = QHBoxLayout()
        new_button = QPushButton("Yeni")
        new_button.setObjectName("secondaryAction")
        new_button.clicked.connect(self.clear_product_form)
        save_button = QPushButton("Kaydet")
        save_button.setObjectName("primaryAction")
        save_button.clicked.connect(self._emit_product_save)
        button_row.addWidget(self.product_mixed_input)
        button_row.addWidget(self.product_active_input)
        button_row.addStretch(1)
        button_row.addWidget(new_button)
        button_row.addWidget(save_button)
        layout.addLayout(button_row, 2, 0, 1, 5)
        return frame

    def _build_rule_form(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("editForm")
        layout = QGridLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        self.rule_match_type_input = QComboBox()
        self.rule_match_type_input.addItems(["EXACT", "STARTS_WITH", "CONTAINS", "REGEX"])
        self.rule_pattern_input = QLineEdit()
        self.rule_product_type_input = QComboBox()
        self.rule_product_type_input.currentTextChanged.connect(self.rule_product_type_changed.emit)
        self.rule_profile_input = QComboBox()
        self.rule_priority_input = QSpinBox()
        self.rule_priority_input.setRange(1, 10_000)
        self.rule_priority_input.setValue(100)
        self.rule_active_input = QCheckBox("Aktif")
        self.rule_active_input.setChecked(True)

        fields = [
            ("Eşleşme", self.rule_match_type_input),
            ("Desen", self.rule_pattern_input),
            ("Ürün Tipi", self.rule_product_type_input),
            ("Profil", self.rule_profile_input),
            ("Öncelik", self.rule_priority_input),
        ]
        for column, (label_text, widget) in enumerate(fields):
            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            layout.addWidget(label, 0, column)
            layout.addWidget(widget, 1, column)

        button_row = QHBoxLayout()
        new_button = QPushButton("Yeni")
        new_button.setObjectName("secondaryAction")
        new_button.clicked.connect(self.clear_rule_form)
        save_button = QPushButton("Kaydet")
        save_button.setObjectName("primaryAction")
        save_button.clicked.connect(self._emit_rule_save)
        button_row.addWidget(self.rule_active_input)
        button_row.addStretch(1)
        button_row.addWidget(new_button)
        button_row.addWidget(save_button)
        layout.addLayout(button_row, 2, 0, 1, 5)
        return frame

    def set_product_types(self, product_types: list[str]) -> None:
        for combo in [self.product_type_input, self.rule_product_type_input]:
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(product_types)
            if current:
                index = combo.findText(current)
                if index >= 0:
                    combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def set_product_profiles(self, profiles: list[str]) -> None:
        current = self.product_profile_input.currentText()
        self.product_profile_input.clear()
        self.product_profile_input.addItems(profiles)
        if current and (index := self.product_profile_input.findText(current)) >= 0:
            self.product_profile_input.setCurrentIndex(index)

    def set_rule_profiles(self, profiles: list[str]) -> None:
        current = self.rule_profile_input.currentText()
        self.rule_profile_input.clear()
        self.rule_profile_input.addItems(profiles)
        if current and (index := self.rule_profile_input.findText(current)) >= 0:
            self.rule_profile_input.setCurrentIndex(index)

    def set_data(self, products: list[ProductListItem], rules: list[ProductCodeRuleListItem]) -> None:
        self.products = products
        self.rules = rules
        self.products_table.setRowCount(0)
        for product in products:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            values = [
                product.product_code,
                product.product_name or "-",
                product.product_type,
                product.profile_name,
                product.packaging_rule,
                "Evet" if product.mixed_box_allowed else "Hayır",
                "Aktif" if product.active else "Pasif",
            ]
            self._set_row(self.products_table, row, values, product.id)

        self.rules_table.setRowCount(0)
        for rule in rules:
            row = self.rules_table.rowCount()
            self.rules_table.insertRow(row)
            values = [
                rule.match_type,
                rule.pattern,
                rule.product_type,
                rule.profile_name or "-",
                str(rule.priority),
                "Aktif" if rule.active else "Pasif",
            ]
            self._set_row(self.rules_table, row, values, rule.id)

    def set_back_button_text(self, text: str) -> None:
        self.back_button.setText(text)

    def _set_row(self, table: QTableWidget, row: int, values: list[str], item_id: int) -> None:
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setData(Qt.UserRole, item_id)
            item.setTextAlignment(Qt.AlignCenter if column >= 4 else Qt.AlignVCenter | Qt.AlignLeft)
            table.setItem(row, column, item)

    def clear_product_form(self) -> None:
        self.selected_product_id = 0
        self.product_code_input.clear()
        self.product_name_input.clear()
        self.product_packaging_input.setCurrentText("BOXED")
        self.product_mixed_input.setChecked(False)
        self.product_active_input.setChecked(True)

    def clear_rule_form(self) -> None:
        self.selected_rule_id = 0
        self.rule_match_type_input.setCurrentText("STARTS_WITH")
        self.rule_pattern_input.clear()
        self.rule_priority_input.setValue(100)
        self.rule_active_input.setChecked(True)

    def _load_selected_product(self) -> None:
        selected_items = self.products_table.selectedItems()
        if not selected_items:
            return
        product_id = selected_items[0].data(Qt.UserRole)
        product = next((item for item in self.products if item.id == product_id), None)
        if product is None:
            return
        self.selected_product_id = product.id
        self.product_code_input.setText(product.product_code)
        self.product_name_input.setText(product.product_name or "")
        self.product_type_input.setCurrentText(product.product_type)
        self.product_profile_input.setCurrentText(product.profile_name)
        self.product_packaging_input.setCurrentText(product.packaging_rule)
        self.product_mixed_input.setChecked(product.mixed_box_allowed)
        self.product_active_input.setChecked(product.active)

    def _load_selected_rule(self) -> None:
        selected_items = self.rules_table.selectedItems()
        if not selected_items:
            return
        rule_id = selected_items[0].data(Qt.UserRole)
        rule = next((item for item in self.rules if item.id == rule_id), None)
        if rule is None:
            return
        self.selected_rule_id = rule.id
        self.rule_match_type_input.setCurrentText(rule.match_type)
        self.rule_pattern_input.setText(rule.pattern)
        self.rule_product_type_input.setCurrentText(rule.product_type)
        if rule.profile_name:
            self.rule_profile_input.setCurrentText(rule.profile_name)
        self.rule_priority_input.setValue(rule.priority)
        self.rule_active_input.setChecked(rule.active)

    def _emit_product_save(self) -> None:
        if not self.product_code_input.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Ürün kodu zorunludur.")
            return
        if not self.product_profile_input.currentText():
            QMessageBox.warning(self, "Eksik Bilgi", "Profil seçilmelidir.")
            return
        product = ProductListItem(
            id=self.selected_product_id,
            product_code=self.product_code_input.text().strip(),
            product_name=self.product_name_input.text().strip() or None,
            product_type=self.product_type_input.currentText(),
            profile_name=self.product_profile_input.currentText(),
            packaging_rule=self.product_packaging_input.currentText(),
            mixed_box_allowed=self.product_mixed_input.isChecked(),
            active=self.product_active_input.isChecked(),
        )
        self.save_product_requested.emit(product)

    def _emit_rule_save(self) -> None:
        if not self.rule_pattern_input.text().strip():
            QMessageBox.warning(self, "Eksik Bilgi", "Desen zorunludur.")
            return
        rule = ProductCodeRuleListItem(
            id=self.selected_rule_id,
            match_type=self.rule_match_type_input.currentText(),
            pattern=self.rule_pattern_input.text().strip(),
            product_type=self.rule_product_type_input.currentText(),
            profile_name=self.rule_profile_input.currentText() or None,
            priority=self.rule_priority_input.value(),
            active=self.rule_active_input.isChecked(),
        )
        self.save_rule_requested.emit(rule)

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
            QLineEdit, QComboBox, QSpinBox {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 13px;
                padding: 7px;
            }
            QTabWidget::pane {
                border: 1px solid #dfe5ec;
                border-radius: 8px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e8eef6;
                color: #172033;
                padding: 9px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1769c2;
                color: #ffffff;
            }
            QTableWidget {
                background: #ffffff;
                alternate-background-color: #f8fafc;
                border: 0;
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
