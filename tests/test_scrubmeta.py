"""Tests for MetaScrub."""

import unittest
from pathlib import Path
import tempfile
import shutil
from io import BytesIO

from PIL import Image

from scrubmeta.utils.file_utils import FileDiscovery, OutputManager
from scrubmeta.utils.result import ResultType
from scrubmeta.scrubbers.image_scrubber import ImageScrubber
from scrubmeta.scrubbers.media_scrubber import MediaScrubber


class TestFileDiscovery(unittest.TestCase):
    """Test file discovery functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_single_file_discovery(self):
        """Test discovering a single file."""
        test_file = self.test_path / "test.jpg"
        test_file.touch()
        
        files = FileDiscovery.discover_files(test_file)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], test_file)
    
    def test_directory_discovery_non_recursive(self):
        """Test discovering files in a directory without recursion."""
        # Create test files
        (self.test_path / "image1.jpg").touch()
        (self.test_path / "image2.png").touch()
        (self.test_path / "document.pdf").touch()
        (self.test_path / "ignored.txt").touch()
        
        # Create subdirectory with files
        sub_dir = self.test_path / "subdir"
        sub_dir.mkdir()
        (sub_dir / "nested.jpg").touch()
        
        files = FileDiscovery.discover_files(self.test_path, recursive=False)
        
        # Should find 3 supported files in root, not in subdirectory
        self.assertEqual(len(files), 3)
        file_names = {f.name for f in files}
        self.assertEqual(file_names, {"image1.jpg", "image2.png", "document.pdf"})
    
    def test_directory_discovery_recursive(self):
        """Test discovering files recursively."""
        # Create test files
        (self.test_path / "root.jpg").touch()
        
        # Create nested structure
        sub_dir = self.test_path / "subdir"
        sub_dir.mkdir()
        (sub_dir / "nested.png").touch()
        
        deep_dir = sub_dir / "deep"
        deep_dir.mkdir()
        (deep_dir / "deep.pdf").touch()
        
        files = FileDiscovery.discover_files(self.test_path, recursive=True)
        
        # Should find all 3 files
        self.assertEqual(len(files), 3)
        file_names = {f.name for f in files}
        self.assertEqual(file_names, {"root.jpg", "nested.png", "deep.pdf"})
    
    def test_is_supported(self):
        """Test file type support detection."""
        self.assertTrue(FileDiscovery.is_supported(Path("test.jpg")))
        self.assertTrue(FileDiscovery.is_supported(Path("test.JPG")))
        self.assertTrue(FileDiscovery.is_supported(Path("test.png")))
        self.assertTrue(FileDiscovery.is_supported(Path("test.pdf")))
        self.assertTrue(FileDiscovery.is_supported(Path("test.docx")))
        self.assertTrue(FileDiscovery.is_supported(Path("movie.mp4")))
        self.assertTrue(FileDiscovery.is_supported(Path("audio.mp3")))
        self.assertFalse(FileDiscovery.is_supported(Path("test.txt")))
        self.assertFalse(FileDiscovery.is_supported(Path("test.zip")))


class TestOutputManager(unittest.TestCase):
    """Test output file management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_output_directory_creation(self):
        """Test that output directory is created."""
        manager = OutputManager(self.output_dir)
        self.assertTrue(self.output_dir.exists())
        self.assertTrue(self.output_dir.is_dir())
    
    def test_flat_output_path(self):
        """Test output path without structure preservation."""
        manager = OutputManager(self.output_dir, keep_structure=False)
        input_path = Path("/some/deep/path/file.jpg")
        
        output_path = manager.get_output_path(input_path)
        
        self.assertEqual(output_path, self.output_dir / "file.jpg")
    
    def test_structured_output_path(self):
        """Test output path with structure preservation."""
        manager = OutputManager(self.output_dir, keep_structure=True)
        base_dir = Path("/input")
        input_path = Path("/input/subdir/file.jpg")
        
        output_path = manager.get_output_path(input_path, base_dir)
        
        self.assertEqual(output_path, self.output_dir / "subdir" / "file.jpg")
    
    def test_collision_handling_no_overwrite(self):
        """Test collision handling when overwrite is disabled."""
        manager = OutputManager(self.output_dir, overwrite=False)
        
        # Create existing file
        existing = self.output_dir / "test.jpg"
        existing.touch()
        
        input_path = Path("/some/path/test.jpg")
        output_path = manager.get_output_path(input_path)
        
        # Should generate unique name
        self.assertNotEqual(output_path, existing)
        self.assertTrue(output_path.name.startswith("test_clean_"))
        self.assertTrue(output_path.name.endswith(".jpg"))
    
    def test_collision_handling_with_overwrite(self):
        """Test collision handling when overwrite is enabled."""
        manager = OutputManager(self.output_dir, overwrite=True)
        
        # Create existing file
        existing = self.output_dir / "test.jpg"
        existing.touch()
        
        input_path = Path("/some/path/test.jpg")
        output_path = manager.get_output_path(input_path)
        
        # Should return same path (allows overwrite)
        self.assertEqual(output_path, existing)


class TestImageScrubber(unittest.TestCase):
    """Test image scrubbing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def create_test_image(self, path: Path, format: str = "JPEG"):
        """Create a test image file."""
        img = Image.new('RGB', (100, 100), color='red')
        img.save(path, format)
    
    def test_can_handle(self):
        """Test file type detection."""
        self.assertTrue(ImageScrubber.can_handle(Path("test.jpg")))
        self.assertTrue(ImageScrubber.can_handle(Path("test.jpeg")))
        self.assertTrue(ImageScrubber.can_handle(Path("test.png")))
        self.assertTrue(ImageScrubber.can_handle(Path("test.webp")))
        self.assertFalse(ImageScrubber.can_handle(Path("test.pdf")))
        self.assertFalse(ImageScrubber.can_handle(Path("test.txt")))


class TestMediaScrubber(unittest.TestCase):
    """Test media scrubbing functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_can_handle(self):
        """Test media type detection."""
        self.assertTrue(MediaScrubber.can_handle(Path("video.mp4")))
        self.assertTrue(MediaScrubber.can_handle(Path("video.MOV")))
        self.assertTrue(MediaScrubber.can_handle(Path("audio.mp3")))
        self.assertTrue(MediaScrubber.can_handle(Path("audio.flac")))
        self.assertFalse(MediaScrubber.can_handle(Path("image.jpg")))
        self.assertFalse(MediaScrubber.can_handle(Path("document.pdf")))

    def test_scrub_without_ffmpeg(self):
        """If ffmpeg is missing, scrubbing should skip gracefully."""
        if MediaScrubber._ffmpeg_available("ffmpeg"):
            self.skipTest("ffmpeg available; skip missing ffmpeg test")

        input_path = self.test_path / "input.mp3"
        input_path.touch()
        output_path = self.test_path / "output.mp3"

        result = MediaScrubber.scrub(input_path, output_path, ffmpeg_cmd="/nonexistent/ffmpeg")

        self.assertEqual(result.result_type, ResultType.SKIP)
        self.assertFalse(output_path.exists())


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
