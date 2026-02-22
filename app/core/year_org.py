"""
Wrapper um year_folder_script.py für die UI-Integration.

Kapselt die Einzelfunktionen, unterdrückt print/tqdm-Output
und gibt strukturierte Dicts zurück.

Jahres-Erkennung: Dateiname zuerst, dann EXIF/Metadata als Fallback.
Kamera-Erkennung: EXIF model → EXIF make → Dateiname-Präfix → Sonstige.
"""

import contextlib
import io
import re
import shutil
from collections import defaultdict
from pathlib import Path

from PIL import Image

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass  # HEIC-Support optional – ohne Plugin werden HEIC-Dateien übersprungen

from unified_media_renamer import get_metadata
from year_folder_script import (
    create_year_folders,
    extract_year_from_filename,
    find_empty_folders,
    find_filename_conflicts,
    move_files_to_year_folders,
)

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic"}
_EXIF_DATETIME_TAGS = (36867, 36868, 306)  # DateTimeOriginal, DateTimeDigitized, DateTime
_CAMERA_MAPPINGS = {
    "GH5": "Lumix",
    "GX80": "Lumix",
    "DJI": "Osmo",
}
# Matcht XMP-Datumsattribute wie MetadataDate="2024-..." oder DateTimeOriginal>2024...
_XMP_DATE_RE = re.compile(
    r'(?:DateTimeOriginal|CreateDate|DateCreated|MetadataDate)[="\s>:]+(\d{4})'
)
_SUPPORTED_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".tiff",
    ".bmp",
    ".heic",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".aac",
    ".wav",
    ".mp3",
    ".m4a",
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
            xmp_raw = img.info.get("xmp")
            if xmp_raw:
                xmp = (
                    xmp_raw.decode("utf-8", errors="ignore")
                    if isinstance(xmp_raw, bytes)
                    else xmp_raw
                )
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
            if f.name == ".DS_Store" or f.name.startswith("._"):
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


def _detect_camera(file_path: Path) -> str:
    """
    Erkennt die Kamera aus EXIF-Daten oder Dateinamen.
    Reihenfolge: EXIF model → EXIF make → Dateiname-Präfix → 'Sonstige'.
    """
    file_type = "image" if file_path.suffix.lower() in _IMAGE_EXTS else "video"
    try:
        meta = _run_silent(get_metadata, str(file_path), file_type)
    except Exception:
        meta = {}

    # 1. EXIF model
    model = meta.get("model", "")
    if model:
        if "DC-GH5" in model or "GH5" in model:
            return _CAMERA_MAPPINGS["GH5"]
        if "DMC-GX80" in model or "GX80" in model:
            return _CAMERA_MAPPINGS["GX80"]
        if "PP-101" in model or "DJI" in model:
            return _CAMERA_MAPPINGS["DJI"]

    # 2. EXIF make
    make = meta.get("make", "")
    if make:
        if "DJI" in make:
            return _CAMERA_MAPPINGS["DJI"]
        if "Panasonic" in make:
            return _CAMERA_MAPPINGS["GX80"]

    # 3. Dateiname-Präfix
    if file_path.name.upper().startswith("DJI_"):
        return _CAMERA_MAPPINGS["DJI"]

    return "Sonstige"


def _extract_year(file_path: Path) -> int | None:
    """
    Jahres-Erkennung mit zwei Stufen:
    1. Dateiname (erste 4 Zeichen, schnell)
    2. EXIF/Metadata-Fallback via get_metadata()
    """
    year = extract_year_from_filename(file_path.name)
    if year:
        return int(year)

    if file_path.suffix.lower() in _IMAGE_EXTS:
        return _read_exif_year(file_path)

    # Video-Fallback: pymediainfo via get_metadata()
    try:
        meta = _run_silent(get_metadata, str(file_path), "video")
        dt = meta.get("datetime")
        if dt:
            y = dt.year
            if 1990 <= y <= 2030:
                return int(y)
    except Exception:
        pass

    return None


def _collect_files_with_years(folder_path: str, group_by_camera: bool = False):
    """
    Sammelt Mediendateien und gruppiert sie nach Jahr (und optional Kamera).

    Rückgabe wenn group_by_camera=False: ({year: [Path, ...]}, invalid_files)
    Rückgabe wenn group_by_camera=True:  ({year: {camera: [Path, ...]}}, invalid_files)
    """
    folder = Path(folder_path)
    if group_by_camera:
        files_by_year: dict = defaultdict(lambda: defaultdict(list))
    else:
        files_by_year = defaultdict(list)
    invalid_files = []

    for file_path in folder.rglob("*"):
        if not file_path.is_file():
            continue
        if (
            file_path.name.startswith("._")
            or file_path.name == ".DS_Store"
            or file_path.name.startswith("rename_log_")
            or file_path.name.startswith("camera_rename_log_")
            or file_path.parent.name == "duplicates"
        ):
            continue
        if file_path.suffix.lower() not in _SUPPORTED_EXTS:
            continue

        year = _extract_year(file_path)
        if year is None:
            invalid_files.append(
                {
                    "path": file_path,
                    "reason": "Jahr nicht erkennbar (Dateiname + Metadata geprüft)",
                }
            )
        elif group_by_camera:
            camera = _detect_camera(file_path)
            files_by_year[year][camera].append(file_path)
        else:
            files_by_year[year].append(file_path)

    return files_by_year, invalid_files


def scan_folder(folder_path: str, group_by_camera: bool = False) -> dict:
    """
    Scannt den Ordner und gibt eine Vorschau zurück – ohne Dateien zu bewegen
    und ohne Log-File zu schreiben.

    Rückgabe (group_by_camera=False):
        {
            "files_by_year":   {int: [Path, ...]},
            "invalid_files":   [...],
            "conflicts":       [...],
            "total_files":     int,
            "group_by_camera": False,
        }

    Rückgabe (group_by_camera=True):
        {
            "files_by_year":   {int: {str: [Path, ...]}},
            "invalid_files":   [...],
            "conflicts":       [...],
            "total_files":     int,
            "group_by_camera": True,
        }
    """
    folder = Path(folder_path)

    files_by_year, invalid_files = _collect_files_with_years(folder_path, group_by_camera)

    # Konflikt-Prüfung braucht flache {year: [Path, ...]} Struktur
    conflicts: list = []
    if files_by_year:
        if group_by_camera:
            flat = {
                year: [f for paths in cam_dict.values() for f in paths]
                for year, cam_dict in files_by_year.items()
            }
        else:
            flat = files_by_year
        conflicts = _run_silent(find_filename_conflicts, flat, folder)

    if group_by_camera:
        total = sum(
            len(paths) for cam_dict in files_by_year.values() for paths in cam_dict.values()
        )
    else:
        total = sum(len(f) for f in files_by_year.values())

    return {
        "files_by_year": {k: dict(v) if group_by_camera else v for k, v in files_by_year.items()},
        "invalid_files": invalid_files,
        "conflicts": conflicts,
        "total_files": total,
        "group_by_camera": group_by_camera,
    }


def _move_with_camera_groups(files_by_year: dict, folder: Path):
    """
    Verschiebt Dateien in <folder>/<year>/<camera>/ Unterordner.
    Gibt (moved_files, errors) zurück.
    """
    moved_files = []
    errors = []

    for year in sorted(files_by_year.keys()):
        cam_dict = files_by_year[year]
        for camera, paths in cam_dict.items():
            target_dir = folder / str(year) / camera
            target_dir.mkdir(parents=True, exist_ok=True)
            for file_path in paths:
                target_path = target_dir / file_path.name
                if target_path.exists() and target_path != file_path:
                    errors.append(
                        {
                            "file": file_path,
                            "target": target_path,
                            "error": "Zieldatei existiert bereits",
                        }
                    )
                    continue
                try:
                    if file_path.parent != target_dir:
                        shutil.move(str(file_path), str(target_path))
                    moved_files.append({"source": file_path, "target": target_path})
                except Exception as e:
                    errors.append({"file": file_path, "target": target_path, "error": str(e)})

    return moved_files, errors


def execute_organization(folder_path: str, group_by_camera: bool = False) -> dict:
    """
    Führt die Jahr-Organisation durch (verschiebt Dateien, löscht leere Ordner).

    Wenn group_by_camera=True: Zielstruktur ist <year>/<camera>/<datei>.

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

    files_by_year, invalid_files = _collect_files_with_years(folder_path, group_by_camera)

    if not files_by_year:
        return {
            "error": "Keine Dateien mit erkennbarem Jahr gefunden.",
            "moved": 0,
            "errors": 0,
            "removed_folders": 0,
            "error_details": [],
        }

    # Konflikt-Prüfung mit flacher Struktur
    if group_by_camera:
        flat = {
            year: [f for paths in cam_dict.values() for f in paths]
            for year, cam_dict in files_by_year.items()
        }
    else:
        flat = files_by_year

    conflicts = _run_silent(find_filename_conflicts, flat, folder)
    if conflicts:
        return {
            "error": f"{len(conflicts)} Dateiname-Konflikte – Organisation abgebrochen.",
            "conflicts": conflicts,
            "moved": 0,
            "errors": 0,
            "removed_folders": 0,
            "error_details": [],
        }

    if group_by_camera:
        moved_files, move_errors = _move_with_camera_groups(files_by_year, folder)
    else:
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
