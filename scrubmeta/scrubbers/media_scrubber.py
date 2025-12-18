"""Media metadata scrubber for audio and video files using ffmpeg."""

from pathlib import Path
import errno
import os
import shutil
import subprocess
import tempfile

from ..utils.result import ScrubResult, ResultType, ErrorCategory


class MediaScrubber:
    """Scrubs metadata from audio and video files using ffmpeg."""

    SUPPORTED_FORMATS = {
        # Video
        ".mp4",
        ".mov",
        ".mkv",
        ".avi",
        ".m4v",
        ".webm",
        ".mpg",
        ".mpeg",
        # Audio
        ".mp3",
        ".wav",
        ".flac",
        ".m4a",
        ".aac",
        ".ogg",
        ".opus",
    }

    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        """Check if this scrubber can handle the file."""
        return file_path.suffix.lower() in cls.SUPPORTED_FORMATS

    @staticmethod
    def _ffmpeg_available(cmd: str) -> bool:
        """Check if ffmpeg binary is available via provided command."""
        return shutil.which(cmd) is not None

    @classmethod
    def scrub(cls, input_path: Path, output_path: Path, ffmpeg_cmd: str = "ffmpeg") -> ScrubResult:
        """
        Scrub metadata from an audio or video file using ffmpeg.

        Args:
            input_path: Source media file
            output_path: Destination for cleaned media
            ffmpeg_cmd: Path or command for ffmpeg binary

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
        
        # Check ffmpeg availability
        if not cls._ffmpeg_available(ffmpeg_cmd):
            return ScrubResult(
                result_type=ResultType.SKIP,
                input_path=input_path,
                reason=f"ffmpeg not available at '{ffmpeg_cmd}' (required for audio/video scrubbing)",
            )
        
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

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=output_path.suffix, dir=output_path.parent) as tmp:
                tmp_path = Path(tmp.name)

            try:
                cmd = [
                    ffmpeg_cmd,
                    "-y",  # overwrite temp file if it exists
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(input_path),
                    "-map_metadata",
                    "-1",
                    "-map_chapters",
                    "-1",
                    "-c",
                    "copy",
                    str(tmp_path),
                ]

                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if proc.returncode != 0:
                    stderr = proc.stderr.strip()
                    
                    # Parse ffmpeg error for better categorization
                    if "No such file or directory" in stderr or "does not exist" in stderr:
                        error_category = ErrorCategory.INPUT_ERROR
                        fix_hint = "Verify input file exists and path is correct"
                    elif "Permission denied" in stderr:
                        error_category = ErrorCategory.PERMISSION_ERROR
                        fix_hint = "Check file permissions or run with appropriate privileges"
                    elif "Invalid data" in stderr or "moov atom not found" in stderr:
                        error_category = ErrorCategory.INPUT_ERROR
                        fix_hint = "File may be corrupted or not a valid media file"
                    elif "Codec" in stderr or "not supported" in stderr:
                        error_category = ErrorCategory.PROCESSING_ERROR
                        fix_hint = "This media format may not be fully supported by ffmpeg"
                    else:
                        error_category = ErrorCategory.PROCESSING_ERROR
                        fix_hint = "Check ffmpeg output for details"
                    
                    error_msg = stderr or "ffmpeg failed to scrub metadata"
                    return ScrubResult(
                        result_type=ResultType.ERROR,
                        input_path=input_path,
                        error=error_msg,
                        error_category=error_category,
                        fix_hint=fix_hint
                    )

                # Atomic move to final destination
                shutil.move(str(tmp_path), str(output_path))
                tmp_path = None  # Successfully moved

                return ScrubResult(
                    result_type=ResultType.SUCCESS,
                    input_path=input_path,
                    output_path=output_path,
                    metadata_removed="Container metadata stripped via ffmpeg",
                )

            except subprocess.TimeoutExpired:
                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error="ffmpeg operation timed out (exceeded 5 minutes)",
                    error_category=ErrorCategory.PROCESSING_ERROR,
                    fix_hint="File may be too large or corrupted. Try smaller files."
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
