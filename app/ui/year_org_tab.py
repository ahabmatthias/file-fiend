"""
UI-Tab: Jahr-Organisation
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from nicegui import ui

from app.ui import theme

_executor = ThreadPoolExecutor(max_workers=1)


def build(shared: dict):
    """Baut den Jahr-Organisations-Tab – wird innerhalb eines tab_panel aufgerufen."""
    # ── Kamera-Checkbox ────────────────────────────────────────────
    camera_checkbox = ui.checkbox("Nach Kamera sortieren").classes("mt-1")
    ui.label("Benötigt EXIF-Daten in den Dateien").classes("mt-hint")

    # ── Status + Spinner ───────────────────────────────────────────
    with ui.row().classes("items-center gap-3 mt-2"):
        spinner = ui.spinner(size="sm").classes("text-[#4f8ef7]")
        spinner.visible = False
        status_label = ui.label("").classes("mt-hint")

    # ── Pills-Zeile ───────────────────────────────────────────────
    pills_row = ui.row().classes("items-center gap-2 mt-1")
    pills_row.visible = False

    progress_bar = ui.linear_progress(value=0).classes("mt-progress")
    progress_bar.visible = False

    preview_col = ui.column().classes("w-full gap-0 mt-2")
    _state: dict = {"scan": None, "folder": None}

    def _show_pills(years: int, invalid: int, conflicts: int):
        pills_row.clear()
        pills_row.visible = True
        with pills_row:
            if years:
                theme.pill(f"{years} Jahre", "info")
            if invalid:
                theme.pill(f"{invalid} ungültig", "neutral")
            if conflicts:
                theme.pill(f"{conflicts} Konflikte", "danger")

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
        pills_row.visible = False
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

        status_label.set_text(f"{result['total_files']} Dateien gefunden")
        _show_pills(
            len(result["files_by_year"]),
            len(result["invalid_files"]),
            len(result["conflicts"]),
        )

        with preview_col:
            with ui.element("div").classes("mt-card"):
                if group_by_camera:
                    ui.html('<div class="mt-card-header">Vorschau – Jahr / Kamera</div>')
                    for year in sorted(result["files_by_year"].keys()):
                        cam_dict = result["files_by_year"][year]
                        total_in_year = sum(len(v) for v in cam_dict.values())
                        ui.html(
                            f'<div style="padding:6px 14px;color:#e2e8f0;'
                            f"font-family:Menlo,monospace;font-size:12px;"
                            f'font-weight:600;">'
                            f'{year}/ <span style="color:#64748b;font-weight:400;">'
                            f"({total_in_year})</span></div>"
                        )
                        for camera in sorted(cam_dict.keys()):
                            count = len(cam_dict[camera])
                            ui.html(
                                f'<div style="padding:3px 14px 3px 32px;'
                                f"font-family:Menlo,monospace;font-size:11px;"
                                f'color:#64748b;">└─ {camera}'
                                f'<span style="color:#4f8ef7;margin-left:8px;">'
                                f"{count}</span></div>"
                            )
                else:
                    ui.html('<div class="mt-card-header">Vorschau – Jahr</div>')
                    for year in sorted(result["files_by_year"].keys()):
                        files = result["files_by_year"][year]
                        ui.html(
                            f'<div style="padding:6px 14px;'
                            f"font-family:Menlo,monospace;font-size:12px;"
                            f'color:#e2e8f0;border-bottom:1px solid #1a2033;">'
                            f'{year}/ <span style="color:#4f8ef7;">→</span> '
                            f'<span style="color:#34d399;">{len(files)} Datei(en)'
                            f"</span></div>"
                        )

                if result["invalid_files"]:
                    ui.html(
                        f'<div class="mt-card-header" style="margin-top:4px;">'
                        f'Ungültig ({len(result["invalid_files"])})</div>'
                    )
                    for inv in result["invalid_files"][:10]:
                        ui.html(
                            f'<div style="padding:3px 14px;'
                            f'font-family:Menlo,monospace;font-size:11px;'
                            f'color:#64748b;">{inv["path"].name}</div>'
                        )
                    if len(result["invalid_files"]) > 10:
                        ui.html(
                            f'<div class="mt-hint" style="padding:3px 14px;">'
                            f'… und {len(result["invalid_files"]) - 10} weitere</div>'
                        )

                if result["conflicts"]:
                    ui.html(
                        f'<div class="mt-card-header" style="margin-top:4px;'
                        f'color:#f87171 !important;">'
                        f'{len(result["conflicts"])} Konflikte – Ausführen blockiert</div>'
                    )
                    for c in result["conflicts"][:5]:
                        ui.html(
                            f'<div style="padding:3px 14px;'
                            f'font-family:Menlo,monospace;font-size:11px;'
                            f'color:#f87171;">{c["filename"]} (Jahr {c["year"]})</div>'
                        )

        if not result["conflicts"]:
            btn_execute.enable()

    ui.button("Vorschau", on_click=do_preview, icon="preview").classes("mt-btn-primary mt-2").props(
        "no-caps"
    )

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
        pills_row.visible = False
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

        status_label.set_text(f"{result['moved']} Datei(en) verschoben")
        pills_row.clear()
        pills_row.visible = True
        with pills_row:
            theme.pill(f"{result['moved']} verschoben", "good")
            if result["errors"]:
                theme.pill(f"{result['errors']} Fehler", "danger")
            if result["removed_folders"]:
                theme.pill(f"{result['removed_folders']} leere Ordner entfernt", "neutral")

        _state["scan"] = None

    btn_execute = (
        ui.button("Ausführen", on_click=do_execute, icon="folder_special")
        .classes("mt-btn-success")
        .props("no-caps")
    )
    btn_execute.disable()

    ui.label("Tipp: Vorher Backup erstellen!").classes("mt-hint mt-1")
