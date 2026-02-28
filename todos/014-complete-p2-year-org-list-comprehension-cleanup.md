---
status: complete
priority: p2
issue_id: "014"
tags: [code-review, performance, quality]
dependencies: []
---

# year_org.py List-Comprehension: Ternary + is_file() Reihenfolge

## Problem Statement

In `_collect_files_with_years()` gibt es zwei Probleme in der Pre-Collection
List-Comprehension: (1) Ein Ternary-Ausdruck wird pro Datei ausgewertet statt einmal
vor der Schleife, (2) `is_file()` (ein syscall) steht vor billigen String-Checks.

## Findings

**Finding 1 – Ternary pro Iteration:**
```python
# app/core/year_org.py:279 – AKTUELL
and f.suffix.lower() in (extensions if extensions is not None else ALL_MEDIA_EXTS)
```
Der Ternary wird bei 100.000 Dateien 100.000× ausgewertet. `renamer.py` macht das
bereits korrekt mit einer Variable vor der Schleife.

**Finding 2 – is_file() als erste Bedingung:**
```python
# app/core/year_org.py:270 – AKTUELL
all_files = [
    f
    for f in folder.rglob("*")
    if (
        f.is_file()              # syscall ZUERST
        and not f.name.startswith("._")    # dann billige String-Checks
        ...
    )
]
```
`is_file()` kostet einen Kernel-Call. String-Checks auf `f.name` kosten nahezu nichts
und könnten viele Einträge bereits eliminieren.

## Proposed Solutions

### Option 1: Beide Probleme in einem Schritt beheben

```python
_active_exts = extensions if extensions is not None else ALL_MEDIA_EXTS

all_files = [
    f
    for f in folder.rglob("*")
    if (
        not f.name.startswith("._")
        and f.name != ".DS_Store"
        and not f.name.startswith("rename_log_")
        and not f.name.startswith("camera_rename_log_")
        and f.parent.name != "duplicates"
        and f.suffix.lower() in _active_exts
        and f.is_file()         # syscall ZULETZT
    )
]
```

**Pros:** Sauber, konsistent mit renamer.py Pattern, minimal bessere Performance
**Cons:** Reihenfolge der Bedingungen ändert sich (kein Behavior-Change)

**Effort:** 10 Minuten
**Risk:** Very Low

## Recommended Action

Option 1 direkt umsetzen.

## Technical Details

**Affected files:**
- `app/core/year_org.py:264-276` – List-Comprehension in `_collect_files_with_years()`

## Resources

- Performance-Agent + Simplicity-Agent + Architecture-Agent Findings (Review 2026-02-28)

## Acceptance Criteria

- [ ] `_active_exts` als Variable vor der Comprehension definiert
- [ ] `f.is_file()` steht als letzte Bedingung in der Comprehension
- [ ] Verhalten unverändert (gleiche Dateien werden gesammelt)

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (performance-oracle + code-simplicity-reviewer agents)
