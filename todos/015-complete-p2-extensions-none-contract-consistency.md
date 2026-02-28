---
status: complete
priority: p2
issue_id: "015"
tags: [code-review, architecture, api-design]
dependencies: []
---

# None-Semantik für extensions inkonsistent + divergenter Fallback

## Problem Statement

Die drei Core-Funktionen haben unterschiedliche Bedeutungen für `extensions=None`,
und der Fallback-Wert in `do_execute` weicht vom Core-Default ab.

## Findings

**Finding 1 – Inkonsistente None-Semantik:**

| Funktion | `None` bedeutet |
|----------|----------------|
| `find_duplicates` | Alle Dateien (kein Filter) |
| `collect_files` (renamer) | `IMAGE_EXTS \| VIDEO_EXTS` |
| `scan_folder` / `execute_organization` | `ALL_MEDIA_EXTS` |

Ein Aufrufer der drei Funktionen mit `extensions=None` bekommt drei verschiedene Scopes.

**Finding 2 – Divergenter Fallback in `do_execute`:**
```python
# app/ui/year_org_tab.py:215
exts = _state.get("extensions") or (IMAGE_EXTS | VIDEO_EXTS)
```
Der Core-Default für `year_org` ist `ALL_MEDIA_EXTS` (inkl. Audio), aber der
UI-Fallback konstruiert `IMAGE_EXTS | VIDEO_EXTS` (ohne Audio) inline im UI-Code.
Das UI-Layer entscheidet hier über einen Scope der ins Core-Layer gehört.

## Proposed Solutions

### Option 1: None-Semantik dokumentieren (minimale Änderung)

Jeden Docstring mit einem expliziten Hinweis ergänzen:
```
extensions: Zu berücksichtigende Dateiendungen.
    None → alle Dateien (kein Filter).  [duplicates]
    None → IMAGE_EXTS | VIDEO_EXTS.     [renamer]
    None → ALL_MEDIA_EXTS.              [year_org]
```
Und Fallback in do_execute auf `ALL_MEDIA_EXTS` vereinheitlichen.

**Effort:** 20 Minuten
**Risk:** Low

---

### Option 2: Fallback aus UI-Code entfernen (bevorzugt)

Da `do_execute` nur erreichbar ist wenn `do_preview` `_state["extensions"]` gesetzt hat:

```python
# app/ui/year_org_tab.py – replace line 215:
exts = _state["extensions"]   # immer gesetzt wenn btn_execute enabled ist
```

**Pros:** Entfernt toter Code + falsche Inline-Konstante aus UI
**Cons:** Keine defensive Absicherung mehr (aber auch keine falsche)

**Effort:** 5 Minuten
**Risk:** Low

## Recommended Action

Option 2 für do_execute + Option 1 für die Docstrings.

## Technical Details

**Affected files:**
- `app/ui/year_org_tab.py:215`
- `app/core/duplicates.py:24` – Docstring
- `app/core/renamer.py:96` – Docstring
- `app/core/year_org.py:302` – Docstring

## Acceptance Criteria

- [ ] Jede Core-Funktion hat einen Docstring der `None`-Verhalten klar beschreibt
- [ ] `do_execute` in year_org_tab greift direkt auf `_state["extensions"]` zu ohne Inline-Set-Konstruktion

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (architecture-strategist + agent-native-reviewer agents)
