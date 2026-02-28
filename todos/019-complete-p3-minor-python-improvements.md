---
status: complete
priority: p3
issue_id: "019"
tags: [code-review, python, quality]
dependencies: []
---

# Kleinere Python-Qualitätsverbesserungen

## Problem Statement

Mehrere kleine Code-Qualitätsprobleme die einzeln trivial sind, aber als Sammlung
den Python-Stil verbessern.

## Findings

**1. `or` auf Set statt `is not None` in year_org_tab.py**
```python
# app/ui/year_org_tab.py:215 – AKTUELL
exts = _state.get("extensions") or (IMAGE_EXTS | VIDEO_EXTS)
```
`or` auf einem Set testet auf Leerheit, nicht auf `None`. `_state["extensions"]` ist
entweder ein nicht-leeres Set oder `None` – nie ein leeres Set. Die explizite Form
`if _state["extensions"] is not None` ist klarer.

**2. Inline-Ternary in List-Comprehension (year_org.py)**
Bereits in Todo #014 erfasst – hier nur als Notiz.

**3. `frozenset` für Konstanten in constants.py**
```python
# app/core/constants.py – AKTUELL
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"}
# BESSER
IMAGE_EXTS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".heic", ".tiff", ".bmp"})
```
`frozenset` signalisiert "unveränderlich" und ist die semantisch korrekte Wahl für
Modul-Konstanten.

**4. Docstring-Stil-Inkonsistenz in duplicates.py**
```python
# Aktuell – gemischter Stil
progress_cb(scanned, total) wird optional nach jedem gehashten File aufgerufen.
extensions: wenn gesetzt, werden nur Dateien mit diesen Extensions berücksichtigt.
```
Entweder alle Parameter als `Args:`-Section (Google-Stil) oder als Prosa – nicht gemischt.

## Proposed Solutions

### Option 1: Alle vier Punkte in einem Commit

Kleine Änderungen, alle in einem kurzen Commit erledigen.

**Effort:** 30 Minuten
**Risk:** Very Low

## Recommended Action

Option 1 – bei nächster Gelegenheit.

## Technical Details

**Affected files:**
- `app/ui/year_org_tab.py:215`
- `app/core/constants.py:5-8`
- `app/core/duplicates.py:28-31`

## Acceptance Criteria

- [ ] `_state["extensions"]` Zugriff ohne `or`-Fallback (nach Fix #015)
- [ ] `constants.py` nutzt `frozenset[str]`
- [ ] Docstring in `duplicates.py` hat konsistenten Stil

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (kieran-python-reviewer agent)
