---
status: complete
priority: p2
issue_id: "013"
tags: [code-review, security]
dependencies: []
---

# validate_folder_path definiert aber nie aufgerufen

## Problem Statement

`app/ui/utils.py` enthält `validate_folder_path()` als expliziten Path-Traversal-Schutz,
aber die Funktion wird in keinem der Tab-Callbacks aufgerufen. Ein Nutzer kann `/`
oder `../../etc` in das Ordner-Eingabefeld tippen und alle Scan/Move-Operationen
laufen gegen diesen Pfad.

## Findings

- `app/ui/utils.py:17-23`: Funktion existiert und prüft `is_relative_to(Path.home())`
- Kein einziger `grep`-Treffer für `validate_folder_path(` im gesamten UI-Code
- Alle Tabs lesen `shared["folder"]` direkt ohne Validierung
- Praktisches Risiko: Nutzer tippt `/` → year_org scannt und verschiebt alle Mediendateien im Root-Verzeichnis

## Proposed Solutions

### Option 1: validate_folder_path in jedem Tab-Callback aufrufen

```python
# In do_scan(), do_preview(), do_execute() nach folder-Auslesen:
from app.ui.utils import validate_folder_path
if not validate_folder_path(folder):
    ui.notify("Ordner muss im Home-Verzeichnis liegen.", type="negative")
    return
```

**Pros:** Nutzt bereits vorhandenen Code, ein-zeilian pro Callback
**Cons:** 6 Call-Sites (3 Tabs × preview+execute)

**Effort:** 30 Minuten
**Risk:** Low

---

### Option 2: Validierung im shared_input on_change-Handler zentral

**Approach:** Im `main.py` shared_input `on_change`-Handler `validate_folder_path` prüfen und
`shared["folder"]` nur setzen wenn gültig.

**Pros:** Eine zentrale Stelle
**Cons:** Fehler erscheint nicht im Tab-Kontext

**Effort:** 15 Minuten
**Risk:** Low

## Recommended Action

Option 1 – einfacher und expliziter je Tab.

## Technical Details

**Affected files:**
- `app/ui/utils.py:17` – Funktion
- `app/ui/duplicates_tab.py` – do_scan()
- `app/ui/renamer_tab.py` – do_preview()
- `app/ui/year_org_tab.py` – do_preview(), do_execute()

## Acceptance Criteria

- [ ] Eingabe von `/` in das Ordnerfeld führt zur Fehlermeldung, nicht zum Scan
- [ ] Alle 4 Callback-Funktionen rufen validate_folder_path auf
- [ ] Gültige Pfade (~/Bilder/) funktionieren weiterhin

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (security-sentinel agent)
