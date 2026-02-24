#!/usr/bin/env python3
"""
FileFiend – Build-Script
Prüft Voraussetzungen und ruft PyInstaller auf.
Erkennt automatisch macOS vs. Windows und wählt die passende Build-Config.

Verwendung:
    python build_app.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"


def get_spec_file() -> Path:
    if IS_MACOS:
        return ROOT / "build" / "macos" / "FileFiend.spec"
    if IS_WINDOWS:
        return ROOT / "build" / "windows" / "FileFiend.spec"
    print(f"FEHLER: Plattform '{sys.platform}' wird nicht unterstützt.")
    sys.exit(1)


def check_prerequisites() -> bool:
    ok = True

    # PyInstaller installiert?
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("FEHLER: PyInstaller nicht installiert.")
        print("  → pip install pyinstaller")
        ok = False

    # Spec-Datei vorhanden?
    spec = get_spec_file()
    if not spec.exists():
        print(f"FEHLER: {spec.relative_to(ROOT)} nicht gefunden.")
        ok = False

    # vendor/ Binaries prüfen
    vendor = ROOT / "vendor"
    if IS_MACOS:
        if not (vendor / "ffmpeg").exists() or not (vendor / "ffprobe").exists():
            print("WARNUNG: vendor/ffmpeg oder vendor/ffprobe nicht gefunden.")
            print("  → bash build/macos/get_ffmpeg.sh")
            print("  (Build wird fortgesetzt, aber die App kann keine Videos komprimieren.)")
    elif IS_WINDOWS:
        if not (vendor / "ffmpeg.exe").exists() or not (vendor / "ffprobe.exe").exists():
            print("WARNUNG: vendor/ffmpeg.exe oder vendor/ffprobe.exe nicht gefunden.")
            print("  → python build/windows/get_ffmpeg.py")
            print("  (Build wird fortgesetzt, aber die App kann keine Videos komprimieren.)")
        if not (vendor / "MediaInfo.dll").exists():
            print("WARNUNG: vendor/MediaInfo.dll nicht gefunden.")
            print("  → python build/windows/get_mediainfo.py")

    # Icon prüfen
    if IS_MACOS:
        icon = ROOT / "assets" / "FileFiend.icns"
        if not icon.exists():
            print("HINWEIS: assets/FileFiend.icns nicht gefunden – App wird ohne Icon gebaut.")
    elif IS_WINDOWS:
        icon = ROOT / "assets" / "FileFiend.ico"
        if not icon.exists():
            print("HINWEIS: assets/FileFiend.ico nicht gefunden – App wird ohne Icon gebaut.")

    return ok


def build():
    if not check_prerequisites():
        sys.exit(1)

    spec = get_spec_file()
    platform_name = "macOS" if IS_MACOS else "Windows"
    print(f"\n==> Starte PyInstaller-Build für {platform_name} …\n")
    print(f"    Spec: {spec.relative_to(ROOT)}\n")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            str(spec),
        ],
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        print("\nFEHLER: Build fehlgeschlagen.")
        sys.exit(1)

    if IS_MACOS:
        app_path = ROOT / "dist" / "FileFiend.app"
        if app_path.exists():
            subprocess.run(["xattr", "-cr", str(app_path)], check=False)
            size_mb = sum(f.stat().st_size for f in app_path.rglob("*") if f.is_file()) / (
                1024 * 1024
            )
            print(f"\n==> Fertig! App: {app_path}")
            print(f"    Größe: {size_mb:.0f} MB")
            print(f"\n    Starten mit: open {app_path}")
        else:
            print("\nFEHLER: FileFiend.app wurde nicht erstellt.")
            sys.exit(1)

    elif IS_WINDOWS:
        exe_path = ROOT / "dist" / "FileFiend" / "FileFiend.exe"
        if exe_path.exists():
            size_mb = sum(f.stat().st_size for f in exe_path.parent.rglob("*") if f.is_file()) / (
                1024 * 1024
            )
            print(f"\n==> Fertig! EXE: {exe_path}")
            print(f"    Größe (gesamt): {size_mb:.0f} MB")
            print(f"\n    Starten mit: {exe_path}")
        else:
            print("\nFEHLER: FileFiend.exe wurde nicht erstellt.")
            sys.exit(1)


if __name__ == "__main__":
    build()
