#!/bin/bash
# Quick sanity check script for MetaScrub
# Run after fresh clone to verify everything works

set -e  # Exit on error

echo "=== MetaScrub Sanity Check ==="
echo ""

# Detect Python (prefer 3.12, fallback to python3)
if command -v python3.12 &> /dev/null; then
    PYTHON=python3.12
    echo "1. Using Python 3.12 (recommended)..."
elif command -v python3 &> /dev/null; then
    PYTHON=python3
    echo "1. Using python3..."
else
    echo "ERROR: Python 3 not found. Install Python 3.8-3.13"
    exit 1
fi

$PYTHON --version
echo "   ✓ Python found"
echo ""

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "2. Creating virtual environment..."
    $PYTHON -m venv .venv
    echo "   ✓ Virtual environment created"
else
    echo "2. Virtual environment exists"
    echo "   ✓ Skipping creation"
fi
echo ""

# Activate and install
echo "3. Installing dependencies..."
source .venv/bin/activate
pip install -q -e .
echo "   ✓ Dependencies installed"
echo ""

# Test CLI entry point
echo "4. Testing CLI entry point..."
scrubmeta --help > /dev/null
echo "   ✓ CLI works (scrubmeta command)"
echo ""

# Test module entry point
echo "5. Testing module entry point..."
python -m scrubmeta --help > /dev/null
echo "   ✓ Module works (python -m scrubmeta)"
echo ""

# Test GUI import (don't launch)
echo "6. Testing GUI imports..."
python -c "from scrubmeta.gui import app; print('   ✓ GUI imports successful')"
echo ""

# Run tests
echo "7. Running test suite..."
pip install -q pytest 2>/dev/null || true
pytest -q
echo "   ✓ All tests passed"
echo ""

# Quick functional test
echo "8. Running functional test..."
echo "This is not a real image" > /tmp/test_bad.jpg
scrubmeta scrub /tmp/test_bad.jpg --out /tmp/metascrub_test 2>&1 | grep -q "ERROR"
rm -f /tmp/test_bad.jpg
rm -rf /tmp/metascrub_test
echo "   ✓ Error handling works"
echo ""

echo "=== All Checks Passed! ==="
echo ""
echo "Next steps:"
echo "  - Run CLI: scrubmeta scrub <file> --out <dir>"
echo "  - Run GUI: python -m scrubmeta.gui"
echo "  - Run tests: pytest -v"
echo ""
