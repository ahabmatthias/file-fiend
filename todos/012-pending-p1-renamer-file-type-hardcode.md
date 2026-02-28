---
status: pending
priority: p1
issue_id: "012"
tags: [code-review, architecture, data-integrity]
dependencies: []
---

# `file_type` hardcoded gegen IMAGE_EXTS nach extensions-Filter

## Problem Statement

In `renamer.py` wird `file_type` nach dem extensions-Filter immer noch gegen das
globale `IMAGE_EXTS` geprüft, nicht gegen die vom Nutzer gewählte Teilmenge `exts`.
Wenn jemand die Funktion mit einem Custom-Extensions-Set aufruft, das z.B. nur `.heic`
enthält, aber `.heic` nicht in `IMAGE_EXTS` ist (es ist drin, aber das Prinzip gilt),
könnten zukünftige Erweiterungen zu stiller Fehlklassifikation führen.

## Findings

- `app/core/renamer.py:102`: `exts = extensions if extensions is not None else _SUPPORTED_EXTS`
- `app/core/renamer.py:112`: `file_type = "image" if file_path.suffix.lower() in IMAGE_EXTS else "video"`
- `IMAGE_EXTS` ist die globale Konstante, nicht `exts`
- Konsequenz: Audio-Dateien (falls via `extensions` übergeben) werden als `"video"` klassifiziert → `MediaInfo.parse()` statt EXIF → falsche/keine Datumsextraktion

## Proposed Solutions

### Option 1: file_type aus exts und IMAGE_EXTS-Schnittmenge ableiten

```python
image_exts_in_scope = IMAGE_EXTS & exts
file_type = "image" if file_path.suffix.lower() in image_exts_in_scope else "video"
```

**Pros:** Korrekt, minimal, verwendet bereits aufgelöstes `exts`
**Cons:** Keiner

**Effort:** 5 Minuten
**Risk:** Very Low

---

### Option 2: Explizit gegen IMAGE_EXTS aus constants prüfen (Verhalten dokumentieren)

Docstring ergänzen: "Audio-Dateien werden als 'video' behandelt (MediaInfo-Fallback)."

**Pros:** Ehrlich über aktuelles Verhalten
**Cons:** Löst das Problem nicht

**Effort:** 5 Minuten
**Risk:** Low (akzeptiert den Bug)

## Recommended Action

Option 1: Eine Zeile anpassen in `renamer.py:112`.

## Technical Details

**Affected files:**
- `app/core/renamer.py:112`

## Resources

- Architecture-Agent + Agent-Native-Agent Finding (Review 2026-02-28)

## Acceptance Criteria

- [ ] `file_type` wird korrekt aus der aktiven `exts`-Menge abgeleitet
- [ ] Audio-Dateien via `extensions=AUDIO_EXTS` übergeben werden korrekt als nicht-image klassifiziert

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (architecture-strategist agent)
