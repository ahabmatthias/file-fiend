"""
UI-Tab: Jahr-Organisation
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from nicegui import ui

_executor = ThreadPoolExecutor(max_workers=1)


def build(shared: dict):
    """Baut den Jahr-Organisations-Tab – wird innerhalb eines tab_panel aufgerufen."""
    # ── Kamera-Checkbox ────────────────────────────────────────────
    camera_checkbox = ui.checkbox("Nach Kamera sortieren").classes("mt-1")
    ui.label("ⓘ Benötigt EXIF-Daten in den Dateien").classes("text-xs text-gray-400")

    # ── Status + Spinner ───────────────────────────────────────────
    with ui.row().classes("items-center gap-3 mt-2"):
        spinner = ui.spinner(size="sm").classes("text-slate-400")
        spinner.visible = False
        status_label = ui.label("").classes("text-slate-500 text-sm")

    progress_bar = ui.linear_progress(value=0).props("stripe")
    progress_bar.visible = False

    preview_col = ui.column().classes("w-full gap-2 mt-2")
    _state: dict = {"scan": None, "folder": None}

    # ── Vorschau ───────────────────────────────────────────────────
    async def do_preview():
        folder = shared["folder"].strip() if shared else ""
        if not folder:
            ui.notify("Bitte einen Ordner eingeben.", type="negative")
            return
        if not os.path.isdir(folder):
            ui.notify("Ordner nicht gefunden.", type="negative")
            return

        group_by_camera = camera_checkbox.value
        spinner.visible = True
        status_label.set_text("Scanne …")
        preview_col.clear()
        _state["scan"] = None
        _state["folder"] = None
        btn_execute.disable()
        progress_bar.set_value(0)
        progress_bar.visible = True

        from app.core.year_org import scan_folder  # noqa: PLC0415

        loop = asyncio.get_event_loop()

        async def _update_scan_progress(value: float):
            progress_bar.set_value(value)

        def scan_progress_cb(done, total):
            asyncio.run_coroutine_threadsafe(_update_scan_progress(done / total), loop)

        result = await loop.run_in_executor(
            _executor,
            lambda: scan_folder(folder, group_by_camera, progress_cb=scan_progress_cb),
        )

        spinner.visible = False
        progress_bar.visible = False

        if not result["files_by_year"]:
            status_label.set_text("Keine Dateien mit erkennbarem Jahr gefunden.")
            return

        _state["scan"] = result
        _state["folder"] = folder

        conflict_info = f" · ⚠ {len(result['conflicts'])} Konflikte" if result["conflicts"] else ""
        status_label.set_text(
            f"{result['total_files']} Dateien · "
            f"{len(result['files_by_year'])} Jahre · "
            f"{len(result['invalid_files'])} Ungültige"
            f"{conflict_info}"
        )

        with preview_col:
            with ui.card().classes("w-full"):
                if group_by_camera:
                    ui.label("Vorschau – Dateien pro Jahr/Kamera:").classes(
                        "font-semibold text-sm mb-2"
                    )
                    for year in sorted(result["files_by_year"].keys()):
                        cam_dict = result["files_by_year"][year]
                        ui.label(f"📁  {year}/").classes("font-mono text-sm font-semibold")
                        for camera in sorted(cam_dict.keys()):
                            count = len(cam_dict[camera])
                            ui.label(f"    └─ {camera}  ({count} Datei(en))").classes(
                                "font-mono text-sm text-slate-300 pl-4"
                            )
                else:
                    ui.label("Vorschau – Dateien pro Jahr:").classes("font-semibold text-sm mb-2")
                    for year in sorted(result["files_by_year"].keys()):
                        files = result["files_by_year"][year]
                        ui.label(f"📁  {year}/  →  {len(files)} Datei(en)").classes(
                            "font-mono text-sm"
                        )

                if result["invalid_files"]:
                    ui.separator().classes("my-2")
                    ui.label(
                        f"Ungültig ({len(result['invalid_files'])}) – kein Jahr erkennbar:"
                    ).classes("text-slate-400 text-sm")
                    for inv in result["invalid_files"][:10]:
                        ui.label(f"  • {inv['path'].name}").classes(
                            "font-mono text-xs text-slate-400"
                        )
                    if len(result["invalid_files"]) > 10:
                        ui.label(f"  … und {len(result['invalid_files']) - 10} weitere").classes(
                            "text-xs text-slate-400"
                        )

                if result["conflicts"]:
                    ui.separator().classes("my-2")
                    ui.label(
                        f"⚠  {len(result['conflicts'])} Konflikte – Ausführen blockiert!"
                    ).classes("text-red-400 text-sm font-semibold")
                    for c in result["conflicts"][:5]:
                        ui.label(f"  • {c['filename']} (Jahr {c['year']})").classes(
                            "font-mono text-xs text-red-300"
                        )

        if not result["conflicts"]:
            btn_execute.enable()

    ui.button("Vorschau", on_click=do_preview, icon="preview").classes("mt-2")

    ui.separator().classes("mt-4")

    # ── Ausführen ──────────────────────────────────────────────────
    async def do_execute():
        folder = _state.get("folder")
        if not _state.get("scan") or not folder:
            return

        spinner.visible = True
        status_label.set_text("Organisiere …")
        btn_execute.disable()
        preview_col.clear()
        progress_bar.set_value(0)
        progress_bar.visible = True

        from app.core.year_org import execute_organization  # noqa: PLC0415

        group_by_camera = _state["scan"].get("group_by_camera", False)
        loop = asyncio.get_event_loop()

        async def _update_exec_progress(value: float):
            progress_bar.set_value(value)

        def exec_progress_cb(done, total):
            asyncio.run_coroutine_threadsafe(_update_exec_progress(done / total), loop)

        result = await loop.run_in_executor(
            _executor,
            lambda: execute_organization(folder, group_by_camera, progress_cb=exec_progress_cb),
        )

        spinner.visible = False
        progress_bar.visible = False

        if result.get("error"):
            ui.notify(result["error"], type="negative")
            status_label.set_text(result["error"])
            _state["scan"] = None
            return

        msg = f"{result['moved']} Datei(en) verschoben."
        if result["errors"]:
            msg += f"  {result['errors']} Fehler."
        if result["removed_folders"]:
            msg += f"  {result['removed_folders']} leere Ordner gelöscht."

        ui.notify(
            msg,
            type="positive" if not result["errors"] else "warning",
        )
        status_label.set_text(msg)
        _state["scan"] = None

    btn_execute = ui.button(
        "Ausführen",
        on_click=do_execute,
        icon="folder_special",
        color="green",
    )
    btn_execute.disable()

    ui.label("Tipp: Vorher Backup erstellen!").classes("text-xs text-slate-400 mt-1")
