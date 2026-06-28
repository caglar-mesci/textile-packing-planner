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

from app.repositories.packing_plan_repository import SavedPlanDetail


class PlanDetailScreen(QWidget):
    back_requested = Signal()

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
        self.title = QLabel("Plan Detayı")
        self.title.setObjectName("screenTitle")
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("screenSubtitle")
        self.subtitle.setWordWrap(True)
        title_block.addWidget(self.title)
        title_block.addWidget(self.subtitle)

        back_button = QPushButton("Geçmiş Planlara Dön")
        back_button.setObjectName("secondaryAction")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        header.addLayout(title_block, 1)
        header.addWidget(back_button, 0, Qt.AlignTop)
        root.addLayout(header)

        summary = QGridLayout()
        summary.setSpacing(12)
        self.quantity_value = self._summary_card(summary, "Ürün Miktarı", 0, 0)
        self.box_count_value = self._summary_card(summary, "Kutu Sayısı", 0, 1)
        self.weight_value = self._summary_card(summary, "Toplam Ağırlık", 0, 2)
        self.vehicle_value = self._summary_card(summary, "Araç", 0, 3)
        root.addLayout(summary)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Sıra", "Kutu Kodu", "Kutu Adı", "Ağırlık", "Doluluk", "Durum"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1)

    def set_detail(self, detail: SavedPlanDetail) -> None:
        summary = detail.summary
        self.title.setText(f"Plan Detayı #{summary.id}")
        self.subtitle.setText(f"Oluşturma tarihi: {summary.created_at}")
        self.quantity_value.setText(str(int(summary.total_product_quantity)))
        self.box_count_value.setText(str(summary.total_box_count))
        self.weight_value.setText(f"{summary.total_weight_kg:.2f} kg")
        self.vehicle_value.setText(f"{summary.vehicle_name or '-'} ({summary.vehicle_count})")

        self.table.setRowCount(0)
        for box in detail.boxes:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(box.sequence_number),
                box.box_code,
                box.box_name,
                f"{box.estimated_gross_weight_kg:.2f} kg",
                f"%{box.fullness_percent:.1f}",
                "Geçerli" if box.is_valid else "Kontrol gerekli",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter if column != 2 else Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)

    def _summary_card(self, grid: QGridLayout, title: str, row: int, column: int) -> QLabel:
        card = QFrame()
        card.setObjectName("summaryCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        title_label = QLabel(title)
        title_label.setObjectName("summaryTitle")
        value_label = QLabel("-")
        value_label.setObjectName("summaryValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        grid.addWidget(card, row, column)
        return value_label

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle { font-size: 30px; font-weight: 700; color: #172033; }
            #screenSubtitle { font-size: 15px; color: #526174; }
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
            """
        )
