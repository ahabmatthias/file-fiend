"""
Geteilte UI-Utilities
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

_executor = ThreadPoolExecutor(max_workers=1)


async def pick_folder() -> Optional[str]:
    """Öffnet nativen Ordner-Auswahl-Dialog via pywebview."""
    loop = asyncio.get_event_loop()

    def _dialog() -> Optional[str]:
        import webview
        from nicegui import app as nicegui_app
        result = nicegui_app.native.main_window.create_file_dialog(
            dialog_type=webview.FOLDER_DIALOG
        )
        return result[0] if result else None

    return await loop.run_in_executor(_executor, _dialog)
