---
status: done
priority: p2
issue_id: "006"
tags: [code-review, security, ci, supply-chain]
dependencies: [005]
---

# 006 – PyInstaller installed unpinned in CI

## Problem Statement

`.github/workflows/build-windows.yml` line 26 runs `pip install pyinstaller` with no version pin. PyInstaller is a highly privileged build tool — it reads, introspects, and bundles the entire Python environment into the output EXE. A compromise of the PyInstaller PyPI package would result in arbitrary code being bundled into the distributed EXE with no detection. This is the highest-privilege tool in the build pipeline.

## Findings

- **File:** `.github/workflows/build-windows.yml:26`
```yaml
run: |
  pip install -r requirements.txt
  pip install pyinstaller  # unpinned
```
- Current working version: 6.19.0 (seen in build output)
- Flagged by: security-sentinel (F-06 P2), architecture-strategist (P2)

## Proposed Solutions

### Option A – Pin in CI command (Quick fix)
```yaml
run: |
  pip install -r requirements.txt
  pip install pyinstaller==6.19.0
```
- **Pros:** Immediate fix, no new files needed
- **Effort:** Small
- **Risk:** None

### Option B – Add to requirements-build.txt (Better)
Create `requirements-build.txt`:
```
pyinstaller==6.19.0
```
Update workflow:
```yaml
run: |
  pip install -r requirements.txt
  pip install -r requirements-build.txt
```
- **Pros:** Visible in repository, version history traceable
- **Effort:** Small (new file + update workflow)
- **Risk:** None

### Option C – Add pyinstaller to requirements.txt directly
Since `pip install pyinstaller` is needed locally too (build_app.py requires it), just add it to requirements.txt:
```
pyinstaller==6.19.0
```
- **Pros:** Single file, simpler
- **Effort:** Minimal

## Recommended Action

Option C (add to `requirements.txt`). Simplest, keeps one dependency file. Pairs with todo 005.

## Technical Details

- **Affected file:** `.github/workflows/build-windows.yml:26`
- **Current version:** 6.19.0 (confirmed from recent build log)

## Acceptance Criteria

- [ ] PyInstaller version is pinned (no bare `pip install pyinstaller`)
- [ ] Version matches what's used locally for macOS builds (6.19.0)

## Work Log

- 2026-02-27: Identified by security-sentinel (F-06)
