---
status: pending
priority: p1
issue_id: "011"
tags: [code-review, security]
dependencies: []
---

# EXIF Camera Model unbereinigt als Pfad-Komponente

## Problem Statement

Der EXIF-Wert `Make`/`Model` wird direkt als Ordnername verwendet, ohne irgendeine
Bereinigung. Ein manipuliertes Bild mit `Model = ../../Library/Preferences` kann dazu
führen, dass Dateien außerhalb des vom Nutzer gewählten Ordners verschoben werden.

## Findings

- `app/core/year_org.py:378`: `target_dir = folder / str(year) / camera`
- `camera` kommt aus EXIF `model` bzw. `make` – direkt aus der Datei-Metadaten
- `pathlib /` normiert NICHT gegen `..`-Traversal in Zwischensegmenten
- `mkdir(parents=True, exist_ok=True)` + `shutil.move` operieren auf dem unresolvten Pfad
- Beispiel: EXIF `Model = ../../Desktop/evil` → Dateien landen im Desktop-Ordner

## Proposed Solutions

### Option 1: Regex-Sanitisierung des Kameranamens

**Approach:** Alle Zeichen entfernen/ersetzen, die nicht alphanumerisch, Leerzeichen, Bindestrich oder Klammer sind.

```python
import re
camera_safe = re.sub(r'[^\w\s\-()\.]', '_', camera).strip('.')
```

**Pros:** Einfach, einzeilig, kein Behavior-Change für normale Kameranamen
**Cons:** Könnte exotische Kameranamen (Sonderzeichen) abschneiden

**Effort:** 15 Minuten
**Risk:** Low

---

### Option 2: `Path.resolve()` und Prüfung ob Zielpfad im Zielordner liegt

**Approach:** Nach Konstruktion des Pfads `target_dir.resolve().is_relative_to(folder.resolve())` prüfen und bei Fehler überspringen.

**Pros:** Exakte Prüfung, keine Zeichenersetzung
**Cons:** Erfordert zweimal resolve(), komplexer

**Effort:** 30 Minuten
**Risk:** Low

## Recommended Action

Option 1 anwenden in `_detect_camera()` – den Rückgabewert bereinigen bevor er als Ordnername verwendet wird.

## Technical Details

**Affected files:**
- `app/core/year_org.py:198-223` – `_detect_camera()` Funktion
- `app/core/year_org.py:367-378` – `_move_with_camera_groups()` Nutzung als Pfad

## Resources

- Security-Agent Finding (Review 2026-02-28)
- Commit: a4efbb4 (berührt `year_org.py`)

## Acceptance Criteria

- [ ] `_detect_camera()` gibt einen Ordner-sicheren String zurück (keine `/`, `..`, `\`)
- [ ] Test: Kameraname `../../evil` wird zu `____evil` o.ä. sanitisiert
- [ ] Test: Normaler Kameraname `iPhone 15 Pro` bleibt unverändert

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (security-sentinel agent)

**Actions:**
- EXIF-Wert direkt als Pfadkomponente identifiziert
- `pathlib /`-Verhalten mit `..`-Segmenten verifiziert
