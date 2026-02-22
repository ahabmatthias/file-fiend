"""
Geteilte UI-Utilities
"""

from pathlib import Path


def short_path(path: str, folder: str) -> str:
    """Pfad relativ zum Parent des Scan-Ordners."""
    base = Path(folder).parent
    try:
        return str(Path(path).relative_to(base))
    except ValueError:
        return "/".join(Path(path).parts[-4:])


def validate_folder_path(folder: str) -> bool:
    """Prüft ob ein Pfad innerhalb des Home-Verzeichnisses liegt (Path-Traversal-Schutz)."""
    try:
        resolved = Path(folder).resolve()
        return resolved.is_relative_to(Path.home())
    except (ValueError, OSError):
        return False


async def pick_folder() -> str | None:
    """Öffnet nativen Ordner-Auswahl-Dialog via pywebview."""
    import webview
    from nicegui import app as nicegui_app

    window = nicegui_app.native.main_window
    if window is None:
        return None
    result = await window.create_file_dialog(dialog_type=webview.FileDialog.FOLDER)
    return result[0] if result else None
