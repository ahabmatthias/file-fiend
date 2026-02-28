---
status: done
priority: p3
issue_id: "010"
tags: [code-review, ci, quality]
dependencies: []
---

# 010 – Artifact retention period not set explicitly

## Problem Statement

`.github/workflows/build-windows.yml` does not set `retention-days` on the artifact upload step. The default is 90 days (configurable per org). This means `gh run download` to retrieve an old build will silently return nothing after 90 days, and the behavior is not documented.

## Findings

- **File:** `.github/workflows/build-windows.yml:38-43`
```yaml
- name: Upload artifact
  uses: actions/upload-artifact@v4
  with:
    name: FileFiend-Windows
    path: dist/FileFiend/
    compression-level: 9
    # retention-days: not set
```
- Flagged by: security-sentinel (F-09 informational), agent-native-reviewer (P3-C)

## Proposed Solution

```yaml
- name: Upload artifact
  uses: actions/upload-artifact@v4
  with:
    name: FileFiend-Windows
    path: dist/FileFiend/
    compression-level: 9
    retention-days: 30
```

## Acceptance Criteria

- [ ] `retention-days` is explicitly set in the artifact upload step

## Work Log

- 2026-02-27: Identified by security-sentinel and agent-native-reviewer
