from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.packing_service import PackingCalculationResult


class ResultScreen(QWidget):
    back_requested = Signal()
    export_requested = Signal()
    save_requested = Signal()

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
        title = QLabel("Paketleme Sonucu")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Bu ilk hesaplama ortalama ürün profilleriyle oluşturuldu.")
        subtitle.setObjectName("screenSubtitle")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        back_button = QPushButton("Ön İzlemeye Dön")
        back_button.setObjectName("secondaryAction")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        export_button = QPushButton("Excel'e Aktar")
        export_button.setObjectName("primaryAction")
        export_button.setCursor(Qt.PointingHandCursor)
        export_button.clicked.connect(self.export_requested.emit)
        save_button = QPushButton("Planı Kaydet")
        save_button.setObjectName("primaryAction")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self.save_requested.emit)
        header.addLayout(title_block, 1)
        header.addWidget(save_button, 0, Qt.AlignTop)
        header.addWidget(export_button, 0, Qt.AlignTop)
        header.addWidget(back_button, 0, Qt.AlignTop)
        root.addLayout(header)

        summary = QGridLayout()
        summary.setSpacing(12)
        self.quantity_value = self._summary_card(summary, "Toplam Miktar", 0, 0)
        self.box_count_value = self._summary_card(summary, "Kutu Sayısı", 0, 1)
        self.weight_value = self._summary_card(summary, "Tahmini Ağırlık", 0, 2)
        self.fullness_value = self._summary_card(summary, "Ortalama Doluluk", 0, 3)
        self.vehicle_value = self._summary_card(summary, "Önerilen Araç", 1, 0)
        self.vehicle_count_value = self._summary_card(summary, "Araç Sayısı", 1, 1)
        self.vehicle_volume_value = self._summary_card(summary, "Hacim Kullanımı", 1, 2)
        self.vehicle_weight_value = self._summary_card(summary, "Ağırlık Kullanımı", 1, 3)
        root.addLayout(summary)

        self.settings_label = QLabel("")
        self.settings_label.setObjectName("settingsLabel")
        self.settings_label.setWordWrap(True)
        root.addWidget(self.settings_label)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Ürün Kodu", "Ürün Adı", "Tip", "Miktar", "Kutu", "Kutu Sayısı", "Durum"]
        )
        self.table.setWordWrap(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(90)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1)

        self.info_label = QLabel("")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        root.addWidget(self.info_label)

    def set_result(self, result: PackingCalculationResult) -> None:
        self.quantity_value.setText(str(result.total_quantity))
        self.box_count_value.setText(str(result.total_box_count))
        self.weight_value.setText(f"{result.estimated_total_weight_kg:.2f} kg")
        self.fullness_value.setText(f"%{result.average_fullness_percent:.1f}")

        if result.vehicle_selection is None:
            self.vehicle_value.setText("-")
            self.vehicle_count_value.setText("0")
            self.vehicle_volume_value.setText("%0.0")
            self.vehicle_weight_value.setText("%0.0")
        else:
            self.vehicle_value.setText(result.vehicle_selection.vehicle.name)
            self.vehicle_count_value.setText(str(result.vehicle_selection.vehicle_count))
            self.vehicle_volume_value.setText(f"%{result.vehicle_selection.volume_utilization_percent:.1f}")
            self.vehicle_weight_value.setText(f"%{result.vehicle_selection.weight_utilization_percent:.1f}")

        vehicle_mode = (
            f"Seçili araç: {result.settings.selected_vehicle_code}"
            if result.settings.selected_vehicle_code
            else "Araç seçimi: otomatik"
        )
        packaging_modes = {
            "automatic": "Paketleme tercihi: otomatik",
            "boxed_only": "Paketleme tercihi: sadece kutulu plan",
            "direct_load_allowed": "Paketleme tercihi: direkt yükleme açık",
        }
        packaging_mode = packaging_modes.get(result.settings.packaging_mode, packaging_modes["automatic"])
        self.settings_label.setText(f"{vehicle_mode} | {packaging_mode}")

        self.table.setRowCount(0)
        for line in result.packed_lines:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                line.product_code,
                line.product_name or "-",
                line.product_type or "-",
                str(line.quantity),
                line.box_code or "-",
                str(line.box_count),
                line.status_text,
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                item.setTextAlignment(Qt.AlignCenter if column >= 3 else Qt.AlignVCenter | Qt.AlignLeft)
                if column == 6:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)
        self.table.resizeRowsToContents()

        if result.warnings:
            self.info_label.setText("\n".join(result.warnings[:6]))
        else:
            self.info_label.setText("")

    def _summary_card(self, grid: QGridLayout, title: str, row: int, column: int) -> QLabel:
        card = QFrame()
        card.setObjectName("summaryCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        title_label = QLabel(title)
        title_label.setObjectName("summaryTitle")
        value_label = QLabel("0")
        value_label.setObjectName("summaryValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        grid.addWidget(card, row, column)
        return value_label

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle {
                font-size: 30px;
                font-weight: 700;
                color: #172033;
            }
            #screenSubtitle {
                font-size: 15px;
                color: #526174;
            }
            #summaryCard {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            #summaryTitle {
                color: #64748b;
                font-size: 13px;
                font-weight: 600;
            }
            #summaryValue {
                color: #172033;
                font-size: 22px;
                font-weight: 700;
            }
            #infoLabel {
                color: #15803d;
                font-size: 13px;
                background: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 6px;
                padding: 8px;
            }
            #settingsLabel {
                color: #526174;
                font-size: 13px;
                padding: 2px;
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
            QPushButton#secondaryAction {
                background: #e8eef6;
                border: 0;
                border-radius: 6px;
                color: #172033;
                font-size: 14px;
                padding: 10px 14px;
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
            """
        )
