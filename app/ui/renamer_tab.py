"""
UI-Tab: Media Renamer
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path

from nicegui import ui

from app.ui import theme
from app.ui.utils import build_ext_filter, validate_folder_path
from app.ui.utils import short_path as _short_path

_executor = ThreadPoolExecutor(max_workers=1)


def build(shared: dict):
    """Baut den Media-Renamer-Tab – wird innerhalb eines tab_panel aufgerufen."""
    with ui.row().classes("items-center gap-4 flex-wrap"):
        cb_recursive = ui.checkbox("Mit Unterordnern", value=True).classes("mt-1")
        cb_fotos = ui.checkbox("Fotos", value=True).classes("mt-1")
        cb_videos = ui.checkbox("Videos", value=True).classes("mt-1")

    # ── Status + Spinner ───────────────────────────────────────────
    with ui.row().classes("items-center gap-3 mt-2"):
        spinner = ui.spinner(size="sm").classes("text-[#4f8ef7]")
        spinner.visible = False
        status_label = ui.label("").classes("mt-hint")

    # ── Pills-Zeile (wird nach Scan / Ausführen befüllt) ──────────
    pills_row = ui.row().classes("items-center gap-2 mt-1")
    pills_row.visible = False

    preview_col = ui.column().classes("w-full gap-0 mt-2")
    _state: dict = {"files": None, "has_preview": False}

    def _show_pills(renames: int, unchanged: int, errors: int):
        pills_row.clear()
        pills_row.visible = True
        with pills_row:
            if renames:
                theme.pill(f"{renames} umbenennen", "neutral")
            if unchanged:
                theme.pill(f"{unchanged} korrekt", "good")
            if errors:
                theme.pill(f"{errors} Fehler", "danger")

    # ── Vorschau ───────────────────────────────────────────────────
    async def do_preview():
        folder = shared["folder"].strip() if shared else ""
        if not folder:
            ui.notify("Bitte einen Ordner eingeben.", type="negative")
            return
        if not os.path.isdir(folder):
            ui.notify("Ordner nicht gefunden.", type="negative")
            return
        if not validate_folder_path(folder):
            ui.notify("Ordner liegt außerhalb des Home-Verzeichnisses.", type="negative")
            return

        exts = build_ext_filter(cb_fotos.value, cb_videos.value)
        if not exts:
            status_label.set_text("Bitte mindestens einen Dateityp wählen.")
            return

        spinner.visible = True
        status_label.set_text("Scanne …")
        preview_col.clear()
        pills_row.visible = False
        _state["files"] = None
        _state["has_preview"] = False
        btn_rename.disable()

        from app.core.renamer import collect_files, process_files  # noqa: PLC0415

        loop = asyncio.get_event_loop()
        recursive = cb_recursive.value
        files = await loop.run_in_executor(
            _executor, lambda: collect_files(folder, recursive=recursive, extensions=exts)
        )

        if not files:
            spinner.visible = False
            status_label.set_text("Keine Mediendateien gefunden.")
            return

        results = await loop.run_in_executor(_executor, lambda: process_files(files, dry_run=True))

        spinner.visible = False
        _state["files"] = files
        _state["renames"] = results["renames"]
        all_changes = results["renames"]

        status_label.set_text(f"{len(files)} Dateien gefunden")
        _show_pills(len(all_changes), results["unchanged"], results["errors"])

        if all_changes:
            _state["has_preview"] = True
            btn_rename.enable()
            with preview_col:
                with ui.element("div").classes("mt-card"):
                    ui.html('<div class="mt-card-header">Vorschau</div>')
                    for item in all_changes[:50]:
                        old_short = _short_path(str(Path(folder) / item["old_name"]), folder)
                        new_short = _short_path(str(Path(folder) / item["new_name"]), folder)
                        ui.html(
                            f'<div class="mt-rename-row">'
                            f'<span class="mt-rename-old">{escape(old_short)}</span>'
                            f'<span class="mt-rename-arrow">→</span>'
                            f'<span class="mt-rename-new">{escape(new_short)}</span>'
                            f"</div>"
                        )
                    if len(all_changes) > 50:
                        ui.label(f"… und {len(all_changes) - 50} weitere").classes(
                            "mt-hint px-3 py-2"
                        )
        else:
            status_label.set_text("Alle Dateien bereits korrekt benannt.")

    ui.button("Vorschau", on_click=do_preview, icon="preview").classes("mt-btn-primary mt-2").props(
        "no-caps"
    )

    ui.separator().classes("mt-4")

    # ── Umbenennen ─────────────────────────────────────────────────
    async def _execute_rename():
        spinner.visible = True
        status_label.set_text("Benenne um …")
        btn_rename.disable()
        preview_col.clear()
        pills_row.visible = False

        from app.core.renamer import process_files  # noqa: PLC0415

        files = _state["files"]
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(_executor, lambda: process_files(files, dry_run=False))

        spinner.visible = False
        total = len(results["renames"])

        status_label.set_text(f"{total} Datei(en) umbenannt")
        _show_pills(0, total, results["errors"])

        if results.get("error_details"):
            with preview_col:
                with ui.element("div").classes("mt-card"):
                    ui.html('<div class="mt-card-header">Fehler</div>')
                    for err in results["error_details"][:20]:
                        ui.html(
                            f'<div class="mt-rename-row">'
                            f'<span class="mt-rename-old">{err["file"]}</span>'
                            f'<span class="mt-rename-arrow">✕</span>'
                            f'<span style="color:#f87171">{err["error"]}</span>'
                            f"</div>"
                        )

        _state["files"] = None
        _state["has_preview"] = False

    async def do_rename():
        if not _state.get("files") or not _state.get("has_preview"):
            return

        n_renames = len(_state.get("renames", []))

        async def _confirm_and_rename():
            dialog.close()
            await _execute_rename()

        with ui.dialog() as dialog, ui.card().classes("mt-card"):
            ui.label(f"{n_renames} Datei(en) umbenennen?").classes("font-semibold text-[#e2e8f0]")
            ui.label("Die Originalnamen gehen verloren.").classes("mt-hint")
            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                ui.button("Abbrechen", on_click=dialog.close).classes("mt-btn-ghost").props(
                    "no-caps"
                )
                ui.button("Umbenennen", on_click=_confirm_and_rename).classes(
                    "mt-btn-success"
                ).props("no-caps")
        dialog.open()

    btn_rename = (
        ui.button(
            "Umbenennen ausführen",
            on_click=do_rename,
            icon="drive_file_rename_outline",
        )
        .classes("mt-btn-success")
        .props("no-caps")
        .style("background-color: #34d399 !important; color: #0f1117 !important")
    )
    btn_rename.disable()

    ui.label("Tipp: Vorher Backup erstellen!").classes("mt-hint mt-1")
