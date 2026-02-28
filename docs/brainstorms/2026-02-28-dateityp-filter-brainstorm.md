---
date: 2026-02-28
topic: dateityp-filter
---

# Dateityp-Filter pro Tab

## Was wird gebaut

Jeder der drei Haupt-Tabs (Duplikate, Umbenennen, Sortieren) bekommt Checkboxen,
mit denen der Nutzer steuert, welche Dateitypen der jeweilige Scan berücksichtigt.
Die Logik bleibt in den Core-Modulen – nur die aktiven Extensions werden als Parameter
übergeben statt als Modulkonstante fixiert.

## Entscheidungen pro Tab

### Duplikate-Tab
- **UI:** Drei Checkboxen – `☑ Fotos  ☑ Videos  ☐ Audio`
- **Default:** Fotos + Videos aktiv, Audio inaktiv
- **Core-Änderung:** `find_duplicates()` bekommt optionalen `extensions`-Parameter;
  ohne Parameter → altes Verhalten (alle Dateien)
- Platzierung: direkt über dem Scan-Button (wie `cb_recursive` im Renamer-Tab)

### Umbenennen-Tab
- **UI:** Zwei Checkboxen – `☑ Fotos  ☑ Videos`
- **Default:** beide aktiv
- **Core-Änderung:** `_SUPPORTED_EXTS` nicht mehr als Modulkonstante, sondern
  als Parameter in `preview_renames()` / `execute_renames()` übergeben
- Platzierung: neben der bestehenden „Mit Unterordnern"-Checkbox

### Sortieren-Tab
- **UI:** Zwei Checkboxen – `☑ Fotos  ☑ Videos` (kein Audio)
- **Default:** beide aktiv
- **Begründung:** Audio-Dateien haben keine EXIF-Jahresdaten; der Tab ist
  ursprünglich für Kamera-Files gedacht
- **Core-Änderung:** `organize_by_year()` filtert nach übergebenem Extensions-Set
  statt `ALL_MEDIA_EXTS`
- Platzierung: neben der „Nach Kamera sortieren"-Checkbox

## Implementierungsansatz

`constants.py` ist bereits gut strukturiert (`IMAGE_EXTS`, `VIDEO_EXTS`, `AUDIO_EXTS`,
`ALL_MEDIA_EXTS`). Kein neues Konzept nötig – nur die UI-State-Parameter in die
Core-Aufrufe weiterleiten.

**Pattern (gleich in allen drei Tabs):**
```python
exts = set()
if cb_fotos.value:  exts |= IMAGE_EXTS
if cb_videos.value: exts |= VIDEO_EXTS
# Duplikate-Tab zusätzlich:
if cb_audio.value:  exts |= AUDIO_EXTS

result = core_function(folder, extensions=exts or None)
```

Wenn kein Typ gewählt → Scan-Button deaktivieren oder Hinweis anzeigen.

## Offene Fragen

*Keine – alle Kernfragen sind geklärt.*

## Nächste Schritte

→ `/workflows:plan` für den Implementierungsplan
