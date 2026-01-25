"""Application entry point for the scrubmeta GUI."""

from __future__ import annotations

import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QFont
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import apply_theme


def main() -> None:
    """Run the GUI application with synthwave theme."""
    # Note: High DPI scaling is enabled by default in Qt 6

    app = QApplication(sys.argv)

    # Set application icon for dock/taskbar
    pixmap = QPixmap(128, 128)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setFont(QFont("Arial", 96))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔮")
    painter.end()
    app.setWindowIcon(QIcon(pixmap))

    # Apply synthwave theme
    apply_theme(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
