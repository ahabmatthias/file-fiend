"""
Geteilte UI-Utilities
"""

from pathlib import Path

from app.core.constants import AUDIO_EXTS, IMAGE_EXTS, VIDEO_EXTS


def short_path(path: str, folder: str) -> str:
    """Pfad relativ zum Parent des Scan-Ordners."""
    base = Path(folder).parent
    try:
        return str(Path(path).relative_to(base))
    except ValueError:
        return "/".join(Path(path).parts[-4:])


def validate_folder_path(folder: str) -> bool:
    """Prüft ob ein Pfad in einem erlaubten Bereich liegt (Home + externe Laufwerke).

    Blockt System-Verzeichnisse wie /System, /usr, C:\\Windows etc.
    Erlaubt Home-Verzeichnis und externe Medien (/Volumes/, D:\\ etc.).
    """
    import sys

    try:
        resolved = Path(folder).resolve()
    except (ValueError, OSError):
        return False

    # Home ist immer erlaubt
    if resolved.is_relative_to(Path.home()):
        return True

    # macOS: /Volumes/ für externe Laufwerke
    if sys.platform == "darwin" and resolved.is_relative_to(Path("/Volumes")):
        return True

    # Windows: jedes Nicht-System-Laufwerk (z.B. D:\, E:\)
    if sys.platform == "win32":
        drive = resolved.drive.upper()
        # Erlaube alles außer leeres Drive; blocke Windows-Systemordner
        if drive and not resolved.is_relative_to(Path(f"{drive}\\Windows")):
            return True

    return False


def build_ext_filter(fotos: bool, videos: bool, audio: bool = False) -> set[str]:
    """Erstellt Extension-Set aus Checkbox-Zuständen."""
    exts: set[str] = set()
    if fotos:
        exts |= IMAGE_EXTS
    if videos:
        exts |= VIDEO_EXTS
    if audio:
        exts |= AUDIO_EXTS
    return exts


async def pick_folder() -> str | None:
    """Öffnet nativen Ordner-Auswahl-Dialog via pywebview."""
    import webview
    from nicegui import app as nicegui_app

    window = nicegui_app.native.main_window
    if window is None:
        return None
    result = await window.create_file_dialog(dialog_type=webview.FileDialog.FOLDER)
    return result[0] if result else None
