"""Synthwave deep purple theme for MetaScrub GUI."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication, QStyleFactory


# Color Palette - Brighter with lighter purples and lavenders
class Colors:
    """Synthwave purple & lavender color tokens - lighter, more vibrant."""
    
    # Base colors - lighter overall
    BACKGROUND = "#1a1028"      # Deep purple-grey (lighter than before)
    SURFACE = "#2d1b47"         # Medium purple
    SURFACE_LIGHT = "#3d2b57"   # Lighter purple card
    SURFACE_HOVER = "#4d3b67"   # Hover state purple
    SURFACE_FOCUS = "#5d4b77"   # Slightly elevated focus state
    
    # Accents
    PRIMARY = "#ff006e"         # Neon magenta
    SECONDARY = "#00d9ff"       # Cyan/teal
    WARNING = "#ffb703"         # Warm amber
    ERROR = "#ff4365"           # Neon red-pink
    SUCCESS = "#00ff88"         # Mint green
    
    # Text - adjusted for lighter background
    TEXT_PRIMARY = "#e8e0ff"    # Light lavender-white (WCAG AA 14:1)
    TEXT_SECONDARY = "#d0c0e8"  # Muted light lavender (WCAG AA 10:1)
    TEXT_DISABLED = "#8070a0"   # Dimmed but readable (7:1)
    
    # Borders & Accents
    BORDER = "#5d3b77"          # Lighter purple border
    BORDER_FOCUS = "#ff006e"    # Magenta focus
    
    # Subtle shadows (RGBA for depth)
    SHADOW_LIGHT = "rgba(0, 0, 0, 0.1)"      # Subtle elevation
    SHADOW_MEDIUM = "rgba(255, 0, 110, 0.05)" # Magenta tint for focus


class Spacing:
    """Spacing constants (4-point scale)."""
    
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32


class Radius:
    """Consistent border-radius system."""
    
    SMALL = 8   # Inputs, checkboxes, small buttons
    MEDIUM = 12 # Cards, standard buttons, groups
    LARGE = 16  # Main containers, panels

def get_qss() -> str:
    """Generate Qt Style Sheet (QSS) for the synthwave theme."""
    
    qss = f"""
    /* === MAIN WINDOW & CENTRAL WIDGET === */
    QMainWindow {{
        background-color: {Colors.BACKGROUND};
        color: {Colors.TEXT_PRIMARY};
    }}
    
    QWidget {{
    
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
    
            /* === GROUP BOXES & CONTAINERS === */
        background-color: {Colors.BACKGROUND};
        color: {Colors.TEXT_PRIMARY};
    }}
    
    /* Group Boxes */
    QGroupBox {{
        background-color: {Colors.SURFACE_LIGHT};
        border: 1px solid {Colors.BORDER};
        border-radius: {Radius.MEDIUM}px;
        margin-top: 8px;
        padding-top: 12px;
        color: {Colors.TEXT_PRIMARY};
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0px 3px 0px 3px;
    
        QFrame {{
            color: {Colors.TEXT_PRIMARY};
        }}
    
        /* === BUTTONS === */
    }}
    
    /* Buttons - Primary */
    QPushButton {{
        background-color: {Colors.SURFACE};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: {Radius.SMALL}px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    
    QPushButton:hover {{
        background-color: {Colors.SURFACE_HOVER};
        border-color: {Colors.SECONDARY};
    }}
    
    QPushButton:pressed {{
        background-color: {Colors.SURFACE_FOCUS};
    
        QPushButton:focus {{
            border: 1px solid {Colors.SECONDARY};
            outline: none;
        }}
    }}
    
    QPushButton:disabled {{
        color: {Colors.TEXT_DISABLED};
            background-color: {Colors.SURFACE};
        border-color: {Colors.TEXT_DISABLED};
    }}
    
    /* Primary Action Button (Scrub) */
    #scrubBtn {{
        background-color: {Colors.PRIMARY};
        color: #ffffff;
        border: none;
        border-radius: {Radius.SMALL}px;
        font-weight: bold;
        padding: 10px 24px;
        font-size: 13px;
    }}
    
    #scrubBtn:hover {{
        background-color: {Colors.SECONDARY};
    }}
    
    #scrubBtn:pressed {{
    
            #scrubBtn:focus {{
                border: 2px solid {Colors.SECONDARY};
            }}
        background-color: {Colors.PRIMARY};
    }}
    
    #scrubBtn:disabled {{
        background-color: {Colors.TEXT_DISABLED};
            border: none;
    
            /* Toggle/Checkable Buttons */
            QPushButton:checked {{
                background-color: {Colors.PRIMARY};
                color: #ffffff;
                border-color: {Colors.PRIMARY};
            }}
    
            /* === TEXT INPUTS === */
        color: {Colors.TEXT_DISABLED};
    }}
    
    /* Line Edits */
    QLineEdit {{
        background-color: {Colors.SURFACE};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: {Radius.SMALL}px;
        padding: 8px 12px;
        selection-background-color: {Colors.PRIMARY};
        selection-color: #ffffff;
    }}
    
    QLineEdit:focus {{
        border: 2px solid {Colors.SECONDARY};
        background-color: {Colors.SURFACE_FOCUS};
        padding: 7px 11px;
    }}
    
    QLineEdit:disabled {{
    
            /* === LABELS === */
        background-color: {Colors.SURFACE};
        color: {Colors.TEXT_DISABLED};
        border-color: {Colors.TEXT_DISABLED};
    }}
    
    /* Labels */
    QLabel {{
        color: {Colors.TEXT_PRIMARY};
    }}
    
    QLabel#secondaryText {{
        color: {Colors.TEXT_SECONDARY};
    
        /* === CHECKBOXES & RADIO BUTTONS === */
    }}
    
    /* Checkboxes */
    QCheckBox {{
        color: {Colors.TEXT_SECONDARY};
        spacing: 6px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
    }}
    
    QCheckBox::indicator:unchecked {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
    }}
    
    QCheckBox::indicator:unchecked:hover {{
            background-color: {Colors.SURFACE_HOVER};
        border-color: {Colors.SECONDARY};
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {Colors.PRIMARY};
        border: 1px solid {Colors.PRIMARY};
    
        QCheckBox:focus {{
            outline: none;
        }}
    }}
    
    /* Radio Buttons & Toggle Buttons */
    QRadioButton {{
        color: {Colors.TEXT_SECONDARY};
        spacing: 6px;
    }}
    
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
    }}
    
    QRadioButton::indicator:unchecked {{
    
            QRadioButton::indicator:unchecked:hover {{
                border-color: {Colors.SECONDARY};
                background-color: {Colors.SURFACE_HOVER};
            }}
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
    }}
    
    QRadioButton::indicator:checked {{
    
            QRadioButton:focus {{
                outline: none;
            }}
        background-color: {Colors.PRIMARY};
        border: 1px solid {Colors.PRIMARY};
    }}
    
    /* === COMBO BOXES === */
    QComboBox {{
        background-color: {Colors.SURFACE};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: {Radius.SMALL}px;
        padding: 6px 12px;
        min-height: 24px;
    
        QComboBox:hover {{
            border-color: {Colors.SECONDARY};
        }}
    }}
    
    QComboBox:focus {{
        border: 2px solid {Colors.SECONDARY};
        background-color: {Colors.SURFACE_FOCUS};
        padding: 5px 11px;
    }}
    
    QComboBox::drop-down {{
        border-left: 1px solid {Colors.BORDER};
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        color: {Colors.TEXT_SECONDARY};
    }}
    
    QComboBox QAbstractItemView {{
            border-radius: {Radius.SMALL}px;
        background-color: {Colors.SURFACE_LIGHT};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        selection-background-color: {Colors.PRIMARY};
        selection-color: #ffffff;
    
        /* === PROGRESS BAR === */
    }}
    
    /* Progress Bar */
    QProgressBar {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: {Radius.SMALL}px;
        text-align: center;
        color: {Colors.TEXT_PRIMARY};
        height: 24px;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {Colors.PRIMARY},
            stop:1 {Colors.SECONDARY}
        );
        border-radius: 6px;
        margin: 1px;
    
        /* === TABLE VIEWS === */
    }}
    
    /* Table Views */
    QTableView {{
        background-color: {Colors.SURFACE};
        alternate-background-color: {Colors.SURFACE_LIGHT};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER};
        border-radius: {Radius.SMALL}px;
        gridline-color: {Colors.BORDER};
    }}
    
    QTableView::item {{
        padding: 6px;
    }}
    
    QTableView::item:selected {{
        background-color: {Colors.PRIMARY};
        color: #ffffff;
    }}
    
    QTableView::item:hover {{
            color: {Colors.TEXT_PRIMARY};
        background-color: {Colors.SURFACE_HOVER};
    }}
    
    QHeaderView::section {{
        background-color: {Colors.SURFACE_LIGHT};
        color: {Colors.TEXT_PRIMARY};
        padding: 8px;
        border: none;
        border-right: 1px solid {Colors.BORDER};
        border-bottom: 2px solid {Colors.PRIMARY};
    
        /* === SCROLLBARS === */
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: {Colors.BACKGROUND};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {Colors.SURFACE_LIGHT};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {Colors.SECONDARY};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none;
        background: none;
    }}
    
    QScrollBar:horizontal {{
        background-color: {Colors.BACKGROUND};
        height: 12px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: {Colors.SURFACE_LIGHT};
        border-radius: 6px;
        min-width: 20px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: {Colors.SECONDARY};
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none;
        background: none;
    }}
    
        /* === HEADER BAR === */
    
    #headerBar {{
        background-color: {Colors.SURFACE_LIGHT};
        border-bottom: 3px solid {Colors.PRIMARY};
    
        /* === STATUS BAR === */
    }}
    
    #statusBar {{
        background-color: {Colors.SURFACE};
        border-top: 2px solid {Colors.BORDER};
    
            /* === STATUS PILL === */
        color: {Colors.TEXT_SECONDARY};
    }}
    
    /* Status Pill */
    #statusPill {{
        background-color: {Colors.SURFACE};
        border-radius: 18px;
        padding: 4px 12px;
        font-weight: bold;
        font-size: 11px;
    }}
    
    #statusPill.idle {{
        border: 1px solid {Colors.TEXT_SECONDARY};
        color: {Colors.TEXT_SECONDARY};
    }}
    
    #statusPill.processing {{
        border: 2px solid {Colors.PRIMARY};
        color: {Colors.PRIMARY};
    }}
    
    #statusPill.success {{
        border: 2px solid {Colors.SUCCESS};
        color: {Colors.SUCCESS};
    }}
    
    #statusPill.error {{
        border: 2px solid {Colors.ERROR};
        color: {Colors.ERROR};
    }}
    """
    
    return qss


def apply_theme(app: QApplication) -> None:
    """Apply the synthwave theme to the application."""
    
    # Set application style
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Apply stylesheet
    app.setStyleSheet(get_qss())
    
    # Set default font
    font = QFont()
    font.setFamily("Segoe UI" if app.styleHints().colorScheme() else "San Francisco")
    font.setPointSize(10)
    app.setFont(font)
