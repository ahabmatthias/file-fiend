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
