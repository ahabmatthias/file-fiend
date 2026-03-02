# FileFiend Redesign – Briefing für Claude Code

> Dieses Dokument ist die einzige Referenz für das Redesign.
> Es ersetzt den alten Plan (`2026-03-01-feat-filefiend-warm-redesign-plan.md`).

---

## Ziel

Das kalte Dark-Mode-Design bleibt als Basis. Die bisherige blaue Akzentfarbe wird
durch das Logo-Rot (#f63138) ersetzt. Keine warmen Brauntöne. Zusätzlich:
Neuer Spinner, neue Tab-Namen, "Mit Unterordnern" wandert in den Header.

---

## 1. Farbpalette

```python
COLORS = {
    # Surfaces
    "bg":       "#0e1015",   # Seiten-Hintergrund
    "surface":  "#161920",   # Header, Tab-Bar, Karten
    "surface2": "#1c2028",   # Inputs, Hover
    "border":   "#262b36",   # Separator, Rahmen
    # Text
    "text":     "#e4e7ec",   # Primärtext (15.3:1 auf bg)
    "muted":    "#7f8694",   # Sekundärtext (5.2:1 auf bg)
    # Semantic
    "accent":   "#f63138",   # Logo-Rot, Primary Buttons
    "success":  "#22c55e",   # Bestätigung, kräftiges Grün
    "danger":   "#f87171",   # Destruktiv (Outline-Buttons)
    "danger_filled": "#dc2626",  # Confirm-Dialog Hintergrund
}
```

Das `$token$` + `str.replace()`-System aus dem alten Plan bleibt.
Token-Keys: `success`/`danger` statt `green`/`red`.

---

## 2. Button-Regeln

| Typ | Stil | Farbe | Text | Verwendung |
|---|---|---|---|---|
| Primary | Gefüllt | `accent` (#f63138) | Weiß | Scannen, Vorschau, Ordner wählen |
| Success | Gefüllt | `success` (#22c55e) | Dunkel (#0e1015) | Ausführen, Komprimieren |
| Danger | **Outline** | Border `danger` (#f87171) | `danger` (#f87171) | Ausgewählte löschen |
| Ghost | Outline | Border `border` (#262b36) | `muted` (#7f8694) | Abbrechen, Schließen |

**Wichtig:** Danger-Buttons sind IMMER Outline, nicht gefüllt.
Das unterscheidet sie visuell von den roten Primary-Buttons.

---

## 3. Farbmapping alt → neu

### theme.py (CSS-Tokens)

| Alter Hex-Wert | Token | Neuer Wert |
|---|---|---|
| `#0f1117` | `bg` | `#0e1015` |
| `#161b27` | `surface` | `#161920` |
| `#1e2535` | `surface2` | `#1c2028` |
| `#2a3147` | `border` | `#262b36` |
| `#4f8ef7` | `accent` | `#f63138` |
| `#6c63ff` | `accent2` | entfällt (durch `accent` ersetzen) |
| `#34d399` | `success` | `#22c55e` |
| `#f87171` | `danger` | `#f87171` (bleibt) |
| `#7dd3fc` | `neutral` | entfällt (durch `muted` + `border` ersetzen) |
| `#64748b` | `muted` | `#7f8694` |
| `#e2e8f0` | `text` | `#e4e7ec` |

### Inline-Farben in Tab-Dateien

| Datei | Zeile(n) | Alt | Neu |
|---|---|---|---|
| `app/main.py:28` | Header bg/border | Tailwind `bg-[#161b27]` etc. | `.mt-header` CSS-Klasse |
| `app/main.py:30,77` | `text-[#4f8ef7]` | → `text-[#f63138]` |
| `app/ui/duplicates_tab.py:141,149` | Thumbnail `.style()` | Hex-Werte ersetzen |
| `app/ui/duplicates_tab.py:152` | `text-[#64748b]` | → `text-[#7f8694]` |
| `app/ui/duplicates_tab.py:214-215` | Success-Button `.style()` | `.style()` entfernen |
| `app/ui/renamer_tab.py:160` | `color:#f87171` | → `#f87171` (bleibt, prüfen) |
| `app/ui/renamer_tab.py:178` | `text-[#e2e8f0]` | → `text-[#e4e7ec]` |
| `app/ui/renamer_tab.py:196-197` | Success-Button `.style()` | `.style()` entfernen |
| `app/ui/video_compress_tab.py:77` | `text-[#4f8ef7]` | → `text-[#f63138]` |
| `app/ui/video_compress_tab.py:271-272` | Success-Button `.style()` | `.style()` entfernen |
| `app/ui/year_org_tab.py:143-167` | ~15 inline `style=` | Hex-Werte direkt ersetzen |
| `app/ui/year_org_tab.py:191` | Conflict-Header | Hex-Werte ersetzen |
| `app/ui/year_org_tab.py:275` | Success-Button `.style()` | `.style()` entfernen |

### Sonderfälle (Hex-Werte ohne direktes Token)

| Alter Hex-Wert | Kontext | Neuer Wert |
|---|---|---|
| `#3b82c4` | pill-neutral border | `#3a4050` (abgedunkeltes border) |
| `#1e3a5f` | tag-compress bg | `rgba(246,49,56,0.12)` (accent-dim) |
| `#1e2a3f` | tag-copy bg | `rgba(127,134,148,0.12)` (muted-dim) |
| `#3b4a63` | rename-arrow | `#555d6e` |
| `#1a2033` | diverse Hintergründe | `#161920` (surface) |

---

## 4. Spinner: Glut-Ring

Ersetzt den Standard-`ui.spinner()` in allen 4 Tabs.

### CSS (in `_CSS_TEMPLATE`)

```css
.mt-ember-spinner {
    width: 22px;
    height: 22px;
    position: relative;
    display: inline-flex;
    align-items: center;
    flex-shrink: 0;
}

.mt-ember-ring {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top-color: $accent$;
    border-right-color: rgba(246, 49, 56, 0.3);
    position: absolute;
    animation: mt-ember-spin 0.8s linear infinite;
    filter: drop-shadow(0 0 4px rgba(246, 49, 56, 0.5));
}

.mt-ember-glow {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    position: absolute;
    animation: mt-ember-pulse 1.6s ease-in-out infinite;
}

@keyframes mt-ember-spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes mt-ember-pulse {
    0%, 100% { box-shadow: 0 0 6px rgba(246, 49, 56, 0.2); }
    50% { box-shadow: 0 0 12px rgba(246, 49, 56, 0.5); }
}

@media (prefers-reduced-motion: reduce) {
    .mt-ember-ring, .mt-ember-glow { animation: none !important; }
    .mt-ember-ring { opacity: 0.6; }
}
```

### Python Helper (in `theme.py`)

```python
def ember_spinner() -> ui.html:
    """Glut-Ring-Spinner. Caller setzt .visible = False."""
    return ui.html('''
    <span class="mt-ember-spinner" role="status" aria-label="Laden">
      <span class="mt-ember-glow"></span>
      <span class="mt-ember-ring"></span>
    </span>''')
```

### Ersetzung in 4 Dateien

```python
# Vorher:
spinner = ui.spinner(size="sm").classes("text-[#4f8ef7]")
spinner.visible = False

# Nachher:
spinner = theme.ember_spinner()
spinner.visible = False
```

Stellen:
- `app/ui/duplicates_tab.py:54`
- `app/ui/renamer_tab.py:31`
- `app/ui/video_compress_tab.py:84`
- `app/ui/year_org_tab.py:37`

---

## 5. Layout-Änderungen

### "Mit Unterordnern" in den Header

Aktuell ist die Checkbox "Mit Unterordnern" in jedem Tab einzeln.
Stattdessen: **eine** Checkbox im Header-Bereich, zwischen Pfad-Input und Tab-Bar.
Gilt dann global für alle Tabs.

Technisch: Die Variable, die den Wert hält, muss für alle Tabs zugänglich sein
(vermutlich schon der Fall, wenn sie in `main.py` lebt).

### Tab-Umbenennung

| Alt | Neu |
|---|---|
| Duplikate | **Duplikate** (bleibt) |
| Umbenennen | **Umbenennen** (bleibt) |
| Sortieren | **Ordnen** |
| Video | **Komprimieren** |

### Checkbox-Umbenennung

| Alt | Neu | Tab |
|---|---|---|
| Nach Kamera sortieren | **Zusätzlich nach Kamera ordnen** | Ordnen |

---

## 6. Ladebildschirm (nach Redesign-Abschluss)

**Erst umsetzen, wenn alle obigen Punkte erledigt und visuell geprüft sind.**

Ein kurzer Splash-Screen beim App-Start, der das App-Icon (Sleek Fiend) zeigt.
Dauer: 1–2 Sekunden oder bis die App geladen ist.
Hintergrund: `bg` (#0e1015). Logo zentriert. Optional: Glut-Ring-Spinner darunter.
Kein Text nötig, das Icon reicht.

---

## Implementierungsreihenfolge

Jeder Schritt ist ein eigener Commit. Nach jedem Schritt: App starten, visuell prüfen.

1. ~~**Token-System** einrichten (`$token$` + `str.replace()`) mit den ALTEN Farbwerten
   → Zero-Visual-Change-Commit. App muss identisch aussehen.~~ ✅

2. ~~**Neue Farbwerte** in `COLORS` eintragen
   → App sieht jetzt anders aus. Visuell prüfen: Surfaces, Text, Akzentfarbe.~~ ✅

3. ~~**Inline-Farben** in allen Tab-Dateien ersetzen (Tabelle oben)
   → Kein Blau/Lila mehr irgendwo.~~ ✅

4. ~~**Button-Stil** anpassen: Danger-Buttons auf Outline umstellen
   → Success-Button `.style()`-Overrides entfernen und testen.~~ ✅

5. ~~**Spinner** ersetzen: `ember_spinner()` Helper + CSS + 4 Aufrufstellen
   → Glut-Ring via `ui.element()` (nicht `ui.html()`), Progress-Bar `transition: none`.~~ ✅

6. ~~**Header-Umbau**: "Mit Unterordnern" hochziehen, aus den Tabs entfernen
   → Globale Checkbox in Header-Sub-Row, reaktives Auto-Fill für Zielordner.~~ ✅

7. ~~**Tab-Namen** ändern: Sortieren → Ordnen, Video → Komprimieren,
   Checkbox "Nach Kamera sortieren" → "Zusätzlich nach Kamera ordnen"~~ ✅

8. ~~**Visueller Gesamtcheck** aller Tabs und Zustände
   → "Ordner wählen" auf accent-primary, flat-Prop-Bug gefixt, RTL-Pfadanzeige.~~ ✅

9. **Ladebildschirm** (optional, separates Feature)

---

## Referenz-Mockup

Das HTML-Mockup `filefiend-final-mockup.html` zeigt das Zieldesign für alle 4 Tabs.
Es ist die visuelle Referenz – im Zweifel gilt das Mockup.
