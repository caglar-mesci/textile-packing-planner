from PySide6.QtCore import Qt
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import APP_NAME, PROJECT_ROOT
from app.domain.exceptions import ExportError
from app.repositories.box_repository import BoxRepository
from app.services.application_settings_service import ApplicationSettingsService
from app.services.backup_service import BackupError, BackupService
from app.services.export_service import ExportService
from app.services.packing_service import PackingService
from app.services.product_matching_service import ProductMatchingService
from app.repositories.packing_plan_repository import PackingPlanRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.ui.screens.backup_screen import BackupScreen
from app.ui.screens.boxes_screen import BoxesScreen
from app.ui.screens.excel_import_screen import ExcelImportScreen
from app.ui.screens.history_screen import HistoryScreen
from app.ui.screens.manual_order_screen import ManualOrderScreen
from app.ui.screens.order_preview_screen import OrderPreviewScreen
from app.ui.screens.packing_settings_screen import PackingSettingsScreen
from app.ui.screens.plan_detail_screen import PlanDetailScreen
from app.ui.screens.profiles_screen import ProfilesScreen
from app.ui.screens.products_screen import ProductsScreen
from app.ui.screens.result_screen import ResultScreen
from app.ui.screens.settings_screen import SettingsScreen
from app.ui.screens.startup_screen import StartupScreen
from app.ui.screens.vehicles_screen import VehiclesScreen


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1120, 720)
        self._init_services()
        self._init_state()
        self._init_screens()
        self._connect_signals()
        self._build_layout()
        self._apply_styles()

    def _init_services(self) -> None:
        self.product_matching_service = ProductMatchingService()
        self.packing_service = PackingService()
        self.export_service = ExportService()
        self.application_settings_service = ApplicationSettingsService()
        self.backup_service = BackupService()
        self.packing_plan_repository = PackingPlanRepository()
        self.vehicle_repository = VehicleRepository()
        self.box_repository = BoxRepository()
        self.profile_repository = ProfileRepository()
        self.product_repository = ProductRepository()

    def _init_state(self) -> None:
        self.current_order_lines: list[dict[str, object]] = []
        self.current_result = None
        self.current_settings = None
        self.return_to_preview_after_product_save = False

    def _init_screens(self) -> None:
        self.stack = QStackedWidget()
        self.startup_screen = StartupScreen()
        self.excel_import_screen = ExcelImportScreen()
        self.history_screen = HistoryScreen()
        self.backup_screen = BackupScreen()
        self.settings_screen = SettingsScreen()
        self.vehicles_screen = VehiclesScreen()
        self.boxes_screen = BoxesScreen()
        self.profiles_screen = ProfilesScreen()
        self.products_screen = ProductsScreen()
        self.manual_order_screen = ManualOrderScreen()
        self.order_preview_screen = OrderPreviewScreen()
        self.packing_settings_screen = PackingSettingsScreen()
        self.plan_detail_screen = PlanDetailScreen()
        self.result_screen = ResultScreen()
        self.stack.addWidget(self.startup_screen)
        self.stack.addWidget(self.excel_import_screen)
        self.stack.addWidget(self.history_screen)
        self.stack.addWidget(self.backup_screen)
        self.stack.addWidget(self.settings_screen)
        self.stack.addWidget(self.vehicles_screen)
        self.stack.addWidget(self.boxes_screen)
        self.stack.addWidget(self.profiles_screen)
        self.stack.addWidget(self.products_screen)
        self.stack.addWidget(self.manual_order_screen)
        self.stack.addWidget(self.order_preview_screen)
        self.stack.addWidget(self.packing_settings_screen)
        self.stack.addWidget(self.plan_detail_screen)
        self.stack.addWidget(self.result_screen)

    def _connect_signals(self) -> None:
        # Navigation is centralized here so each screen stays focused on its own form logic.
        self.startup_screen.excel_import_requested.connect(self.show_excel_import)
        self.excel_import_screen.back_requested.connect(self.show_startup)
        self.excel_import_screen.preview_requested.connect(self.show_order_preview)
        self.startup_screen.manual_order_requested.connect(self.show_manual_order)
        self.manual_order_screen.back_requested.connect(self.show_startup)
        self.manual_order_screen.preview_requested.connect(self.show_order_preview)
        self.order_preview_screen.back_requested.connect(self.show_manual_order)
        self.order_preview_screen.continue_requested.connect(self.show_packing_settings)
        self.order_preview_screen.order_lines_changed.connect(self.update_order_preview_lines)
        self.packing_settings_screen.back_requested.connect(lambda: self.stack.setCurrentWidget(self.order_preview_screen))
        self.packing_settings_screen.continue_requested.connect(self.calculate_current_plan)
        self.result_screen.back_requested.connect(lambda: self.stack.setCurrentWidget(self.packing_settings_screen))
        self.result_screen.export_requested.connect(self.export_current_result)
        self.result_screen.save_requested.connect(self.save_current_result)
        self.history_screen.back_requested.connect(self.show_startup)
        self.history_screen.plan_detail_requested.connect(self.show_plan_detail)
        self.plan_detail_screen.back_requested.connect(self.show_history)
        self.backup_screen.back_requested.connect(self.show_startup)
        self.backup_screen.create_backup_requested.connect(self.create_backup)
        self.backup_screen.restore_backup_requested.connect(self.restore_backup)
        self.settings_screen.back_requested.connect(self.show_startup)
        self.settings_screen.save_requested.connect(self.save_application_settings)
        self.settings_screen.browse_export_requested.connect(self.browse_export_directory)
        self.settings_screen.browse_backup_requested.connect(self.browse_backup_directory)
        self.vehicles_screen.back_requested.connect(self.show_startup)
        self.boxes_screen.back_requested.connect(self.show_startup)
        self.profiles_screen.back_requested.connect(self.show_startup)
        self.products_screen.back_requested.connect(self.handle_products_back)
        self.boxes_screen.save_requested.connect(self.save_box)
        self.vehicles_screen.save_requested.connect(self.save_vehicle)
        self.profiles_screen.save_requested.connect(self.save_profile)
        self.products_screen.save_product_requested.connect(self.save_product)
        self.products_screen.save_rule_requested.connect(self.save_product_rule)
        self.products_screen.product_type_changed.connect(self.refresh_product_profile_choices)
        self.products_screen.rule_product_type_changed.connect(self.refresh_rule_profile_choices)

    def _build_layout(self) -> None:
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_navigation(), 0)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_app_header(), 0)
        content_layout.addWidget(self.stack, 1)

        layout.addWidget(content, 1)
        self.setCentralWidget(root)

    def _build_navigation(self) -> QWidget:
        navigation = QFrame()
        navigation.setObjectName("navigation")
        navigation.setFixedWidth(230)

        layout = QVBoxLayout(navigation)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(10)

        title = QLabel("Paketleme\nPlanlayıcı")
        title.setObjectName("navigationTitle")
        layout.addWidget(title)
        layout.addSpacing(16)

        buttons = [
            ("Yeni Plan", self.show_startup),
            ("Ürünler", self.show_products),
            ("Profiller", self.show_profiles),
            ("Kutular", self.show_boxes),
            ("Araçlar", self.show_vehicles),
            ("Geçmiş Planlar", self.show_history),
            ("Ayarlar", self.show_settings),
            ("Yedekleme", self.show_backup),
        ]

        for text, handler in buttons:
            button = QPushButton(text)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(handler)
            layout.addWidget(button)

        layout.addStretch(1)
        notice = QLabel("Örnek veriler şirket değerleriyle güncellenmelidir.")
        notice.setObjectName("navigationNotice")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        return navigation

    def _build_app_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("appHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 16, 28, 16)
        layout.setSpacing(10)

        text_block = QVBoxLayout()
        text_block.setSpacing(2)
        app_title = QLabel("Paketleme Planlayıcı")
        app_title.setObjectName("appHeaderTitle")
        app_note = QLabel("Tekstil siparişleri için kutu ve araç planlama")
        app_note.setObjectName("appHeaderNote")
        text_block.addWidget(app_title)
        text_block.addWidget(app_note)

        layout.addLayout(text_block, 1)
        return header

    def show_startup(self) -> None:
        recent_plans = self.packing_plan_repository.list_recent_plans(limit=1)
        self.startup_screen.set_recent_plan(recent_plans[0] if recent_plans else None)
        self.stack.setCurrentWidget(self.startup_screen)

    def show_manual_order(self) -> None:
        self.stack.setCurrentWidget(self.manual_order_screen)

    def show_excel_import(self) -> None:
        self.stack.setCurrentWidget(self.excel_import_screen)

    def show_history(self) -> None:
        self.history_screen.set_plans(self.packing_plan_repository.list_recent_plans())
        self.stack.setCurrentWidget(self.history_screen)

    def show_plan_detail(self, plan_id: int) -> None:
        detail = self.packing_plan_repository.get_plan_detail(plan_id)
        if detail is None:
            QMessageBox.information(self, "Plan Bulunamadı", "Seçilen plan bulunamadı.")
            self.show_history()
            return
        self.plan_detail_screen.set_detail(detail)
        self.stack.setCurrentWidget(self.plan_detail_screen)

    def show_backup(self) -> None:
        settings = self.application_settings_service.load()
        self.backup_service.backup_dir = Path(settings.default_backup_dir)
        self.backup_screen.set_status(
            self.backup_service.database_status(),
            self.backup_service.list_backups(),
        )
        self.stack.setCurrentWidget(self.backup_screen)

    def show_settings(self) -> None:
        self.settings_screen.set_settings(self.application_settings_service.load())
        self.stack.setCurrentWidget(self.settings_screen)

    def show_vehicles(self) -> None:
        self.vehicles_screen.set_vehicles(self.vehicle_repository.list_active_vehicles())
        self.stack.setCurrentWidget(self.vehicles_screen)

    def show_boxes(self) -> None:
        self.boxes_screen.set_boxes(self.box_repository.list_active_boxes())
        self.stack.setCurrentWidget(self.boxes_screen)

    def show_profiles(self) -> None:
        self.profiles_screen.set_product_types(self.profile_repository.list_product_types())
        self.profiles_screen.set_profiles(self.profile_repository.list_active_profiles())
        self.stack.setCurrentWidget(self.profiles_screen)

    def show_products(self) -> None:
        self.return_to_preview_after_product_save = False
        self._show_products_screen()

    def show_products_for_current_order(self) -> None:
        self.return_to_preview_after_product_save = True
        self._show_products_screen()

    def handle_products_back(self) -> None:
        if self.return_to_preview_after_product_save and self.current_order_lines:
            self.show_order_preview(self.current_order_lines)
            return
        self.show_startup()

    def _show_products_screen(self) -> None:
        back_text = "Ön İzlemeye Dön" if self.return_to_preview_after_product_save else "Yeni Plana Dön"
        self.products_screen.set_back_button_text(back_text)
        product_types = self.product_repository.list_product_types()
        self.products_screen.set_product_types(product_types)
        if product_types:
            self.products_screen.set_product_profiles(self.product_repository.list_profiles_for_type(product_types[0]))
            self.products_screen.set_rule_profiles(self.product_repository.list_profiles_for_type(product_types[0]))
        self.products_screen.set_data(
            self.product_repository.list_products(),
            self.product_repository.list_code_rules(),
        )
        self.stack.setCurrentWidget(self.products_screen)

    def refresh_product_profile_choices(self, product_type: str) -> None:
        if product_type:
            self.products_screen.set_product_profiles(self.product_repository.list_profiles_for_type(product_type))

    def refresh_rule_profile_choices(self, product_type: str) -> None:
        if product_type:
            self.products_screen.set_rule_profiles(self.product_repository.list_profiles_for_type(product_type))

    def save_box(self, box: object) -> None:
        try:
            self.box_repository.save_box(box)
        except Exception as exc:
            QMessageBox.warning(self, "Kutu Kaydedilemedi", str(exc))
            return
        self.boxes_screen.set_boxes(self.box_repository.list_active_boxes())
        QMessageBox.information(self, "Kutu Kaydedildi", "Kutu bilgileri kaydedildi.")

    def save_vehicle(self, vehicle: object) -> None:
        try:
            self.vehicle_repository.save_vehicle(vehicle)
        except Exception as exc:
            QMessageBox.warning(self, "Araç Kaydedilemedi", str(exc))
            return
        self.vehicles_screen.set_vehicles(self.vehicle_repository.list_active_vehicles())
        QMessageBox.information(self, "Araç Kaydedildi", "Araç bilgileri kaydedildi.")

    def save_profile(self, profile: object) -> None:
        try:
            self.profile_repository.save_profile(profile)
        except Exception as exc:
            QMessageBox.warning(self, "Profil Kaydedilemedi", str(exc))
            return
        self.profiles_screen.set_product_types(self.profile_repository.list_product_types())
        self.profiles_screen.set_profiles(self.profile_repository.list_active_profiles())
        QMessageBox.information(self, "Profil Kaydedildi", "Profil bilgileri kaydedildi.")

    def save_product(self, product: object) -> None:
        try:
            self.product_repository.save_product(product)
        except Exception as exc:
            QMessageBox.warning(self, "Ürün Kaydedilemedi", self._friendly_save_error(str(exc), "ürün kodu"))
            return
        if self.return_to_preview_after_product_save and self.current_order_lines:
            self.return_to_preview_after_product_save = False
            self.show_order_preview(self.current_order_lines)
            QMessageBox.information(
                self,
                "Ürün Kaydedildi",
                "Ürün bilgisi kaydedildi. Sipariş ön izlemesi güncellendi.",
            )
            return
        self._show_products_screen()
        QMessageBox.information(self, "Ürün Kaydedildi", "Ürün kodu bilgileri kaydedildi.")

    def save_product_rule(self, rule: object) -> None:
        try:
            self.product_repository.save_code_rule(rule)
        except Exception as exc:
            QMessageBox.warning(self, "Kural Kaydedilemedi", self._friendly_save_error(str(exc), "kod kuralı"))
            return
        if self.return_to_preview_after_product_save and self.current_order_lines:
            self.return_to_preview_after_product_save = False
            self.show_order_preview(self.current_order_lines)
            QMessageBox.information(
                self,
                "Kural Kaydedildi",
                "Kod eşleştirme kuralı kaydedildi. Sipariş ön izlemesi güncellendi.",
            )
            return
        self._show_products_screen()
        QMessageBox.information(self, "Kural Kaydedildi", "Kod eşleştirme kuralı kaydedildi.")

    def _friendly_save_error(self, message: str, item_name: str) -> str:
        if "UNIQUE constraint failed" in message:
            return f"Bu {item_name} zaten kayıtlı. Tablodan mevcut kaydı seçip güncelleyebilirsiniz."
        return message

    def show_order_preview(self, lines: list[dict[str, object]]) -> None:
        enriched_lines = self.product_matching_service.enrich_lines(lines)
        self.current_order_lines = enriched_lines
        self.order_preview_screen.set_product_types(self.product_repository.list_product_types())
        self.order_preview_screen.set_order_lines(enriched_lines)
        self.stack.setCurrentWidget(self.order_preview_screen)

    def update_order_preview_lines(self, lines: list[dict[str, object]]) -> None:
        self.show_order_preview(lines)

    def show_packing_settings(self) -> None:
        if self._warn_if_order_preview_blocked(return_to_preview=False):
            return
        self.packing_settings_screen.set_vehicles(self.vehicle_repository.list_active_vehicles())
        self.packing_settings_screen.set_application_defaults(self.application_settings_service.load())
        self.stack.setCurrentWidget(self.packing_settings_screen)

    def calculate_current_plan(self, settings: object | None = None) -> None:
        if self._warn_if_order_preview_blocked(return_to_preview=True):
            return
        if settings is None:
            settings = self.packing_settings_screen.current_settings()
        self.current_settings = settings
        result = self.packing_service.calculate(self.current_order_lines, settings)
        if result.validation_result and result.validation_result.errors:
            error_text = "\n".join(message.message for message in result.validation_result.errors[:6])
            QMessageBox.warning(
                self,
                "Paketleme Tamamlanamadı",
                f"Bu plan tamamlanmadan sonuç ekranına geçilemez:\n\n{error_text}",
            )
            return
        self.current_result = result
        self.result_screen.set_result(result)
        self.stack.setCurrentWidget(self.result_screen)

    def _warn_if_order_preview_blocked(self, return_to_preview: bool) -> bool:
        issues = self.order_preview_screen.blocking_issue_messages()
        if not issues:
            return False
        issue_text = "\n".join(issues[:6])
        QMessageBox.warning(
            self,
            "Eksik Bilgi Var",
            f"Paketleme hesabından önce şu eksikleri tamamlayın:\n\n{issue_text}",
        )
        if return_to_preview:
            self.stack.setCurrentWidget(self.order_preview_screen)
        return True

    def export_current_result(self) -> None:
        if self.current_result is None:
            QMessageBox.information(self, "Sonuç Yok", "Önce paketleme planı oluşturun.")
            return
        export_dir = Path(self.application_settings_service.load().default_export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Excel olarak kaydet",
            str(export_dir / "paketleme_plani.xlsx"),
            "Excel Dosyası (*.xlsx)",
        )
        if not file_name:
            return
        export_path = Path(file_name)
        if export_path.suffix.lower() != ".xlsx":
            export_path = export_path.with_suffix(".xlsx")
        try:
            self.export_service.export_packing_result(self.current_result, export_path)
        except ExportError as exc:
            QMessageBox.warning(self, "Aktarma Başarısız", str(exc))
            return
        QMessageBox.information(self, "Excel Hazır", "Paketleme planı Excel dosyasına aktarıldı.")

    def save_current_result(self) -> None:
        if self.current_result is None:
            QMessageBox.information(self, "Sonuç Yok", "Önce paketleme planı oluşturun.")
            return
        plan_id = self.packing_plan_repository.save_calculated_plan(self.current_result)
        recent_plans = self.packing_plan_repository.list_recent_plans(limit=1)
        self.startup_screen.set_recent_plan(recent_plans[0] if recent_plans else None)
        QMessageBox.information(self, "Plan Kaydedildi", f"Paketleme planı kaydedildi. Plan no: {plan_id}")

    def create_backup(self) -> None:
        settings = self.application_settings_service.load()
        self.backup_service.backup_dir = Path(settings.default_backup_dir)
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Yedek dosyasını kaydet",
            str(self.backup_service.backup_dir / "paketleme_yedek.zip"),
            "Yedek Dosyası (*.zip)",
        )
        if not file_name:
            return
        try:
            backup_path = self.backup_service.create_backup(Path(file_name))
        except BackupError as exc:
            QMessageBox.warning(self, "Yedek Alınamadı", str(exc))
            return
        self.show_backup()
        QMessageBox.information(self, "Yedek Hazır", f"Yedek dosyası oluşturuldu:\n{backup_path}")

    def restore_backup(self) -> None:
        settings = self.application_settings_service.load()
        self.backup_service.backup_dir = Path(settings.default_backup_dir)
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Yedek dosyasını seç",
            str(self.backup_service.backup_dir),
            "Yedek Dosyası (*.zip)",
        )
        if not file_name:
            return
        answer = QMessageBox.question(
            self,
            "Yedekten Geri Yükle",
            "Seçilen yedek mevcut uygulama verilerinin üzerine yazılacak. Devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.backup_service.restore_backup(Path(file_name))
        except BackupError as exc:
            QMessageBox.warning(self, "Geri Yükleme Başarısız", str(exc))
            return
        self.show_backup()
        QMessageBox.information(self, "Geri Yükleme Tamamlandı", "Yedek başarıyla geri yüklendi.")

    def save_application_settings(self, settings: object) -> None:
        try:
            self.application_settings_service.save(settings)
            self.application_settings_service.ensure_directories(settings)
            self.backup_service.backup_dir = Path(settings.default_backup_dir)
        except Exception as exc:
            QMessageBox.warning(self, "Ayarlar Kaydedilemedi", str(exc))
            return
        QMessageBox.information(self, "Ayarlar Kaydedildi", "Uygulama ayarları kaydedildi.")

    def browse_export_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Excel klasörünü seç",
            self.settings_screen.export_dir_input.text(),
        )
        self.settings_screen.set_export_dir(directory)

    def browse_backup_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self,
            "Yedek klasörünü seç",
            self.settings_screen.backup_dir_input.text(),
        )
        self.settings_screen.set_backup_dir(directory)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f7f9fb;
            }
            #navigation {
                background: #ffffff;
                border-right: 1px solid #dfe5ec;
            }
            #navigationTitle {
                color: #172033;
                font-size: 24px;
                font-weight: 700;
                line-height: 1.2;
            }
            #navigation QPushButton {
                background: transparent;
                border: 0;
                border-radius: 6px;
                color: #334155;
                font-size: 15px;
                padding: 10px 12px;
                text-align: left;
            }
            #navigation QPushButton:hover {
                background: #eef5ff;
                color: #1457a8;
            }
            #navigationNotice {
                color: #64748b;
                font-size: 12px;
            }
            #appHeader {
                background: #ffffff;
                border-bottom: 1px solid #dfe5ec;
            }
            #appHeaderTitle {
                color: #172033;
                font-size: 20px;
                font-weight: 700;
            }
            #appHeaderNote {
                color: #64748b;
                font-size: 13px;
            }
            QLabel {
                color: #172033;
            }
            QTableWidget {
                color: #172033;
            }
            QTableWidget::item {
                color: #172033;
            }
            QTableWidget::item:selected {
                background: #dbeafe;
                color: #172033;
            }
            QPushButton#secondaryAction {
                background: #e8eef6;
                border: 0;
                border-radius: 6px;
                color: #172033;
                font-size: 15px;
                padding: 10px 16px;
            }
            """
        )
