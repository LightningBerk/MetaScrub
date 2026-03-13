# MetaScrub

A cross-platform Python tool for stripping metadata from files. Supports images, PDFs, Office documents, audio, and video. Available as a **CLI** and an interactive **Terminal UI (TUI)**.

---

## Features

- **Broad format support** — JPG, PNG, WebP, PDF, DOCX/XLSX/PPTX, MP4, MOV, MKV, MP3, FLAC, and more
- **Batch processing** — scrub single files or entire directory trees
- **Safe by design** — originals are never modified; atomic writes prevent corruption
- **Interactive TUI** — built with [Textual](https://github.com/Textualize/textual); browse files, toggle options, and watch progress in-terminal
- **Actionable errors** — every failure is categorized with a human-readable fix hint
- **Pre-built binaries** — standalone executables for Windows, macOS, and Linux via GitHub Actions

---

## Installation

### Option A — Download a standalone binary (no Python required)

1. Go to the **Actions** tab on the [GitHub repository](https://github.com/LightningBerk/MetaScrub).
2. Open the latest successful **Build Standalone Executables** run.
3. Download the artifact `.zip` for your OS (Linux / macOS / Windows).
4. Extract and run the `metascrub` binary.

### Option B — Install from source

**Requirements:** Python 3.8+ and `pip`.

```bash
git clone https://github.com/LightningBerk/MetaScrub.git
cd MetaScrub

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e .
```

For **audio/video** scrubbing you also need `ffmpeg`:

| OS      | Command                                                        |
| ------- | -------------------------------------------------------------- |
| macOS   | `brew install ffmpeg`                                          |
| Linux   | `apt install ffmpeg` or `dnf install ffmpeg`                   |
| Windows | Download from [ffmpeg.org](https://ffmpeg.org/download.html)   |

For **PDF** scrubbing, `pikepdf` requires the `qpdf` system library:

| OS      | Command              |
| ------- | -------------------- |
| macOS   | `brew install qpdf`  |
| Linux   | `apt install qpdf`   |

---

## Usage

### CLI

```bash
# Scrub a single file
scrubmeta scrub photo.jpg --out cleaned/

# Scrub a folder recursively
scrubmeta scrub photos/ --out cleaned/ --recursive

# Dry-run (preview only)
scrubmeta scrub documents/ --out cleaned/ --dry-run

# Preserve directory structure in output
scrubmeta scrub archive/ --out cleaned/ --recursive --keep-structure

# Use a custom ffmpeg binary
scrubmeta scrub media/ --out cleaned/ --ffmpeg-path /usr/local/bin/ffmpeg
```

**CLI flags:**

| Flag               | Description                                             |
| ------------------ | ------------------------------------------------------- |
| `--recursive`      | Process subdirectories                                  |
| `--dry-run`        | Preview without writing                                 |
| `--overwrite`      | Overwrite existing outputs (default: append `_clean_N`) |
| `--keep-structure` | Mirror input directory tree in output                   |
| `--ffmpeg-path`    | Path to a custom `ffmpeg` binary                        |

### TUI

```bash
scrubmeta tui
```

- Browse and select input files/folders with an interactive **DirectoryTree**
- Toggle options via visual checkboxes (green `✓` / red `✗`)
- Watch a live progress bar and color-coded results table

---

## Supported File Types

| Type       | Extensions                                                       | Method                                |
| ---------- | ---------------------------------------------------------------- | ------------------------------------- |
| **Images** | `.jpg`, `.jpeg`, `.png`, `.webp`                                 | Pillow — strips EXIF, IPTC, XMP       |
| **PDFs**   | `.pdf`                                                           | pikepdf — clears doc-info and XMP     |
| **Office** | `.docx`, `.xlsx`, `.pptx`                                        | ZIP manipulation — removes `docProps` |
| **Video**  | `.mp4`, `.mov`, `.mkv`, `.avi`, `.m4v`, `.webm`, `.mpg`, `.mpeg` | ffmpeg `-map_metadata -1 -c copy`     |
| **Audio**  | `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.opus`         | ffmpeg `-map_metadata -1 -c copy`     |

---

## How It Works

### Images (JPG, PNG, WebP)

Opens the image with Pillow, creates a clean copy without metadata, and re-encodes at quality 95.

### PDFs

Uses `pikepdf` to clear the document info dictionary and XMP metadata stream while preserving content.

### Office Documents (DOCX, XLSX, PPTX)

Treats files as OOXML ZIP archives, removes `docProps/` metadata XMLs, and repackages.

### Audio / Video (ffmpeg)

Runs `ffmpeg -map_metadata -1 -map_chapters -1 -c copy` to strip container metadata **without** re-encoding, so there is no quality loss.

### Safety & Atomicity

1. **Never modifies originals** — reads input, writes to a new file.
2. **Atomic writes** — uses temp files; moves to final path only on success.
3. **Automatic cleanup** — temp files are removed on failure.
4. **Collision handling** — appends `_clean_N` suffix when the output already exists.

---

## Error Handling

Every error is classified into a category and paired with a fix hint:

```text
ERROR | /path/to/file.jpg | Not a valid image file or unsupported format
  Fix: Verify file is a valid JPG, PNG, or WebP image
```

**Categories:** `INPUT_ERROR`, `PERMISSION_ERROR`, `DEPENDENCY_ERROR`, `PROCESSING_ERROR`, `OUTPUT_ERROR`, `CANCELLED`

A summary with per-category counts is printed at the end of every run.

---

## CLI Output

```text
SUCCESS | input.jpg -> cleaned/input.jpg | removed: EXIF/IPTC/XMP metadata
SKIP    | notes.txt                      | Unsupported file type: .txt
ERROR   | corrupt.pdf                    | Failed to open file

============================================================
SUMMARY
============================================================
Total scanned:  15
Successfully scrubbed: 12
Skipped:        2
Errors:         1
============================================================
```

---

## Limitations

- **JPEG quality** — re-encoded at quality 95 (minor loss possible)
- **Embedded content** — metadata inside embedded files (e.g., images in PDFs) is not scrubbed
- **Unsupported formats** — silently skipped (not copied)
- **Office macros** — not removed or scanned
- **Partial metadata** — some obscure fields may persist

---

## Troubleshooting

| Problem             | Fix                                                              |
| ------------------- | ---------------------------------------------------------------- |
| PDF scrubbing fails | Install `qpdf`: `brew install qpdf` / `apt install qpdf`        |
| Audio/video skipped | Install `ffmpeg`: `brew install ffmpeg` / `apt install ffmpeg`   |
| Permission errors   | Check permissions with `ls -la`; ensure output dir is writable   |
| TUI won't launch    | Verify Textual: `python -c "import textual; print('OK')"`       |

---

## Project Structure

```text
MetaScrub/
├── scrubmeta/
│   ├── __init__.py
│   ├── __main__.py            # python -m scrubmeta
│   ├── cli.py                 # CLI entry point
│   ├── core.py                # Shared scrub orchestration
│   ├── tui/
│   │   ├── app.py             # TUI layout & app
│   │   └── widgets.py         # VisualCheckbox, SelectPathModal
│   ├── scrubbers/
│   │   ├── image_scrubber.py
│   │   ├── pdf_scrubber.py
│   │   ├── ooxml_scrubber.py
│   │   └── media_scrubber.py
│   └── utils/
│       ├── file_utils.py      # File discovery & output management
│       └── result.py          # ScrubResult, ErrorCategory
├── tests/
├── setup.py
├── requirements.txt
└── README.md
```

---

## Dependencies

| Package             | Purpose                      |
| ------------------- | ---------------------------- |
| `Pillow` ≥ 10.0     | Image processing             |
| `piexif` ≥ 1.1.3    | EXIF metadata handling       |
| `pikepdf` ≥ 8.0     | PDF manipulation             |
| `textual` ≥ 0.40    | Terminal UI framework        |
| `ffmpeg` *(system)* | Audio/video metadata removal |

---

## Running Tests

```bash
pip install pytest
pytest -v
```

---

## License

MIT License — use at your own risk. Always keep backups of important files.

**Last Updated:** March 2026 · **Version:** 1.0.0
