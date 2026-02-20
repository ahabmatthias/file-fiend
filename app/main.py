#!/usr/bin/env python3
"""
Media Tools – Einstiegspunkt
Starten mit: python app/main.py
"""

from nicegui import ui


def main():
    # Header
    with ui.header().classes('bg-slate-800 text-white px-6 py-4'):
        ui.label('Media Tools').classes('text-xl font-bold')

    # Hauptbereich – vorerst leer
    with ui.column().classes('w-full max-w-4xl mx-auto p-8 gap-4'):
        ui.label('Willkommen').classes('text-2xl font-semibold text-slate-700')
        ui.label(
            'Wähle einen Ordner, um Medien-Dateien zu analysieren.'
        ).classes('text-slate-500')

    # native=True öffnet ein echtes Fenster (kein Browser)
    # Requires: pip install pywebview
    ui.run(
        title='Media Tools',
        native=True,
        window_size=(1000, 680),
        reload=False,
    )


if __name__ == '__main__':
    main()
