"""
UI-Tab: Duplikat-Finder
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from nicegui import ui

from app.core.duplicates import find_duplicates
from app.ui.utils import pick_folder as _pick_folder

_executor = ThreadPoolExecutor(max_workers=1)


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
            dupes = await loop.run_in_executor(
                _executor, find_duplicates, folder
            )

            spinner.visible = False

            if not dupes:
                status_label.set_text("Keine Duplikate gefunden.")
                return

            total_files = sum(len(v) for v in dupes.values())
            status_label.set_text(
                f"{len(dupes)} Duplikat-Gruppe(n) · {total_files} Dateien"
            )

            with results_col:
                for group_hash, paths in dupes.items():
                    with ui.card().classes("w-full"):
                        ui.label(f"Hash: {group_hash[:12]}…").classes(
                            "text-xs text-slate-400 font-mono"
                        )
                        for path in paths:
                            size_kb = Path(path).stat().st_size // 1024
                            cb = ui.checkbox(f"{path}  ({size_kb} KB)")
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
            ui.label("Tipp: Mindestens eine Kopie behalten!").classes(
                "text-xs text-slate-400"
            )
