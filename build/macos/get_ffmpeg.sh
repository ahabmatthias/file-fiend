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

# SHA256-Hashes der gepinnten Versionen.
# Nach URL-Update: neuen Hash mit `shasum -a 256 <datei>.zip` ermitteln.
EXPECTED_SHA256_FFMPEG="8d7917c1cebd7a29e68c0a0a6cc4ecc3fe05c7fffed958636c7018b319afdda4"
EXPECTED_SHA256_FFPROBE="5a0a77d5e0c689f7b577788e286dd46b2c6120babd14301cce7a79fcfd3f7d28"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

verify_sha256() {
    local file="$1"
    local expected="$2"
    local actual
    actual=$(shasum -a 256 "$file" | awk '{print $1}')
    if [ "$actual" != "$expected" ]; then
        echo "    FEHLER: SHA256 stimmt nicht ueberein!"
        echo "    Erwartet: $expected"
        echo "    Erhalten: $actual"
        exit 1
    fi
    echo "    Hash OK"
}

echo "    ffmpeg …"
curl -fSL "$FFMPEG_URL" -o "$TMP_DIR/ffmpeg.zip"
verify_sha256 "$TMP_DIR/ffmpeg.zip" "$EXPECTED_SHA256_FFMPEG"
unzip -o -q "$TMP_DIR/ffmpeg.zip" -d "$TMP_DIR"
mv "$TMP_DIR/ffmpeg" "$VENDOR_DIR/ffmpeg"
chmod +x "$VENDOR_DIR/ffmpeg"

echo "    ffprobe …"
curl -fSL "$FFPROBE_URL" -o "$TMP_DIR/ffprobe.zip"
verify_sha256 "$TMP_DIR/ffprobe.zip" "$EXPECTED_SHA256_FFPROBE"
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
