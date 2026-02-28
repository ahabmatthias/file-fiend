---
title: "feat: Dateityp-Filter pro Tab (Fotos / Videos / Audio)"
type: feat
status: completed
date: 2026-02-28
origin: docs/brainstorms/2026-02-28-dateityp-filter-brainstorm.md
---

# feat: Dateityp-Filter pro Tab

## Overview

Drei Tabs (Duplikate, Umbenennen, Sortieren) bekommen je Checkboxen, mit denen der
Nutzer steuert, welche Dateitypen der Scan berücksichtigt. Die Extension-Sets aus
`constants.py` sind bereits sauber definiert – die Änderung besteht im Wesentlichen
darin, sie als Parameter statt als Modulkonstanten zu verwenden.

## Proposed Solution

Jeder Core-Funktion wird ein optionaler `extensions: set[str] | None = None`-Parameter
hinzugefügt. `None` bedeutet „keine Filterung" (bisheriges Verhalten). Die UI-Tabs
lesen die Checkbox-Werte und bauen daraus das extensions-Set zusammen, bevor sie den
`run_in_executor`-Aufruf machen.

## Changes per File

### `app/core/duplicates.py`

**Aktuelle Signatur (Zeile 24):**
```python
def find_duplicates(folder: str, progress_cb=None) -> dict[str, list[str]]:
```

**Neue Signatur:**
```python
def find_duplicates(
    folder: str,
    progress_cb=None,
    extensions: set[str] | None = None,
) -> dict[str, list[str]]:
```

**Walk-Filter (Zeilen 32–39):** Wenn `extensions` gesetzt, `name.suffix.lower() not in extensions` überspringen.

---

### `app/core/renamer.py`

**Modul-Konstante (Zeile 17):**
```python
_SUPPORTED_EXTS = IMAGE_EXTS | VIDEO_EXTS  # bleibt als Default
```

**`collect_files` (Zeile 96):**
```python
def collect_files(
    folder_path: str,
    recursive: bool = True,
    extensions: set[str] | None = None,
) -> list[dict]:
```
Filter auf Zeile 105 nutzt `extensions or _SUPPORTED_EXTS`.

`process_files` bleibt unverändert (bekommt already-gefiltertes `files`-List).

---

### `app/core/year_org.py`

**`_collect_files_with_years` (Zeile 248):** Neuer Parameter `extensions: set[str]`.
Zeile 274 ersetzt `ALL_MEDIA_EXTS` durch den Parameter.

**`scan_folder` (Zeile 300):**
```python
def scan_folder(
    folder_path: str,
    group_by_camera: bool = False,
    extensions: set[str] | None = None,
    progress_cb=None,
) -> dict:
```
Default: `extensions or (IMAGE_EXTS | VIDEO_EXTS)` — Audio ausgeschlossen.

**`execute_organization` (Zeile 391):** Gleicher neuer Parameter, wird an
`_collect_files_with_years` weitergegeben.

---

### `app/ui/duplicates_tab.py`

**Neue Checkboxen** über dem Scan-Button (nach `_executor`-Definition):
```python
cb_fotos  = ui.checkbox("Fotos",  value=True).classes("mt-1")
cb_videos = ui.checkbox("Videos", value=True).classes("mt-1")
cb_audio  = ui.checkbox("Audio",  value=False).classes("mt-1")
```

**In `do_scan()` (vor Zeile 86):**
```python
exts = set()
if cb_fotos.value:  exts |= IMAGE_EXTS
if cb_videos.value: exts |= VIDEO_EXTS
if cb_audio.value:  exts |= AUDIO_EXTS
if not exts:
    status_label.set_text("Bitte mindestens einen Dateityp wählen.")
    return
dupes = await loop.run_in_executor(
    _executor, lambda: find_duplicates(folder, progress_cb, extensions=exts)
)
```

---

### `app/ui/renamer_tab.py`

**Neue Checkboxen** neben `cb_recursive` (Zeile 20):
```python
cb_recursive = ui.checkbox("Mit Unterordnern", value=True).classes("mt-1")
cb_fotos     = ui.checkbox("Fotos",  value=True).classes("mt-1 ml-4")
cb_videos    = ui.checkbox("Videos", value=True).classes("mt-1")
```

**In `do_preview()` (vor Zeile 67):**
```python
exts = set()
if cb_fotos.value:  exts |= IMAGE_EXTS
if cb_videos.value: exts |= VIDEO_EXTS
if not exts:
    status_label.set_text("Bitte mindestens einen Dateityp wählen.")
    return
recursive = cb_recursive.value
files = await loop.run_in_executor(
    _executor, lambda: collect_files(folder, recursive=recursive, extensions=exts)
)
```

---

### `app/ui/year_org_tab.py`

**Neue Checkboxen** neben `camera_checkbox` (Zeile 19):
```python
camera_checkbox = ui.checkbox("Nach Kamera sortieren").classes("mt-1")
cb_fotos        = ui.checkbox("Fotos",  value=True).classes("mt-1 ml-4")
cb_videos       = ui.checkbox("Videos", value=True).classes("mt-1")
```

**In `do_preview()` (vor Zeile 84):** Extensions-Set berechnen, in `_state["scan"]`
gemeinsam mit `group_by_camera` speichern:
```python
exts = set()
if cb_fotos.value:  exts |= IMAGE_EXTS
if cb_videos.value: exts |= VIDEO_EXTS
if not exts:
    status_label.set_text("Bitte mindestens einen Dateityp wählen.")
    return
group_by_camera = camera_checkbox.value
result = await loop.run_in_executor(
    _executor,
    lambda: scan_folder(folder, group_by_camera, extensions=exts, progress_cb=...),
)
_state["scan"]["extensions"] = exts   # für do_execute
```

**In `do_execute()` (vor Zeile 207):**
```python
exts = _state["scan"].get("extensions", IMAGE_EXTS | VIDEO_EXTS)
result = await loop.run_in_executor(
    _executor,
    lambda: execute_organization(folder, group_by_camera, extensions=exts, progress_cb=...),
)
```

---

## Technical Considerations

- **Reihenfolge der Imports:** `IMAGE_EXTS`, `VIDEO_EXTS`, `AUDIO_EXTS` in den UI-Tabs
  importieren (bisher nicht alle drei importiert).
- **Validierung:** Wenn kein Typ gewählt → `status_label` zeigen, Return; kein Dialog nötig.
- **Year Org – Audio-Default:** Core-Default ist `IMAGE_EXTS | VIDEO_EXTS` (kein Audio),
  da `ALL_MEDIA_EXTS` im Year-Org-Tab keinen Sinn macht (keine EXIF-Jahres­daten für Audio).
- **Backwards-Compat:** Alle neuen Parameter haben Defaults → kein Breaking Change.

## Acceptance Criteria

- [x] **Duplikate-Tab:** Checkboxen Fotos/Videos/Audio; Default Fotos+Videos; Scan
      filtert korrekt; leere Auswahl → Hinweis, kein Absturz
- [x] **Umbenennen-Tab:** Checkboxen Fotos/Videos; Default beide aktiv; Preview + Ausführen
      respektieren die Auswahl
- [x] **Sortieren-Tab:** Checkboxen Fotos/Videos (kein Audio); Default beide aktiv;
      Preview und Ausführen nutzen denselben Extensions-State aus `_state["extensions"]`
- [x] Alle bestehenden Funktionen ohne Angabe von `extensions` verhalten sich wie bisher
- [x] `find_duplicates(folder)` ohne `extensions`-Arg scannt weiterhin alle Dateitypen

## Dependencies & Risks

- **Kein Breaking Risk:** Alle neuen Parameter optional mit sinnvollen Defaults
- **Year Org – Audio in _collect_files_with_years:** Die Funktion hat aktuell keine
  File-Type-Erkennung für Audio (treated as "video", Zeile 203). Mit dem Filter ist das
  egal – Audio wird gar nicht erst gesammelt.

## Sources

- **Origin brainstorm:** [docs/brainstorms/2026-02-28-dateityp-filter-brainstorm.md](../brainstorms/2026-02-28-dateityp-filter-brainstorm.md)
  Key decisions: (1) Duplikate: 3 Checkboxen inkl. Audio; (2) Umbenennen: 2 Checkboxen ohne Audio;
  (3) Sortieren: 2 Checkboxen ohne Audio
- `app/core/constants.py` – Extension-Sets
- `app/core/duplicates.py:24` – `find_duplicates` Signatur
- `app/core/renamer.py:96` – `collect_files` Signatur
- `app/core/year_org.py:300,391` – `scan_folder`, `execute_organization`
- `app/ui/duplicates_tab.py:86` – Aufruf `find_duplicates`
- `app/ui/renamer_tab.py:20,67` – `cb_recursive`-Pattern
- `app/ui/year_org_tab.py:19,62,197` – `camera_checkbox`-Pattern mit `_state`
