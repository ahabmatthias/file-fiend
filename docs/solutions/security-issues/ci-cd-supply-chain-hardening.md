---
title: "CI/CD Supply Chain Hardening"
date: "2026-02-27"
category: security-issues
tags:
  - supply-chain
  - sha256-verification
  - github-actions
  - dependency-pinning
  - least-privilege
  - windows-build
  - unicode-encoding
components:
  - build/windows/get_ffmpeg.py
  - build/windows/get_mediainfo.py
  - build/macos/get_ffmpeg.sh
  - .github/workflows/build-windows.yml
  - build_app.py
  - requirements.txt
problem_type: security_issue
severity: high
commits:
  - cbf0ece  # fix: Unicode in Build-Skripten
  - b8d2bcf  # security: Hash-Verifikation, gepinnte URLs, CI-Permissions
  - 717bc86  # security: SHA256-Hash fuer gepinnten ffmpeg-Build setzen
  - a8ccdf2  # security: Code-Review-Findings beheben
related_docs:
  - docs/plans/2026-02-24-feat-windows-portierung-plan.md
  - docs/brainstorms/2026-02-24-windows-portierung-brainstorm.md
  - todos/001-pending-p1-dead-none-branch-get-ffmpeg.md
  - todos/002-pending-p1-macos-get-ffmpeg-no-hash-verification.md
  - todos/003-pending-p1-github-actions-not-pinned-to-sha.md
  - todos/006-pending-p2-pyinstaller-unpinned-in-ci.md
  - todos/010-pending-p3-artifact-retention-explicit.md
---

# CI/CD Supply Chain Hardening

Im Zuge der Windows-Portierung (siehe Plan: `docs/plans/2026-02-24-feat-windows-portierung-plan.md`)
wurde ein Security-Review durchgeführt, das mehrere Angriffsvektoren in der Build-Pipeline
aufdeckte. Alle Probleme wurden in vier aufeinanderfolgenden Commits (Feb 24–27, 2026) behoben.

---

## Problem-Symptoms

1. Download-Scripts holten `ffmpeg`/`ffprobe` über `/latest/`-URLs – ohne Hash-Verifikation.
2. GitHub Actions nutzte mutable Tags (`@v4`, `@v5`) statt gepinnte Commit-SHAs.
3. Der CI-Workflow hatte keine expliziten Permissions → Default ist `write-all`.
4. Python `print()`-Aufrufe mit Unicode-Zeichen (`→`, `…`, `ü`) crashten auf Windows CP1252.
5. HTTP-Requests ohne `timeout` konnten unbegrenzt hängen.
6. `requirements.txt` hatte ungepinnte Paketversionen; `pyinstaller` fehlte ganz.
7. Tote Code-Branches (`if EXPECTED_SHA256 is None`) blieben nach initialer TODO-Phase übrig.
8. macOS-Script `get_ffmpeg.sh` lud Binaries ohne jede Verifikation.

---

## Root Cause

Der Windows-Port wurde zunächst als reine Packaging-Aufgabe betrachtet (see brainstorm).
Security-Aspekte der Build-Pipeline wurden erst im separaten Review-Pass (Claude Opus als Reviewer)
systematisch analysiert. Alle Schwachstellen entstanden durch:

- **Supply Chain:** Externe Binaries ohne Integritätsprüfung = MITM-Risiko oder stille
  Server-seitige Ersetzung.
- **CI/CD:** Mutable Action-Tags + Default-Permissions = mögliche Kompromittierung des
  Repository-Zustands durch gekaperte Action-Updates.
- **Platform mismatch:** Windows CP1252 Console ist ein bekanntes Problem bei Python-Scripts,
  die für macOS/Linux geschrieben wurden.

---

## Solution

### 1. Windows CP1252 – Unicode in `print()` ersetzen (commit `cbf0ece`)

**Regel:** Nur ASCII in `print()`-Ausgaben in Build-Scripts. Docstrings und Kommentare dürfen
weiter Deutsch mit Umlauten enthalten.

```python
# Vorher (crasht auf Windows CP1252):
print("==> Lade ffmpeg für Windows x86_64 …")
print(f"    → {target}")

# Nachher:
print("==> Lade ffmpeg fuer Windows x86_64 ...")
print(f"    -> {target}")
```

Betrifft: `build/windows/get_ffmpeg.py`, `build/windows/get_mediainfo.py` – je 5 `print()`-Stellen.

---

### 2. Download-URL pinnen + SHA256-Verifikation (commits `b8d2bcf` + `717bc86`)

**Regel:** Niemals `/latest/`-URLs. Immer konkretes Release + SHA256-Hash im Code.

**Vorgehen (zweistufig, weil Hash erst nach CI-Run bekannt):**

**Schritt 1** – URL pinnen, Hash-Verifikation-Gerüst einfügen (Platzhalter `None`):
```python
FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/"
    "autobuild-2026-02-24-16-00/"
    "ffmpeg-n7.1.3-40-gcddd06f3b9-win64-gpl-7.1.zip"
)
EXPECTED_SHA256 = None  # Nach erstem CI-Run mit gepinnter URL setzen

# ...
sha256 = hashlib.sha256(data).hexdigest()
print(f"SHA256: {sha256}")  # Im CI-Log sichtbar
if EXPECTED_SHA256 is None:
    print("WARNUNG: Hash nicht verifiziert!")
elif sha256 != EXPECTED_SHA256:
    print("FEHLER: Hash stimmt nicht ueberein!")
    sys.exit(1)
```

**Schritt 2** – Hash aus CI-Log übernehmen:
```python
EXPECTED_SHA256 = "53e8df0587165ed1d3868225ed9f866a6f261a7a707ba5ffcf5c4d611869297e"
```

**Gültige Hashes (Stand 2026-02-25):**

| Binary | Quelle | SHA256 |
|--------|--------|--------|
| ffmpeg (Windows x64) | BtbN autobuild-2026-02-24 | `53e8df0587165ed1d...` |
| ffprobe (indirekt via ZIP) | — | im selben ZIP |
| MediaInfo.dll (Windows x64) | MediaArea 26.01 | `3e6fbb6595f7b7d18...` |
| ffmpeg (macOS) | evermeet.cx 7.1.1 | `8d7917c1cebd7a29e...` |
| ffprobe (macOS) | evermeet.cx 7.1.1 | `5a0a77d5e0c689f7b...` |

---

### 3. Toten `is None`-Branch entfernen + `timeout=120` + `-> None` Annotation (commit `a8ccdf2`)

Nachdem der Hash gesetzt ist, ist der `is None`-Zweig nie erreichbar → entfernen.
Gleichzeitig: `timeout` für alle HTTP-Requests, Return-Typ-Annotation.

```python
def download_and_extract() -> None:
    with urlopen(FFMPEG_URL, timeout=120) as resp:
        data = resp.read()

    sha256 = hashlib.sha256(data).hexdigest()
    if sha256 != EXPECTED_SHA256:
        print("FEHLER: Hash stimmt nicht ueberein!")
        print(f"Erwartet: {EXPECTED_SHA256}")
        print(f"Erhalten: {sha256}")
        sys.exit(1)
    print("Hash OK")
```

---

### 4. macOS-Script `get_ffmpeg.sh` – SHA256-Verifikation (commit `a8ccdf2`)

Bash-Äquivalent mit `shasum -a 256`:

```bash
FFMPEG_URL="https://evermeet.cx/ffmpeg/ffmpeg-7.1.1.zip"
EXPECTED_SHA256_FFMPEG="8d7917c1cebd7a29e68c0a0a6cc4ecc3fe05c7fffed958636c7018b319afdda4"

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

curl -fSL "$FFMPEG_URL" -o "$TMP_DIR/ffmpeg.zip"
verify_sha256 "$TMP_DIR/ffmpeg.zip" "$EXPECTED_SHA256_FFMPEG"
```

---

### 5. GitHub Actions auf Commit-SHAs pinnen + Least Privilege (commit `a8ccdf2`)

**Regel:** Tags sind mutable (`@v4` kann jederzeit auf einen anderen Commit zeigen). SHA ist
unveränderlich.

```yaml
# Vorher (unsicher):
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
- uses: actions/upload-artifact@v4

# Nachher (sicher):
- uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5      # v4
- uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065  # v5
- uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
```

**Least Privilege:**
```yaml
permissions:
  contents: read  # Nur Lesen, kein Schreiben ins Repo
```

**Artifact Retention:**
```yaml
- uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4
  with:
    name: FileFiend-Windows
    path: dist/FileFiend/
    retention-days: 30
```

**`pyinstaller` aus `requirements.txt` statt separatem `pip install`:**
```yaml
# Vorher:
run: |
  pip install -r requirements.txt
  pip install pyinstaller  # unpinned!

# Nachher:
run: pip install -r requirements.txt  # pyinstaller==6.19.0 ist jetzt drin
```

---

### 6. `requirements.txt` – Alle Pakete auf exakte Versionen pinnen

```
# Vorher (floating):
pillow
nicegui
pyinstaller  # fehlte komplett

# Nachher (exact pins):
pillow==12.1.1
pillow-heif==1.2.1
pymediainfo==7.0.1
tqdm==4.67.3
nicegui==3.7.1
pywebview==6.1
pyinstaller==6.19.0
```

---

### 7. `build_app.py` – Kleinere Fixes

```python
# Vorher:
ROOT = Path(__file__).parent

# Nachher (eliminiert Symlinks):
ROOT = Path(__file__).resolve().parent
```

Return-Typ-Annotation:
```python
def build() -> None:
    ...
```

---

## Hash-Update-Prozess (für zukünftige Upgrades)

Wenn `ffmpeg` oder `MediaInfo` eine neue Version bekommt:

1. URL im Script auf neue Version aktualisieren
2. `EXPECTED_SHA256 = None` setzen (temporär)
3. CI-Run triggern → SHA256 wird im Log gedruckt (`SHA256: abc123...`)
4. Hash aus Log in den Code übernehmen
5. Commit: `security: [binary] hash auf [version] aktualisieren`

Für GitHub Actions SHA-Update:
```bash
# SHA für eine Action-Version finden:
gh api repos/actions/checkout/releases/tags/v4 --jq '.target_commitish'
# Oder: GitHub UI → actions/checkout → Releases → v4 → Commit SHA
```

---

## Prevention Checklist

- [ ] Alle externen Binary-Downloads: spezifische URL, `EXPECTED_SHA256` gesetzt, `timeout` gesetzt
- [ ] Kein `/latest/` in Download-URLs
- [ ] GitHub Actions: `@SHA` statt `@vN`
- [ ] `permissions: contents: read` im Workflow
- [ ] `requirements.txt`: alle Pakete mit `==X.Y.Z`
- [ ] Build-Script-`print()`: kein Unicode (nur ASCII)
- [ ] Nach Binary-Upgrade: Hash-Update-Prozess (s.o.) durchführen

---

## Learnings

- **Security-Review als separaten Schritt** einplanen, nicht inline während Feature-Entwicklung.
  Der Windows-Port war als Packaging-Task gestartet; alle Security-Lücken wurden erst im
  dedizierten Review-Pass gefunden.
- **Zweistufiges Hash-Pinning** ist der pragmatische Weg: erst URL pinnen + CI laufen lassen,
  dann Hash übernehmen. Nicht versuchen, den Hash vorab manuell zu berechnen.
- **Windows CP1252** trifft immer dann, wenn Python-Scripts für Unix geschrieben und nicht auf
  Windows getestet wurden. Einfachste Lösung: ASCII-only in `print()`.
- **`actions/checkout@v4` ist ein Sicherheitsrisiko** – auch wenn es bequemer ist. SHA-Pins mit
  Versions-Kommentar (`# v4`) sind der beste Kompromiss aus Sicherheit und Lesbarkeit.
