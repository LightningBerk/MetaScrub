"""PyInstaller entry point for MetaScrub.

This file uses absolute imports so PyInstaller can bundle it correctly
as a standalone executable.
"""

from scrubmeta.cli import main

if __name__ == "__main__":
    main()
