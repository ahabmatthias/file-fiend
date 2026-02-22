"""
UI-Tab: Media Renamer
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from nicegui import ui

from app.ui.utils import short_path as _short_path

_executor = ThreadPoolExecutor(max_workers=1)


def build(shared: dict):
    """Baut den Media-Renamer-Tab – wird innerhalb eines tab_panel aufgerufen."""
    cb_recursive = ui.checkbox("Mit Unterordnern", value=True).classes("mt-1")

    # ── Status + Spinner ───────────────────────────────────────────
    with ui.row().classes("items-center gap-3 mt-2"):
        spinner = ui.spinner(size="sm").classes("text-slate-400")
        spinner.visible = False
        status_label = ui.label("").classes("text-slate-500 text-sm")

    preview_col = ui.column().classes("w-full gap-2 mt-2")
    _state: dict = {"files": None, "has_preview": False}

    # ── Vorschau ───────────────────────────────────────────────────
    async def do_preview():
        folder = shared["folder"].strip() if shared else ""
        if not folder:
            ui.notify("Bitte einen Ordner eingeben.", type="negative")
            return
        if not os.path.isdir(folder):
            ui.notify("Ordner nicht gefunden.", type="negative")
            return

        spinner.visible = True
        status_label.set_text("Scanne …")
        preview_col.clear()
        _state["files"] = None
        _state["has_preview"] = False
        btn_rename.disable()

        from app.core.renamer import collect_files, process_files  # noqa: PLC0415

        loop = asyncio.get_event_loop()
        recursive = cb_recursive.value
        files = await loop.run_in_executor(
            _executor, lambda: collect_files(folder, recursive=recursive)
        )

        if not files:
            spinner.visible = False
            status_label.set_text("Keine Mediendateien gefunden.")
            return

        results = await loop.run_in_executor(_executor, lambda: process_files(files, dry_run=True))

        spinner.visible = False
        _state["files"] = files
        all_changes = results["renames"]

        status_label.set_text(
            f"{len(files)} Dateien gefunden · "
            f"{len(all_changes)} würden umbenannt · "
            f"{results['unchanged']} bereits korrekt · "
            f"{results['errors']} Fehler"
        )

        if all_changes:
            _state["has_preview"] = True
            btn_rename.enable()
            with preview_col:
                with ui.card().classes("w-full"):
                    ui.label("Vorschau (alt → neu):").classes("font-semibold text-sm mb-2")
                    for item in all_changes[:50]:
                        old_short = _short_path(str(Path(folder) / item["old_name"]), folder)
                        new_short = _short_path(str(Path(folder) / item["new_name"]), folder)
                        with ui.row().classes("w-full items-center gap-2"):
                            ui.label(old_short).classes(
                                "text-red-400 flex-1 truncate font-mono text-xs"
                            )
                            ui.icon("arrow_forward").classes("text-slate-400 text-xs")
                            ui.label(new_short).classes(
                                "text-green-400 flex-1 truncate font-mono text-xs"
                            )
                    if len(all_changes) > 50:
                        ui.label(f"… und {len(all_changes) - 50} weitere").classes(
                            "text-xs text-slate-400 mt-1"
                        )
        else:
            status_label.set_text("Alle Dateien bereits korrekt benannt. ✓")

    ui.button("Vorschau", on_click=do_preview, icon="preview").classes("mt-2")

    ui.separator().classes("mt-4")

    # ── Umbenennen ─────────────────────────────────────────────────
    async def _execute_rename():
        spinner.visible = True
        status_label.set_text("Benenne um …")
        btn_rename.disable()
        preview_col.clear()

        from app.core.renamer import process_files  # noqa: PLC0415

        files = _state["files"]
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(_executor, lambda: process_files(files, dry_run=False))

        spinner.visible = False
        total = len(results["renames"])
        msg = f"{total} Datei(en) umbenannt."
        if results["errors"]:
            msg += f"  {results['errors']} Fehler."
        ui.notify(msg, type="positive" if not results["errors"] else "warning")

        if results.get("error_details"):
            with preview_col:
                with ui.card().classes("w-full"):
                    ui.label("Fehler:").classes("font-semibold text-sm text-red-400 mb-1")
                    for err in results["error_details"][:20]:
                        ui.label(f"{err['file']}: {err['error']}").classes(
                            "text-xs text-red-300 font-mono"
                        )
        status_label.set_text(msg)
        _state["files"] = None
        _state["has_preview"] = False

    async def do_rename():
        if not _state.get("files") or not _state.get("has_preview"):
            return

        n_renames = len([f for f in _state["files"] if not f["is_renamed"]])

        async def _confirm_and_rename():
            dialog.close()
            await _execute_rename()

        with ui.dialog() as dialog, ui.card():
            ui.label(f"{n_renames} Datei(en) umbenennen?").classes("font-semibold")
            ui.label("Die Originalnamen gehen verloren.").classes("text-sm text-slate-500")
            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Abbrechen", on_click=dialog.close)
                ui.button("Umbenennen", on_click=_confirm_and_rename, color="green")
        dialog.open()

    btn_rename = ui.button(
        "Umbenennen ausführen",
        on_click=do_rename,
        icon="drive_file_rename_outline",
        color="green",
    )
    btn_rename.disable()

    ui.label("Tipp: Vorher Backup erstellen!").classes("text-xs text-slate-400 mt-1")
