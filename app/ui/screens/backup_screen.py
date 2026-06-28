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

from app.services.backup_service import BackupInfo


class BackupScreen(QWidget):
    back_requested = Signal()
    create_backup_requested = Signal()
    restore_backup_requested = Signal()

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
        title = QLabel("Yedekleme")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Ürün, profil, kutu, araç ve geçmiş plan verilerini güvenli bir yedek dosyasında saklayın.")
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

        summary = QGridLayout()
        summary.setSpacing(12)
        self.database_status_value = self._summary_card(summary, "Veri Durumu", 0, 0)
        self.database_size_value = self._summary_card(summary, "Veri Boyutu", 0, 1)
        self.last_backup_value = self._summary_card(summary, "Son Yedek", 0, 2)
        root.addLayout(summary)

        action_row = QHBoxLayout()
        create_button = QPushButton("Yedek Al")
        create_button.setObjectName("primaryAction")
        create_button.setCursor(Qt.PointingHandCursor)
        create_button.clicked.connect(self.create_backup_requested.emit)
        restore_button = QPushButton("Yedekten Geri Yükle")
        restore_button.setObjectName("dangerAction")
        restore_button.setCursor(Qt.PointingHandCursor)
        restore_button.clicked.connect(self.restore_backup_requested.emit)
        action_row.addWidget(create_button)
        action_row.addWidget(restore_button)
        action_row.addStretch(1)
        root.addLayout(action_row)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Dosya", "Tarih", "Boyut"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table, 1)

        self.info_label = QLabel(
            "Yedek dosyası uygulamanın kendi veritabanını içerir; Excel çıktılarından farklıdır."
        )
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        root.addWidget(self.info_label)

    def set_status(self, status: dict[str, object], backups: list[BackupInfo]) -> None:
        exists = bool(status.get("exists"))
        self.database_status_value.setText("Hazır" if exists else "Henüz oluşmadı")
        self.database_size_value.setText(self._format_size(int(status.get("size_bytes") or 0)))
        self.last_backup_value.setText(backups[0].created_at.strftime("%d.%m.%Y %H:%M") if backups else "-")

        self.table.setRowCount(0)
        for backup in backups:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                backup.file_name,
                backup.created_at.strftime("%d.%m.%Y %H:%M"),
                self._format_size(backup.size_bytes),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, str(backup.path))
                item.setTextAlignment(Qt.AlignCenter if column else Qt.AlignVCenter | Qt.AlignLeft)
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

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes <= 0:
            return "0 KB"
        size_kb = size_bytes / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        return f"{size_kb / 1024:.2f} MB"

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle { font-size: 30px; font-weight: 700; color: #172033; }
            #screenSubtitle, #infoLabel { font-size: 14px; color: #526174; }
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
            QPushButton#primaryAction {
                background: #1769c2;
                border: 0;
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: 700;
                padding: 10px 16px;
            }
            QPushButton#dangerAction {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                border-radius: 6px;
                color: #9f1239;
                font-size: 14px;
                font-weight: 700;
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
