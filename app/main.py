#!/usr/bin/env python3
"""
Media Tools – Einstiegspunkt
Starten mit: python -m app.main
"""

from nicegui import ui

from app.ui import duplicates_tab, renamer_tab, year_org_tab


def main():
    with ui.header().classes("bg-slate-800 text-white px-6 py-4"):
        ui.label("Media Tools").classes("text-xl font-bold")

    with ui.column().classes("w-full max-w-4xl mx-auto p-6"):
        with ui.tabs().classes("w-full") as tabs:
            tab_dupes = ui.tab("Duplikate", icon="content_copy")
            tab_renamer = ui.tab("Umbenennen", icon="drive_file_rename_outline")
            tab_year = ui.tab("Jahr-Ordner", icon="calendar_month")

        with ui.tab_panels(tabs, value=tab_dupes).classes("w-full mt-4"):
            panel_dupes = ui.tab_panel(tab_dupes)
            duplicates_tab.build(panel_dupes)

            panel_renamer = ui.tab_panel(tab_renamer)
            renamer_tab.build(panel_renamer)

            panel_year = ui.tab_panel(tab_year)
            year_org_tab.build(panel_year)

    ui.run(
        title="Media Tools",
        native=True,
        window_size=(1000, 680),
        reload=False,
    )


if __name__ == "__main__":
    main()
