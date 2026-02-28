---
status: done
priority: p1
issue_id: "003"
tags: [code-review, security, ci, supply-chain]
dependencies: []
---

# 003 – GitHub Actions not pinned to full SHA commit hash

## Problem Statement

`.github/workflows/build-windows.yml` uses mutable version tags (`@v4`, `@v5`) for all three action references. A tag can be force-pushed at any time. If any of these action repositories were compromised, the next CI run would silently execute malicious code with full runner access — including access to the built artifact before it's uploaded. For `actions/*` repos (GitHub-owned) the risk is lower than for third-party actions, but the hygiene gap is real and easy to fix.

## Findings

- **File:** `.github/workflows/build-windows.yml`, lines 15, 21, 38
```yaml
uses: actions/checkout@v4         # mutable
uses: actions/setup-python@v5     # mutable
uses: actions/upload-artifact@v4  # mutable
```
- Flagged by: security-sentinel (F-01 P1)

## Proposed Solutions

### Option A – Pin to full SHA with version comment (Recommended)
```yaml
uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683        # v4.2.2
uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2    # v5.3.0
uses: actions/upload-artifact@65462800fd760344b1a7b4382951275a0aba2ab  # v4.3.3
```
**IMPORTANT:** Verify these SHAs against the actual release tags on github.com before committing. The SHAs above are examples — look up the current ones.

- **Pros:** Immutable reference, standard GitHub security hardening practice
- **Effort:** Small (~15 minutes to look up and verify SHAs)
- **Risk:** None (behavior identical, just reference is immutable)

### Option B – Use Dependabot for action version management
Add `.github/dependabot.yml` to auto-update pinned action SHAs:
```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```
- **Pros:** Pins SHAs AND keeps them updated automatically
- **Effort:** Small
- **Risk:** None

## Recommended Action

Option A (pin SHAs now) + Option B (add Dependabot to keep them updated). Both together are the industry standard.

## Technical Details

- **Affected file:** `.github/workflows/build-windows.yml`
- Look up current SHAs at:
  - `https://github.com/actions/checkout/releases/tag/v4` → click the tag → copy commit SHA
  - `https://github.com/actions/setup-python/releases/tag/v5` → same
  - `https://github.com/actions/upload-artifact/releases/tag/v4` → same

## Acceptance Criteria

- [ ] All three `uses:` lines reference full SHA hashes (40 hex chars)
- [ ] Each SHA is followed by a comment showing the version tag (e.g. `# v4.2.2`)
- [ ] Verified that SHAs match the actual release tag commits on github.com

## Work Log

- 2026-02-27: Identified by security-sentinel as F-01 (P1 Critical)
