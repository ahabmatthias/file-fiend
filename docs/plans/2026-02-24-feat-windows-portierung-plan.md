---
title: "feat: Windows-Portierung als portable .exe"
type: feat
status: active
date: 2026-02-24
origin: docs/brainstorms/2026-02-24-windows-portierung-brainstorm.md
---

# feat: Windows-Portierung als portable .exe

## Overview

FileFiend soll als portable `.exe` (ZIP-Distribution) an Windows-Nutzer weitergegeben werden. Alle Abhängigkeiten (ffmpeg, ffprobe, MediaInfo) werden mitgebundelt. Die macOS-App wird parallel weiterentwickelt – beide Plattformen müssen sauber im selben Repo koexistieren.

## Problem Statement / Motivation

Die App ist aktuell macOS-only. Potenzielle Nutzer auf Windows können sie nicht verwenden. Der Code ist zu ~95% plattformunabhängig (pathlib, kein shell=True, alle Dependencies haben Windows-Wheels). Die Portierung ist primär eine Packaging-Aufgabe, kein Code-Rewrite.

## Proposed Solution

Plattform-spezifische Build-Konfiguration (Spec-Dateien, Build-Scripts, Binary-Download) sauber vom gemeinsamen Code trennen. Der geteilte Code in `app/` bleibt unverändert oder erhält minimale Platform-Guards wo nötig.

### Repo-Struktur nach Portierung

```
media_tools/
├── app/                          # Gemeinsamer Code (unverändert)
│   ├── core/                     # Business-Logik
│   ├── ui/                       # Tab-Module
│   └── main.py                   # Einstiegspunkt
├── build/                        # NEU: Plattform-spezifische Build-Configs
│   ├── macos/
│   │   ├── FileFiend.spec        # (verschoben von Root)
│   │   ├── FileFiend.icns
│   │   └── get_ffmpeg.sh         # (verschoben von scripts/)
│   └── windows/
│       ├── FileFiend.spec        # NEU: Windows-Spec
│       ├── FileFiend.ico         # NEU: Windows-Icon
│       └── get_ffmpeg.py         # NEU: Windows-ffmpeg-Download
├── build_app.py                  # Erweitert: erkennt OS, wählt Config
├── vendor/                       # Binaries (gitignored, plattformspezifisch)
└── ...
```

## Technical Considerations

### Was sich ändert

#### 1. Build-Verzeichnis reorganisieren (`build/macos/`, `build/windows/`)

Bestehende macOS-Dateien (`FileFiend.spec`, `scripts/get_ffmpeg.sh`, Icon) in `build/macos/` verschieben. Windows-Pendants in `build/windows/` anlegen. So bleiben beide Builds sauber getrennt und die macOS-Entwicklung wird nicht gestört.

**Betroffene Dateien:**
- `FileFiend.spec` → `build/macos/FileFiend.spec` (Pfade im Spec anpassen)
- `scripts/get_ffmpeg.sh` → `build/macos/get_ffmpeg.sh`
- `assets/FileFiend.icns` → `build/macos/FileFiend.icns`

#### 2. Windows PyInstaller-Spec (`build/windows/FileFiend.spec`)

Basiert auf der macOS-Spec mit folgenden Änderungen:
- `EXE()` statt `BUNDLE()` (kein `.app`-Bundle)
- `.ico` statt `.icns` Icon
- Kein `target_arch="arm64"` (Windows: x86_64)
- Keine PyObjC hidden imports (`objc`, `Foundation`, `AppKit`, `WebKit`, `PyObjCTools` entfernen)
- `pywebview` nutzt auf Windows automatisch den richtigen Backend (EdgeChromium/MSHTML)
- Windows-ffmpeg-Binaries (`ffmpeg.exe`, `ffprobe.exe`) statt macOS-Binaries

**Beizubehalten:** Hidden imports für uvicorn, fastapi, starlette, engineio, socketio, PIL, pymediainfo, tqdm, nicegui.

#### 3. Windows-ffmpeg-Download (`build/windows/get_ffmpeg.py`)

Python-Script (kein Bash), das:
- Statisch-gelinkte Windows-x86_64-Binaries von [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) herunterlädt
- `ffmpeg.exe` und `ffprobe.exe` nach `vendor/` extrahiert
- SHA256-Hash verifiziert
- Vor dem PyInstaller-Build ausgeführt wird

(see brainstorm: docs/brainstorms/2026-02-24-windows-portierung-brainstorm.md – Entscheidung: BtbN als Quelle)

#### 4. MediaInfo-DLL bundlen

`pymediainfo` braucht auf Windows die `MediaInfo.dll`. Optionen:
- **Empfohlen:** DLL von [MediaArea](https://mediaarea.net/en/MediaInfo/Download/Windows) herunterladen und in `vendor/` legen
- Im Windows-Spec als `datas` oder `binaries` einbinden
- `pymediainfo` findet die DLL automatisch wenn sie im PATH oder neben der .exe liegt

#### 5. `build_app.py` erweitern

```python
import sys

if sys.platform == "darwin":
    spec_file = "build/macos/FileFiend.spec"
    # xattr nach Build
elif sys.platform == "win32":
    spec_file = "build/windows/FileFiend.spec"
    # kein xattr nötig
```

#### 6. Icon-Konvertierung

`.icns` → `.ico` mit ImageMagick oder Online-Tool. Einmalig, manueller Schritt.

### Was sich NICHT ändert

- **Gesamter `app/`-Ordner:** Keine Code-Änderungen nötig
- **Codec-Fallback:** `hevc_videotoolbox` → `libx265` funktioniert bereits automatisch (see brainstorm)
- **`.DS_Store`-Filter:** Harmloser No-Op auf Windows
- **Pfad-Handling:** Durchgehend `pathlib.Path`, `os.pathsep` in `runtime.py`
- **Subprocess-Aufrufe:** Alle als Listen, kein `shell=True`

### Bekannte Risiken und Edge Cases

| Risiko | Auswirkung | Mitigation |
|--------|-----------|------------|
| **Windows SmartScreen** warnt vor unsignierter .exe | Nutzer sieht "Unbekannter Herausgeber" | Anleitung in README beifügen ("Weitere Infos" → "Trotzdem ausführen") |
| **Datei gesperrt** durch Antivirus/Explorer | Löschen/Umbenennen schlägt fehl | Bestehende Error-Handling in `app/core/` fängt OSError bereits ab; ggf. Fehlermeldung verbessern |
| **pywebview Backend** unterscheidet sich auf Windows | File-Dialog sieht anders aus | pywebview nutzt EdgeChromium auf Windows – funktional identisch, nur optisch anders |
| **Lange Pfade** (>260 Zeichen) | Dateizugriff schlägt fehl | Für V1 akzeptieren; Windows 10+ unterstützt Long Paths per Registry |

## Acceptance Criteria

- [x] `build/macos/` enthält bestehende macOS-Build-Dateien (verschoben, nicht kopiert)
- [ ] `build/windows/FileFiend.spec` erzeugt lauffähige `.exe`
- [x] `build/windows/get_ffmpeg.py` lädt Windows-ffmpeg herunter und legt es in `vendor/`
- [x] `build_app.py` erkennt OS und wählt korrekte Build-Config
- [ ] `.exe` startet auf Windows 10/11 ohne Python-Installation
- [ ] Alle vier Tabs funktionieren: Duplikate, Renamer, Jahr-Organisation, Video-Compress
- [ ] Video-Compress nutzt `libx265` (Software-Encoding) auf Windows
- [ ] ffmpeg, ffprobe und MediaInfo.dll sind in der `.exe` gebundelt
- [x] macOS-Build funktioniert weiterhin unverändert nach Reorganisation
- [ ] Portable ZIP-Distribution: entpacken und starten, kein Installer nötig

## Success Metrics

- App startet auf frischer Windows 10/11 VM ohne zusätzliche Installationen
- Alle vier Kern-Features (Duplikate, Renamer, Jahr-Org, Video-Compress) durchlaufen erfolgreich
- macOS-Build ist nicht beeinträchtigt (Regressionstest)

## Dependencies & Risks

**Dependencies:**
- Windows Cloud-VM (Azure/AWS) für Build und Test (~0.10-0.50 EUR/h)
- ffmpeg-Binaries von BtbN/FFmpeg-Builds (externe Abhängigkeit)
- MediaInfo-DLL von MediaArea (externe Abhängigkeit)

**Risiken:**
- Ungetestete Plattform: Erste Builds werden vermutlich Kleinigkeiten aufdecken (DLL-Abhängigkeiten, Pfade)
- pywebview-Verhalten auf Windows kann sich von macOS unterscheiden (File-Dialoge, Fenster-Lifecycle)
- Kein Code-Signing: SmartScreen-Warnung kann Nutzer abschrecken

## Implementation Phases

### Phase 1: Repo-Reorganisation (auf macOS, kein Windows nötig)

1. ~~`build/macos/` und `build/windows/` Verzeichnisse anlegen~~ ✅
2. ~~`FileFiend.spec` → `build/macos/FileFiend.spec` verschieben, Pfade anpassen~~ ✅
3. ~~`scripts/get_ffmpeg.sh` → `build/macos/get_ffmpeg.sh` verschieben~~ ✅
4. Icon nach `build/macos/FileFiend.icns` verschieben – ⏳ Icon existiert noch nicht, Pfad vorbereitet
5. ~~`build_app.py` erweitern: OS-Erkennung, Spec-Auswahl~~ ✅
6. ~~macOS-Build testen: `python build_app.py` funktioniert weiterhin~~ ✅
7. `.ico`-Icon erstellen und in `assets/` ablegen – ⏳ manuell

### Phase 2: Windows-Build-Config erstellen (auf macOS, theoretisch)

1. ~~`build/windows/FileFiend.spec` erstellen (basierend auf macOS-Spec)~~ ✅
2. ~~`build/windows/get_ffmpeg.py` schreiben (Download von BtbN)~~ ✅
3. ~~MediaInfo-DLL-Download dokumentieren oder in Script integrieren~~ ✅

### Phase 3: Windows-VM und Test

1. Windows Cloud-VM starten (Azure/AWS)
2. Python 3.13 + Git installieren
3. Repo klonen, venv einrichten
4. `build/windows/get_ffmpeg.py` ausführen → ffmpeg in `vendor/`
5. MediaInfo-DLL in `vendor/` legen
6. `python build_app.py` auf Windows ausführen
7. `.exe` testen: alle vier Tabs durchklicken
8. ZIP erstellen und auf zweiter sauberer VM testen (ohne Python)

### Phase 4: Feinschliff

1. Fehlermeldungen für Windows-typische Probleme verbessern (falls nötig)
2. README mit Windows-Hinweisen ergänzen (SmartScreen, Entpacken)
3. Ggf. GitHub Actions für automatischen Windows-Build (optional, später)

## Sources & References

- **Origin brainstorm:** [docs/brainstorms/2026-02-24-windows-portierung-brainstorm.md](docs/brainstorms/2026-02-24-windows-portierung-brainstorm.md) — Key decisions: alles gebundelt, nur libx265, portable ZIP, Cloud-VM
- Bestehende macOS-Spec: `FileFiend.spec`
- Bestehender Build: `build_app.py`
- Runtime-Setup: `app/core/runtime.py`
- Codec-Detection: `app/core/video_compress.py:57-66`
- BtbN FFmpeg-Builds: https://github.com/BtbN/FFmpeg-Builds/releases
- MediaInfo Downloads: https://mediaarea.net/en/MediaInfo/Download/Windows
- pywebview Windows-Support: https://pywebview.flowrl.com/
