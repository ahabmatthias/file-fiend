"""
Runtime-Helfer für den PyInstaller-Frozen-Modus.

Im gebündelten .app liegen ffmpeg/ffprobe unter vendor/.
setup_path() fügt diesen Pfad zu $PATH hinzu, damit shutil.which() sie findet.
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_vendor_dir() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS) / "vendor"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent.parent / "vendor"


def setup_path() -> None:
    vendor = get_vendor_dir()
    if vendor.is_dir():
        os.environ["PATH"] = str(vendor) + os.pathsep + os.environ.get("PATH", "")
