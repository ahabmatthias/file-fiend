"""
Geteilte UI-Utilities
"""

import asyncio
import tkinter
import tkinter.filedialog
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

_tk_executor = ThreadPoolExecutor(max_workers=1)


async def pick_folder() -> Optional[str]:
    """Öffnet nativen Ordner-Auswahl-Dialog via tkinter."""
    loop = asyncio.get_event_loop()

    def _dialog() -> Optional[str]:
        root = tkinter.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", True)
        folder = tkinter.filedialog.askdirectory()
        root.destroy()
        return folder or None

    return await loop.run_in_executor(_tk_executor, _dialog)
