"""
Duplikat-Finder: Scannt einen Ordner und gruppiert Dateien nach MD5-Hash.
"""

import hashlib
import os
from collections import defaultdict
from pathlib import Path


def _md5(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def find_duplicates(folder: str) -> dict[str, list[str]]:
    """
    Scannt `folder` rekursiv.
    Gibt {hash: [pfad1, pfad2, ...]} zurück – nur Gruppen mit ≥ 2 Dateien.
    """
    hashes: dict[str, list[str]] = defaultdict(list)

    for root, _, files in os.walk(folder):
        for name in files:
            path = Path(root) / name
            if path.is_file() and not name.startswith("."):
                try:
                    h = _md5(path)
                    hashes[h].append(str(path))
                except (OSError, PermissionError):
                    pass  # Datei nicht lesbar – überspringen

    return {h: paths for h, paths in hashes.items() if len(paths) > 1}
