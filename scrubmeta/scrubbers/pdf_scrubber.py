"""PDF metadata scrubber."""

from pathlib import Path
import tempfile
import shutil
import os
import errno

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False

from ..utils.result import ScrubResult, ResultType, ErrorCategory


class PDFScrubber:
    """Scrubs metadata from PDF files."""

    SUPPORTED_FORMATS = {'.pdf'}

    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        """Check if this scrubber can handle the file."""
        return file_path.suffix.lower() in cls.SUPPORTED_FORMATS

    @classmethod
    def scrub(cls, input_path: Path, output_path: Path) -> ScrubResult:
        """
        Scrub metadata from a PDF file.

        Args:
            input_path: Source PDF file
            output_path: Destination for cleaned PDF

        Returns:
            ScrubResult with operation outcome
        """
        if not PIKEPDF_AVAILABLE:
            return ScrubResult(
                result_type=ResultType.SKIP,
                input_path=input_path,
                reason="pikepdf not installed (required for PDF scrubbing)",
                error_category=ErrorCategory.DEPENDENCY_ERROR,
                fix_hint="Install pikepdf: pip install pikepdf>=8.0.0"
            )

        # Validate input
        if not input_path.exists():
            return ScrubResult(
                result_type=ResultType.ERROR,
                input_path=input_path,
                error="File not found",
                error_category=ErrorCategory.INPUT_ERROR,
                fix_hint="Verify the file path is correct"
            )

        if not os.access(input_path, os.R_OK):
            return ScrubResult(
                result_type=ResultType.ERROR,
                input_path=input_path,
                error="Cannot read file (permission denied)",
                error_category=ErrorCategory.PERMISSION_ERROR,
                fix_hint="Check file permissions or run with appropriate privileges"
            )

        tmp_path = None
        try:
            # Validate output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if not os.access(output_path.parent, os.W_OK):
                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error="Cannot write to output directory (permission denied)",
                    error_category=ErrorCategory.PERMISSION_ERROR,
                    fix_hint=f"Check write permissions for: {output_path.parent}"
                )

            # Use a temporary file to ensure atomic writes
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=output_path.parent) as tmp:
                tmp_path = Path(tmp.name)

            try:
                # Open PDF and remove metadata
                with pikepdf.open(input_path, allow_overwriting_input=False) as pdf:
                    # Remove document info dictionary
                    if pdf.docinfo:
                        metadata_fields = list(pdf.docinfo.keys())
                        for key in metadata_fields:
                            del pdf.docinfo[key]

                    # Remove XMP metadata if present
                    with pdf.open_metadata() as meta:
                        meta.clear()

                    # Save cleaned PDF
                    pdf.save(tmp_path)

                # Atomic move to final destination
                shutil.move(str(tmp_path), str(output_path))
                tmp_path = None  # Successfully moved

                return ScrubResult(
                    result_type=ResultType.SUCCESS,
                    input_path=input_path,
                    output_path=output_path,
                    metadata_removed="PDF document info and XMP metadata"
                )

            except pikepdf.PasswordError:
                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error="PDF is password-protected",
                    error_category=ErrorCategory.INPUT_ERROR,
                    fix_hint="Decrypt the PDF first before scrubbing metadata"
                )

            except pikepdf.PdfError as e:
                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error=f"Invalid or corrupted PDF: {e}",
                    error_category=ErrorCategory.INPUT_ERROR,
                    fix_hint="Verify file is a valid PDF or try repairing it first"
                )

            except OSError as e:
                if e.errno == errno.ENOSPC:
                    error_msg = "No space left on device"
                    hint = "Free up disk space on the output drive"
                elif e.errno == errno.EROFS:
                    error_msg = "Output filesystem is read-only"
                    hint = "Choose a writable output location"
                else:
                    error_msg = f"I/O error: {e}"
                    hint = "Check filesystem and disk health"

                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error=error_msg,
                    error_category=ErrorCategory.OUTPUT_ERROR,
                    fix_hint=hint
                )

            except Exception as e:
                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error=f"Unexpected error: {type(e).__name__}: {e}",
                    error_category=ErrorCategory.PROCESSING_ERROR,
                    fix_hint="Report this error if it persists"
                )

        finally:
            # Ensure temp file cleanup
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass  # Best effort cleanup
