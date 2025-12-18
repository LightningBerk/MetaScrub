#!/usr/bin/env python3
"""Cross-platform build helper for MetaScrub GUI releases.

Run this script on the target OS to produce a double-clickable build using PyInstaller.
- macOS: produces MetaScrub.app in dist/ (optionally wrap into a dmg if create-dmg is installed)
- Windows: produces MetaScrub.exe (one-folder) in dist/MetaScrub/
- Linux: produces a one-folder build; optionally wrap into an AppImage if appimagetool is installed

Usage examples:
  python scripts/build_release.py              # auto-detect OS and build
  python scripts/build_release.py --dmg        # on macOS, also create a dmg if create-dmg is available
  python scripts/build_release.py --appimage   # on Linux, attempt AppImage packaging if appimagetool is available
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRYPOINT = ROOT / "scrubmeta" / "gui" / "app.py"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:  # pragma: no cover - tooling guard
        raise SystemExit("PyInstaller is not installed. Activate venv and run: pip install pyinstaller") from exc


def icon_arg(path: Path) -> list[str]:
    if path.exists():
        return [f"--icon={path}"]
    return []


def build_mac(dmg: bool) -> None:
    icns = ROOT / "assets" / "icon.icns"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--windowed",
        "--noconfirm",
        "--name",
        "MetaScrub",
        *icon_arg(icns),
        str(ENTRYPOINT),
    ]
    run(cmd)

    if dmg and shutil.which("create-dmg"):
        app_path = DIST_DIR / "MetaScrub.app"
        dmg_path = ROOT / "MetaScrub-macOS.dmg"
        if app_path.exists():
            run([
                "create-dmg",
                "--overwrite",
                "--volname",
                "MetaScrub",
                "--window-size",
                "540",
                "380",
                str(dmg_path),
                str(app_path),
            ])
        else:
            print("[warn] MetaScrub.app not found; skipping dmg")
    elif dmg:
        print("[warn] create-dmg not found; skipping dmg packaging")


def build_windows() -> None:
    ico = ROOT / "assets" / "icon.ico"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--noconsole",
        "--name",
        "MetaScrub",
        *icon_arg(ico),
        str(ENTRYPOINT),
    ]
    run(cmd)
    print("[info] Windows build: dist/MetaScrub/MetaScrub.exe (one-folder build)")


def build_linux(appimage: bool) -> None:
    png = ROOT / "assets" / "icon.png"
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--name",
        "MetaScrub",
        *icon_arg(png),
        str(ENTRYPOINT),
    ]
    run(cmd)

    if appimage and shutil.which("appimagetool"):
        appdir = DIST_DIR / "MetaScrub.AppDir"
        # Minimal AppDir setup using PyInstaller output; assumes dist/MetaScrub exists
        src = DIST_DIR / "MetaScrub"
        if src.exists():
            if appdir.exists():
                shutil.rmtree(appdir)
            shutil.copytree(src, appdir)
            desktop = appdir / "MetaScrub.desktop"
            desktop.write_text(
                """[Desktop Entry]\nType=Application\nName=MetaScrub\nExec=MetaScrub\nIcon=icon\nTerminal=false\nCategories=Utility;""",
                encoding="utf-8",
            )
            # copy icon if present
            if png.exists():
                shutil.copy(png, appdir / "icon.png")
            run(["appimagetool", str(appdir), str(ROOT / "MetaScrub-Linux.AppImage")])
        else:
            print("[warn] dist/MetaScrub not found; skipping AppImage")
    elif appimage:
        print("[warn] appimagetool not found; skipping AppImage packaging")


def clean() -> None:
    for path in (DIST_DIR, BUILD_DIR):
        if path.exists():
            shutil.rmtree(path)
            print(f"[info] removed {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MetaScrub GUI for current platform")
    parser.add_argument("--clean", action="store_true", help="Remove previous dist/build before building")
    parser.add_argument("--dmg", action="store_true", help="(macOS) Also create a dmg if create-dmg is available")
    parser.add_argument("--appimage", action="store_true", help="(Linux) Attempt AppImage packaging if appimagetool is available")
    args = parser.parse_args()

    if args.clean:
        clean()

    ensure_pyinstaller()

    plat = sys.platform
    if plat == "darwin":
        build_mac(dmg=args.dmg)
    elif plat.startswith("win"):
        build_windows()
    elif plat.startswith("linux"):
        build_linux(appimage=args.appimage)
    else:
        raise SystemExit(f"Unsupported platform: {plat}")

    print("[done] Build finished")


if __name__ == "__main__":
    main()
