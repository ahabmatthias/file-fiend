---
status: done
priority: p2
issue_id: "008"
tags: [code-review, quality, python]
dependencies: []
---

# 008 – `platform_name` ternary silently mislabels unknown platforms

## Problem Statement

`build_app.py:80` uses `platform_name = "macOS" if IS_MACOS else "Windows"`. If `IS_MACOS` is false for any reason (including if the `sys.exit` guard in `get_spec_file` were ever removed), this silently prints "Windows" even on Linux. It's a misleading fallthrough that contradicts the explicit unsupported-platform guard established 60 lines earlier.

## Findings

- **File:** `build_app.py:80`
```python
platform_name = "macOS" if IS_MACOS else "Windows"
```
- The `else` branch is `"Windows"` which is wrong for any non-macOS, non-Windows platform
- Flagged by: architecture-strategist (P2), kieran-python-reviewer (P2)

## Proposed Solutions

### Option A – Three-way expression
```python
platform_name = "macOS" if IS_MACOS else "Windows" if IS_WINDOWS else sys.platform
```

### Option B – Derive from spec file path (cleanest)
```python
spec = get_spec_file()
platform_name = "macOS" if IS_MACOS else "Windows"
# get_spec_file() already hard-fails on unsupported platforms, so this ternary is safe
```
Actually at `build_app.py:80`, `get_spec_file()` has already been called and validated. The ternary is technically safe since unsupported platforms never reach line 80. But the code pattern still trains readers to expect `elif IS_WINDOWS` as exhaustive.

### Option C – Just add a comment
```python
# get_spec_file() above already exits on unsupported platforms, so IS_MACOS=False ⟹ IS_WINDOWS=True
platform_name = "macOS" if IS_MACOS else "Windows"
```

## Recommended Action

Option C for now (add comment, explain why it's safe). Option A if you add Linux later.

## Technical Details

- **Affected file:** `build_app.py:80`

## Acceptance Criteria

- [ ] Either a comment explains why the ternary is safe, or it's updated to a three-way expression

## Work Log

- 2026-02-27: Identified by architecture-strategist and kieran-python-reviewer
