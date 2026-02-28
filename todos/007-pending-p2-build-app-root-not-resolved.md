---
status: done
priority: p2
issue_id: "007"
tags: [code-review, quality, python]
dependencies: []
---

# 007 – `build_app.py` ROOT path not resolved

## Problem Statement

`build_app.py:15` uses `ROOT = Path(__file__).parent` without calling `.resolve()`. If the script is invoked via a symlink or with a relative path (e.g. `python ../../build_app.py`), `__file__` may be relative, making ROOT relative. All downstream operations (`ROOT / "vendor"`, `spec.relative_to(ROOT)`) then fail or produce confusing output. The download scripts correctly use `Path(__file__).resolve().parent.parent.parent`.

## Findings

- **File:** `build_app.py:15`
```python
ROOT = Path(__file__).parent      # Not resolved
```
vs. download scripts:
```python
ROOT = Path(__file__).resolve().parent.parent.parent  # Resolved
```
- Flagged by: kieran-python-reviewer (P3)

## Proposed Solution

One-character fix:
```python
ROOT = Path(__file__).resolve().parent
```

## Technical Details

- **Affected file:** `build_app.py:15`
- **Fix:** Add `.resolve()` before `.parent`

## Acceptance Criteria

- [ ] `ROOT = Path(__file__).resolve().parent`
- [ ] `python build_app.py` still works when called from any directory

## Work Log

- 2026-02-27: Identified by kieran-python-reviewer
