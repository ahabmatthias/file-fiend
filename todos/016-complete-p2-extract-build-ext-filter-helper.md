---
status: complete
priority: p2
issue_id: "016"
tags: [code-review, quality, duplication]
dependencies: []
---

# „Build exts set" Pattern 3× wiederholt – in utils.py extrahieren

## Problem Statement

Das Muster „lese Checkbox-Werte, baue Extensions-Set, validiere nicht-leer"
ist in allen drei Tabs identisch, aber inline kopiert.

## Findings

Dieses Block taucht in `duplicates_tab.py`, `renamer_tab.py` und `year_org_tab.py` auf:
```python
exts: set[str] = set()
if cb_fotos.value:
    exts |= IMAGE_EXTS
if cb_videos.value:
    exts |= VIDEO_EXTS
# (+ Audio in duplicates_tab)
if not exts:
    status_label.set_text("Bitte mindestens einen Dateityp wählen.")
    return
```

~6 Zeilen × 3 Tabs = 18 Zeilen Duplikat. Jede zukünftige Änderung
(neue Extension, neue Meldung) muss 3× gemacht werden.

## Proposed Solutions

### Option 1: Hilfsfunktion in app/ui/utils.py

```python
# app/ui/utils.py
from app.core.constants import IMAGE_EXTS, VIDEO_EXTS, AUDIO_EXTS

def build_ext_filter(*pairs: tuple[bool, set]) -> set[str]:
    """Kombiniert aktive Extension-Sets. Gibt leeres Set zurück wenn nichts aktiv."""
    exts: set[str] = set()
    for active, ext_set in pairs:
        if active:
            exts |= ext_set
    return exts
```

Aufruf:
```python
exts = build_ext_filter(
    (cb_fotos.value, IMAGE_EXTS),
    (cb_videos.value, VIDEO_EXTS),
)
if not exts:
    status_label.set_text("Bitte mindestens einen Dateityp wählen.")
    return
```

**Pros:** DRY, testbar, eine Stelle für Änderungen
**Cons:** Winzige Indirection

**Effort:** 20 Minuten
**Risk:** Very Low

## Recommended Action

Option 1 umsetzen. Die Validierungsmeldung bleibt im Tab (ist UI-Kontext).

## Technical Details

**Affected files:**
- `app/ui/utils.py` – neue Funktion
- `app/ui/duplicates_tab.py` – Aufruf ersetzen
- `app/ui/renamer_tab.py` – Aufruf ersetzen
- `app/ui/year_org_tab.py` – Aufruf ersetzen

## Acceptance Criteria

- [ ] `build_ext_filter()` in utils.py definiert
- [ ] Alle 3 Tabs nutzen die Hilfsfunktion
- [ ] Verhalten identisch zu vorher

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (code-simplicity-reviewer agent)
