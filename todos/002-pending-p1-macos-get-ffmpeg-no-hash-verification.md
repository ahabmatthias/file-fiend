---
status: done
priority: p1
issue_id: "002"
tags: [code-review, security, supply-chain]
dependencies: []
---

# 002 – macOS `get_ffmpeg.sh` has no SHA256 hash verification

## Problem Statement

`build/macos/get_ffmpeg.sh` downloads ffmpeg and ffprobe from `evermeet.cx` and immediately extracts + uses them without any integrity check. The Windows equivalents (`get_ffmpeg.py`, `get_mediainfo.py`) both verify SHA256 and exit on mismatch. This asymmetry means the macOS build has a weaker supply chain posture: a MITM, DNS hijack, or compromise of evermeet.cx would silently embed a trojaned binary into the macOS app.

`evermeet.cx` is an individual-operated site. The Windows build uses GitHub's official BtbN/FFmpeg-Builds which has broader trust. The macOS source is riskier, making hash verification more important, not less.

## Findings

- **File:** `build/macos/get_ffmpeg.sh:18-33`
- `curl -fSL "$FFMPEG_URL" -o "$TMP_DIR/ffmpeg.zip"` → `unzip` → `mv` — no hash check
- `evermeet.cx` publishes SHA256 checksums at `https://evermeet.cx/ffmpeg/info/ffmpeg/<version>` (JSON API) — currently not used
- Windows standard (established by commits `b8d2bcf`, `717bc86`) requires SHA256 pinning
- Flagged by: security-sentinel (F-02 P1), architecture-strategist (P1 risk), agent-native-reviewer (P2-A)

## Proposed Solutions

### Option A – Add `shasum` check to shell script (Recommended)
```bash
# After download, before unzip:
EXPECTED_SHA256_FFMPEG="<hash>"
EXPECTED_SHA256_FFPROBE="<hash>"

actual=$(shasum -a 256 "$TMP_DIR/ffmpeg.zip" | awk '{print $1}')
if [ "$actual" != "$EXPECTED_SHA256_FFMPEG" ]; then
    echo "FEHLER: ffmpeg SHA256 stimmt nicht ueberein!"
    echo "  Erwartet: $EXPECTED_SHA256_FFMPEG"
    echo "  Erhalten: $actual"
    exit 1
fi
echo "  Hash OK"
```

Get hashes from: `curl -s https://evermeet.cx/ffmpeg/info/ffmpeg/7.1.1 | python3 -c "import sys,json; print(json.load(sys.stdin)['download']['zip']['sha256'])"`

- **Pros:** Matches Windows standard, protects against supply chain attack
- **Effort:** Medium (need to get current hashes, add to script)
- **Risk:** Low — `shasum` available on all macOS

### Option B – Rewrite `get_ffmpeg.sh` as Python script
Port to `get_ffmpeg.py` following the exact pattern of `build/windows/get_ffmpeg.py`. Eliminates the macOS/Windows asymmetry in both language and verification.
- **Pros:** Consistent interface (Python), same verification pattern, easier to maintain
- **Effort:** Medium
- **Risk:** Low

## Recommended Action

Option A now (fast fix). Option B is worth considering if Linux support is added (already have Python on macOS).

## Technical Details

- **Affected file:** `build/macos/get_ffmpeg.sh`
- **Hash source:** `https://evermeet.cx/ffmpeg/info/ffmpeg/7.1.1` and `https://evermeet.cx/ffmpeg/info/ffprobe/7.1.1`
- Run the info URLs to get current SHA256 values before committing

## Acceptance Criteria

- [ ] `get_ffmpeg.sh` verifies SHA256 of both downloaded ZIPs before extracting
- [ ] Script exits non-zero on hash mismatch
- [ ] Expected hashes are hardcoded (not fetched at runtime)
- [ ] macOS build still works: `bash build/macos/get_ffmpeg.sh` completes successfully

## Work Log

- 2026-02-27: Identified as most severe security gap by security-sentinel and architecture-strategist
