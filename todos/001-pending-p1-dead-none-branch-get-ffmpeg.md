---
status: done
priority: p1
issue_id: "001"
tags: [code-review, security, quality]
dependencies: []
---

# 001 – Dead `is None` branch in `get_ffmpeg.py`

## Problem Statement

`get_ffmpeg.py` line 46 checks `if EXPECTED_SHA256 is None:` and prints a warning without failing. But `EXPECTED_SHA256` is a string literal set on line 30 — it can never be `None`. This is unreachable dead code that silently implies hash verification can be skipped, which is a security landmine. `get_mediainfo.py` already does this correctly (no None check, always enforces).

## Findings

- **File:** `build/windows/get_ffmpeg.py:46-48`
- Dead branch: `if EXPECTED_SHA256 is None: print("WARNUNG: ...")` — `EXPECTED_SHA256` is `str`, never `None`
- If a developer sets `EXPECTED_SHA256 = None` following the comment on line 29 ("CI laufen lassen, neuen Hash aus Log uebernehmen"), CI would succeed silently with no integrity check
- `get_mediainfo.py:43` does this correctly — no `None` branch, always checks
- Flagged by: kieran-python-reviewer (P1), security-sentinel (F-07 P3), code-simplicity-reviewer (P1), architecture-strategist (P3), performance-oracle (note), agent-native-reviewer (P3-B)

## Proposed Solutions

### Option A – Remove dead branch (Recommended)
```python
# Before (get_ffmpeg.py:46-48)
if EXPECTED_SHA256 is None:
    print("    WARNUNG: Kein EXPECTED_SHA256 gesetzt -- Hash nicht verifiziert!")
elif sha256 != EXPECTED_SHA256:
    ...

# After – matches get_mediainfo.py exactly
if sha256 != EXPECTED_SHA256:
    print("    FEHLER: Hash stimmt nicht ueberein!")
    print(f"    Erwartet: {EXPECTED_SHA256}")
    print(f"    Erhalten: {sha256}")
    sys.exit(1)
print("    Hash OK")
```
- **Pros:** Simple, consistent with `get_mediainfo.py`, eliminates security confusion
- **Effort:** Small (3 lines removed, 1 line unchanged)
- **Risk:** None

### Option B – Type as `str | None` with explicit documentation
```python
# Set to None to skip hash verification (CI bootstrap only, NEVER commit None)
EXPECTED_SHA256: str | None = "53e8df0587..."
if EXPECTED_SHA256 is None:
    sys.exit("FEHLER: EXPECTED_SHA256 nicht gesetzt. Build abgebrochen.")
```
- **Pros:** Makes "skip mode" explicit and safe (exits instead of warning)
- **Effort:** Small
- **Risk:** Low

## Recommended Action

Option A. Match `get_mediainfo.py` exactly. Simplest fix with no downside.

## Technical Details

- **Affected file:** `build/windows/get_ffmpeg.py`, lines 46-48
- **Fix:** Remove 3 lines, restructure `elif` to `if`

## Acceptance Criteria

- [ ] `get_ffmpeg.py` no longer contains `if EXPECTED_SHA256 is None`
- [ ] Both download scripts use the same hash-check pattern
- [ ] `python build/windows/get_ffmpeg.py` still exits non-zero on hash mismatch

## Work Log

- 2026-02-27: Identified by 5 of 7 review agents
