"""
Geteilte UI-Utilities
"""

from pathlib import Path
from typing import Optional


def validate_folder_path(folder: str) -> bool:
    """Prüft ob ein Pfad innerhalb des Home-Verzeichnisses liegt (Path-Traversal-Schutz)."""
    try:
        resolved = Path(folder).resolve()
        return resolved.is_relative_to(Path.home())
    except (ValueError, OSError):
        return False


async def pick_folder() -> Optional[str]:
    """Öffnet nativen Ordner-Auswahl-Dialog via pywebview."""
    import webview
    from nicegui import app as nicegui_app

    result = await nicegui_app.native.main_window.create_file_dialog(
        dialog_type=webview.FileDialog.FOLDER
    )
    return result[0] if result else None
