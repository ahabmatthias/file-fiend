"""
Wrapper um year_folder_script.py für die UI-Integration.

Kapselt die Einzelfunktionen, unterdrückt print/tqdm-Output
und gibt strukturierte Dicts zurück.

Jahres-Erkennung: Dateiname zuerst, dann EXIF/Metadata als Fallback.
"""

import contextlib
import io
import re
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass  # HEIC-Support optional – ohne Plugin werden HEIC-Dateien übersprungen

# Projekt-Root zum Importpfad hinzufügen
_ROOT = Path(__file__).parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from unified_media_renamer import get_metadata  # noqa: E402
from year_folder_script import (  # noqa: E402
    create_year_folders,
    extract_year_from_filename,
    find_empty_folders,
    find_filename_conflicts,
    move_files_to_year_folders,
)

_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.heic'}
_EXIF_DATETIME_TAGS = (36867, 36868, 306)  # DateTimeOriginal, DateTimeDigitized, DateTime
# Matcht XMP-Datumsattribute wie MetadataDate="2024-..." oder DateTimeOriginal>2024...
_XMP_DATE_RE = re.compile(
    r'(?:DateTimeOriginal|CreateDate|DateCreated|MetadataDate)[="\s>:]+(\d{4})'
)
_SUPPORTED_EXTS = {
    '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.heic',
    '.mp4', '.mov', '.avi', '.mkv', '.aac', '.wav', '.mp3', '.m4a',
}


def _read_exif_year(file_path: Path) -> int | None:
    """
    Liest das Aufnahmejahr aus Bilddateien.
    Stufen: EXIF IFD0 → EXIF Sub-IFD (34665) → XMP-Metadaten.
    """
    try:
        with Image.open(file_path) as img:
            exif = img.getexif()
            # IFD0 + EXIF-Sub-IFD durchsuchen
            for source in (exif, exif.get_ifd(34665)):
                for tag in _EXIF_DATETIME_TAGS:
                    val = source.get(tag)
                    if val:
                        year = int(str(val)[:4])
                        if 1990 <= year <= 2030:
                            return year
            # XMP-Fallback (z.B. Photoshop-bearbeitete Sony-Dateien ohne DateTimeOriginal)
            xmp_raw = img.info.get('xmp')
            if xmp_raw:
                xmp = xmp_raw.decode('utf-8', errors='ignore') if isinstance(xmp_raw, bytes) else xmp_raw
                m = _XMP_DATE_RE.search(xmp)
                if m:
                    year = int(m.group(1))
                    if 1990 <= year <= 2030:
                        return year
    except Exception:
        pass
    return None


def _remove_empty_folders(empty_folders: list) -> list:
    """Löscht leere Ordner – entfernt vorher macOS-Systemdateien (.DS_Store, ._*)."""
    removed = []
    for folder in empty_folders:
        for f in folder.iterdir():
            if f.name == '.DS_Store' or f.name.startswith('._'):
                f.unlink()
        try:
            folder.rmdir()
            removed.append(folder)
        except OSError:
            pass  # Ordner doch nicht leer (z.B. Race condition)
    return removed


def _run_silent(fn, *args, **kwargs):
    """Führt fn(*args, **kwargs) aus und unterdrückt jede Ausgabe."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        return fn(*args, **kwargs)


def _extract_year(file_path: Path) -> int | None:
    """
    Jahres-Erkennung mit zwei Stufen:
    1. Dateiname (erste 4 Zeichen, schnell)
    2. EXIF/Metadata-Fallback via get_metadata()
    """
    year = extract_year_from_filename(file_path.name)
    if year:
        return year

    if file_path.suffix.lower() in _IMAGE_EXTS:
        return _read_exif_year(file_path)

    # Video-Fallback: pymediainfo via get_metadata()
    try:
        meta = _run_silent(get_metadata, str(file_path), "video")
        dt = meta.get("datetime")
        if dt:
            y = dt.year
            if 1990 <= y <= 2030:
                return y
    except Exception:
        pass

    return None


def _collect_files_with_years(folder_path: str):
    """
    Sammelt Mediendateien und gruppiert sie nach Jahr.
    Nutzt _extract_year() statt reiner Filename-Erkennung.
    """
    folder = Path(folder_path)
    files_by_year = defaultdict(list)
    invalid_files = []

    for file_path in folder.rglob('*'):
        if not file_path.is_file():
            continue
        if (
            file_path.name.startswith('._')
            or file_path.name == '.DS_Store'
            or file_path.name.startswith('rename_log_')
            or file_path.name.startswith('camera_rename_log_')
            or file_path.parent.name == 'duplicates'
        ):
            continue
        if file_path.suffix.lower() not in _SUPPORTED_EXTS:
            continue

        year = _extract_year(file_path)
        if year is None:
            invalid_files.append({
                'path': file_path,
                'reason': 'Jahr nicht erkennbar (Dateiname + Metadata geprüft)',
            })
        else:
            files_by_year[year].append(file_path)

    return files_by_year, invalid_files


def scan_folder(folder_path: str) -> dict:
    """
    Scannt den Ordner und gibt eine Vorschau zurück – ohne Dateien zu bewegen
    und ohne Log-File zu schreiben.

    Rückgabe:
        {
            "files_by_year": {int: [Path, ...]},
            "invalid_files": [{"path": Path, "reason": str}, ...],
            "conflicts":     [{"filename": str, "year": int, ...}, ...],
            "total_files":   int,
        }
    """
    folder = Path(folder_path)

    files_by_year, invalid_files = _collect_files_with_years(folder_path)

    conflicts: list = []
    if files_by_year:
        conflicts = _run_silent(find_filename_conflicts, files_by_year, folder)

    total = sum(len(f) for f in files_by_year.values())

    return {
        "files_by_year": dict(files_by_year),
        "invalid_files": invalid_files,
        "conflicts": conflicts,
        "total_files": total,
    }


def execute_organization(folder_path: str) -> dict:
    """
    Führt die Jahr-Organisation durch (verschiebt Dateien, löscht leere Ordner).

    Rückgabe:
        {
            "moved":           int,
            "errors":          int,
            "removed_folders": int,
            "error_details":   list,
            "error":           str | None,
        }
    """
    folder = Path(folder_path)

    files_by_year, invalid_files = _collect_files_with_years(folder_path)

    if not files_by_year:
        return {"error": "Keine Dateien mit erkennbarem Jahr gefunden.", "moved": 0,
                "errors": 0, "removed_folders": 0, "error_details": []}

    conflicts = _run_silent(find_filename_conflicts, files_by_year, folder)
    if conflicts:
        return {
            "error": f"{len(conflicts)} Dateiname-Konflikte – Organisation abgebrochen.",
            "conflicts": conflicts,
            "moved": 0, "errors": 0, "removed_folders": 0, "error_details": [],
        }

    _run_silent(create_year_folders, files_by_year, folder, dry_run=False)
    moved_files, move_errors = _run_silent(
        move_files_to_year_folders, files_by_year, folder, dry_run=False
    )

    empty_folders = _run_silent(find_empty_folders, folder_path)
    removed = _remove_empty_folders(empty_folders)

    return {
        "moved": len(moved_files),
        "errors": len(move_errors),
        "removed_folders": len(removed),
        "error_details": move_errors,
        "error": None,
    }
