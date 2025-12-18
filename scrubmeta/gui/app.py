"""Application entry point for the scrubmeta GUI."""

from __future__ import annotations

import sys
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import apply_theme


def main() -> None:
    """Run the GUI application with synthwave theme."""
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    
    # Apply synthwave theme
    apply_theme(app)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
