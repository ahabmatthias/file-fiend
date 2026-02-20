"""
Geteilte UI-Utilities
"""

from typing import Optional


async def pick_folder() -> Optional[str]:
    """Öffnet nativen Ordner-Auswahl-Dialog via pywebview."""
    import webview
    from nicegui import app as nicegui_app
    result = await nicegui_app.native.main_window.create_file_dialog(
        dialog_type=webview.FileDialog.FOLDER
    )
    return result[0] if result else None
