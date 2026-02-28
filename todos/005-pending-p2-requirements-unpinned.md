---
status: done
priority: p2
issue_id: "005"
tags: [code-review, security, supply-chain, ci]
dependencies: []
---

# 005 – `requirements.txt` has no pinned versions

## Problem Statement

`requirements.txt` lists 6 packages (pillow, pillow-heif, pymediainfo, tqdm, nicegui, pywebview) with no version constraints. Every `pip install -r requirements.txt` resolves the latest available versions at that moment. A malicious package update or compromise of any of these packages would silently bake malicious code into the built EXE. Additionally, builds are not reproducible — two runs of the same commit can produce different binaries.

## Findings

- **File:** `requirements.txt`
```
pillow
pillow-heif
pymediainfo
tqdm
nicegui
pywebview
```
- Flagged by: security-sentinel (F-05 P2)

## Proposed Solutions

### Option A – Pin to exact versions (Minimum fix)
Run `pip freeze | grep -E "pillow|pymediainfo|tqdm|nicegui|pywebview"` and pin the current versions:
```
pillow==11.x.x
pillow-heif==0.x.x
pymediainfo==6.x.x
tqdm==4.x.x
nicegui==2.x.x
pywebview==5.x.x
```
- **Pros:** Simple, reproducible builds, requires no new tools
- **Effort:** Small (run pip freeze, paste versions)
- **Risk:** Need to manually update when you want upgrades

### Option B – Use `requirements.in` + `requirements.lock` with `pip-tools`
```bash
pip install pip-tools
# requirements.in lists abstract deps (like current requirements.txt)
pip-compile requirements.in -o requirements.lock
# CI uses: pip install -r requirements.lock
```
- **Pros:** Fully locked with hashes, reproducible, `pip-sync` keeps env in sync
- **Effort:** Medium (restructure, add pip-tools to workflow)
- **Risk:** Low, but adds tooling dependency

### Option C – Pin major versions only (Pragmatic middle ground)
```
nicegui>=2.0,<3.0
pywebview>=5.0,<6.0
pillow>=10.0,<12.0
```
- **Pros:** Allows patch updates, blocks breaking changes, minimal effort
- **Effort:** Small (lookup current major versions, pin them)
- **Risk:** Patch releases could still introduce issues

## Recommended Action

Option A for now (pin exact versions from current working state). Option B if the project grows or becomes more security-sensitive.

## Technical Details

- Run `source .venv/bin/activate && pip freeze` to get exact current versions
- Update `requirements.txt` with the versions
- Update CI workflow to use the same file (it already does `pip install -r requirements.txt`)

## Acceptance Criteria

- [ ] All packages in `requirements.txt` have explicit version pins (at minimum `==X.Y.Z`)
- [ ] `pip install -r requirements.txt` installs the same versions on any machine

## Work Log

- 2026-02-27: Identified by security-sentinel (F-05)
