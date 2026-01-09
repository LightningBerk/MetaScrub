#!/bin/bash
# One-click installer/launcher for MetaScrub on macOS.
# Double-click this file (after making it executable) to install dependencies and launch the GUI.

set -euo pipefail

# Resolve repository root (the folder containing this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Pick a Python 3 interpreter (allow override via PYTHON_BIN env var)
PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "[error] Python 3.8+ is required but not found." >&2
    exit 1
  fi
fi

# Verify Python version >= 3.8
"$PYTHON_BIN" - <<'PY'
import sys
major, minor = sys.version_info[:2]
if (major, minor) < (3, 8):
    sys.stderr.write(f"[error] Python 3.8+ required (found {major}.{minor}).\n")
    sys.exit(1)
print(f"[info] Using Python {major}.{minor}")
PY

VENV_DIR="$SCRIPT_DIR/.venv"

# Create venv if missing
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[info] Creating virtual environment in .venv"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Activate venv
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

# Upgrade pip tooling
python -m pip install --upgrade pip wheel >/dev/null

# Ensure ffmpeg is available (for media scrubbing)
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[info] ffmpeg not found; attempting Homebrew install..."
  if command -v brew >/dev/null 2>&1; then
    brew install ffmpeg || { echo "[error] Homebrew failed to install ffmpeg. Please run: brew install ffmpeg" >&2; exit 1; }
  else
    echo "[error] ffmpeg not found and Homebrew is not installed. Please install Homebrew (https://brew.sh) then run: brew install ffmpeg" >&2
    exit 1
  fi
else
  echo "[info] ffmpeg already available at $(command -v ffmpeg)"
fi

# Install MetaScrub (editable install to keep local changes live)
echo "[info] Installing MetaScrub dependencies (this may take a minute)..."
python -m pip install -e . >/dev/null

# Launch GUI
echo "[info] Starting MetaScrub GUI..."
python -m scrubmeta.gui
