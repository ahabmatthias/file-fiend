---
status: done
priority: p3
issue_id: "009"
tags: [code-review, quality, python]
dependencies: []
---

# 009 – Missing `-> None` return type hints on build script functions

## Problem Statement

Three functions in the build scripts are missing return type annotations. Minor issue for scripts, but inconsistent with the existing annotations in the same files.

## Findings

- `build/windows/get_ffmpeg.py:33` — `def download_and_extract():` → should be `def download_and_extract() -> None:`
- `build/windows/get_mediainfo.py:30` — same
- `build_app.py:75` — `def build():` → should be `def build() -> None:`
- Flagged by: kieran-python-reviewer (P2)

## Proposed Solution

```python
# get_ffmpeg.py:33
def download_and_extract() -> None:

# get_mediainfo.py:30
def download_and_extract() -> None:

# build_app.py:75
def build() -> None:
```

## Acceptance Criteria

- [ ] All three functions have `-> None` annotations

## Work Log

- 2026-02-27: Identified by kieran-python-reviewer
