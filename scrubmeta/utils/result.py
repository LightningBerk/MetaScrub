"""Result tracking for scrubbing operations."""

from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ResultType(Enum):
    """Type of scrubbing result."""
    SUCCESS = "SUCCESS"
    SKIP = "SKIP"
    ERROR = "ERROR"


class ErrorCategory(Enum):
    """Standard error categories for consistent error handling."""
    INPUT_ERROR = "input_error"  # Invalid paths, missing files, unsupported types
    PERMISSION_ERROR = "permission_error"  # Cannot read/write file or folder
    DEPENDENCY_ERROR = "dependency_error"  # Optional library missing
    PROCESSING_ERROR = "processing_error"  # Scrubber failed on file
    OUTPUT_ERROR = "output_error"  # Temp write, rename, overwrite collision
    CANCELLED = "cancelled"  # User-initiated stop


@dataclass
class ScrubResult:
    """Result of a single file scrubbing operation."""
    result_type: ResultType
    input_path: Path
    output_path: Optional[Path] = None
    metadata_removed: Optional[str] = None
    reason: Optional[str] = None
    error: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    fix_hint: Optional[str] = None

    def format_line(self) -> str:
        """Format result as a single line for output."""
        if self.result_type == ResultType.SUCCESS:
            removed = self.metadata_removed or "unknown metadata"
            return f"SUCCESS | {self.input_path} -> {self.output_path} | removed: {removed}"
        elif self.result_type == ResultType.SKIP:
            return f"SKIP | {self.input_path} | {self.reason or 'unknown reason'}"
        else:  # ERROR
            error_msg = f"ERROR | {self.input_path} | {self.error or 'unknown error'}"
            if self.fix_hint:
                error_msg += f"\n  Fix: {self.fix_hint}"
            return error_msg
