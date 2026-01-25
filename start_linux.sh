#!/bin/bash
set -euo pipefail

# MetaScrub One-Click Launcher for Linux

# Resolve script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python 3 not found."
    echo "Please install python3 via your package manager (e.g., apt, dnf, pacman)."
    exit 1
fi

# Check Python version >= 3.8
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" || {
    echo "[ERROR] Python 3.8+ required."
    exit 1
}

VENV_DIR=".venv"

# Create venv if missing
if [[ ! -d "$VENV_DIR" ]]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Install/Update dependencies
echo "[INFO] Installing/Updating dependencies..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -e . >/dev/null

# Check for ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "[INFO] ffmpeg not found. Attempting installation..."
    INSTALLED=0
    if command -v apt >/dev/null 2>&1; then
        echo "Detected apt. Installing ffmpeg (may ask for sudo password)..."
        sudo apt update && sudo apt install -y ffmpeg && INSTALLED=1
    elif command -v dnf >/dev/null 2>&1; then
        echo "Detected dnf. Installing ffmpeg (may ask for sudo password)..."
        sudo dnf install -y ffmpeg && INSTALLED=1
    elif command -v pacman >/dev/null 2>&1; then
        echo "Detected pacman. Installing ffmpeg (may ask for sudo password)..."
        sudo pacman -S --noconfirm ffmpeg && INSTALLED=1
    elif command -v zypper >/dev/null 2>&1; then
         echo "Detected zypper. Installing ffmpeg (may ask for sudo password)..."
         sudo zypper install -y ffmpeg && INSTALLED=1
    fi

    if [ $INSTALLED -eq 0 ]; then
        echo "[WARNING] Automatic installation failed or no supported package manager found."
        echo "Please install ffmpeg manually."
        sleep 3
    else
        echo "[INFO] ffmpeg installed successfully."
    fi
fi

# Launch GUI
echo "[INFO] Starting MetaScrub..."
python -m scrubmeta.gui
