"""
Mediendateien umbenennen nach Schema YYYY-MM-DD_HHMMSS_<original-stem>.<ext>.
Bereits umbenannte Dateien (Muster erkannt) werden übersprungen.
"""

import re
from datetime import datetime
from pathlib import Path

from app.core.constants import IMAGE_EXTS, VIDEO_EXTS

_SUPPORTED_EXTS = IMAGE_EXTS | VIDEO_EXTS

_RENAMED_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}_(?:\d{2}-\d{2}-\d{2}|\d{6})_[A-Za-z0-9].*\.[a-zA-Z0-9]+$"
)


def detect_file_status(filename: str) -> bool:
    """Gibt True zurück wenn die Datei bereits umbenannt wurde."""
    return _RENAMED_PATTERN.match(filename) is not None


def get_metadata(file_path: str, file_type: str) -> dict:
    """Extrahiert datetime, make, model aus Bild/Video-Metadaten."""
    from PIL import Image  # noqa: PLC0415
    from PIL.ExifTags import TAGS  # noqa: PLC0415
    from pymediainfo import MediaInfo  # noqa: PLC0415

    try:
        if file_type == "image":
            with Image.open(file_path) as image:
                exif_data = image.getexif()
                if not exif_data:
                    return {}
                metadata: dict = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if (
                        tag == "DateTimeOriginal" or tag == "DateTime"
                    ) and "datetime" not in metadata:
                        try:
                            metadata["datetime"] = datetime.strptime(
                                str(value), "%Y:%m:%d %H:%M:%S"
                            )
                        except ValueError:
                            pass
                    elif tag in ("Make", "Model"):
                        metadata[str(tag).lower()] = str(value)
                return metadata
        elif file_type == "video":
            media_info = MediaInfo.parse(file_path)
            for track in media_info.tracks:
                if track.track_type != "General":
                    continue
                raw_date = track.recorded_date or track.encoded_date or track.tagged_date
                if not raw_date:
                    continue
                date_str = str(raw_date).replace(" UTC", "")[:19]
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        return {"datetime": datetime.strptime(date_str, fmt)}
                    except ValueError:
                        continue
    except Exception:
        pass
    return {}


def _generate_filename(file_path: Path, metadata: dict) -> str:
    """Generiert neuen Dateinamen: YYYY-MM-DD_HHMMSS_<original-stem>.<ext>"""
    date_time = None

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", file_path.name)
    if date_match:
        try:
            date_time = datetime.strptime(date_match.group(1) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    if not date_time:
        date_time = metadata.get("datetime")

    if not date_time:
        date_time = datetime.fromtimestamp(file_path.stat().st_mtime)

    date_str = date_time.strftime("%Y-%m-%d_%H%M%S")
    ext = file_path.suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"

    return f"{date_str}_{file_path.stem}{ext}"


def collect_files(
    folder_path: str, recursive: bool = True, extensions: set[str] | None = None
) -> list[dict]:
    """Sammelt alle Mediendateien im Ordner."""
    folder = Path(folder_path)
    files = []
    exts = extensions if extensions is not None else _SUPPORTED_EXTS
    image_exts_in_scope = IMAGE_EXTS & exts

    glob_fn = folder.rglob if recursive else folder.glob
    for file_path in glob_fn("*"):
        if (
            file_path.is_file()
            and file_path.suffix.lower() in exts
            and not file_path.name.startswith("._")
            and file_path.name != ".DS_Store"
        ):
            file_type = "image" if file_path.suffix.lower() in image_exts_in_scope else "video"
            files.append(
                {
                    "path": file_path,
                    "type": file_type,
                    "is_renamed": detect_file_status(file_path.name),
                }
            )

    return files


def process_files(files_list: list[dict], dry_run: bool = True) -> dict:
    """Benennt Dateien um (oder simuliert es im dry_run)."""
    results: dict = {
        "processed": 0,
        "unchanged": 0,
        "errors": 0,
        "error_details": [],
        "renames": [],
    }

    for file_info in files_list:
        try:
            file_path = file_info["path"]

            if file_info["is_renamed"]:
                results["unchanged"] += 1
                continue

            metadata = get_metadata(str(file_path), file_info["type"])
            new_filename = _generate_filename(file_path, metadata)

            if new_filename == file_path.name:
                results["unchanged"] += 1
                continue

            new_path = file_path.parent / new_filename
            if new_path.exists():
                base_stem, _, ext = new_filename.rpartition(".")
                counter = 1
                while new_path.exists():
                    new_filename = f"{base_stem}_({counter}).{ext}"
                    new_path = file_path.parent / new_filename
                    counter += 1

            if not dry_run:
                file_path.rename(new_path)

            results["renames"].append({"old_name": file_path.name, "new_name": new_filename})
            results["processed"] += 1

        except Exception as e:
            results["errors"] += 1
            results["error_details"].append(
                {"file": str(file_info.get("path", "?")), "error": str(e)}
            )

    return results


__all__ = ["collect_files", "detect_file_status", "process_files", "get_metadata"]
