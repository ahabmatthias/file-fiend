---
status: complete
priority: p3
issue_id: "018"
tags: [code-review, security, xss]
dependencies: []
---

# XSS in Webview: EXIF/Dateinamen in ui.html() ohne Escaping

## Problem Statement

EXIF-Werte (Kameraname) und Dateinamen werden direkt in `ui.html()` f-Strings
interpoliert ohne HTML-Escaping. NiceGUI rendert das in einem pywebview-Fenster –
ein präparierter Dateiname wie `<script>...</script>` würde als JS ausgeführt.

## Findings

- `app/ui/year_org_tab.py:125`: `└─ {camera}` – EXIF-Wert direkt in HTML
- `app/ui/year_org_tab.py:148`: `{inv["path"].name}` – Dateiname direkt in HTML
- `app/ui/renamer_tab.py:109-114`: `{old_short}`, `{new_short}` – Pfade direkt in HTML
- `app/ui/duplicates_tab.py:103-104`: Hash in `ui.html()` – unkritisch (interne Berechnung)

**Kontext:** NiceGUI/pywebview – kein sandboxed Browser. JS-Ausführung potenziell
mit Zugriff auf Python-Backend über pywebview js_api.

**Praktische Exploitabilität:** Erfordert manipuliertes Bild mit EXIF-Payload im Ordner.
Für ein lokales Desktop-Tool ist das Risiko begrenzt, aber vermeidbar.

## Proposed Solutions

### Option 1: html.escape() für alle interpolierten Werte

```python
from html import escape

# year_org_tab.py
f'└─ {escape(camera)}'
f'{escape(inv["path"].name)}'

# renamer_tab.py
f'<span class="mt-rename-old">{escape(old_short)}</span>'
```

**Pros:** Stdlib, einzeiling, kein Extra-Dependency
**Cons:** 5-6 Stellen im Code

**Effort:** 20 Minuten
**Risk:** Very Low

---

### Option 2: Stellen auf ui.label() umstellen wo möglich

Einfache Textanzeigen auf `ui.label()` umstellen – NiceGUI escaped dort automatisch.
Nur für Stellen ohne komplexes HTML-Styling.

**Effort:** 30 Minuten
**Risk:** Low (Layout-Check nötig)

## Recommended Action

Option 1 – `html.escape()` an allen betroffenen Stellen.

## Technical Details

**Affected files:**
- `app/ui/year_org_tab.py:125,148`
- `app/ui/renamer_tab.py:109-114`

## Acceptance Criteria

- [ ] Alle user-controlled Strings in `ui.html()` durch `html.escape()` geschützt
- [ ] Dateiname `<script>alert(1)</script>` wird als Text angezeigt, nicht ausgeführt

## Work Log

### 2026-02-28 – Discovery via Code Review

**By:** Claude Code (security-sentinel agent)
