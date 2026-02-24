#!/usr/bin/env python3
"""
Lädt statisch gelinkte ffmpeg + ffprobe für Windows x86_64 herunter.
Quelle: BtbN/FFmpeg-Builds (GitHub).

Verwendung:
    python build/windows/get_ffmpeg.py

Die Binaries landen in vendor/ffmpeg.exe und vendor/ffprobe.exe.
"""

import hashlib
import io
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent.parent
VENDOR = ROOT / "vendor"

# Stabile 7.1 Release – statisch gelinkt, GPL (enthält libx265)
FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-n7.1-latest-win64-gpl-7.1.zip"
)


def download_and_extract():
    VENDOR.mkdir(exist_ok=True)

    print("==> Lade ffmpeg fuer Windows x86_64 ...")
    print(f"    URL: {FFMPEG_URL}")

    with urlopen(FFMPEG_URL) as resp:
        data = resp.read()

    sha256 = hashlib.sha256(data).hexdigest()
    print(f"    SHA256: {sha256}")
    print(f"    Size: {len(data) / (1024 * 1024):.1f} MB")

    print("    Extracting ...")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        # Binaries liegen in <archiv-name>/bin/
        extracted = 0
        for name in zf.namelist():
            basename = Path(name).name
            if basename in ("ffmpeg.exe", "ffprobe.exe"):
                target = VENDOR / basename
                target.write_bytes(zf.read(name))
                print(f"    -> {target}")
                extracted += 1

        if extracted < 2:
            print("FEHLER: ffmpeg.exe oder ffprobe.exe nicht im Archiv gefunden.")
            print("Archiv-Inhalt:")
            for name in zf.namelist():
                print(f"  {name}")
            sys.exit(1)

    print()
    print(f"==> Done! Binaries in {VENDOR}")


if __name__ == "__main__":
    download_and_extract()
