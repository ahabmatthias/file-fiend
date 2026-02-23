#!/usr/bin/env python3
"""
FileFiend – Build-Script
Prüft Voraussetzungen und ruft PyInstaller auf.

Verwendung:
    python build_app.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def check_prerequisites() -> bool:
    ok = True

    # PyInstaller installiert?
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("FEHLER: PyInstaller nicht installiert.")
        print("  → pip install pyinstaller")
        ok = False

    # vendor/ffmpeg vorhanden?
    vendor = ROOT / "vendor"
    if not (vendor / "ffmpeg").exists() or not (vendor / "ffprobe").exists():
        print("WARNUNG: vendor/ffmpeg oder vendor/ffprobe nicht gefunden.")
        print("  → bash scripts/get_ffmpeg.sh")
        print("  (Build wird fortgesetzt, aber die App kann keine Videos komprimieren.)")

    # Icon vorhanden?
    icon = ROOT / "assets" / "FileFiend.icns"
    if not icon.exists():
        print("HINWEIS: assets/FileFiend.icns nicht gefunden – App wird ohne Icon gebaut.")

    # Spec-Datei vorhanden?
    if not (ROOT / "FileFiend.spec").exists():
        print("FEHLER: FileFiend.spec nicht gefunden.")
        ok = False

    return ok


def build():
    if not check_prerequisites():
        sys.exit(1)

    print("\n==> Starte PyInstaller-Build …\n")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            str(ROOT / "FileFiend.spec"),
        ],
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        print("\nFEHLER: Build fehlgeschlagen.")
        sys.exit(1)

    app_path = ROOT / "dist" / "FileFiend.app"
    if app_path.exists():
        # Gatekeeper-Quarantine-Flag entfernen
        subprocess.run(["xattr", "-cr", str(app_path)], check=False)

        size_mb = sum(f.stat().st_size for f in app_path.rglob("*") if f.is_file()) / (1024 * 1024)
        print(f"\n==> Fertig! App: {app_path}")
        print(f"    Größe: {size_mb:.0f} MB")
        print(f"\n    Starten mit: open {app_path}")
    else:
        print("\nFEHLER: FileFiend.app wurde nicht erstellt.")
        sys.exit(1)


if __name__ == "__main__":
    build()
