---
status: done
priority: p2
issue_id: "004"
tags: [code-review, performance, reliability, ci]
dependencies: []
---

# 004 – `urlopen` has no timeout — CI can hang indefinitely

## Problem Statement

Both download scripts call `urlopen(URL)` without a timeout argument. If the remote server accepts the TCP connection but stalls the response body, `resp.read()` blocks forever. GitHub Actions' default job timeout is 6 hours, so a stalled download ties up a runner for hours before being killed — with no diagnostic signal.

## Findings

- **File:** `build/windows/get_ffmpeg.py:39`
- **File:** `build/windows/get_mediainfo.py:36`
```python
with urlopen(FFMPEG_URL) as resp:
    data = resp.read()  # No timeout
```
- Flagged by: performance-oracle (P2), security-sentinel (F-04 P2), python-reviewer (P3)

## Proposed Solution

Two-line fix in each file:
```python
with urlopen(FFMPEG_URL, timeout=120) as resp:
    data = resp.read()
```

120 seconds is generous: a 100 MB file at 10 Mbit/s (slow CI) takes ~80s. If download exceeds 2 minutes something is genuinely wrong.

**Optional bonus — retry loop (add alongside timeout):**
```python
import time

def _download(url: str, timeout: int = 120) -> bytes:
    for attempt in range(1, 4):
        try:
            with urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            if attempt == 3:
                raise
            wait = 2 ** attempt
            print(f"    Attempt {attempt} failed ({exc}), retry in {wait}s ...")
            time.sleep(wait)
```

## Recommended Action

Add `timeout=120` first (2 lines, minimal change). Add retry loop only if CI shows flaky download failures.

## Technical Details

- **Affected files:** `build/windows/get_ffmpeg.py:39`, `build/windows/get_mediainfo.py:36`
- **Fix:** Add `timeout=120` parameter to `urlopen()` in both files

## Acceptance Criteria

- [ ] Both `urlopen()` calls include `timeout=120`
- [ ] A stalled download now fails cleanly after 2 minutes instead of hanging indefinitely

## Work Log

- 2026-02-27: Identified by performance-oracle (P2) and security-sentinel (F-04)
