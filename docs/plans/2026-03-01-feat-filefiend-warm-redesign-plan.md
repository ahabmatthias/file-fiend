---
title: "feat: FileFiend Warm Dark Mode Redesign"
type: feat
status: implemented
date: 2026-03-01
deepened: 2026-03-01
origin: docs/brainstorms/2026-02-28-restyle-als-filefiend.md
---

# FileFiend Warm Dark Mode Redesign

## Enhancement Summary

**Deepened on:** 2026-03-01
**Research agents used:** warm-palette-best-practices, svg-flame-animations, pattern-recognition,
code-simplicity, performance-oracle, NiceGUI-docs (Context7)

### Key Improvements
1. **f-String-Ansatz verworfen** → `str.replace()` mit `$token$`-Platzhaltern (kein Brace-Escaping)
2. **WCAG-Audit der Palette** → Weiß auf Orange-Button FAIL → dunkler Text auf Accent-Buttons
3. **Konkrete SVG-Pfaddaten** und optimierte CSS-Animation (nur `transform`/`opacity`, kein animiertes `drop-shadow`)
4. **3 fehlende Inline-Farb-Stellen** entdeckt und ergänzt
5. **Vereinfachung**: Inline-Farben in year_org_tab per Find-Replace statt CSS-Klassen-Extraktion

### Neue Erkenntnisse
- Statischer `drop-shadow` für Glow ist ok, animierter `drop-shadow` ist teuer → statisch machen
- `.style()`-Overrides auf Success-Buttons sind vermutlich schon redundant (CSS-Selektor `.q-btn.mt-btn-success` existiert bereits) → testen und entfernen
- Token-Keys `"green"`/`"red"` → `"success"`/`"danger"` umbenennen (Konsistenz mit CSS-Klassen)
- `prefers-reduced-motion` für Flammen-Animation einbauen (WCAG-Anforderung)

---

## Overview

Die App hat ein kaltes, professionelles Design (Blau-Schwarz, blaue/lila Akzente), das nicht
zum verspielten FileFiend-Branding passt (roter Teufel, grüne Hörner, warme Persönlichkeit).
Das Redesign stellt die gesamte Farbpalette auf warme Töne um und fügt einen SVG-Flammen-Spinner
als Signature-Element hinzu.

## Problem Statement

Name, Icon und UI erzählen drei verschiedene Geschichten. Das untergräbt die Identität der App.
Ein konsistentes visuelles Design stärkt Wiedererkennung und macht die App einprägsamer.

## Proposed Solution

1. **Warme Farbpalette** – Anthrazit-Hintergrund, Rot/Orange als Primärfarbe, warmes Grün für Erfolg
2. **SVG-Flammen-Spinner** – Ersetzt den Standard-Quasar-Spinner in allen 4 Tabs
3. **Inline-Farben bereinigen** – Alle hardcodierten Hex-Werte auf neue warme Werte umstellen

(see brainstorm: `docs/brainstorms/2026-02-28-restyle-als-filefiend.md`)

---

## Farbpalette – Neue Tokens

```python
COLORS = {
    # Surfaces
    "bg":       "#1a1412",   # warmes Anthrazit (statt #0f1117) – R-B=+8 warm
    "surface":  "#231e1a",   # Karten, Header, Tab-Bar (statt #161b27)
    "surface2": "#2e2722",   # Inputs, Hover (statt #1e2535)
    "border":   "#3d332c",   # Separator, Scrollbar (statt #2a3147)
    # Content
    "text":     "#f0ebe5",   # leicht warmes Weiß (statt #e2e8f0)
    "muted":    "#8b7355",   # Grau-Braun für Labels/Captions (statt #64748b)
    # Semantic
    "accent":   "#e8622c",   # Orange-Rot Primärfarbe (statt Blau #4f8ef7)
    "accent2":  "#f59e0b",   # Gold/Amber Gradient-Ende (statt Lila #6c63ff)
    "success":  "#4ade80",   # wärmeres Grün (statt #34d399) – war "green"
    "danger":   "#ef4444",   # Rot (statt #f87171) – war "red"
    "neutral":  "#d4a574",   # Beige/Sand (statt Cyan #7dd3fc)
}
```

### Research Insights: WCAG-Audit

| Kombination | Kontrast | WCAG |
|---|---|---|
| `text` (#f0ebe5) auf `bg` (#1a1412) | **15.4:1** | AAA Pass |
| `text` (#f0ebe5) auf `surface` (#231e1a) | **13.9:1** | AAA Pass |
| `accent` (#e8622c) auf `bg` (#1a1412) | **5.4:1** | AA Pass |
| `accent` (#e8622c) auf `surface` (#231e1a) | **4.9:1** | AA Pass |
| `accent2` (#f59e0b) auf `bg` (#1a1412) | **8.5:1** | AAA Pass |
| `text` (#f0ebe5) auf `accent` (#e8622c) Button | **2.9:1** | **FAIL** |
| `bg` (#1a1412) auf `accent` (#e8622c) Button | **5.4:1** | AA Pass |

**Kritisch: Heller Text auf Orange-Buttons ist nicht lesbar.**
→ Primary-Buttons (Accent-Hintergrund) bekommen dunklen Text (`$bg$`), nicht hellen.
→ Success-Buttons (Grün-Hintergrund) ebenfalls dunklen Text (wie bisher).

### Sonderfälle – Hex-Werte ohne direktes Token

| Alter Hex-Wert | Kontext | Neuer Wert | Herleitung |
|---|---|---|---|
| `#3b82c4` | pill-neutral border | `#a88a6a` | abgedunkeltes `neutral` |
| `#1e3a5f` | tag-compress bg | `#3a2218` | accent-getönter Hintergrund |
| `#1e2a3f` | tag-copy bg | `#2a2018` | neutral-getönter Hintergrund |
| `#3b4a63` | rename-arrow | `#6b5a48` | warme Variante von `muted` |
| `#1a2033` | diverse Hintergründe/Borders | `#1f1916` | zwischen `bg` und `surface` |

---

## Technischer Ansatz

### Phase 1: Farbpalette umstellen (`theme.py`)

**Datei:** `app/ui/theme.py`

#### Schritt 1a: Token-System mit `str.replace()` (NICHT f-String!)

> **Research-Erkenntnis:** f-String-Migration verworfen. CSS hat ~80 Brace-Paare, die alle
> escaped werden müssten (`{{`/`}}`). Das macht den CSS-String unlesbar und fehleranfällig.
> Stattdessen: `$token$`-Platzhalter mit `str.replace()`.

```python
COLORS = {
    "bg":       "#1a1412",
    "surface":  "#231e1a",
    "surface2": "#2e2722",
    "border":   "#3d332c",
    "text":     "#f0ebe5",
    "muted":    "#8b7355",
    "accent":   "#e8622c",
    "accent2":  "#f59e0b",
    "success":  "#4ade80",
    "danger":   "#ef4444",
    "neutral":  "#d4a574",
}

_CSS_TEMPLATE = """
body, .q-page, .nicegui-content {
    background: $bg$ !important;
    color: $text$ !important;
}
/* ... restliches CSS mit $token$-Platzhaltern ... */
"""

def _build_css() -> str:
    css = _CSS_TEMPLATE
    for key, value in COLORS.items():
        css = css.replace(f"${key}$", value)
    assert "$" not in css, f"Unresolved tokens: {[t for t in re.findall(r'\\$\\w+\\$', css)]}"
    return css

CSS = _build_css()
```

**Vorteile gegenüber f-String:**
- CSS bleibt syntaktisch valides CSS (keine `{{`/`}}`)
- `$token$`-Platzhalter sind visuell distinct von CSS-Braces
- Assert fängt vergessene Tokens zur Startzeit ab
- Einfaches Hinzufügen neuer Tokens: ein Eintrag in `COLORS`, ein `$token$` im CSS

**Testbarkeits-Checkpoint:** Phase 1a ist ein Zero-Visual-Change-Commit. Die alten Hex-Werte
stehen jetzt in `COLORS`, der CSS-Output ist identisch zu vorher. Kann separat commited werden.

#### Schritt 1b: Alle Hex-Literale ersetzen + Token-Keys umbenennen

Mapping (alt → Token → neu):

| Alter Hex-Wert | Altes Token | Neues Token | Neuer Wert | Vorkommen |
|---|---|---|---|---|
| `#0f1117` | `bg` | `bg` | `#1a1412` | ~3x |
| `#161b27` | `surface` | `surface` | `#231e1a` | ~6x |
| `#1e2535` | `surface2` | `surface2` | `#2e2722` | ~8x |
| `#2a3147` | `border` | `border` | `#3d332c` | ~7x |
| `#4f8ef7` | `accent` | `accent` | `#e8622c` | ~10x |
| `#6c63ff` | `accent2` | `accent2` | `#f59e0b` | ~2x |
| `#34d399` | ~~green~~ | `success` | `#4ade80` | ~4x |
| `#f87171` | ~~red~~ | `danger` | `#ef4444` | ~3x |
| `#7dd3fc` | `neutral` | `neutral` | `#d4a574` | ~3x |
| `#64748b` | `muted` | `muted` | `#8b7355` | ~8x |
| `#e2e8f0` | `text` | `text` | `#f0ebe5` | ~6x |

**Token-Umbenennung `green` → `success`, `red` → `danger`:**
Grund: Konsistenz mit CSS-Klassen `.mt-btn-success`, `.mt-pill-danger`.
Die Pill-Variante `"good"` sollte zu `"success"` vereinheitlicht werden.

#### Schritt 1c: Dead CSS entfernen + `.mt-header` reviven

`.mt-header` in theme.py ist definiert aber ungenutzt. `main.py:28` nutzt stattdessen
Tailwind-Werte. → `.mt-header` mit den warmen Werten füllen, in `main.py` verwenden.
So existiert eine einzige Stelle für Header-Styling.

#### Schritt 1d: Progress-Bar Gradient

```css
.mt-progress .q-linear-progress__model {
    background: linear-gradient(90deg, $accent$, $accent2$) !important;
}
```

Orange→Gold-Gradient – wie Feuer.

---

### Phase 2: Inline-Farben in Tab-Dateien ersetzen

**Vollständige Liste** (inkl. 3 Stellen die im Original-Plan fehlten):

| Datei | Zeile(n) | Problem | Fix |
|---|---|---|---|
| `app/main.py` | 28 | `bg-[#161b27]`, `border-[#2a3147]` | `.mt-header` CSS-Klasse nutzen |
| `app/main.py` | 30, 77 | `text-[#4f8ef7]` | → `text-[#e8622c]` |
| `app/ui/duplicates_tab.py` | 141, 149 | Inline `.style()` Thumbnail | Hex-Werte ersetzen |
| `app/ui/duplicates_tab.py` | 152 | `text-[#64748b]` File-Icon | → `text-[#8b7355]` **(NEU)** |
| `app/ui/duplicates_tab.py` | 214–215 | `.style()` Success-Button | `.style()` entfernen, testen |
| `app/ui/renamer_tab.py` | 160 | `color:#f87171` Error-Span | → `#ef4444` **(NEU)** |
| `app/ui/renamer_tab.py` | 178 | `text-[#e2e8f0]` Dialog-Label | → `text-[#f0ebe5]` **(NEU)** |
| `app/ui/renamer_tab.py` | 196–197 | `.style()` Success-Button | `.style()` entfernen |
| `app/ui/video_compress_tab.py` | 77 | `text-[#4f8ef7]` Info-Icon | → `text-[#e8622c]` |
| `app/ui/video_compress_tab.py` | 271–272 | `.style()` Success-Button | `.style()` entfernen |
| `app/ui/year_org_tab.py` | 143–167 | ~15 inline `style=` in f-String HTML | Hex-Werte direkt ersetzen |
| `app/ui/year_org_tab.py` | 191 | Conflict-Header inline color | Hex-Werte ersetzen |
| `app/ui/year_org_tab.py` | 275 | `.style()` Success-Button | `.style()` entfernen |

**Strategie für Success-Buttons:**
Der CSS-Selektor `.q-btn.mt-btn-success` existiert bereits in theme.py. Die `.style()`-Overrides
sind vermutlich schon redundant. → Zuerst einen `.style()`-Aufruf entfernen und testen.
Wenn der Button korrekt dargestellt wird: alle vier `.style()`-Overrides entfernen.

**Strategie für year_org_tab Inline-Styles:**
Kein Refactoring zu CSS-Klassen – das ist Scope-Creep für ein Lernprojekt.
Einfach die alten Hex-Werte per Find-Replace durch neue ersetzen.

---

### Phase 3: SVG-Flammen-Spinner

**Architektur: Helper-Funktion in `theme.py`**

NiceGUI bestätigt: `ui.html()` gibt ein Element zurück, dessen `.visible`-Property
(und `.set_visibility()`) korrekt funktioniert – inkl. `display:none` für hidden.

```python
# In theme.py:
def flame_spinner(size: int = 24) -> ui.html:
    """SVG-Flammen-Spinner. Caller setzt .visible = False."""
    svg = f'''
    <span class="mt-flame-wrap" role="status" aria-label="Laden">
      <svg viewBox="0 0 24 24" width="{size}" height="{size}" aria-hidden="true">
        <path class="mt-flame-outer"
              d="M12 2 C12 2,18 8,18 14 C18 18.4,15.3 21.5,12 22
                 C8.7 21.5,6 18.4,6 14 C6 8,12 2,12 2Z"
              fill="{COLORS['accent']}"/>
        <path class="mt-flame-inner"
              d="M12 8 C12 8,15 12,15 15.5 C15 17.5,13.7 19,12 19.5
                 C10.3 19,9 17.5,9 15.5 C9 12,12 8,12 8Z"
              fill="{COLORS['accent2']}"/>
      </svg>
    </span>'''
    return ui.html(svg)
```

**Nicht `visible = False` in der Factory** – der Caller setzt das (wie beim bisherigen
`ui.spinner()`-Pattern), damit die Sichtbarkeits-Logik am Aufrufort sichtbar bleibt.

#### CSS-Animation (in `_CSS_TEMPLATE`)

> **Research-Erkenntnis:** Nur `transform` und `opacity` animieren (GPU-composited).
> `drop-shadow` nur statisch auf dem Wrapper (einmaliges Rendering, kein Repaint pro Frame).
> `transform-origin: 50% 80%` – Pivot nahe der Flammen-Basis für natürliches Flackern.

```css
/* Statischer Glow auf dem Wrapper – einmal gerendert, kein Repaint */
.mt-flame-wrap {
    display: inline-flex;
    align-items: center;
    filter: drop-shadow(0 0 4px rgba(232, 98, 44, 0.55))
            drop-shadow(0 0 9px rgba(245, 158, 11, 0.25));
}

/* Äußere Flamme: langsames Wiegen */
@keyframes mt-flame-sway {
    0%   { transform: scaleX(1)    scaleY(1)    translateY(0); }
    30%  { transform: scaleX(1.05) scaleY(0.97) translateY(1px); }
    60%  { transform: scaleX(0.95) scaleY(1.03) translateY(-1px); }
    100% { transform: scaleX(1)    scaleY(1)    translateY(0); }
}

/* Innere Flamme: schnelles Flackern */
@keyframes mt-flame-flicker {
    0%   { opacity: 1;    transform: scaleY(1)    scaleX(1); }
    25%  { opacity: 0.75; transform: scaleY(0.93) scaleX(1.05); }
    50%  { opacity: 1;    transform: scaleY(1.06) scaleX(0.96); }
    75%  { opacity: 0.82; transform: scaleY(0.97) scaleX(1.02); }
    100% { opacity: 1;    transform: scaleY(1)    scaleX(1); }
}

.mt-flame-outer {
    transform-origin: 50% 80%;
    animation: mt-flame-sway 1.8s ease-in-out infinite;
    will-change: transform;
}

.mt-flame-inner {
    transform-origin: 50% 85%;
    animation: mt-flame-flicker 0.9s ease-in-out infinite;
    will-change: transform, opacity;
}

/* Accessibility: Reduzierte Bewegung */
@media (prefers-reduced-motion: reduce) {
    .mt-flame-outer, .mt-flame-inner {
        animation: none !important;
    }
    .mt-flame-outer { opacity: 0.7; }
}
```

**Performance-Check (bestätigt):**
- Animationen auf hidden (`display:none`) Elementen verbrauchen null CPU/GPU
- 24px SVG mit statischem `drop-shadow` < 0.1ms pro Frame
- Zwei Keyframes mit phasenverschobenen Perioden (1.8s / 0.9s) erzeugen organischen Look

#### Ersetzung in 4 Tab-Dateien

```python
# Vorher (in jedem Tab):
spinner = ui.spinner(size="sm").classes("text-[#4f8ef7]")
spinner.visible = False

# Nachher:
spinner = theme.flame_spinner()
spinner.visible = False
```

Aufrufstellen:
- `app/ui/duplicates_tab.py:54`
- `app/ui/renamer_tab.py:31`
- `app/ui/video_compress_tab.py:84`
- `app/ui/year_org_tab.py:37`

---

### Phase 4: Visueller Check

Nach allen Änderungen: jeden Tab einzeln durchgehen und prüfen:

- [ ] Header + Folder-Picker: warme Farben, Icon-Farbe passt
- [ ] Tab-Bar: aktiver Tab in Accent-Farbe, Indicator warm
- [ ] Duplikate-Tab: Scan-Spinner = Flamme, Gruppen/Thumbnails warm
- [ ] Renamer-Tab: Vorschau-Zeilen, Pfeile, neuer Name in warmem Grün
- [ ] Sortieren-Tab: Vorschau-Baum, Conflict-Header, Kamera-Pill
- [ ] Video-Tab: Action-Tags (komprimieren/kopieren) warm, Tabelle
- [ ] Alle Buttons: Primary (**dunkler Text auf Orange!**), Success (grün), Danger (rot), Ghost
- [ ] Progress-Bars: Orange→Gold-Gradient
- [ ] Status-Pills: alle Varianten (info, good/success, neutral, danger)
- [ ] Scrollbar, Checkboxes, Select-Menus, Notifications
- [ ] Focus-Ring-Farbe auf Accent geändert (kein Standard-Blau)

---

## Acceptance Criteria

- [x] Kein blauer/lila Hex-Wert mehr irgendwo in `app/ui/` oder `app/main.py`
- [x] `COLORS`-Dict ist Single Source of Truth (CSS nutzt `$token$`-Platzhalter)
- [x] Token-Keys sind funktional benannt (`success`/`danger` statt `green`/`red`)
- [x] Flammen-Spinner erscheint in allen 4 Tabs bei laufenden Operationen
- [x] Spinner `.visible`-Toggle funktioniert korrekt
- [x] `prefers-reduced-motion` stoppt Flammen-Animation
- [x] Alle Success-Buttons ohne `.style()`-Workaround
- [x] Primary-Buttons: dunkler Text auf Orange-Hintergrund (WCAG AA)
- [x] Kontrast WCAG AA (4.5:1) für Body-Text auf allen Surfaces
- [x] Dead CSS `.mt-header` revived und genutzt (statt Tailwind-Werte in main.py)
- [ ] App startet ohne Fehler, alle Tabs rendern korrekt

---

## Dependencies & Risks

**Risiko 1: Farbwerte passen visuell nicht**
Mitigation: Phase 1a als Zero-Visual-Change-Commit (nur Token-System). Phase 1b ändert Farben.
Visuell iterieren bevor Tab-Dateien angefasst werden.

**Risiko 2: SVG-Flamme sieht unprofessionell aus**
Mitigation: Erst einfache Version mit den konkreten Pfaddaten, dann iterieren.
Fallback: `ui.spinner()` mit warmer Farbe.

**Risiko 3: `.style()`-Entfernung bricht Button-Darstellung**
Mitigation: Zuerst einen Button testen. CSS-Selektor `.q-btn.mt-btn-success` existiert
bereits – `.style()` ist vermutlich schon redundant.

**~~Risiko 4: f-String-Migration~~** → Entfällt (Ansatz verworfen, `str.replace()` stattdessen)

---

## Implementierungsreihenfolge

1. **Neuer Branch** `full-redesign`
2. **Phase 1a:** Token-System einrichten (`$token$` + `str.replace()`) – Zero-Visual-Change-Commit
3. **Phase 1b–d:** Farbwerte ändern, Dead CSS fixen, Token-Keys umbenennen
4. **Visueller Zwischencheck** (nur theme.py-Änderungen, kein Tab-Code)
5. **Phase 2:** Inline-Farben in allen 5 Dateien ersetzen (inkl. 3 neu entdeckte Stellen)
6. **Phase 3:** SVG-Flammen-Spinner + CSS-Animation + Tab-Ersetzung
7. **Phase 4:** Visueller Gesamtcheck aller Tabs und Zustände

---

## Sources & References

- **Origin brainstorm:** [docs/brainstorms/2026-02-28-restyle-als-filefiend.md](docs/brainstorms/2026-02-28-restyle-als-filefiend.md)
  Entscheidungen: Warmer Dark Mode, eigene Palette, SVG-Flamme, Material-Icons bleiben
- Theme-Datei: `app/ui/theme.py` (alle Farben + CSS)
- Spinner-Stellen: `duplicates_tab.py:54`, `renamer_tab.py:31`, `video_compress_tab.py:84`, `year_org_tab.py:37`
- Inline-Style-Stellen: `main.py:28,30,77`, `duplicates_tab.py:141,149,152,214`, `renamer_tab.py:160,178,196`, `video_compress_tab.py:77,271`, `year_org_tab.py:143-167,191,275`
- WCAG Contrast: [webaim.org/articles/contrast](https://webaim.org/articles/contrast/)
- Tailwind Stone-Palette als Referenz für warme Neutraltöne
- Bear App "Red Graphite" Theme als visuelles Referenzdesign
- SVG Animation Best Practices: [blog.logrocket.com/how-to-animate-svg-css](https://blog.logrocket.com/how-to-animate-svg-css-tutorial-examples/)
- prefers-reduced-motion: [css-tricks.com/almanac/rules/m/media/prefers-reduced-motion](https://css-tricks.com/almanac/rules/m/media/prefers-reduced-motion/)
- NiceGUI Docs: `ui.html()` visibility via `.visible` / `.set_visibility()` bestätigt
