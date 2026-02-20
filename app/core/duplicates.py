"""
Duplikat-Finder: Scannt einen Ordner und gruppiert Dateien nach MD5-Hash.

Strategie:
  1. Alle Dateien nach Größe gruppieren  (nur stat-Aufruf, sehr schnell)
  2. Nur Größen-Gruppen mit ≥ 2 Dateien hashen  (eliminiert den Großteil)
  3. Hash-Gruppen mit ≥ 2 Dateien zurückgeben
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
    # Schritt 1: nach Größe gruppieren
    by_size: dict[int, list[Path]] = defaultdict(list)
    for root, _, files in os.walk(folder):
        for name in files:
            path = Path(root) / name
            if path.is_file() and not name.startswith("."):
                try:
                    by_size[path.stat().st_size].append(path)
                except (OSError, PermissionError):
                    pass

    # Schritt 2: nur Kandidaten (gleiche Größe) hashen
    hashes: dict[str, list[str]] = defaultdict(list)
    for paths in by_size.values():
        if len(paths) < 2:
            continue  # einzigartige Größe → kein Duplikat möglich
        for path in paths:
            try:
                h = _md5(path)
                hashes[h].append(str(path))
            except (OSError, PermissionError):
                pass

    return {h: paths for h, paths in hashes.items() if len(paths) > 1}
