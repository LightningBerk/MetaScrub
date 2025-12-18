# MetaScrub

A Python tool for removing metadata from files. Supports images, PDFs, Office documents, audio, and video files. Available as both CLI and GUI.

## Features

- **Multiple file types**: JPG/PNG/WebP, PDF, DOCX/XLSX/PPTX, MP4/MOV/MP3/etc
- **Batch processing**: Single files or entire directories
- **Safe operations**: Never modifies originals, uses atomic writes
- **Cross-platform GUI**: Desktop app built with PySide6/Qt
- **Flexible output**: Preserve directory structure or flatten
- **Robust error handling**: Clear messages with actionable recovery hints

---

## Quick Start

**Requirements**: Python 3.8-3.13 (Python 3.12 recommended)

> **Note**: PySide6 (GUI framework) currently supports Python up to 3.13. If you have Python 3.14+, use Python 3.12 instead.

### 1. Setup

```bash
# Clone or download this repo
cd metaScrub

# Create virtual environment (use python3.12 if you have Python 3.14+)
python3 -m venv .venv
# OR: python3.12 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate
# Activate (Windows)
# .venv\Scripts\activate

# Install
pip install -e .
```

**Note**: For audio/video support, install `ffmpeg` separately:
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg` or `yum install ffmpeg`
- Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### 2. Run CLI

```bash
# Scrub a single file
scrubmeta scrub photo.jpg --out cleaned/

# Scrub a folder (recursive)
scrubmeta scrub photos/ --out cleaned/ --recursive

# Preview without writing (dry-run)
scrubmeta scrub documents/ --out cleaned/ --dry-run

# Preserve directory structure
scrubmeta scrub archive/ --out cleaned/ --recursive --keep-structure
```

### 3. Run GUI

```bash
python -m scrubmeta.gui
```

**GUI Features:**
- Pick file/folder, choose output directory
- Progress bar, results table with filters
- Export reports (CSV/JSON), open output folder
- Settings persist across sessions

### 4. Run Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest -v

# Quick smoke test
pytest -q
```

---

## Usage

### CLI Options

```
scrubmeta scrub <input_path> --out <output_dir> [options]

Options:
  --recursive         Process subdirectories
  --dry-run          Preview without writing
  --overwrite        Overwrite existing outputs (default: append suffix)
  --keep-structure   Preserve directory structure
  --ffmpeg-path PATH Custom ffmpeg binary path
```

### Examples

```bash
# Single file
scrubmeta scrub document.pdf --out cleaned/

# Batch with structure preserved
scrubmeta scrub photos/ --out cleaned/ --recursive --keep-structure

# Custom ffmpeg path
scrubmeta scrub media/ --out cleaned/ --ffmpeg-path /usr/local/bin/ffmpeg
```

---

## Supported File Types

| Type | Extensions | Method |
|------|-----------|--------|
| **Images** | `.jpg`, `.png`, `.webp` | Pillow (EXIF/IPTC/XMP removed) |
| **PDFs** | `.pdf` | pikepdf (metadata + XMP cleared) |
| **Office** | `.docx`, `.xlsx`, `.pptx` | ZIP manipulation (docProps removed) |
| **Video** | `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, etc | ffmpeg `-map_metadata -1` |
| **Audio** | `.mp3`, `.flac`, `.m4a`, `.ogg`, etc | ffmpeg `-map_metadata -1` |

---

## Build Standalone App (Optional)

Package GUI as standalone executable using PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --onefile --windowed --name MetaScrub scrubmeta/gui/app.py

# Output in dist/MetaScrub (or dist/MetaScrub.exe on Windows)
```

**Note**: Built executables go to `dist/` (ignored by git).

---

## Local Development

### Project Structure

```
metaScrub/
├── scrubmeta/              # Main package
│   ├── __init__.py
│   ├── __main__.py         # python -m scrubmeta
│   ├── cli.py              # CLI entry point
│   ├── core.py             # Shared scrubbing logic
│   ├── gui/                # Desktop GUI
│   │   ├── app.py
│   │   ├── main_window.py
│   │   ├── worker.py
│   │   └── models.py
│   ├── scrubbers/          # File-type handlers
│   │   ├── image_scrubber.py
│   │   ├── pdf_scrubber.py
│   │   ├── ooxml_scrubber.py
│   │   └── media_scrubber.py
│   └── utils/              # Shared utilities
│       ├── file_utils.py
│       └── result.py
├── tests/                  # Test suite
├── docs/                   # Additional documentation
├── setup.py                # Package metadata
├── requirements.txt        # Dependencies
└── README.md
```

### Quick Sanity Checks

```bash
# 1. Verify CLI works
scrubmeta scrub tests/fixtures/test_image.jpg --out /tmp/test_output 2>&1 | head -5

# 2. Verify GUI launches
python -m scrubmeta.gui &
# Close window, verify no crash

# 3. Test error handling (bad file)
echo "not an image" > /tmp/bad.jpg
scrubmeta scrub /tmp/bad.jpg --out /tmp/test_output
# Should show clear error + fix hint

# 4. Run full test suite
pytest -v
# All tests should pass
```

### Dependencies

Core:
- `Pillow>=10.0.0` - Image processing
- `piexif>=1.1.3` - EXIF handling
- `pikepdf>=8.0.0` - PDF manipulation (requires `qpdf` system library)
- `PySide6>=6.6` - Qt GUI framework

External:
- `ffmpeg` - Audio/video metadata removal (binary, not Python package)

---

## How It Works

### Safety & Atomic Operations

1. **Never modifies originals** - Reads input, writes to new file
2. **Atomic writes** - Uses temp files, moves only on success
3. **Automatic cleanup** - Failed operations clean up temp files
4. **Collision handling** - Appends `_clean_N` suffix when outputs exist

### Error Handling

All errors are categorized and include actionable fix hints:

```
ERROR | /path/to/file.jpg | Not a valid image file or unsupported format
  Fix: Verify file is a valid JPG, PNG, or WebP image

Error breakdown by category:
  input_error: 1
```

Error categories: `INPUT_ERROR`, `PERMISSION_ERROR`, `DEPENDENCY_ERROR`, `PROCESSING_ERROR`, `OUTPUT_ERROR`, `CANCELLED`

See `docs/ERROR_HANDLING.md` for comprehensive error documentation.

---

## Limitations

- **JPEG re-encoding**: Images are re-encoded at quality=95 (minor quality loss)
- **Embedded content**: Doesn't scrub metadata from embedded files (e.g., images in PDFs)
- **Unsupported files**: Skipped (not copied to output)
- **Office macros**: Not removed or scanned

---

## Troubleshooting

**PDF scrubbing fails:**
```bash
# Install qpdf system library
# macOS:
brew install qpdf
# Linux:
apt install qpdf
```

**Audio/video skipped:**
```bash
# Install ffmpeg
brew install ffmpeg  # macOS
apt install ffmpeg   # Linux
```

**Permission errors:**
- Check file/directory permissions: `ls -la <path>`
- Ensure output directory is writable

**GUI won't launch:**
- Verify PySide6 installed: `python -c "import PySide6; print('OK')"`
- Check Python version: `python --version` (requires 3.8-3.13)

---

## License

MIT License - Use at your own risk. Always keep backups of important files.

---

## Additional Resources

- **Error handling guide**: `docs/ERROR_HANDLING.md`
- **Implementation report**: `docs/ERROR_HANDLING_REPORT.md`
- **Tests**: `tests/`

---

**Last Updated**: December 2025 | **Version**: 1.0.0

## Usage (GUI)

Launch the desktop app (PySide6/Qt):

```bash
python -m scrubmeta.gui
```

Features:
- Pick single file or folder (batch), choose output directory
- Options: recursive, keep structure, overwrite, dry-run
- Progress bar, status text, per-file results table with filters
- Copy log / export report (CSV/JSON) / open output folder
- Cancel support; settings persist via `QSettings`

Packaging (example):

```bash
pyinstaller --onefile --windowed -n ScrubMeta scrubmeta/gui/app.py
```

## Supported File Types

| File Type | Extensions | Metadata Removed |
|-----------|-----------|------------------|
| **Images** | `.jpg`, `.jpeg`, `.png`, `.webp` | EXIF, IPTC, XMP |
| **PDFs** | `.pdf` | Document info, XMP metadata |
| **Office Docs** | `.docx`, `.xlsx`, `.pptx` | Core properties, app properties, custom properties |
| **Video** | `.mp4`, `.mov`, `.mkv`, `.avi`, `.m4v`, `.webm`, `.mpg`, `.mpeg` | Container metadata via ffmpeg (`-map_metadata -1`) |
| **Audio** | `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.opus` | Container metadata via ffmpeg (`-map_metadata -1`) |

## Output Format

The tool prints a line for each file processed:

```
SUCCESS | /path/to/input.jpg -> /path/to/output.jpg | removed: EXIF/IPTC/XMP metadata
SKIP | /path/to/file.txt | Unsupported file type: .txt
ERROR | /path/to/corrupt.pdf | Failed to open file
```

At the end, a summary is printed:

```
============================================================
SUMMARY
============================================================
Total scanned:  15
Successfully scrubbed: 12
Skipped:        2
Errors:         1
============================================================
```

## How It Works

### Images (JPG, PNG, WebP)

- Opens the image with Pillow
- Creates a new clean image without metadata
- Re-encodes with high quality settings
- **Note**: This is a lossy operation for JPEGs (quality=95)

### PDFs

- Uses `pikepdf` to open and modify PDFs
- Removes document info dictionary entries
- Clears XMP metadata streams
- Preserves document content and structure

### Office Documents (DOCX, XLSX, PPTX)

- Treats files as ZIP archives (OOXML format)
- Extracts contents
- Removes metadata XML files from `docProps/` directory
- Repackages into a clean archive

### Audio/Video (ffmpeg)

- Requires `ffmpeg` installed and on `PATH`
- Uses `ffmpeg -map_metadata -1 -map_chapters -1 -c copy` to strip container metadata without re-encoding
- Original streams are copied to avoid quality loss

## Limitations (v1)

1. **Image Quality**: JPEG images are re-encoded at quality=95, which may result in minor quality loss
2. **Embedded Content**: Does not scrub metadata from embedded files (e.g., images inside PDFs)
3. **Unsupported Files**: Files with unsupported extensions are skipped (not copied)
4. **Partial Metadata**: Some obscure metadata fields may not be removed
5. **Office Macros**: Does not remove or scan macro content in Office files

## Safety & Correctness

- **No Original Modification**: Original files are never modified
- **Atomic Writes**: Files are written to temporary locations then moved to prevent corruption
- **Validation**: Output directory is created if it doesn't exist
- **Unicode Support**: Handles unicode filenames correctly
- **Error Recovery**: Failed operations clean up temporary files

## Development

### Project Structure

```
metaScrub/
├── scrubmeta/
│   ├── __init__.py
│   ├── __main__.py          # Module entry point
│   ├── cli.py               # CLI implementation
│   ├── core.py              # Shared scrub API (CLI + GUI)
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── __main__.py      # python -m scrubmeta.gui
│   │   ├── app.py           # GUI entry point
│   │   ├── main_window.py   # UI layout and interactions
│   │   ├── worker.py        # Background worker
│   │   └── models.py        # Table models / filters
│   ├── scrubbers/
│   │   ├── __init__.py
│   │   ├── image_scrubber.py   # JPG/PNG/WebP handler
│   │   ├── pdf_scrubber.py     # PDF handler
│   │   ├── ooxml_scrubber.py   # DOCX/XLSX/PPTX handler
│   │   └── media_scrubber.py   # Audio/Video handler (ffmpeg)
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py    # File discovery & output management
│       └── result.py        # Result tracking
├── tests/                   # Test suite
├── requirements.txt
├── setup.py
└── README.md
```

### Running Tests

```bash
python -m pytest tests/
```

## Dependencies

- **Pillow** (>=10.0.0): Image processing
- **piexif** (>=1.1.3): EXIF metadata handling
- **pikepdf** (>=8.0.0): PDF manipulation
- **PySide6** (>=6.6): GUI
- **ffmpeg**: required binary for audio/video scrubbing (use `--ffmpeg-path` to point to a custom binary)

## Future Enhancements (Not in v1)

- Deep scrubbing of embedded content
- Verification mode to check if files have metadata
- Parallel processing for large batches
- Progress bars for long operations (CLI)
- Logging to file

## License

This is a v1 implementation for metadata scrubbing. Use at your own risk and always keep backups of important files.
