---
title: "fix: UX-Fixes – Fortschritt, Checkboxen, Video-Zielordner"
type: fix
status: active
date: 2026-02-28
origin: docs/brainstorms/2026-02-28-weitere-ideen.md
---

# fix: UX-Fixes – Fortschritt, Checkboxen, Video-Zielordner

## Overview

Sieben kleine Beobachtungen aus dem täglichen Gebrauch werden in einem Commit behoben.
Beobachtung 6 (strukturelle Checkbox-Gruppierung via `ui.separator()`) ist die Grundlage
für Beobachtung 4 (Spacing) und 5 (Mit Unterordnern), daher werden alle sieben gemeinsam
umgesetzt (see brainstorm: docs/brainstorms/2026-02-28-weitere-ideen.md).

## Acceptance Criteria

- [ ] **B1** – Fortschrittswert zeigt `92 %` statt `0.9173` (Duplikate- und Sortieren-Tab)
- [ ] **B2** – Fortschrittsbalken erscheint in allen Tabs an derselben Position (direkt unter Status-Label)
- [ ] **B3** – Video-Tab: Zielordner wird automatisch mit `<Quellordner>_compressed` vorausgefüllt, überschreibt keine manuell gesetzten Werte
- [ ] **B4** – Kein redundantes `mt-1` auf einzelnen Checkboxen; Spacing nur über `gap-4` auf dem Row-Container
- [ ] **B5** – Duplikate- und Sortieren-Tab haben eine „Mit Unterordnern"-Checkbox (Default: an)
- [ ] **B6** – `ui.separator()` trennt Scope-Option von Typ-Filtern in allen drei Tabs; im Sortieren-Tab auch Typ von Kamera-Option
- [ ] **B7** – Kamera-Checkbox und Info-Icon liegen in einer gemeinsamen `ui.row().classes("items-center gap-2")`

---

## Implementation

### B1 + B2 – Progress: Prozent + konsistente Position

**`app/ui/duplicates_tab.py`**

```python
# Vorher (Zeile 57):
progress_bar = ui.linear_progress(value=0).classes("mt-progress")

# Nachher:
progress_bar = ui.linear_progress(value=0, show_value=False).classes("mt-progress")
```

```python
# Vorher (Zeile 96–97):
async def _update_progress(value: float):
    progress_bar.set_value(value)

# Nachher:
async def _update_progress(value: float):
    progress_bar.set_value(value)
    status_label.set_text(f"Scanne … {int(value * 100)} %")
```

Position passt bereits (nach status_row, vor results_col) → kein Change nötig.

---

**`app/ui/year_org_tab.py`**

```python
# Vorher (Zeile 39):
progress_bar = ui.linear_progress(value=0).classes("mt-progress")

# Nachher:
progress_bar = ui.linear_progress(value=0, show_value=False).classes("mt-progress")
```

```python
# Vorher (Zeile 91–92):
async def _update_scan_progress(value: float):
    progress_bar.set_value(value)

# Nachher:
async def _update_scan_progress(value: float):
    progress_bar.set_value(value)
    status_label.set_text(f"Scanne … {int(value * 100)} %")
```

```python
# Vorher (Zeile 218–219):
async def _update_exec_progress(value: float):
    progress_bar.set_value(value)

# Nachher:
async def _update_exec_progress(value: float):
    progress_bar.set_value(value)
    status_label.set_text(f"Organisiere … {int(value * 100)} %")
```

**Position (B2):** `progress_bar` steht aktuell nach `pills_row` → vor `pills_row` verschieben,
sodass die Reihenfolge `status_row → progress_bar → pills_row → preview_col` ist.

---

### B3 – Video-Tab: Zielordner Auto-Fill

**`app/ui/video_compress_tab.py`**

Nach dem Erstellen von `target_input` (aktuell Zeile ~36) einfügen:

```python
# Auto-Fill Zielordner aus Quellordner
src = (shared.get("folder") or "").strip()
if src and not target_input.value:
    target_input.set_value(src + "_compressed")
```

Nur beim initialen `build()`-Aufruf. Nicht reaktiv – der Nutzer kann danach frei ändern.

---

### B4 – Checkbox-Spacing bereinigen

In allen drei Tabs: `.classes("mt-1")` von einzelnen Checkboxen entfernen.
Der `gap-4` auf dem Row-Container regelt das Spacing bereits vollständig.

**`app/ui/duplicates_tab.py`** (Zeilen 65–67):
```python
# Vorher:
cb_fotos  = ui.checkbox("Fotos",  value=True).classes("mt-1")
cb_videos = ui.checkbox("Videos", value=True).classes("mt-1")
cb_audio  = ui.checkbox("Audio",  value=False).classes("mt-1")

# Nachher:
cb_fotos  = ui.checkbox("Fotos",  value=True)
cb_videos = ui.checkbox("Videos", value=True)
cb_audio  = ui.checkbox("Audio",  value=False)
```

Gleiches Muster in `renamer_tab.py` (Zeilen 22–24) und `year_org_tab.py` (Zeilen 26–27) prüfen.

---

### B5 – „Mit Unterordnern" in Duplikate- und Sortieren-Tab

**`app/core/duplicates.py`** – `recursive`-Parameter ergänzen:

```python
# Vorher:
def find_duplicates(folder: str, progress_cb=None, extensions=None) -> dict:

# Nachher:
def find_duplicates(folder: str, progress_cb=None, extensions=None, recursive: bool = True) -> dict:
    # rglob → glob wechseln je nach recursive:
    glob_fn = Path(folder).rglob if recursive else Path(folder).glob
```

**`app/core/year_org.py`** – analog prüfen ob `recursive`-Parameter bereits existiert,
sonst ergänzen.

**`app/ui/duplicates_tab.py`** – Checkbox hinzufügen (wird in B6 in Scope-Gruppe eingebaut):

```python
cb_recursive = ui.checkbox("Mit Unterordnern", value=True)
```

Im `do_scan()`-Callback:
```python
result = find_duplicates(folder, progress_cb, extensions=exts, recursive=cb_recursive.value)
```

**`app/ui/year_org_tab.py`** – analog, `cb_recursive` in `do_preview()` und `do_execute()` weitergeben.

---

### B6 – `ui.separator()` zwischen Checkbox-Gruppen

(see brainstorm: docs/brainstorms/2026-02-28-weitere-ideen.md – Entscheidung: Trennstrich)

**`app/ui/duplicates_tab.py`** – finales Layout Optionsbereich:

```python
with ui.row().classes("items-center gap-4 flex-wrap mt-1"):
    cb_recursive = ui.checkbox("Mit Unterordnern", value=True)
ui.separator()
with ui.row().classes("items-center gap-4 flex-wrap mt-1"):
    cb_fotos  = ui.checkbox("Fotos",  value=True)
    cb_videos = ui.checkbox("Videos", value=True)
    cb_audio  = ui.checkbox("Audio",  value=False)
```

**`app/ui/renamer_tab.py`** – finales Layout:

```python
with ui.row().classes("items-center gap-4 flex-wrap"):
    cb_recursive = ui.checkbox("Mit Unterordnern", value=True)
ui.separator()
with ui.row().classes("items-center gap-4 flex-wrap"):
    cb_fotos  = ui.checkbox("Fotos",  value=True)
    cb_videos = ui.checkbox("Videos", value=True)
```

**`app/ui/year_org_tab.py`** – finales Layout (drei Gruppen):

```python
with ui.row().classes("items-center gap-4 flex-wrap mt-1"):
    cb_recursive = ui.checkbox("Mit Unterordnern", value=True)
ui.separator()
with ui.row().classes("items-center gap-4 flex-wrap mt-1"):
    cb_fotos  = ui.checkbox("Fotos",  value=True)
    cb_videos = ui.checkbox("Videos", value=True)
ui.separator()
with ui.row().classes("items-center gap-2 mt-1"):     # ← B7 bereits eingebaut
    camera_checkbox = ui.checkbox("Nach Kamera sortieren")
    ui.icon("info_outline").classes("text-[#4f8ef7] text-sm cursor-default").tooltip(
        "Kamera-Erkennung liest EXIF Make/Model aus den Dateien. "
        "Dateien ohne EXIF landen im Ordner 'Sonstige'."
    )
```

---

### B7 – Info-Icon korrekt wrappen

Bereits in B6 oben eingebaut. Separat: `camera_checkbox` und Icon aus ihren aktuellen
Positionen (Zeilen 20–24 `year_org_tab.py`) in eine `ui.row()` ziehen.

---

## Betroffene Dateien

| Datei | Änderungen |
|-------|-----------|
| `app/ui/duplicates_tab.py` | B1, B4, B5, B6 |
| `app/ui/year_org_tab.py` | B1, B2, B4, B5, B6, B7 |
| `app/ui/renamer_tab.py` | B4, B6 |
| `app/ui/video_compress_tab.py` | B3 |
| `app/core/duplicates.py` | B5 (`recursive`-Parameter) |
| `app/core/year_org.py` | B5 (`recursive`-Parameter prüfen/ergänzen) |

---

## Reihenfolge der Umsetzung

1. Core-Änderungen zuerst: `duplicates.py`, `year_org.py` – `recursive`-Parameter ergänzen
2. `year_org_tab.py` – größte Änderung (B1, B2, B4, B5, B6, B7)
3. `duplicates_tab.py` (B1, B4, B5, B6)
4. `renamer_tab.py` (B4, B6 – keine Core-Änderung)
5. `video_compress_tab.py` (B3 – kleinste Änderung)

---

## Sources & References

- **Origin brainstorm:** [docs/brainstorms/2026-02-28-weitere-ideen.md](../brainstorms/2026-02-28-weitere-ideen.md)
  - Entschieden: `ui.separator()` zwischen Gruppen (B6)
  - Entschieden: `show_value=False` + Status-Label für Prozentanzeige (B1)
  - Entschieden: Auto-Fill nur wenn Zielfeld leer (B3)
- Bestehendes Muster `cb_recursive`: `app/ui/renamer_tab.py:22`
- Bestehendes Muster Info-Icon: `app/ui/year_org_tab.py:21–24`
- NiceGUI `ui.linear_progress` Doku: show_value-Parameter
