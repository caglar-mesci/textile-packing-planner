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

from app.repositories.packing_plan_repository import SavedPlanSummary


class HistoryScreen(QWidget):
    back_requested = Signal()
    plan_detail_requested = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.plans: list[SavedPlanSummary] = []
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(42, 36, 42, 36)
        root.setSpacing(18)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("Önceki Planlar")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Kaydedilen paketleme planlarını burada görebilirsiniz.")
        subtitle.setObjectName("screenSubtitle")
        subtitle.setWordWrap(True)
        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        back_button = QPushButton("Yeni Plana Dön")
        back_button.setObjectName("secondaryAction")
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(self.back_requested.emit)
        detail_button = QPushButton("Detay Aç")
        detail_button.setObjectName("primaryAction")
        detail_button.setCursor(Qt.PointingHandCursor)
        detail_button.clicked.connect(self._emit_detail_requested)
        header.addLayout(title_block, 1)
        header.addWidget(detail_button, 0, Qt.AlignTop)
        header.addWidget(back_button, 0, Qt.AlignTop)
        root.addLayout(header)

        summary = QGridLayout()
        summary.setSpacing(12)
        self.plan_count_value = self._summary_card(summary, "Plan Sayısı", 0, 0)
        self.total_box_value = self._summary_card(summary, "Toplam Kutu", 0, 1)
        self.last_plan_value = self._summary_card(summary, "Son Plan", 0, 2)
        root.addLayout(summary)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Plan No", "Tarih", "Durum", "Ürün Miktarı", "Kutu", "Ağırlık", "Araç", "Geçerlilik"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1)

    def set_plans(self, plans: list[SavedPlanSummary]) -> None:
        self.plans = plans
        self.table.setRowCount(0)
        for plan in plans:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                str(plan.id),
                plan.created_at,
                self._status_text(plan.status),
                str(int(plan.total_product_quantity)),
                str(plan.total_box_count),
                f"{plan.total_weight_kg:.2f} kg",
                f"{plan.vehicle_name or '-'} ({plan.vehicle_count})",
                "Geçerli" if plan.is_valid else "Kontrol gerekli",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, plan.id)
                item.setTextAlignment(Qt.AlignCenter if column != 1 else Qt.AlignVCenter | Qt.AlignLeft)
                self.table.setItem(row, column, item)

        self.plan_count_value.setText(str(len(plans)))
        self.total_box_value.setText(str(sum(plan.total_box_count for plan in plans)))
        self.last_plan_value.setText(plans[0].created_at if plans else "-")

    def _status_text(self, status: str) -> str:
        return {
            "VALID": "Geçerli",
            "INVALID": "Kontrol gerekli",
            "DRAFT": "Taslak",
        }.get(status, status)

    def _emit_detail_requested(self) -> None:
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        plan_id = selected_items[0].data(Qt.UserRole)
        if plan_id is not None:
            self.plan_detail_requested.emit(int(plan_id))

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
                font-weight: 700;
                padding: 10px 16px;
            }
            """
        )
