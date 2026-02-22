# Media Tools – Projektplan

Ziel: Lern-Projekt. Minimale Desktop-App mit NiceGUI, später als macOS `.app` verpackt.
Fokus auf funktionierende Features – kein Anspruch auf poliertes Design.

---

## To-Do

### Phase 1: Funktionen

- [x] Schritt 1: NiceGUI-Grundgerüst – leeres Fenster öffnet sich (`app/main.py`)
- [x] Schritt 2: Duplikat-Finder schreiben (`app/core/duplicates.py`)
  - Dateien in Ordner scannen
  - Duplikate per Hash (MD5/SHA1) erkennen
  - Ergebnis in der UI anzeigen (Thumbnails + Liste)
  - Duplikate auswählen und löschen können
- [x] Schritt 3: Renamer-Tab (`app/core/renamer.py`)
  - Ordner auswählen
  - Vorschau der Umbenennungen (dry-run)
  - Umbenennen ausführen
- [x] Schritt 4: Video-Compress-Tab (`app/core/video_compress.py`)
  - Ordner oder Einzeldatei auswählen
  - Komprimierungsoptionen (Qualität, Format)
  - Fortschrittsanzeige
- [x] Schritt 5: Jahr-Ordner-Tab (`app/core/year_org.py`)
  - Ordner auswählen
  - Vorschau der Ordnerstruktur
  - Sortierung ausführen
- [x] Schritt 5b: Jahr-Ordner-Tool – optionale Kamera-Unterordner
  - Checkbox „Nach Kamera untergliedern" (Standard: aus)
  - Vorschau zeigt `year/camera`-Baum wenn aktiviert
  - Ausführen legt `<year>/<camera>/`-Struktur an

### Phase 1b: UX-Verbesserungen

- [ ] Gemeinsamer Ordner-Picker: globalen Ordner in Header/oberhalb der Tabs, Tabs lesen aus shared State (Video-Tab behält eigene Quell-/Zielordner)
- [ ] Fortschrittsanzeige für Duplikat-Scan und Jahr-Organisation (nicht nur Spinner)
- [ ] Kamera-Mapping konfigurierbar machen oder EXIF Make/Model direkt als Ordnername nutzen
- [ ] Hinweis bei Kamera-Checkbox: EXIF-Daten nötig
- [ ] Hinweis bei Video-Tab: Hardware-Codec ist macOS-only
- [ ] Renamer: Option für nicht-rekursiven Scan

### Phase 2: Packaging

- [ ] Schritt 6: Als macOS `.app` verpacken
  - Tool: PyInstaller (py2app hat häufiger Probleme mit modernen Python-Versionen)
  - Build-Script erstellen
  - Testen ob natives Fenster funktioniert

---

## Stack

- Python 3.10+ (3.13 empfohlen – venv nutzt 3.13)
- [NiceGUI](https://nicegui.io) – UI-Framework (Web-basiert, native Window via pywebview)
- pywebview – für natives macOS-Fenster
- gesamte Logik in `app/core/`, UI-Tabs in `app/ui/`

## Starten

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```
