"""Core scrubbing API shared by CLI and GUI."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .scrubbers import ImageScrubber, PDFScrubber, OOXMLScrubber, MediaScrubber
from .utils.file_utils import FileDiscovery, OutputManager
from .utils.result import ResultType, ScrubResult, ErrorCategory


@dataclass
class ScrubCallbacks:
    """Optional callbacks invoked during scrubbing."""

    on_scan_start: Optional[Callable[[int], None]] = None
    on_file_start: Optional[Callable[[int, int, Path], None]] = None
    on_file_result: Optional[Callable[[ScrubResult], None]] = None
    on_progress: Optional[Callable[[int, int], None]] = None
    on_done: Optional[Callable[["ScrubSummary"], None]] = None


class CancelToken:
    """Cooperative cancellation token checked between file operations."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation."""
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        """Return whether cancellation was requested."""
        return self._cancelled


@dataclass
class ScrubSummary:
    """Aggregate summary for a scrubbing run."""

    total: int
    success: int
    skipped: int
    errors: int
    cancelled: bool


class CoreScrubber:
    """Main scrubbing orchestrator for reusable core logic."""

    def __init__(self, ffmpeg_cmd: str = "ffmpeg") -> None:
        self.scrubbers = [
            ImageScrubber,
            PDFScrubber,
            OOXMLScrubber,
            MediaScrubber,
        ]
        self.ffmpeg_cmd = ffmpeg_cmd

    def scrub_file(self, input_path: Path, output_path: Path) -> ScrubResult:
        """Find the appropriate scrubber for a single file and run it."""
        # Handle MediaScrubber separately since it needs the ffmpeg_cmd argument
        if MediaScrubber.can_handle(input_path):
            return MediaScrubber.scrub(input_path, output_path, ffmpeg_cmd=self.ffmpeg_cmd)

        # Try other scrubbers (they don't need special arguments)
        for scrubber_class in [ImageScrubber, PDFScrubber, OOXMLScrubber]:
            if scrubber_class.can_handle(input_path):
                return scrubber_class.scrub(input_path, output_path)

        return ScrubResult(
            result_type=ResultType.SKIP,
            input_path=input_path,
            reason=f"Unsupported file type: {input_path.suffix}",
        )

    def _make_error_response(
        self,
        input_path: Path,
        error: str,
        error_category: ErrorCategory,
        fix_hint: str,
        callbacks: ScrubCallbacks,
    ) -> Tuple[List[ScrubResult], ScrubSummary]:
        """Create an error response with a single error result."""
        error_result = ScrubResult(
            result_type=ResultType.ERROR,
            input_path=input_path,
            error=error,
            error_category=error_category,
            fix_hint=fix_hint
        )
        summary = ScrubSummary(total=0, success=0, skipped=0, errors=1, cancelled=False)
        if callbacks.on_file_result:
            callbacks.on_file_result(error_result)
        if callbacks.on_done:
            callbacks.on_done(summary)
        return [error_result], summary

    def _process_files(
        self,
        files: List[Path],
        output_manager: OutputManager,
        base_input_dir: Path,
        dry_run: bool,
        callbacks: ScrubCallbacks,
        cancel_token: CancelToken,
    ) -> Tuple[List[ScrubResult], ScrubSummary]:
        """Process all discovered files and return results with summary."""
        results: List[ScrubResult] = []
        success = skipped = errors = 0
        cancelled = False
        total = len(files)

        for index, file_path in enumerate(files, start=1):
            if cancel_token.cancelled:
                cancelled = True
                break

            if callbacks.on_file_start:
                callbacks.on_file_start(index, total, file_path)

            output_path = output_manager.get_output_path(file_path, base_input_dir)

            if dry_run:
                result = ScrubResult(
                    result_type=ResultType.SKIP,
                    input_path=file_path,
                    output_path=output_path,
                    reason="dry-run (no changes written)",
                )
            else:
                result = self.scrub_file(file_path, output_path)

            results.append(result)

            if result.result_type == ResultType.SUCCESS:
                success += 1
            elif result.result_type == ResultType.SKIP:
                skipped += 1
            else:
                errors += 1

            if callbacks.on_file_result:
                callbacks.on_file_result(result)

            if callbacks.on_progress:
                callbacks.on_progress(index, total)

        # Mark remaining as skipped if cancelled mid-run
        if cancelled and len(results) < total:
            skipped += total - len(results)

        summary = ScrubSummary(
            total=total,
            success=success,
            skipped=skipped,
            errors=errors,
            cancelled=cancelled,
        )

        if callbacks.on_done:
            callbacks.on_done(summary)

        return results, summary

    def scrub_path(
        self,
        input_path: Path,
        output_dir: Path,
        recursive: bool = False,
        keep_structure: bool = False,
        overwrite: bool = False,
        dry_run: bool = False,
        callbacks: Optional[ScrubCallbacks] = None,
        cancel_token: Optional[CancelToken] = None,
    ) -> Tuple[List[ScrubResult], ScrubSummary]:
        """
        Scrub metadata from a path (file or directory).

        Args:
            input_path: Source file or directory
            output_dir: Destination directory for cleaned files
            recursive: Recurse into subdirectories when input is a directory
            keep_structure: Preserve directory structure relative to input
            overwrite: Allow overwriting existing outputs
            dry_run: Simulate run without writing files
            callbacks: Optional callbacks for progress and results
            cancel_token: Cancellation token, checked between files

        Returns:
            (list of results, summary)
        """
        callbacks = callbacks or ScrubCallbacks()
        cancel_token = cancel_token or CancelToken()

        # Validate input path exists
        if not input_path.exists():
            return self._make_error_response(
                input_path, "Input path does not exist",
                ErrorCategory.INPUT_ERROR, "Verify the path is correct", callbacks
            )

        # Validate read permissions
        if not os.access(input_path, os.R_OK):
            return self._make_error_response(
                input_path, "Cannot read input path (permission denied)",
                ErrorCategory.PERMISSION_ERROR,
                "Check permissions or run with appropriate privileges", callbacks
            )

        # Discover files
        try:
            files = FileDiscovery.discover_files(input_path, recursive)
        except OSError as e:
            return self._make_error_response(
                input_path, f"Failed to scan directory: {type(e).__name__}: {e}",
                ErrorCategory.INPUT_ERROR,
                "Verify the path is valid and accessible", callbacks
            )

        if callbacks.on_scan_start:
            callbacks.on_scan_start(len(files))

        output_manager = OutputManager(output_dir, overwrite, keep_structure)
        base_input_dir = input_path if input_path.is_dir() else input_path.parent

        return self._process_files(
            files, output_manager, base_input_dir, dry_run, callbacks, cancel_token
        )


def scrub_path(
    input_path: Path,
    output_dir: Path,
    recursive: bool = False,
    keep_structure: bool = False,
    overwrite: bool = False,
    dry_run: bool = False,
    ffmpeg_cmd: str = "ffmpeg",
    callbacks: Optional[ScrubCallbacks] = None,
    cancel_token: Optional[CancelToken] = None,
) -> Tuple[List[ScrubResult], ScrubSummary]:
    """Convenience function to run scrubbing with the core orchestrator."""
    scrubber = CoreScrubber(ffmpeg_cmd=ffmpeg_cmd)
    return scrubber.scrub_path(
        input_path=input_path,
        output_dir=output_dir,
        recursive=recursive,
        keep_structure=keep_structure,
        overwrite=overwrite,
        dry_run=dry_run,
        callbacks=callbacks,
        cancel_token=cancel_token,
    )
