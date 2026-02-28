# Brainstorm: Windows-Portierung von FileFiend

**Datum:** 2026-02-24
**Status:** Entwurf

---

## Was wir bauen wollen

FileFiend soll als `.exe` an Windows-Nutzer weitergegeben werden können. Die App soll out-of-the-box funktionieren – ohne dass Nutzer Python, ffmpeg oder andere Tools selbst installieren müssen.

## Warum dieser Ansatz

Der bestehende Code ist zu ~95% plattformunabhängig. Die Hauptarbeit liegt beim Packaging (PyInstaller `.exe` statt `.app`) und dem Bundling von Windows-spezifischen Binaries (ffmpeg). Der Code selbst braucht nur minimale Anpassungen.

## Bestandsaufnahme: Was ist schon cross-platform?

| Komponente | Status | Anmerkung |
|---|---|---|
| Pfad-Handling | Fertig | Durchgehend `pathlib.Path` |
| Python-Dependencies | Fertig | Alle haben Windows-Wheels |
| NiceGUI + pywebview | Fertig | Funktionieren auf Windows |
| Duplikat-Finder | Fertig | Rein Python-basiert |
| Renamer | Fertig | Rein Python-basiert |
| Jahr-Organisation | Fertig | `.DS_Store`-Filter ist harmloser No-Op |
| Video-Compress Logik | Fertig | Fallback auf `libx265` existiert |
| Subprocess-Aufrufe | Fertig | Kein `shell=True`, saubere Listen |

## Was angepasst werden muss

### 1. PyInstaller-Konfiguration (Hoch)

**Problem:** `FileFiend.spec` ist macOS-spezifisch (`.app`-Bundle, `arm64`, PyObjC-Imports, `.icns`-Icon).

**Lösung:** Eigene `FileFiend-Windows.spec` erstellen:
- `EXE()` statt `BUNDLE()`
- `.ico`-Icon (konvertiert aus bestehendem `.icns`)
- Keine PyObjC hidden imports
- Windows-ffmpeg-Binaries in `vendor/` einpacken

### 2. ffmpeg/ffprobe für Windows (Hoch)

**Problem:** `scripts/get_ffmpeg.sh` lädt macOS-arm64-Binaries von evermeet.cx.

**Lösung:** Plattformübergreifendes Python-Script `scripts/get_ffmpeg.py`:
- Erkennt OS automatisch
- Lädt Windows-Binaries von BtbN/FFmpeg-Builds (GitHub)
- Legt sie in `vendor/` ab
- Wird vor dem PyInstaller-Build ausgeführt

### 3. Build-Script anpassen (Niedrig)

**Problem:** `build_app.py` nutzt `xattr -cr` (macOS-only, Zeile 72).

**Lösung:** `if sys.platform == "darwin":` Guard um den xattr-Aufruf.

### 4. MediaInfo-DLL (Mittel)

**Problem:** `pymediainfo` braucht auf Windows die `MediaInfo.dll`.

**Lösung:** DLL in `vendor/` bundlen und im PyInstaller-Spec als Data-File einbinden.

### 5. Video-Codec-Auswahl (Nichts zu tun)

`hevc_videotoolbox` wird auf Windows nicht gefunden → Fallback auf `libx265` greift automatisch. UI zeigt bereits Hardware vs. Software Auswahl – auf Windows wird Software-Encoding die einzige Option.

**Entscheidung:** Kein NVENC-Support, nur `libx265`. Hält es einfach.

### 6. UI-Platzhalter-Pfade (Kosmetisch)

`/Users/du/Bilder` und `/Users/du/Videos_compressed` sind macOS-Pfade in Placeholder-Texten. Könnten plattformabhängig gesetzt werden, ist aber optional da der Folder-Picker die echte Auswahl macht.

## Entwicklungs- und Test-Setup

- **Entwicklung:** Weiterhin auf macOS, Code ist plattformunabhängig
- **Build & Test:** Windows Cloud-VM (Azure/AWS), per RDP verbinden
- **Kosten:** ~0.10-0.50 EUR/Stunde, nur bei Bedarf
- **Workflow:** Code auf macOS schreiben → Push → auf Windows-VM pullen → bauen → testen

## Geschätzter Aufwand

| Schritt | Aufwand |
|---|---|
| `get_ffmpeg.py` (cross-platform) | ~1-2h |
| `FileFiend-Windows.spec` | ~1-2h |
| `build_app.py` anpassen | ~15min |
| MediaInfo-DLL bundlen | ~30min |
| Icon `.icns` → `.ico` konvertieren | ~15min |
| Windows-VM aufsetzen + testen | ~2-3h |
| **Gesamt** | **~5-8h** |

## Key Decisions

1. **Alles gebundelt:** ffmpeg, MediaInfo-DLL und alle Dependencies in der `.exe`
2. **Nur Software-Encoding:** Kein NVENC, nur `libx265` auf Windows
3. **Cloud-VM zum Testen:** Keine lokale Windows-VM, Azure/AWS bei Bedarf
4. **Getrennte Spec-Dateien:** `FileFiend.spec` (macOS) und `FileFiend-Windows.spec`

## Resolved Questions

1. **Installer oder portable?** → Erstmal portable ZIP-Distribution. Installer kann später hinzugefügt werden.
2. **Auto-Update?** → Erstmal nicht. Manueller Download neuer Versionen reicht. Kann später ergänzt werden.

## Open Questions

Keine offenen Fragen.
