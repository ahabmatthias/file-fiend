---
status: complete
priority: p2
issue_id: "017"
tags: [code-review, type-safety, python]
dependencies: []
---

# progress_cb ohne Typ-Annotation in allen Core-Funktionen

## Problem Statement

`progress_cb=None` ist in allen Core-Funktionen untypisiert. Die Callback-Signatur
ist `(done: int, total: int) -> None`, aber das ist nirgendwo annotiert.
Als Lernprojekt ist das die wichtigste Gewohnheit: wenn du einen Parameter hinzufügst,
annotiere ihn.

## Findings

Betroffen (alle mit `progress_cb=None`):
- `app/core/duplicates.py:25`
- `app/core/renamer.py` – nicht betroffen (`collect_files` hat kein progress_cb)
- `app/core/year_org.py:249` (`_collect_files_with_years`)
- `app/core/year_org.py:305` (`scan_folder`)
- `app/core/year_org.py:401` (`execute_organization`)

Außerdem fehlt der Return-Type von `_collect_files_with_years`:
- `app/core/year_org.py:248` – gibt `tuple[dict, list[dict]]` zurück, aber keine Annotation

## Proposed Solutions

### Option 1: Callable-Annotation mit collections.abc

```python
from collections.abc import Callable

def find_duplicates(
    folder: str,
    progress_cb: Callable[[int, int], None] | None = None,
    extensions: set[str] | None = None,
) -> dict[str, list[str]]:
```

Für `_collect_files_with_years`:
```python
def _collect_files_with_years(
    folder_path: str,
    group_by_camera: bool = False,
    extensions: set[str] | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
) -> tuple[dict, list[dict]]:
```

**Effort:** 30 Minuten
**Risk:** Very Low (rein additive Änderung)

## Recommended Action

Option 1 umsetzen.

## Technical Details

**Affected files:**
- `app/core/duplicates.py:25`
- `app/core/year_org.py:248, 305, 401`

## Acceptance Criteria

- [ ] `progress_cb` in allen Core-Funktionen mit `Callable[[int, int], None] | None` annotiert
- [ ] `_collect_files_with_years` hat Return-Type `tuple[dict, list[dict]]`
- [ ] `mypy` läuft durch (bereits im pre-commit-hook)

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (kieran-python-reviewer agent)
