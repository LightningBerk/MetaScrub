"""OOXML (Office document) metadata scrubber for DOCX, XLSX, PPTX."""

from pathlib import Path
import tempfile
import shutil
import zipfile
import os
import errno

from ..utils.result import ScrubResult, ResultType, ErrorCategory


class OOXMLScrubber:
    """Scrubs metadata from Office Open XML documents."""

    SUPPORTED_FORMATS = {'.docx', '.xlsx', '.pptx'}

    # Common metadata files in OOXML archives
    METADATA_FILES = {
        'docProps/core.xml',
        'docProps/app.xml',
        'docProps/custom.xml',
    }

    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        """Check if this scrubber can handle the file."""
        return file_path.suffix.lower() in cls.SUPPORTED_FORMATS

    @classmethod
    def scrub(cls, input_path: Path, output_path: Path) -> ScrubResult:
        """
        Scrub metadata from an OOXML document.

        Args:
            input_path: Source OOXML file
            output_path: Destination for cleaned document

        Returns:
            ScrubResult with operation outcome
        """
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

        tmp_output = None
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

            # Use a temporary directory for extraction
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                extract_dir = tmp_path / "extracted"
                extract_dir.mkdir()

                try:
                    # Extract the OOXML archive
                    with zipfile.ZipFile(input_path, 'r') as zip_in:
                        zip_in.extractall(extract_dir)

                except zipfile.BadZipFile:
                    return ScrubResult(
                        result_type=ResultType.ERROR,
                        input_path=input_path,
                        error="Not a valid Office document (corrupted or invalid ZIP)",
                        error_category=ErrorCategory.INPUT_ERROR,
                        fix_hint="Verify file is a valid DOCX/XLSX/PPTX or try opening it in Office first"
                    )

                # Track which metadata files were removed
                removed_files = []

                # Remove metadata files
                for metadata_file in cls.METADATA_FILES:
                    metadata_path = extract_dir / metadata_file
                    if metadata_path.exists():
                        metadata_path.unlink()
                        removed_files.append(metadata_file)

                # Create cleaned archive
                with tempfile.NamedTemporaryFile(delete=False, suffix=output_path.suffix, dir=output_path.parent) as tmp_out:
                    tmp_output = Path(tmp_out.name)

                try:
                    with zipfile.ZipFile(tmp_output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                        # Add all files except the removed metadata
                        for root, dirs, files in os.walk(extract_dir):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = file_path.relative_to(extract_dir)
                                zip_out.write(file_path, arcname)

                    # Atomic move to final destination
                    shutil.move(str(tmp_output), str(output_path))
                    tmp_output = None  # Successfully moved

                    metadata_desc = f"Office metadata files ({', '.join(removed_files)})" if removed_files else "no metadata files found"

                    return ScrubResult(
                        result_type=ResultType.SUCCESS,
                        input_path=input_path,
                        output_path=output_path,
                        metadata_removed=metadata_desc
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
            if tmp_output and tmp_output.exists():
                try:
                    tmp_output.unlink()
                except Exception:
                    pass  # Best effort cleanup
