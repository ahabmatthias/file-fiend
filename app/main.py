#!/usr/bin/env python3
"""
Media Tools – Einstiegspunkt
Starten mit: python -m app.main
"""

from nicegui import ui

from app.ui import duplicates_tab, renamer_tab, theme, video_compress_tab, year_org_tab
from app.ui.utils import pick_folder


def main():
    theme.apply()

    with ui.header().classes("bg-[#161b27] border-b border-[#2a3147] px-5 py-2"):
        with ui.row().classes("items-center gap-3 w-full"):
            ui.icon("folder_open").classes("text-[#4f8ef7] text-base")
            shared_input = (
                ui.input(
                    placeholder="/Users/du/Bilder",
                )
                .classes("flex-1")
                .props("outlined dense")
            )

            shared: dict = {"folder": ""}
            shared_input.on("change", lambda e: shared.update({"folder": e.value}))

            async def on_pick_shared():
                result = await pick_folder()
                if result:
                    shared["folder"] = result
                    shared_input.set_value(result)

            ui.button("Ordner wählen", on_click=on_pick_shared).classes("mt-btn-ghost").props(
                "no-caps"
            )

    with ui.tabs().classes("w-full") as tabs:
        tab_dupes = ui.tab("Duplikate", icon="content_copy")
        tab_rename = ui.tab("Umbenennen", icon="drive_file_rename_outline")
        tab_year = ui.tab("Sortieren", icon="layers")
        tab_video = ui.tab("Video", icon="movie")

    with ui.tab_panels(tabs, value=tab_dupes).classes("w-full"):
        with ui.tab_panel(tab_dupes):
            duplicates_tab.build(shared)
        with ui.tab_panel(tab_rename):
            renamer_tab.build(shared)
        with ui.tab_panel(tab_year):
            year_org_tab.build(shared)
        with ui.tab_panel(tab_video):
            video_compress_tab.build(shared)

    ui.run(
        title="Media Tools",
        native=True,
        window_size=(1000, 680),
        reload=False,
    )


if __name__ == "__main__":
    main()
