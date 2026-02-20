# Media Tools – Projektplan

Ziel: Lern-Projekt. Minimale Desktop-App mit NiceGUI, später als macOS `.app` verpackt.
Fokus auf funktionierende Features – kein Anspruch auf poliertes Design.

---

## To-Do

### Phase 1: Funktionen

- [x] Schritt 1: NiceGUI-Grundgerüst – leeres Fenster öffnet sich (`app/main.py`)
- [ ] Schritt 2: Duplikat-Finder schreiben (`app/core/duplicates.py`)
  - Dateien in Ordner scannen
  - Duplikate per Hash (MD5/SHA1) erkennen
  - Ergebnis in der UI anzeigen (Liste der Duplikate)
  - Duplikate auswählen und löschen können
- [ ] Schritt 3: `unified_media_renamer.py` als Tab integrieren
  - Ordner auswählen
  - Vorschau der Umbenennungen
  - Umbenennen ausführen
- [ ] Schritt 4: `video_compress.py` als Tab integrieren
  - Ordner oder Einzeldatei auswählen
  - Komprimierungsoptionen (Qualität, Format)
  - Fortschrittsanzeige
- [ ] Schritt 5: `year_folder_script.py` als Tab integrieren
  - Ordner auswählen
  - Vorschau der Ordnerstruktur
  - Sortierung ausführen

### Phase 2: Packaging

- [ ] Schritt 6: Als macOS `.app` verpacken
  - Tool evaluieren: `py2app` oder `PyInstaller`
  - Build-Script erstellen
  - Testen ob natives Fenster funktioniert

---

## Stack

- Python 3.9+
- [NiceGUI](https://nicegui.io) – UI-Framework (Web-basiert, native Window via pywebview)
- pywebview – für natives macOS-Fenster
- bestehende Scripts in `app/core/` einbinden

## Starten

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```
