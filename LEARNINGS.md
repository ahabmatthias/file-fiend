# Learnings & Entscheidungen

Chronologisches Lerntagebuch – für mich zum Nachschlagen, nicht als Projektdoku.

---

## 2026-02 – Quality-Gate-Architektur

### Pre-commit Hooks
- Hooks sind **repo-lokal** – jeder neue Klon braucht `pre-commit install` einmalig
- Die Config-Datei (`.pre-commit-config.yaml`) ist im Repo, der eigentliche Hook liegt in `.git/hooks/` und wird nicht versioniert
- Hooks greifen bei **allen lokalen Commits**, egal von wem oder auf welchem Branch – nicht bei GitHub Web-UI oder CI

### mypy vs. ruff
- **ruff** ist schnell und findet Stil-Probleme, Unused Imports, unsichere Patterns
- **mypy** prüft Typen und findet andere Klassen von Bugs: falsche Rückgabetypen, Monkey-Patching auf Module, `Any`-Werte die als konkreter Typ behandelt werden
- Beide zusammen sinnvoll – sie überschneiden sich kaum

### Python-Versionen
- `int | None` Union-Syntax ist **Python 3.10+**, nicht 3.9
- CLAUDE.md hatte „3.9+" stehen, obwohl der Code bereits 3.10-Syntax nutzte und das venv auf 3.13 läuft → Versionsdoku war irreführend
- Lektion: Mindestversion immer am tatsächlichen Code messen, nicht an einer Wunschvorstellung

### Coverage
- 52% auf `app/core/` nach erster Test-Session
- Lücken: EXIF-Parsing (`_read_exif_year`, `_detect_camera`) braucht echte Testbilder mit Metadaten oder Mocks – aufwändiger als reine Logik-Tests
- `app/core/renamer.py` zeigt 0% weil Tests direkt `unified_media_renamer` importieren, nicht den Wrapper

### Legacy-Script-Integration (sys.path, install_packages)
- Legacy-Scripts im Projekt-Root (`unified_media_renamer.py`, `year_folder_script.py`) wurden ursprünglich mit `sys.path`-Hacks importiert
- `install_packages()` wurde beim Modulimport ausgeführt → blockiert UI beim Start
- Beides entfernbar wenn: (a) App immer aus Projekt-Root gestartet wird, (b) Packages in `requirements.txt` stehen

---

## 2026-02 – Startup-Performance: Lazy Imports

### Problem
App startete in ~4 Sekunden. Ursache: Alle drei Tab-Module wurden beim Start vollständig
importiert, obwohl der Nutzer zunächst nur das Fenster sehen will.

Die Importkette beim Start:
- `renamer_tab.py` → `app.core.renamer` → `unified_media_renamer` → **`pymediainfo`** (lädt
  native C-Bibliothek `libmediainfo`) + `PIL`
- `year_org_tab.py` → `app.core.year_org` → `PIL`, **`pillow_heif.register_heif_opener()`**
  (Seiteneffekt auf Modul-Ebene!), `pymediainfo` (nochmal), `year_folder_script`

`pymediainfo` war der größte Einzelbrocken – es lädt beim Import eine native shared library.

### Fix: Lazy Imports in den Handler-Funktionen
Core-Module erst beim ersten Klick auf „Vorschau" importieren, nicht beim App-Start:

```python
# vorher (Modul-Ebene):
from app.core.renamer import collect_files, process_files

# nachher (innerhalb von do_preview()):
from app.core.renamer import collect_files, process_files  # noqa: PLC0415
```

Python cached Module – nach dem ersten Aufruf ist der Import instant.

### Ergebnis
Startzeit von ~4 Sekunden auf ~1 Sekunde reduziert. Die verbleibende Sekunde ist NiceGUI
selbst (uvicorn + pywebview), kaum optimierbar ohne Framework-Wechsel.

### Muster
Überall wo schwere C-Extensions (pymediainfo, pillow-heif, PIL) nur für bestimmte
Funktionen gebraucht werden: Import in die Funktion verschieben statt auf Modul-Ebene.
`# noqa: PLC0415` unterdrückt die ruff-Warnung für Import-not-at-top-of-file.

---

## 2026-02 – Kamera-Sortierung: Refactoring einer Querschnitts-Funktion

### Ausgangslage
Der Renamer schrieb den Kameranamen (`Lumix`, `Osmo`) als Token in den Dateinamen:
`2024-03-15_143022_Lumix_P1020123.jpg`. Das war gedacht, um Aufnahmen verschiedener Kameras
unterscheidbar zu machen. In der Praxis war das unübersichtlich und vermischte zwei Aufgaben:
_Datum_ und _Herkunft_ in einem einzigen Dateinamen-Schema.

### Entscheidung: Kamera als Ordner, nicht als Namensteil
Statt `year/datei` (mit Kamera im Namen) wird jetzt `year/camera/datei` als optionale Struktur
im Jahr-Ordner-Tool angeboten. Der Dateiname selbst ist sauber: `YYYY-MM-DD_HHMMSS_<stem>.<ext>`.

**Warum Ordner besser ist als Name:**
- Ordner ist filterbar im Finder ohne Suche
- Dateiname bleibt kürzer und maschinenlesbarer
- Kamera-Information liegt im EXIF – die braucht nicht im Namen redundant zu stehen
- Schema funktioniert auch für Kameras, die keinen Kamera-Token bekommen hätten

### Rückwärtskompatibilität bewusst weggelassen
Bereits umbenannte Dateien mit `_Lumix_` im Namen werden vom Renamer jetzt übersprungen statt
„korrigiert". Der Korrektur-Zweig war nur für eigene Altdateien nötig – externe Nutzer haben
keine Dateien im alten Format. Das vereinfacht `generate_filename()` und `process_files()`
erheblich.

### Wo `detect_camera()` jetzt lebt
Die Funktion existierte in `unified_media_renamer.py` und wurde in `app/core/year_org.py` neu
implementiert (als `_detect_camera()`). Bewusst _nicht_ importiert: Die Erkennungslogik für
den Renamer (der Dateinamen-Fallback für bereits umbenannte Dateien) ist anders als die für
die Jahr-Sortierung (EXIF-first, Dateiname nur als letzter Fallback). Getrennte Implementierung
ist hier klarer als ein gemeinsamer Import.

### Architektur-Muster: group_by_camera als Parameter
`scan_folder()` und `execute_organization()` bekamen einen `group_by_camera: bool = False`-
Parameter. Defaultwert `False` hält den normalen Workflow unverändert. Die UI-Checkbox setzt
diesen Wert und speichert ihn im Scan-Ergebnis (`_state["scan"]["group_by_camera"]`), damit
`do_execute()` exakt dieselbe Option nutzt wie die vorangegangene Vorschau.

### Tests haben den Merge abgesichert
28 Tests liefen nach dem Merge grün durch – darunter Tests für `scan_folder` und
`execute_organization`, die die Kernlogik abdecken. Die Kamera-Erkennung selbst (EXIF-Parsing)
ist noch nicht getestet, weil dafür echte Testbilder mit Metadaten nötig wären.

---

## 2026-02 – Video-Compress-Tab: Integration & UX-Iterationen

### Wrapper-Pattern: Direkter Import statt Copy-Paste
`app/core/video_compress.py` importiert direkt aus dem Root-Script `video_compress.py` –
keine Code-Duplizierung. Der Wrapper ergänzt nur das, was für die UI fehlt: strukturierte
Rückgabewerte, `progress_cb`-Parameter, Unterdrückung von print-Output.

Wo die Root-Logik zu monolithisch war (die Haupt-Loop in `compress_videos()` gibt nichts
zurück), wurde sie in `compress_files()` neu implementiert – aber mit denselben Hilfsfunktionen
(`collect_files`, `ffprobe_json`, `pick_target_bitrate`, `should_skip_copy`, `build_ffmpeg_cmd`).

### Pre-commit: ruff SIM108
ruff hat einen if/else-Block durch einen Ternary-Ausdruck ersetzt (SIM108). Kann direkt beim
Schreiben vermieden werden – bei `codec == "auto"` war die Ternary-Form tatsächlich lesbarer:
```python
use_vt = detect_videotoolbox() if codec == "auto" else codec == "hevc_videotoolbox"
```

### UX: Labels sind wichtiger als technische Bezeichnungen
Erste Version der Codec-Auswahl nutzte technische Namen: `"Auto (empfohlen)"`,
`"VideoToolbox (HW)"`, `"libx265 (SW)"`. Das sagt Nutzern ohne Encoding-Hintergrund nichts.

Überarbeitete Labels:
- `"Automatisch"` – beschreibt das Verhalten, nicht den Mechanismus
- `"Hardware (schnell)"` – der relevante Unterschied ist Geschwindigkeit
- `"Software (langsam)"` – ehrlich, keine Verschleierung

Gleiches Muster bei der Checkbox: `"Rekursiv"` → `"Unterordner einbeziehen"`. Fachbegriff
gegen direkte Beschreibung der Konsequenz austauschen.

**Merksatz für Labels:** Was passiert, wenn ich das aktiviere? Die Antwort ist der Label.

### UX-Block als bewusste Entscheidung
Design und Labels werden immer wieder angefasst – das ist kein Fehler, sondern sinnvoll.
Einzelne Korrekturen direkt mitzudenken spart später aufwändigere Refactorings. Ein
dedizierter UX-Review-Block (alle Tabs auf einmal) ist trotzdem geplant, um konsistente
Sprache und Verhalten über die gesamte App sicherzustellen.

---

## 2026-01 – NiceGUI & UI-Integration

### tqdm/print in Legacy-Scripts
- Legacy-Scripts nutzen `tqdm` und `print` für Terminal-Output
- In der UI stört das: Output landet im Terminal statt in der UI, kann Logs zumüllen
- Fix: Im Wrapper-Modul `_renamer_module.tqdm` und `_renamer_module.print` nach Import überschreiben (Monkey-Patching)

### Async in NiceGUI
- NiceGUI-Event-Handler müssen `async def` sein wenn sie auf Ergebnisse warten
- Blocking-Code (Datei-Scan, Umbenennungen) in `ThreadPoolExecutor` auslagern mit `await loop.run_in_executor(...)`
- Sonst friert die UI ein

### HEIC-Support
- `pillow` öffnet HEIC-Dateien nicht nativ – braucht `pillow-heif` als Plugin
- Plugin muss vor dem ersten Öffnen registriert werden: `pillow_heif.register_heif_opener()`
- Optional halten: im `try/except ImportError` wrappen, damit die App auch ohne das Plugin startet
