"""
UI-Tab: Video Komprimierung
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

from nicegui import ui

from app.ui.utils import pick_folder

_executor = ThreadPoolExecutor(max_workers=1)

_ACTION_LABEL = {
    "compress": "Komprimieren",
    "skip": "Überspringen",
    "skip_and_copy": "Kopieren",
}


def build(tab_panel):
    """Baut den Video-Komprimierungs-Tab in das übergebene tab_panel."""
    with tab_panel:
        # ── Ordner-Auswahl ─────────────────────────────────────────────
        with ui.row().classes("w-full items-center gap-2"):
            source_input = ui.input(
                label="Quellordner",
                placeholder="/Users/du/Videos",
            ).classes("flex-1")

            async def on_pick_source():
                result = await pick_folder()
                if result:
                    source_input.set_value(result)

            ui.button("Ordner wählen", on_click=on_pick_source, icon="folder_open")

        with ui.row().classes("w-full items-center gap-2 mt-1"):
            target_input = ui.input(
                label="Zielordner",
                placeholder="/Users/du/Videos_compressed",
            ).classes("flex-1")

            async def on_pick_target():
                result = await pick_folder()
                if result:
                    target_input.set_value(result)

            ui.button("Ordner wählen", on_click=on_pick_target, icon="folder_open")

        # ── Optionen ───────────────────────────────────────────────────
        with ui.row().classes("items-center gap-4 mt-2"):
            codec_select = ui.select(
                label="Codec",
                options={
                    "auto": "Automatisch",
                    "hevc_videotoolbox": "Hardware (schnell)",
                    "libx265": "Software (langsam)",
                },
                value="auto",
            ).classes("w-52")

            min_size_input = ui.number(label="Min-Größe (MB)", value=30.0, min=0, step=5).classes(
                "w-32"
            )

            recursive_cb = ui.checkbox("Unterordner einbeziehen")

        # ── Status + Spinner ───────────────────────────────────────────
        with ui.row().classes("items-center gap-3 mt-2"):
            spinner = ui.spinner(size="sm").classes("text-slate-400")
            spinner.visible = False
            status_label = ui.label("").classes("text-slate-500 text-sm")

        preview_col = ui.column().classes("w-full gap-2 mt-2")
        _state: dict = {"preview": None, "source": None, "target": None, "config": None}

        # ── Vorschau ───────────────────────────────────────────────────
        async def do_preview():
            source = source_input.value.strip()
            target = target_input.value.strip()

            if not source:
                ui.notify("Bitte einen Quellordner eingeben.", type="negative")
                return
            if not os.path.isdir(source):
                ui.notify("Quellordner nicht gefunden.", type="negative")
                return
            if not target:
                ui.notify("Bitte einen Zielordner eingeben.", type="negative")
                return
            if os.path.abspath(source) == os.path.abspath(target):
                ui.notify("Quell- und Zielordner dürfen nicht identisch sein.", type="negative")
                return

            spinner.visible = True
            status_label.set_text("Scanne …")
            preview_col.clear()
            _state["preview"] = None
            btn_execute.disable()

            from app.core.video_compress import preview_compression  # noqa: PLC0415

            config = {
                "recursive": recursive_cb.value,
                "min_size_mb": float(min_size_input.value or 30.0),
                "codec": codec_select.value,
            }

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor, lambda: preview_compression(source, target, **config)
            )

            spinner.visible = False

            if not result:
                status_label.set_text("Keine Video-Dateien im Quellordner gefunden.")
                return

            _state["preview"] = result
            _state["source"] = source
            _state["target"] = target
            _state["config"] = config

            n_compress = sum(1 for f in result if f["action"] == "compress")
            n_skip = sum(1 for f in result if f["action"] == "skip")
            n_copy = sum(1 for f in result if f["action"] == "skip_and_copy")
            status_label.set_text(
                f"{len(result)} Dateien: {n_compress} komprimieren, "
                f"{n_skip} überspringen, {n_copy} kopieren"
            )

            MAX_SHOWN = 50
            columns = [
                {"name": "name", "label": "Dateiname", "field": "name", "align": "left"},
                {"name": "size_mb", "label": "Größe", "field": "size_mb", "align": "right"},
                {"name": "resolution", "label": "Auflösung", "field": "resolution"},
                {"name": "bitrate", "label": "Bitrate", "field": "bitrate"},
                {"name": "action_label", "label": "Aktion", "field": "action_label"},
            ]
            rows = [
                {
                    "name": e["name"],
                    "size_mb": f"{e['size_mb']} MB",
                    "resolution": e["resolution"],
                    "bitrate": (
                        f"{e['current_bitrate_mbps']} Mbps"
                        if e["current_bitrate_mbps"] is not None
                        else "–"
                    ),
                    "action_label": _ACTION_LABEL.get(e["action"], "?"),
                }
                for e in result[:MAX_SHOWN]
            ]

            with preview_col:
                with ui.card().classes("w-full"):
                    ui.table(columns=columns, rows=rows).classes("w-full text-sm")
                    if len(result) > MAX_SHOWN:
                        ui.label(f"… und {len(result) - MAX_SHOWN} weitere").classes(
                            "text-xs text-slate-400 mt-1"
                        )

            btn_execute.enable()

        ui.button("Vorschau", on_click=do_preview, icon="preview").classes("mt-2")

        ui.separator().classes("mt-4")

        # ── Komprimieren ───────────────────────────────────────────────
        async def do_execute():
            if not _state.get("preview") or not _state.get("source"):
                return

            source = _state["source"]
            target = _state["target"]
            config = _state["config"]

            spinner.visible = True
            btn_execute.disable()
            preview_col.clear()

            from app.core.video_compress import compress_files  # noqa: PLC0415

            loop = asyncio.get_event_loop()

            async def _set_status(text: str):
                status_label.set_text(text)

            def progress_cb(current, total, filename):
                asyncio.run_coroutine_threadsafe(
                    _set_status(f"[{current}/{total}] {filename}"), loop
                )

            result = await loop.run_in_executor(
                _executor,
                lambda: compress_files(source, target, **config, progress_cb=progress_cb),
            )

            spinner.visible = False
            _state["preview"] = None

            msg = f"{result['compressed']} komprimiert, {result['skipped']} übersprungen"
            if result["failed"]:
                msg += f", {result['failed']} Fehler"
            status_label.set_text(msg)
            ui.notify(msg, type="positive" if not result["failed"] else "warning")

        btn_execute = ui.button(
            "Komprimieren",
            on_click=do_execute,
            icon="movie",
            color="green",
        )
        btn_execute.disable()
