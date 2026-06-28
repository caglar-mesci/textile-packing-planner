import sys

from app.config import APP_NAME
from app.repositories.database import Database


def main() -> None:
    Database().initialize()

    try:
        from PySide6.QtWidgets import QApplication

        from app.ui.main_window import MainWindow
    except ModuleNotFoundError:
        print(f"{APP_NAME} hazır. Masaüstü arayüzü için PySide6 kurulmalı.")
        return

    application = QApplication(sys.argv)
    application.setApplicationName(APP_NAME)
    _apply_light_palette(application)
    window = MainWindow()
    window.show()
    sys.exit(application.exec())


def _apply_light_palette(application: object) -> None:
    from PySide6.QtGui import QColor, QPalette

    application.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f7f9fb"))
    palette.setColor(QPalette.WindowText, QColor("#172033"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.Text, QColor("#172033"))
    palette.setColor(QPalette.Button, QColor("#e8eef6"))
    palette.setColor(QPalette.ButtonText, QColor("#172033"))
    palette.setColor(QPalette.Highlight, QColor("#dbeafe"))
    palette.setColor(QPalette.HighlightedText, QColor("#172033"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#172033"))
    application.setPalette(palette)


if __name__ == "__main__":
    main()
