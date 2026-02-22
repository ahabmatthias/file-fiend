#!/usr/bin/env python3
"""
Media Tools – Einstiegspunkt
Starten mit: python -m app.main
"""

from nicegui import ui

from app.ui import duplicates_tab, renamer_tab, video_compress_tab, year_org_tab
from app.ui.utils import pick_folder


def main():
    with ui.header().classes("bg-slate-800 text-white px-6 py-4"):
        ui.label("Media Tools").classes("text-xl font-bold")

    with ui.column().classes("w-full max-w-4xl mx-auto p-6"):
        # ── Gemeinsamer Ordner-Picker ────────────────────────────────────
        shared: dict = {"folder": "", "inputs": []}

        with ui.row().classes("w-full items-center gap-2 mb-2"):
            shared_input = ui.input(
                label="Ordner (gemeinsam)",
                placeholder="/Users/du/Bilder",
            ).classes("flex-1")

            async def on_pick_shared():
                result = await pick_folder()
                if result:
                    shared["folder"] = result
                    shared_input.set_value(result)
                    for inp in shared["inputs"]:
                        inp.set_value(result)

            ui.button("Ordner wählen", on_click=on_pick_shared, icon="folder_open")

        ui.separator().classes("mb-2")

        with ui.tabs().classes("w-full") as tabs:
            tab_dupes = ui.tab("Duplikate", icon="content_copy")
            tab_renamer = ui.tab("Umbenennen", icon="drive_file_rename_outline")
            tab_year = ui.tab("Jahr-Ordner", icon="calendar_month")
            tab_video = ui.tab("Video", icon="movie")

        with ui.tab_panels(tabs, value=tab_dupes).classes("w-full mt-4"):
            panel_dupes = ui.tab_panel(tab_dupes)
            duplicates_tab.build(panel_dupes, shared)

            panel_renamer = ui.tab_panel(tab_renamer)
            renamer_tab.build(panel_renamer, shared)

            panel_year = ui.tab_panel(tab_year)
            year_org_tab.build(panel_year, shared)

            panel_video = ui.tab_panel(tab_video)
            video_compress_tab.build(panel_video)

    ui.run(
        title="Media Tools",
        native=True,
        window_size=(1000, 680),
        reload=False,
    )


if __name__ == "__main__":
    main()
