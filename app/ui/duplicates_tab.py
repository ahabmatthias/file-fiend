"""
UI-Tab: Duplikat-Finder
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from nicegui import app as nicegui_app
from nicegui import ui

from app.core.duplicates import find_duplicates
from app.ui.utils import pick_folder as _pick_folder

_executor = ThreadPoolExecutor(max_workers=1)

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}

# Gemountete Static-Routen merken um Duplikate zu vermeiden
_mounted_routes: set[str] = set()


def _static_url(path: str) -> str | None:
    """Gibt eine servierbare URL für lokale Bilddateien zurück."""
    p = Path(path)
    ext = p.suffix.lower()
    if ext not in _IMAGE_EXTS:
        return None
    folder = str(p.parent)
    route = f"/preview{abs(hash(folder)) % 100000}"
    if route not in _mounted_routes:
        nicegui_app.add_static_files(route, folder)
        _mounted_routes.add(route)
    return f"{route}/{p.name}"


def _file_icon(path: str) -> str:
    """Gibt ein Material-Icon für den Dateityp zurück."""
    ext = Path(path).suffix.lower()
    if ext in _VIDEO_EXTS:
        return "videocam"
    if ext == ".heic":
        return "photo"
    return "insert_drive_file"


def build(tab_panel):
    """Baut den Duplikat-Finder-Tab in das übergebene tab_panel."""
    with tab_panel:
        # ── Ordner-Auswahl ─────────────────────────────────────────────
        with ui.row().classes("w-full items-center gap-2"):
            folder_input = ui.input(
                label="Ordner",
                placeholder="/Users/du/Bilder",
            ).classes("flex-1")

            async def on_pick():
                result = await _pick_folder()
                if result:
                    folder_input.set_value(result)

            ui.button("Ordner wählen", on_click=on_pick, icon="folder_open")

        # ── Status + Spinner ───────────────────────────────────────────
        with ui.row().classes("items-center gap-3 mt-2"):
            spinner = ui.spinner(size="sm").classes("text-slate-400")
            spinner.visible = False
            status_label = ui.label("").classes("text-slate-500 text-sm")

        results_col = ui.column().classes("w-full gap-4 mt-2")
        checkboxes: dict = {}

        # ── Scan ───────────────────────────────────────────────────────
        async def do_scan():
            folder = folder_input.value.strip()
            if not folder or not os.path.isdir(folder):
                ui.notify("Bitte einen gültigen Ordner eingeben.", type="negative")
                return

            spinner.visible = True
            status_label.set_text("Scanne …")
            results_col.clear()
            checkboxes.clear()

            loop = asyncio.get_event_loop()
            dupes = await loop.run_in_executor(_executor, find_duplicates, folder)

            spinner.visible = False

            if not dupes:
                status_label.set_text("Keine Duplikate gefunden.")
                return

            total_files = sum(len(v) for v in dupes.values())
            status_label.set_text(f"{len(dupes)} Duplikat-Gruppe(n) · {total_files} Dateien")

            with results_col:
                for _group_hash, paths in dupes.items():
                    with ui.card().classes("w-full p-3"):
                        for path in paths:
                            size_kb = Path(path).stat().st_size // 1024
                            url = _static_url(path)
                            with ui.row().classes("items-center gap-3 w-full"):
                                # Vorschau
                                if url:
                                    ui.image(url).classes("w-20 h-20 object-cover rounded")
                                else:
                                    with ui.element("div").classes(
                                        "w-20 h-20 flex items-center justify-center "
                                        "bg-slate-100 rounded text-slate-400"
                                    ):
                                        ui.icon(_file_icon(path), size="2rem")

                                # Info + Checkbox
                                with ui.column().classes("flex-1 gap-0"):
                                    cb = ui.checkbox(Path(path).name)
                                    base = Path(folder).parent
                                    try:
                                        short = str(Path(path).relative_to(base))
                                    except ValueError:
                                        short = "/".join(Path(path).parts[-4:])
                                    ui.label(short).classes(
                                        "text-xs text-slate-400 truncate max-w-lg"
                                    )
                                    ui.label(f"{size_kb} KB").classes("text-xs text-slate-400")
                                checkboxes[cb] = path

        ui.button("Scannen", on_click=do_scan, icon="search")

        ui.separator().classes("mt-4")

        # ── Löschen ────────────────────────────────────────────────────
        async def do_delete():
            to_delete = [path for cb, path in checkboxes.items() if cb.value]
            if not to_delete:
                ui.notify("Keine Dateien ausgewählt.", type="warning")
                return

            deleted, errors = 0, []
            for path in to_delete:
                try:
                    if os.path.islink(path):
                        errors.append(f"{path}: Symlinks werden nicht gelöscht")
                        continue
                    os.remove(path)
                    deleted += 1
                except OSError as e:
                    errors.append(f"{path}: {e}")

            msg = f"{deleted} Datei(en) gelöscht."
            if errors:
                msg += f"  {len(errors)} Fehler."
            ui.notify(msg, type="positive" if not errors else "warning")
            await do_scan()

        with ui.row().classes("items-center gap-4"):
            ui.button(
                "Ausgewählte löschen",
                on_click=do_delete,
                icon="delete",
                color="red",
            )
            ui.label("Tipp: Mindestens eine Kopie behalten!").classes("text-xs text-slate-400")
