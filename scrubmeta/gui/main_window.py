"""Main window for the scrubmeta GUI."""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import List

from PySide6.QtCore import QCoreApplication, QSettings, Qt, QThread, QUrl, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve, QTimer
from PySide6.QtGui import QDesktopServices, QColor, QPainter, QRadialGradient, QIcon, QPixmap, QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTableView,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QScrollArea,
)

from .models import ResultFilterProxy, ResultsTableModel
from .worker import ScrubWorker
from .theme import Colors
from .stars_background import Star
import random


class StarsCentralWidget(QWidget):
    """Central widget that paints stars in background before rendering UI."""

    def __init__(self, stars: list[Star], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stars = stars

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        """Paint stars background, then let UI render."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Paint the background color first
        painter.fillRect(self.rect(), QColor(Colors.BACKGROUND))
        
        # Draw stars with prominent glow
        for star in self.stars:
            # Create radial gradient glow for each star
            glow_radius = star.radius * 8  # Larger glow area
            gradient = QRadialGradient(star.x, star.y, glow_radius)
            
            # Bright magenta core and purple glow
            core_color = QColor("#ff006e")  # Bright magenta like logo
            core_color.setAlphaF(star.current_opacity * 0.8)
            
            glow_color = QColor("#bb00dd")  # Purple glow
            glow_color.setAlphaF(star.current_opacity * 0.4)
            
            edge_color = QColor("#8800bb")
            edge_color.setAlphaF(star.current_opacity * 0.1)
            
            gradient.setColorAt(0.0, core_color)
            gradient.setColorAt(0.4, glow_color)
            gradient.setColorAt(1.0, edge_color)
            
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            # Draw larger star
            painter.drawEllipse(
                int(star.x - glow_radius),
                int(star.y - glow_radius),
                int(glow_radius * 2),
                int(glow_radius * 2),
            )
        
        painter.end()
        
        # Let parent class render UI widgets on top
        super().paintEvent(event)


class MainWindow(QMainWindow):
    """Primary application window with modern synthwave layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ScrubMeta")
        
        # Set window icon to crystal ball emoji
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setFont(QFont("Arial", 48))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔮")
        painter.end()
        self.setWindowIcon(QIcon(pixmap))
        
        self.setMinimumSize(1200, 700)
        QCoreApplication.setOrganizationName("scrubmeta")
        QCoreApplication.setApplicationName("ScrubMeta")

        self.settings = QSettings()
        self.thread: QThread | None = None
        self.worker: ScrubWorker | None = None
        
        # Initialize stars with deterministic seed only once
        random.seed(42)
        self.stars: list[Star] = []
        self._generate_stars_internal()
        # Now let random be truly random for drift
        random.seed()
        
        # Animation timer for stars - faster update for smooth motion
        self.stars_timer = QTimer()
        self.stars_timer.timeout.connect(self._update_stars)
        self.stars_timer.start(50)  # 50ms = 20 FPS for smooth animation

        self._build_ui()
        self._load_settings()
        self._update_action_state()

    # UI construction
    def _build_ui(self) -> None:
        """Build the main UI with header, two-column layout, and status bar."""
        
        # Create central widget with stars background painting
        central = StarsCentralWidget(self.stars)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar
        main_layout.addWidget(self._build_header_bar())

        # Main content area (two-column split)
        main_layout.addWidget(self._build_content_area(), 1)

        # Status bar
        main_layout.addWidget(self._build_status_bar())

        central.setLayout(main_layout)
        self.setCentralWidget(central)
        
        # Store reference for updates
        self.central_widget = central

    def _build_header_bar(self) -> QWidget:
        """Build the header bar with animated logo, title and status pill."""
        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(70)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(16)

        # Animated logo section
        logo_label = QLabel("🔮")
        logo_label.setObjectName("animatedLogo")
        logo_label.setStyleSheet(f"""
            QLabel#animatedLogo {{
                font-size: 48px;
                color: {Colors.PRIMARY};
            }}
        """)
        logo_label.setMinimumSize(60, 60)
        logo_label.setAlignment(Qt.AlignCenter)
        
        # Apply pulsing animation
        self._animate_logo(logo_label)

        # Title section
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)  # Tight spacing between title and subtitle
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("ScrubMeta")
        title_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {Colors.PRIMARY}; line-height: 1.0;")
        subtitle_label = QLabel("Remove metadata safely — single or batch")
        subtitle_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        layout.addWidget(logo_label, 0)
        layout.addLayout(title_layout, 1)

        # Status pill
        self.status_pill = QLabel("Ready")
        self.status_pill.setObjectName("statusPill")
        self.status_pill.setObjectName("statusPill idle")
        self.status_pill.setStyleSheet(f"""
            background-color: rgba(61, 0, 102, 0.6);
            border: 1px solid {Colors.TEXT_SECONDARY};
            border-radius: 16px;
            padding: 6px 14px;
            color: {Colors.TEXT_SECONDARY};
            font-weight: bold;
            font-size: 10px;
        """)

        layout.addWidget(self.status_pill, 0, Qt.AlignRight | Qt.AlignCenter)

        header.setLayout(layout)
        return header

    def _animate_logo(self, logo: QLabel) -> None:
        """Apply pulsing purple glow effect to the logo."""
        # Create a glowing shadow effect and store as instance variable
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(5)
        self.glow_effect.setXOffset(0)
        self.glow_effect.setYOffset(0)
        self.glow_effect.setColor(QColor("#ff006e"))  # Magenta glow
        logo.setGraphicsEffect(self.glow_effect)
        
        # Animate the blur radius to create pulsing glow
        self.glow_animation_in = QPropertyAnimation(self.glow_effect, b"blurRadius")
        self.glow_animation_in.setDuration(1500)
        self.glow_animation_in.setStartValue(5)
        self.glow_animation_in.setEndValue(30)
        self.glow_animation_in.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.glow_animation_out = QPropertyAnimation(self.glow_effect, b"blurRadius")
        self.glow_animation_out.setDuration(1500)
        self.glow_animation_out.setStartValue(30)
        self.glow_animation_out.setEndValue(5)
        self.glow_animation_out.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Create looping sequence
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(self.glow_animation_in)
        self.animation_group.addAnimation(self.glow_animation_out)
        self.animation_group.setLoopCount(-1)
        self.animation_group.start()

    def _build_content_area(self) -> QWidget:
        """Build the two-column main content area."""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 16, 16, 0)
        layout.setSpacing(16)

        # Left column: Configuration
        left_column = self._build_left_column()
        
        # Right column: Results and Progress
        right_column = self._build_right_column()

        # Use splitter for resizable columns
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_column)
        splitter.addWidget(right_column)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)
        container.setLayout(layout)
        return container

    def _build_left_column(self) -> QWidget:
        """Build the left configuration panel."""
        container = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addWidget(self._build_input_group())
        layout.addWidget(self._build_output_group())
        layout.addWidget(self._build_options_group())
        layout.addLayout(self._build_actions_row())
        layout.addStretch()

        container.setLayout(layout)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        return scroll

    def _build_right_column(self) -> QWidget:
        """Build the right results and progress panel."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        layout.addLayout(self._build_progress_row())
        layout.addWidget(self._build_results_panel(), 1)

        container.setLayout(layout)
        return container

    def _build_status_bar(self) -> QWidget:
        """Build the bottom status bar."""
        bar = QWidget()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(40)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 8, 24, 8)
        layout.setSpacing(12)

        self.summary_label = QLabel("Ready")
        self.summary_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        
        layout.addWidget(self.summary_label, 1)

        bar.setLayout(layout)
        return bar

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox("Input")
        form = QFormLayout()

        # Single picker button (auto-detects file vs folder)
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setReadOnly(True)
        self.input_path_edit.setPlaceholderText("Choose a file or folder…")
        self.input_path_edit.setMinimumHeight(32)

        self.pick_input_btn = QPushButton("📂 Select File/Folder")
        self.pick_input_btn.setMinimumHeight(32)

        pick_row = QHBoxLayout()
        pick_row.addWidget(self.pick_input_btn)

        form.addRow("Select", pick_row)
        form.addRow(self.input_path_edit)

        group.setLayout(form)

        # Connection
        self.pick_input_btn.clicked.connect(self._pick_input)

        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox("Output Destination")
        form = QFormLayout()

        self.output_path_edit = QLineEdit()
        self.output_path_edit.setReadOnly(True)
        self.output_path_edit.setPlaceholderText("Choose an output folder…")
        self.output_path_edit.setMinimumHeight(32)

        self.pick_output_btn = QPushButton("📂 Select Output")
        self.pick_output_btn.setMinimumHeight(32)
        pick_row = QHBoxLayout()
        pick_row.addWidget(self.pick_output_btn)

        form.addRow("Destination", pick_row)
        form.addRow(self.output_path_edit)

        group.setLayout(form)

        self.pick_output_btn.clicked.connect(self._pick_output_folder)

        return group

    def _build_options_group(self) -> QGroupBox:
        group = QGroupBox("Options")
        layout = QVBoxLayout()

        # Checkboxes in compact grid
        checks_row = QVBoxLayout()
        self.recursive_cb = QCheckBox("Recursive (include subfolders)")
        self.keep_structure_cb = QCheckBox("Keep folder structure")
        self.overwrite_cb = QCheckBox("Overwrite existing outputs")
        self.dry_run_cb = QCheckBox("Dry run (preview only)")

        checks_row.addWidget(self.recursive_cb)
        checks_row.addWidget(self.keep_structure_cb)
        checks_row.addWidget(self.overwrite_cb)
        checks_row.addWidget(self.dry_run_cb)

        layout.addLayout(checks_row)

        # ffmpeg path
        ffmpeg_row = QHBoxLayout()
        self.ffmpeg_path_edit = QLineEdit()
        self.ffmpeg_path_edit.setPlaceholderText("ffmpeg (from PATH)")
        self.ffmpeg_path_edit.setReadOnly(True)
        self.ffmpeg_path_edit.setMinimumHeight(28)
        ffmpeg_btn = QPushButton("🎬 ffmpeg")
        ffmpeg_btn.setMinimumHeight(28)
        ffmpeg_row.addWidget(ffmpeg_btn, 0)
        ffmpeg_row.addWidget(self.ffmpeg_path_edit, 1)

        ffmpeg_label = QLabel("Audio/Video")
        ffmpeg_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 10px;")
        
        layout.addWidget(ffmpeg_label)
        layout.addLayout(ffmpeg_row)

        group.setLayout(layout)

        self.recursive_cb.stateChanged.connect(self._update_action_state)
        self.keep_structure_cb.stateChanged.connect(self._update_action_state)
        self.overwrite_cb.stateChanged.connect(self._update_action_state)
        self.dry_run_cb.stateChanged.connect(self._update_action_state)

        ffmpeg_btn.clicked.connect(self._pick_ffmpeg)

        return group

    def _build_actions_row(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self.scrub_btn = QPushButton("✨ Scrub Metadata")
        self.scrub_btn.setObjectName("scrubBtn")
        self.scrub_btn.setMinimumHeight(40)
        self.scrub_btn.setMinimumWidth(200)
        self.scrub_btn.setDefault(True)
        
        self.cancel_btn = QPushButton("⏹ Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)
        
        self.open_output_btn = QPushButton("📂 Open Output")
        self.open_output_btn.setMinimumHeight(40)

        row.addWidget(self.scrub_btn)
        row.addWidget(self.cancel_btn)
        row.addWidget(self.open_output_btn)
        row.addStretch()

        self.scrub_btn.clicked.connect(self._start_scrub)
        self.cancel_btn.clicked.connect(self._request_cancel)
        self.open_output_btn.clicked.connect(self._open_output_folder)

        return row

    def _build_progress_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        
        # Current file and status
        info_layout = QVBoxLayout()
        self.current_file_label = QLabel("Idle")
        self.current_file_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 10px;")
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(1)
        self.progress.setValue(0)
        self.progress.setMinimumHeight(24)
        
        info_layout.addWidget(self.current_file_label)
        info_layout.addWidget(self.progress)
        
        row.addLayout(info_layout)
        
        return row

    def _build_results_panel(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Control bar
        controls_row = QHBoxLayout()
        
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 11px;")
        controls_row.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "SUCCESS", "SKIP", "ERROR"])
        self.filter_combo.setMaximumWidth(120)
        controls_row.addWidget(self.filter_combo)
        
        controls_row.addStretch()

        self.copy_log_btn = QPushButton("📋 Copy")
        self.copy_log_btn.setMaximumWidth(100)
        self.export_btn = QPushButton("💾 Export")
        self.export_btn.setMaximumWidth(100)
        self.clear_btn = QPushButton("🗑 Clear")
        self.clear_btn.setMaximumWidth(100)

        controls_row.addWidget(self.copy_log_btn)
        controls_row.addWidget(self.export_btn)
        controls_row.addWidget(self.clear_btn)

        layout.addLayout(controls_row)

        # Results table
        self.results_model = ResultsTableModel()
        self.results_proxy = ResultFilterProxy()
        self.results_proxy.setSourceModel(self.results_model)

        self.results_view = QTableView()
        self.results_view.setModel(self.results_proxy)
        self.results_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_view.setSelectionBehavior(QTableView.SelectRows)
        self.results_view.setAlternatingRowColors(True)
        self.results_view.setEditTriggers(QTableView.NoEditTriggers)
        self.results_view.setMinimumHeight(200)

        layout.addWidget(self.results_view, 1)
        container.setLayout(layout)

        # Connections
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self.copy_log_btn.clicked.connect(self._copy_log)
        self.export_btn.clicked.connect(self._export_report)
        self.clear_btn.clicked.connect(self._clear_results)

        return container

    # Input picker (auto-detects file vs folder)
    def _pick_input(self) -> None:
        """Open file/folder picker dialog."""
        path = QFileDialog.getExistingDirectory(self, "Select file or folder to scrub")
        if path:
            self.input_path_edit.setText(path)
            self._update_input_options()
            self._update_action_state()

    def _update_input_options(self) -> None:
        """Update recursive/structure options based on input type."""
        input_path = self._input_path()
        is_folder = input_path and input_path.is_dir()
        
        self.recursive_cb.setEnabled(is_folder)
        self.keep_structure_cb.setEnabled(is_folder)
        
        if not is_folder:
            self.recursive_cb.setChecked(False)
            self.keep_structure_cb.setChecked(False)

    def _pick_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select output folder")
        if path:
            self.output_path_edit.setText(path)
        self._update_action_state()

    def _pick_ffmpeg(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select ffmpeg binary")
        if path:
            self.ffmpeg_path_edit.setText(path)

    # Validation helpers
    def _input_path(self) -> Path | None:
        text = self.input_path_edit.text().strip()
        return Path(text) if text else None

    def _output_path(self) -> Path | None:
        text = self.output_path_edit.text().strip()
        return Path(text) if text else None

    def _is_valid(self) -> bool:
        input_path = self._input_path()
        output_path = self._output_path()
        if not input_path or not input_path.exists():
            return False
        if not output_path:
            return False
        return True

    def _update_action_state(self) -> None:
        self.scrub_btn.setEnabled(self._is_valid())
        self.open_output_btn.setEnabled(bool(self.output_path_edit.text().strip()))

    # Scrubbing lifecycle
    def _start_scrub(self) -> None:
        if not self._is_valid():
            QMessageBox.warning(self, "Invalid selection", "Please select a valid input and output")
            return

        input_path = self._input_path()
        output_path = self._output_path()
        assert input_path is not None
        assert output_path is not None

        # Prevent accidental overwrite of input
        if input_path.resolve() == output_path.resolve():
            confirm = QMessageBox.warning(
                self,
                "Output matches input",
                "Output folder matches input. This tool never modifies originals but writing into the same folder is discouraged. Continue?",
                QMessageBox.Yes | QMessageBox.Cancel,
            )
            if confirm != QMessageBox.Yes:
                return

        output_path.mkdir(parents=True, exist_ok=True)

        recursive = self.recursive_cb.isChecked()
        keep_structure = self.keep_structure_cb.isChecked()
        overwrite = self.overwrite_cb.isChecked()
        dry_run = self.dry_run_cb.isChecked()
        ffmpeg_cmd = self.ffmpeg_path_edit.text().strip() or "ffmpeg"

        # Set up worker thread
        self.thread = QThread()
        self.worker = ScrubWorker(
            input_path=input_path,
            output_dir=output_path,
            recursive=recursive,
            keep_structure=keep_structure,
            overwrite=overwrite,
            dry_run=dry_run,
            ffmpeg_cmd=ffmpeg_cmd,
        )
        self.worker.moveToThread(self.thread)

        # Wire signals
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.status.connect(self._on_status)
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.started.connect(self._on_worker_started)
        self.thread.finished.connect(self.thread.deleteLater)

        # Start
        self.thread.start()

    def _on_worker_started(self) -> None:
        self._update_status_pill("Processing…", "processing")
        self.current_file_label.setText("Scanning files…")
        self.progress.setMaximum(0)  # indeterminate until scan emits
        self.progress.setValue(0)
        self.scrub_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def _request_cancel(self) -> None:
        if self.worker:
            self.worker.request_cancel()
            self.current_file_label.setText("Cancelling…")
            self.cancel_btn.setEnabled(False)

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        percent = int((current / total * 100)) if total > 0 else 0
        self.current_file_label.setText(f"Progress: {current}/{total} ({percent}%)")

    def _on_status(self, text: str) -> None:
        self.current_file_label.setText(text)

    def _on_result(self, row: dict) -> None:
        self.results_model.append_row(row)

    def _on_finished(self, summary: dict) -> None:
        self.scrub_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress.setMaximum(1)
        self.progress.setValue(0)

        if self.thread:
            self.thread.quit()
            self.thread.wait()
            self.thread = None
            self.worker = None

        # Update status pill and summary
        if summary.get("cancelled"):
            self._update_status_pill("Cancelled", "error")
            msg_text = "Scrub was cancelled"
        elif summary.get("errors", 0) > 0:
            self._update_status_pill("Done (Errors)", "error")
            msg_text = f"Complete with errors: {summary.get('errors')} failed"
        else:
            self._update_status_pill("Success", "success")
            msg_text = f"Successfully scrubbed {summary.get('success')} files"

        self.current_file_label.setText(msg_text)
        self.summary_label.setText(
            f"Total: {summary.get('total')} | Success: {summary.get('success')} | "
            f"Skipped: {summary.get('skipped')} | Errors: {summary.get('errors')}"
        )

        # Show completion dialog
        msg = QMessageBox(self)
        msg.setWindowTitle("Scrub Complete" if not summary.get("cancelled") else "Scrub Cancelled")
        msg.setIcon(QMessageBox.Information if not summary.get("errors") else QMessageBox.Warning)
        msg.setText(
            "Total: {total}\nSuccess: {success}\nSkipped: {skipped}\nErrors: {errors}".format(**summary)
        )
        msg.addButton("OK", QMessageBox.AcceptRole)
        open_btn = msg.addButton("📂 Open Output", QMessageBox.ActionRole)
        msg.exec()
        if msg.clickedButton() == open_btn:
            self._open_output_folder()

    def _on_error(self, message: str) -> None:
        self._update_status_pill("Error", "error")
        QMessageBox.critical(self, "Error", message)

    def _update_status_pill(self, text: str, status: str) -> None:
        """Update the status pill with text and style class."""
        self.status_pill.setText(text)
        style = f"""
            background-color: rgba(61, 0, 102, 0.6);
            border-radius: 16px;
            padding: 6px 14px;
            font-weight: bold;
            font-size: 10px;
        """
        
        if status == "idle":
            style += f"border: 1px solid {Colors.TEXT_SECONDARY}; color: {Colors.TEXT_SECONDARY};"
        elif status == "processing":
            style += f"border: 1px solid {Colors.PRIMARY}; color: {Colors.PRIMARY};"
        elif status == "success":
            style += f"border: 1px solid {Colors.SUCCESS}; color: {Colors.SUCCESS};"
        elif status == "error":
            style += f"border: 1px solid {Colors.ERROR}; color: {Colors.ERROR};"
        
        self.status_pill.setStyleSheet(style)

    # Results helpers
    def _on_filter_changed(self, status: str) -> None:
        self.results_proxy.set_status_filter(status)

    def _copy_log(self) -> None:
        rows = self.results_model.rows()
        if not rows:
            return
        lines = [
            f"{r['status']} | {r['input']} -> {r['output']} | {r['message']}" for r in rows
        ]
        QApplication.clipboard().setText("\n".join(lines))

    def _export_report(self) -> None:
        if not self.results_model.rows():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export report",
            "scrubmeta_report.csv",
            "CSV Files (*.csv);;JSON Files (*.json)",
        )
        if not path:
            return
        rows = self.results_model.rows()
        if path.lower().endswith(".json"):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2)
        else:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["status", "input", "output", "message"])
                writer.writeheader()
                writer.writerows(rows)

    def _clear_results(self) -> None:
        self.results_model.clear()

    def _open_output_folder(self) -> None:
        output_path = self._output_path()
        if output_path and output_path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_path)))

    # Settings persistence
    def _load_settings(self) -> None:
        output = self.settings.value("output_path", "")
        if output:
            self.output_path_edit.setText(output)

        self.recursive_cb.setChecked(self.settings.value("recursive", False, bool))
        self.keep_structure_cb.setChecked(self.settings.value("keep_structure", False, bool))
        self.overwrite_cb.setChecked(self.settings.value("overwrite", False, bool))
        self.dry_run_cb.setChecked(self.settings.value("dry_run", False, bool))
        self.ffmpeg_path_edit.setText(self.settings.value("ffmpeg_path", ""))

    def _save_settings(self) -> None:
        self.settings.setValue("output_path", self.output_path_edit.text())
        self.settings.setValue("recursive", self.recursive_cb.isChecked())
        self.settings.setValue("keep_structure", self.keep_structure_cb.isChecked())
        self.settings.setValue("overwrite", self.overwrite_cb.isChecked())
        self.settings.setValue("dry_run", self.dry_run_cb.isChecked())
        self.settings.setValue("ffmpeg_path", self.ffmpeg_path_edit.text())

    def showEvent(self, event) -> None:  # type: ignore[override]
        """Regenerate stars after window is shown with proper size."""
        super().showEvent(event)
        self._generate_stars()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._save_settings()
        if self.thread and self.thread.isRunning():
            self._request_cancel()
            self.thread.quit()
            self.thread.wait(2000)
        super().closeEvent(event)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Regenerate stars on window resize."""
        super().resizeEvent(event)
        self._generate_stars()

    def _generate_stars_internal(self) -> None:
        """Generate initial star field (called during init with seed)."""
        # Use actual window dimensions when available
        if self.geometry().isValid():
            width = max(self.width(), 1200)
            height = max(self.height(), 700)
        else:
            width = 1200
            height = 700
        
        # More stars, more visible
        star_count = max(60, min(150, (width * height) // 10000))
        
        self.stars = [
            Star(
                x=random.uniform(0, width),
                y=random.uniform(0, height),
                radius=random.uniform(2.5, 5.0),
                base_opacity=random.uniform(0.15, 0.35),
                width=float(width),
                height=float(height),
            )
            for _ in range(star_count)
        ]

    def _generate_stars(self) -> None:
        """Regenerate star field on resize (no seed - allows drift)."""
        # Use actual window dimensions when available
        if self.geometry().isValid():
            width = max(self.width(), 1200)
            height = max(self.height(), 700)
        else:
            width = 1200
            height = 700
        
        # Update existing stars' boundaries
        for star in self.stars:
            star.width = float(width)
            star.height = float(height)

    def _update_stars(self) -> None:
        """Update star opacity and request repaint."""
        for star in self.stars:
            star.update()
        # Force repaint of central widget
        self.update()
