from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class StartupScreen(QWidget):
    excel_import_requested = Signal()
    manual_order_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.recent_order_label: QLabel | None = None
        self.recent_status_label: QLabel | None = None
        self._build()
        self._apply_styles()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 44, 48, 44)
        root.setSpacing(28)

        header = QVBoxLayout()
        header.setSpacing(8)

        title = QLabel("Paketleme Planı Oluştur")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Siparişi Excel’den yükleyin veya ürünleri elle girerek yeni plana başlayın.")
        subtitle.setObjectName("screenSubtitle")
        subtitle.setWordWrap(True)
        header.addWidget(title)
        header.addWidget(subtitle)
        root.addLayout(header)

        actions = QHBoxLayout()
        actions.setSpacing(18)
        actions.addWidget(
            self._build_action_card(
                "Excel’den Sipariş Yükle",
                "Hazır sipariş dosyasını seç, sütunları eşleştir ve ön izlemeye geç.",
                "Dosya Seç",
                self.excel_import_requested.emit,
            )
        )
        actions.addWidget(
            self._build_action_card(
                "Manuel Sipariş Gir",
                "Ürün kodlarını ve miktarları doğrudan girerek plan oluştur.",
                "Elle Giriş Yap",
                self.manual_order_requested.emit,
            )
        )
        root.addLayout(actions)

        recent_section = QVBoxLayout()
        recent_section.setSpacing(10)
        recent_title = QLabel("Son Planlar")
        recent_title.setObjectName("sectionTitle")
        recent_section.addWidget(recent_title)
        recent_section.addWidget(self._build_recent_plan_row())
        root.addLayout(recent_section)
        root.addStretch(1)

    def _build_action_card(
        self,
        title: str,
        description: str,
        button_text: str,
        handler: object,
    ) -> QWidget:
        card = QFrame()
        card.setObjectName("actionCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("actionTitle")
        description_label = QLabel(description)
        description_label.setObjectName("actionDescription")
        description_label.setWordWrap(True)

        button = QPushButton(button_text)
        button.setObjectName("primaryAction")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(handler)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch(1)
        layout.addWidget(button, 0, Qt.AlignLeft)
        return card

    def _build_recent_plan_row(self) -> QWidget:
        row = QFrame()
        row.setObjectName("recentRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(16)

        order_label = QLabel("Henüz kayıtlı plan yok")
        order_label.setObjectName("recentOrder")
        status_label = QLabel("Yeni plan oluşturabilirsiniz")
        status_label.setObjectName("recentStatus")
        self.recent_order_label = order_label
        self.recent_status_label = status_label
        layout.addWidget(order_label, 1)
        layout.addWidget(status_label, 0)
        return row

    def set_recent_plan(self, plan: object | None) -> None:
        if self.recent_order_label is None or self.recent_status_label is None:
            return
        if plan is None:
            self.recent_order_label.setText("Henüz kayıtlı plan yok")
            self.recent_status_label.setText("Yeni plan oluşturabilirsiniz")
            return
        self.recent_order_label.setText(f"Plan {plan.id}   {plan.total_box_count} kutu")
        self.recent_status_label.setText("Geçerli" if plan.is_valid else "Kontrol gerekli")

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle {
                font-size: 34px;
                font-weight: 700;
                color: #172033;
            }
            #screenSubtitle {
                font-size: 16px;
                color: #526174;
            }
            #actionCard {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
                min-height: 210px;
            }
            #actionTitle {
                font-size: 22px;
                font-weight: 700;
                color: #172033;
            }
            #actionDescription {
                font-size: 14px;
                color: #526174;
            }
            QPushButton#primaryAction {
                background: #1769c2;
                border: 0;
                border-radius: 6px;
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 18px;
            }
            QPushButton#primaryAction:hover {
                background: #1457a8;
            }
            #sectionTitle {
                font-size: 18px;
                font-weight: 700;
                color: #172033;
            }
            #recentRow {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            #recentOrder {
                font-size: 15px;
                color: #172033;
            }
            #recentStatus {
                font-size: 14px;
                color: #64748b;
            }
            """
        )
