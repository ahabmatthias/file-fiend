#!/usr/bin/env python3
"""
Lädt die MediaInfo-DLL für Windows x86_64 herunter.
Quelle: MediaArea.net

Verwendung:
    python build/windows/get_mediainfo.py

Die DLL landet in vendor/MediaInfo.dll.
"""

import hashlib
import io
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent.parent
VENDOR = ROOT / "vendor"

MEDIAINFO_URL = (
    "https://mediaarea.net/download/binary/libmediainfo0/26.01/"
    "MediaInfo_DLL_26.01_Windows_x64_WithoutInstaller.zip"
)


def download_and_extract():
    VENDOR.mkdir(exist_ok=True)

    print("==> Lade MediaInfo-DLL für Windows x86_64 …")
    print(f"    URL: {MEDIAINFO_URL}")

    with urlopen(MEDIAINFO_URL) as resp:
        data = resp.read()

    sha256 = hashlib.sha256(data).hexdigest()
    print(f"    SHA256: {sha256}")
    print(f"    Größe: {len(data) / (1024 * 1024):.1f} MB")

    print("    Entpacke …")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        # DLL liegt typischerweise direkt oder in einem Unterordner
        found = False
        for name in zf.namelist():
            if Path(name).name == "MediaInfo.dll":
                target = VENDOR / "MediaInfo.dll"
                target.write_bytes(zf.read(name))
                print(f"    → {target}")
                found = True
                break

        if not found:
            print("FEHLER: MediaInfo.dll nicht im Archiv gefunden.")
            print("Archiv-Inhalt:")
            for name in zf.namelist():
                print(f"  {name}")
            sys.exit(1)

    print()
    print(f"==> Fertig! DLL in {VENDOR}")


if __name__ == "__main__":
    download_and_extract()
