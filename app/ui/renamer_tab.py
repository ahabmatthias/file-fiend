"""
UI-Tab: Media Renamer
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from nicegui import ui

from app.core.renamer import collect_files, process_files
from app.ui.utils import pick_folder

_executor = ThreadPoolExecutor(max_workers=1)


def build(tab_panel):
    """Baut den Media-Renamer-Tab in das übergebene tab_panel."""
    with tab_panel:
        # ── Ordner-Auswahl ─────────────────────────────────────────────
        with ui.row().classes("w-full items-center gap-2"):
            folder_input = ui.input(
                label="Ordner",
                placeholder="/Users/du/Bilder",
            ).classes("flex-1")

            async def on_pick():
                result = await pick_folder()
                if result:
                    folder_input.set_value(result)

            ui.button("Ordner wählen", on_click=on_pick, icon="folder_open")

        # ── Status / Ergebnis ──────────────────────────────────────────
        status_label = ui.label("").classes("text-slate-500 text-sm")
        preview_col = ui.column().classes("w-full gap-2")

        # Zwischenspeicher für Vorschau-Daten
        _state: dict = {"files": None, "has_preview": False}

        # ── Vorschau ───────────────────────────────────────────────────
        async def do_preview():
            folder = folder_input.value.strip()
            if not folder:
                ui.notify("Bitte einen Ordner eingeben.", type="negative")
                return
            if not os.path.isdir(folder):
                ui.notify("Ordner nicht gefunden.", type="negative")
                return

            status_label.set_text("Scanne …")
            preview_col.clear()
            _state["files"] = None
            _state["has_preview"] = False
            btn_rename.disable()

            loop = asyncio.get_event_loop()
            files = await loop.run_in_executor(_executor, collect_files, folder)

            if not files:
                status_label.set_text("Keine Mediendateien gefunden.")
                return

            results = await loop.run_in_executor(
                _executor, lambda: process_files(files, dry_run=True)
            )

            _state["files"] = files
            all_changes = results["renames"] + results["corrections"]

            status_label.set_text(
                f"{len(files)} Dateien · {len(all_changes)} Umbenennungen · "
                f"{results['unchanged']} unverändert · {results['errors']} Fehler"
            )

            if all_changes:
                _state["has_preview"] = True
                btn_rename.enable()
                with preview_col:
                    with ui.card().classes("w-full"):
                        ui.label("Vorschau (alt → neu):").classes(
                            "font-semibold text-sm mb-1"
                        )
                        shown = all_changes[:50]
                        for item in shown:
                            with ui.row().classes("w-full items-center gap-2"):
                                ui.label(item["old_name"]).classes(
                                    "text-red-400 flex-1 truncate font-mono text-xs"
                                )
                                ui.icon("arrow_forward").classes("text-slate-400 text-xs")
                                ui.label(item["new_name"]).classes(
                                    "text-green-400 flex-1 truncate font-mono text-xs"
                                )
                        if len(all_changes) > 50:
                            ui.label(
                                f"… und {len(all_changes) - 50} weitere"
                            ).classes("text-xs text-slate-400 mt-1")
            else:
                status_label.set_text("Alle Dateien bereits korrekt benannt. ✓")

        ui.button("Vorschau", on_click=do_preview, icon="preview").classes("mt-2")

        ui.separator()

        # ── Umbenennen ─────────────────────────────────────────────────
        async def do_rename():
            if not _state.get("files") or not _state.get("has_preview"):
                return

            status_label.set_text("Benenne um …")
            btn_rename.disable()
            preview_col.clear()

            files = _state["files"]
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                _executor, lambda: process_files(files, dry_run=False)
            )

            total = len(results["renames"]) + len(results["corrections"])
            msg = f"{total} Datei(en) umbenannt."
            if results["errors"]:
                msg += f"  {results['errors']} Fehler."
            ui.notify(msg, type="positive" if not results["errors"] else "warning")
            status_label.set_text(msg)
            _state["files"] = None
            _state["has_preview"] = False

        btn_rename = ui.button(
            "Umbenennen ausführen",
            on_click=do_rename,
            icon="drive_file_rename_outline",
            color="green",
        )
        btn_rename.disable()

        ui.label("Tipp: Vorher Backup erstellen!").classes("text-xs text-slate-400 mt-1")
