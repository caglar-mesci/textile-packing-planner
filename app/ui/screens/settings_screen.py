from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.application_settings_service import ApplicationSettings


class SettingsScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal(object)
    browse_export_requested = Signal()
    browse_backup_requested = Signal()

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
        title = QLabel("Ayarlar")
        title.setObjectName("screenTitle")
        subtitle = QLabel("Uygulamanın varsayılan klasörlerini ve paketleme tercihlerini yönetin.")
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

        form = QFrame()
        form.setObjectName("settingsForm")
        layout = QGridLayout(form)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        self.export_dir_input = QLineEdit()
        self.backup_dir_input = QLineEdit()
        export_browse = QPushButton("Seç")
        export_browse.setObjectName("secondaryAction")
        export_browse.clicked.connect(self.browse_export_requested.emit)
        backup_browse = QPushButton("Seç")
        backup_browse.setObjectName("secondaryAction")
        backup_browse.clicked.connect(self.browse_backup_requested.emit)

        layout.addWidget(self._field_label("Excel klasörü"), 0, 0)
        layout.addWidget(self.export_dir_input, 0, 1)
        layout.addWidget(export_browse, 0, 2)
        layout.addWidget(self._field_label("Yedek klasörü"), 1, 0)
        layout.addWidget(self.backup_dir_input, 1, 1)
        layout.addWidget(backup_browse, 1, 2)

        self.allow_partial_boxes_input = QCheckBox("Varsayılan: son kutu yarım dolu olabilir")
        self.prefer_small_final_box_input = QCheckBox("Varsayılan: son kutuda küçük kutu tercih et")
        self.merge_duplicate_lines_input = QCheckBox("Varsayılan: aynı ürün satırlarını birleştir")
        self.allow_direct_load_fabric_rolls_input = QCheckBox("Varsayılan: kumaş rulosunda direkt yüklemeye izin ver")

        layout.addWidget(self.allow_partial_boxes_input, 2, 0, 1, 3)
        layout.addWidget(self.prefer_small_final_box_input, 3, 0, 1, 3)
        layout.addWidget(self.merge_duplicate_lines_input, 4, 0, 1, 3)
        layout.addWidget(self.allow_direct_load_fabric_rolls_input, 5, 0, 1, 3)

        root.addWidget(form)
        root.addStretch(1)

        action_row = QHBoxLayout()
        save_button = QPushButton("Ayarları Kaydet")
        save_button.setObjectName("primaryAction")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self._emit_save)
        action_row.addStretch(1)
        action_row.addWidget(save_button)
        root.addLayout(action_row)

    def set_settings(self, settings: ApplicationSettings) -> None:
        self.export_dir_input.setText(settings.default_export_dir)
        self.backup_dir_input.setText(settings.default_backup_dir)
        self.allow_partial_boxes_input.setChecked(settings.default_allow_partial_boxes)
        self.prefer_small_final_box_input.setChecked(settings.default_prefer_small_final_box)
        self.merge_duplicate_lines_input.setChecked(settings.default_merge_duplicate_lines)
        self.allow_direct_load_fabric_rolls_input.setChecked(settings.default_allow_direct_load_fabric_rolls)

    def set_export_dir(self, path: str) -> None:
        if path:
            self.export_dir_input.setText(path)

    def set_backup_dir(self, path: str) -> None:
        if path:
            self.backup_dir_input.setText(path)

    def current_settings(self) -> ApplicationSettings:
        return ApplicationSettings(
            default_export_dir=self.export_dir_input.text().strip(),
            default_backup_dir=self.backup_dir_input.text().strip(),
            default_allow_partial_boxes=self.allow_partial_boxes_input.isChecked(),
            default_prefer_small_final_box=self.prefer_small_final_box_input.isChecked(),
            default_merge_duplicate_lines=self.merge_duplicate_lines_input.isChecked(),
            default_allow_direct_load_fabric_rolls=self.allow_direct_load_fabric_rolls_input.isChecked(),
        )

    def _emit_save(self) -> None:
        self.save_requested.emit(self.current_settings())

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            #screenTitle { font-size: 30px; font-weight: 700; color: #172033; }
            #screenSubtitle { font-size: 15px; color: #526174; }
            #settingsForm {
                background: #ffffff;
                border: 1px solid #dfe5ec;
                border-radius: 8px;
            }
            #fieldLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 700;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-size: 14px;
                padding: 8px;
            }
            QCheckBox {
                color: #334155;
                font-size: 14px;
                padding: 4px;
            }
            QPushButton#primaryAction {
                background: #1769c2;
                border: 0;
                border-radius: 6px;
                color: #ffffff;
                font-size: 15px;
                font-weight: 700;
                padding: 11px 18px;
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
