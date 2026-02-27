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
# Gepinnt auf konkreten Autobuild (nicht "latest") fuer reproduzierbare Builds.
FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
    "autobuild-2026-02-24-16-00/"
    "ffmpeg-n7.1.3-40-gcddd06f3b9-win64-gpl-7.1.zip"
)
# Nach URL-Update: CI laufen lassen, neuen Hash aus Log uebernehmen.
EXPECTED_SHA256 = "53e8df0587165ed1d3868225ed9f866a6f261a7a707ba5ffcf5c4d611869297e"


def download_and_extract() -> None:
    VENDOR.mkdir(exist_ok=True)

    print("==> Lade ffmpeg fuer Windows x86_64 ...")
    print(f"    URL: {FFMPEG_URL}")

    with urlopen(FFMPEG_URL, timeout=120) as resp:
        data = resp.read()

    sha256 = hashlib.sha256(data).hexdigest()
    print(f"    SHA256: {sha256}")
    print(f"    Size: {len(data) / (1024 * 1024):.1f} MB")

    if sha256 != EXPECTED_SHA256:
        print("    FEHLER: Hash stimmt nicht ueberein!")
        print(f"    Erwartet: {EXPECTED_SHA256}")
        print(f"    Erhalten: {sha256}")
        sys.exit(1)
    print("    Hash OK")

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
