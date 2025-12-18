"""Image metadata scrubber for JPG, PNG, WebP files."""

from pathlib import Path
import tempfile
import shutil
import os
import errno

from PIL import Image, UnidentifiedImageError

from ..utils.result import ScrubResult, ResultType, ErrorCategory


class ImageScrubber:
    """Scrubs metadata from image files."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    @classmethod
    def can_handle(cls, file_path: Path) -> bool:
        """Check if this scrubber can handle the file."""
        return file_path.suffix.lower() in cls.SUPPORTED_FORMATS
    
    @classmethod
    def scrub(cls, input_path: Path, output_path: Path) -> ScrubResult:
        """
        Scrub metadata from an image file.
        
        Args:
            input_path: Source image file
            output_path: Destination for cleaned image
            
        Returns:
            ScrubResult with operation outcome
        """
        # Validate input exists and is readable
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
                fix_hint="Check file permissions with chmod or run with appropriate privileges"
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
            with tempfile.NamedTemporaryFile(delete=False, suffix=output_path.suffix, dir=output_path.parent) as tmp:
                tmp_path = Path(tmp.name)
            
            try:
                # Open and validate image
                with Image.open(input_path) as img:
                    img_format = img.format
                    
                    if not img_format:
                        raise ValueError("Could not determine image format")
                    
                    # Create a new image without metadata
                    data = list(img.getdata())
                    clean_img = Image.new(img.mode, img.size)
                    clean_img.putdata(data)
                    
                    # Determine save format
                    if img_format == 'JPEG':
                        clean_img.save(tmp_path, 'JPEG', quality=95, optimize=True)
                    elif img_format == 'PNG':
                        clean_img.save(tmp_path, 'PNG', optimize=True)
                    elif img_format == 'WEBP':
                        clean_img.save(tmp_path, 'WEBP', quality=95)
                    else:
                        clean_img.save(tmp_path, img_format)
                
                # Atomic move to final destination
                shutil.move(str(tmp_path), str(output_path))
                tmp_path = None  # Successfully moved
                
                return ScrubResult(
                    result_type=ResultType.SUCCESS,
                    input_path=input_path,
                    output_path=output_path,
                    metadata_removed="EXIF/IPTC/XMP metadata"
                )
            
            except UnidentifiedImageError:
                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error="Not a valid image file or unsupported format",
                    error_category=ErrorCategory.INPUT_ERROR,
                    fix_hint="Verify file is a valid JPG, PNG, or WebP image"
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
            
            except (ValueError, RuntimeError) as e:
                return ScrubResult(
                    result_type=ResultType.ERROR,
                    input_path=input_path,
                    error=f"Processing failed: {e}",
                    error_category=ErrorCategory.PROCESSING_ERROR,
                    fix_hint="File may be corrupted or use an unusual image variant"
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
