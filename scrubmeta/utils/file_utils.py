"""File discovery and output management utilities."""

from pathlib import Path
from typing import List


class FileDiscovery:
    """Handles file discovery for single file or batch processing."""
    
    SUPPORTED_EXTENSIONS = {
        # Images
        '.jpg', '.jpeg', '.png', '.webp',
        # PDFs
        '.pdf',
        # Office documents
        '.docx', '.xlsx', '.pptx',
        # Video
        '.mp4', '.mov', '.mkv', '.avi', '.m4v', '.webm', '.mpg', '.mpeg',
        # Audio
        '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.opus'
    }
    
    @classmethod
    def discover_files(cls, input_path: Path, recursive: bool = False) -> List[Path]:
        """
        Discover files to process.
        
        Args:
            input_path: Single file or directory path
            recursive: Whether to recurse into subdirectories
            
        Returns:
            List of file paths to process
        """
        if input_path.is_file():
            return [input_path]
        
        if not input_path.is_dir():
            raise ValueError(f"Input path does not exist: {input_path}")
        
        files = []
        pattern = "**/*" if recursive else "*"
        
        for item in input_path.glob(pattern):
            if item.is_file() and cls.is_supported(item):
                files.append(item)
        
        return sorted(files)
    
    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """Check if file type is supported."""
        return file_path.suffix.lower() in cls.SUPPORTED_EXTENSIONS


class OutputManager:
    """Manages output file paths and collision handling."""
    
    def __init__(self, output_dir: Path, overwrite: bool = False, keep_structure: bool = False):
        """
        Initialize output manager.
        
        Args:
            output_dir: Base output directory
            overwrite: Whether to overwrite existing files
            keep_structure: Whether to preserve directory structure
        """
        self.output_dir = output_dir
        self.overwrite = overwrite
        self.keep_structure = keep_structure
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_output_path(self, input_path: Path, base_input_dir: Path = None) -> Path:
        """
        Determine output path for a file.
        
        Args:
            input_path: Original file path
            base_input_dir: Base directory for preserving structure (used with keep_structure)
            
        Returns:
            Output file path
        """
        if self.keep_structure and base_input_dir:
            # Preserve directory structure relative to base input dir
            relative_path = input_path.relative_to(base_input_dir)
            output_path = self.output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Flat output - just use filename
            output_path = self.output_dir / input_path.name
        
        # Handle collisions (protect against permission errors when checking)
        try:
            if not self.overwrite and output_path.exists():
                output_path = self._get_unique_path(output_path)
        except (PermissionError, OSError):
            # If we can't check existence due to permissions, proceed anyway
            # The scrubber will handle the permission error during write
            pass
        
        return output_path
    
    def _get_unique_path(self, path: Path) -> Path:
        """
        Generate a unique path by appending suffix.
        
        Args:
            path: Desired path
            
        Returns:
            Unique path that doesn't exist
        """
        try:
            if not path.exists():
                return path
        except (PermissionError, OSError):
            # Can't check, return original path and let scrubber handle error
            return path
        
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        counter = 1
        while True:
            new_name = f"{stem}_clean_{counter}{suffix}"
            new_path = parent / new_name
            try:
                if not new_path.exists():
                    return new_path
            except (PermissionError, OSError):
                # Can't check, return this path and let scrubber handle error
                return new_path
            counter += 1
