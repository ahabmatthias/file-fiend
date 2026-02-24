#!/usr/bin/env bash
# Lädt statisch gelinkte ffmpeg + ffprobe für macOS arm64 herunter.
# Quelle: evermeet.cx (Martin Riedl) – die bekannteste Quelle für macOS-ffmpeg-Builds.
#
# Verwendung:
#   bash build/macos/get_ffmpeg.sh
#
# Die Binaries landen in vendor/ffmpeg und vendor/ffprobe.

set -euo pipefail

VENDOR_DIR="$(cd "$(dirname "$0")/../.." && pwd)/vendor"
mkdir -p "$VENDOR_DIR"

echo "==> Lade statisches ffmpeg für macOS arm64 …"

# evermeet.cx liefert .zip-Archive mit der neuesten Version
FFMPEG_URL="https://evermeet.cx/ffmpeg/ffmpeg-7.1.1.zip"
FFPROBE_URL="https://evermeet.cx/ffmpeg/ffprobe-7.1.1.zip"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "    ffmpeg …"
curl -fSL "$FFMPEG_URL" -o "$TMP_DIR/ffmpeg.zip"
unzip -o -q "$TMP_DIR/ffmpeg.zip" -d "$TMP_DIR"
mv "$TMP_DIR/ffmpeg" "$VENDOR_DIR/ffmpeg"
chmod +x "$VENDOR_DIR/ffmpeg"

echo "    ffprobe …"
curl -fSL "$FFPROBE_URL" -o "$TMP_DIR/ffprobe.zip"
unzip -o -q "$TMP_DIR/ffprobe.zip" -d "$TMP_DIR"
mv "$TMP_DIR/ffprobe" "$VENDOR_DIR/ffprobe"
chmod +x "$VENDOR_DIR/ffprobe"

echo ""
echo "==> Fertig! Binaries in $VENDOR_DIR:"
ls -lh "$VENDOR_DIR/ffmpeg" "$VENDOR_DIR/ffprobe"
echo ""
echo "Versionen:"
"$VENDOR_DIR/ffmpeg" -version 2>&1 | head -1
"$VENDOR_DIR/ffprobe" -version 2>&1 | head -1
