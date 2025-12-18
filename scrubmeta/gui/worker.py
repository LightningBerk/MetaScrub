"""Background worker for running scrubbing without blocking the UI thread."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QObject, Signal

from ..core import CancelToken, ScrubCallbacks, scrub_path
from ..utils.result import ResultType, ScrubResult


class ScrubWorker(QObject):
    """Runs scrub operations in a background thread and emits UI-friendly signals."""

    progress = Signal(int, int)  # current, total
    status = Signal(str)
    result = Signal(dict)  # row data for the table
    finished = Signal(dict)  # summary dict
    error = Signal(str)
    started = Signal()

    def __init__(
        self,
        input_path: Path,
        output_dir: Path,
        recursive: bool,
        keep_structure: bool,
        overwrite: bool,
        dry_run: bool,
        ffmpeg_cmd: str,
    ) -> None:
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.recursive = recursive
        self.keep_structure = keep_structure
        self.overwrite = overwrite
        self.dry_run = dry_run
        self.ffmpeg_cmd = ffmpeg_cmd
        self.cancel_token = CancelToken()

    def request_cancel(self) -> None:
        """Signal the worker to cancel upcoming work."""
        self.cancel_token.cancel()

    def _to_row(self, result: ScrubResult) -> Dict[str, str]:
        """Convert a ScrubResult to a table-friendly dict."""
        message = result.metadata_removed or result.reason or result.error or ""
        output = str(result.output_path) if result.output_path else ""
        return {
            "status": result.result_type.value,
            "input": str(result.input_path),
            "output": output,
            "message": message,
        }

    def run(self) -> None:
        """Execute scrubbing and emit signals for UI consumption."""
        try:
            self.started.emit()
            self.status.emit("Scanning…")

            def on_scan_start(total: int) -> None:
                # Initialize progress bar bounds
                self.progress.emit(0, max(total, 1))

            def on_file_start(index: int, total: int, file_path: Path) -> None:
                self.status.emit(f"Scrubbing {index}/{total}: {file_path.name}")

            def on_file_result(res: ScrubResult) -> None:
                self.result.emit(self._to_row(res))

            def on_progress(current: int, total: int) -> None:
                self.progress.emit(current, total)

            callbacks = ScrubCallbacks(
                on_scan_start=on_scan_start,
                on_file_start=on_file_start,
                on_file_result=on_file_result,
                on_progress=on_progress,
                on_done=None,
            )

            _, summary = scrub_path(
                input_path=self.input_path,
                output_dir=self.output_dir,
                recursive=self.recursive,
                keep_structure=self.keep_structure,
                overwrite=self.overwrite,
                dry_run=self.dry_run,
                ffmpeg_cmd=self.ffmpeg_cmd,
                callbacks=callbacks,
                cancel_token=self.cancel_token,
            )

            summary_dict = {
                "total": summary.total,
                "success": summary.success,
                "skipped": summary.skipped,
                "errors": summary.errors,
                "cancelled": summary.cancelled,
            }

            status_text = "Cancelled" if summary.cancelled else "Done"
            self.status.emit(status_text)
            self.finished.emit(summary_dict)

        except Exception as exc:  # pylint: disable=broad-except
            self.error.emit(str(exc))
            self.status.emit("Error")
            self.finished.emit(
                {
                    "total": 0,
                    "success": 0,
                    "skipped": 0,
                    "errors": 1,
                    "cancelled": False,
                }
            )
