"""
Zentrales Design-System für Media Tools.
Einbinden mit: theme.apply()
"""

import re

from nicegui import ui

# ── Design-Tokens – Warme Palette ─────────────────────────────────────────────
COLORS = {
    # Surfaces
    "bg": "#1a1412",  # warmes Anthrazit
    "surface": "#231e1a",  # Karten, Header, Tab-Bar
    "surface2": "#2e2722",  # Inputs, Hover
    "border": "#3d332c",  # Separator, Scrollbar
    # Content
    "text": "#f0ebe5",  # leicht warmes Weiß
    "muted": "#8b7355",  # Grau-Braun für Labels/Captions
    # Semantic
    "accent": "#e8622c",  # Orange-Rot Primärfarbe
    "accent2": "#f59e0b",  # Gold/Amber Gradient-Ende
    "success": "#4ade80",  # wärmeres Grün
    "danger": "#ef4444",  # Rot
    "neutral": "#d4a574",  # Beige/Sand
}

_CSS_TEMPLATE = """
/* ── Reset & Base ──────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

body, .q-page, .nicegui-content {
    background: $bg$ !important;
    color: $text$ !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif !important;
    font-size: 13px !important;
}

/* ── Scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: $border$; border-radius: 3px; }

/* ── Header / Folder Picker ────────────────────────────────── */
.mt-header {
    background: $surface$;
    border-bottom: 1px solid $border$;
    padding: 10px 20px;
}

/* ── Tabs ──────────────────────────────────────────────────── */
.q-tabs { background: $surface$ !important; border-bottom: 1px solid $border$; }
.q-tab  { color: $muted$ !important; font-size: 12px !important; font-weight: 500 !important; }
.q-tab--active { color: $accent$ !important; }
.q-tab__indicator { background: $accent$ !important; }
.q-tab-panels, .q-tab-panel { background: $bg$ !important; }

/* ── Inputs ────────────────────────────────────────────────── */
.q-field__control { background: $surface2$ !important; }
.q-field__native, .q-field__input { color: $text$ !important; }
.q-field--outlined .q-field__control::before {
    border-color: $border$ !important;
}
.q-field--outlined.q-field--focused .q-field__control::before {
    border-color: $accent$ !important;
}
.q-field__label { color: $muted$ !important; }

/* ── Buttons ───────────────────────────────────────────────── */
/* Shared base – overrides Quasar inline styles */
.q-btn.mt-btn-primary,
.q-btn.mt-btn-success,
.q-btn.mt-btn-danger,
.q-btn.mt-btn-ghost {
    border-radius: 6px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 0 14px !important;
    height: 32px !important;
    box-shadow: none !important;
}

/* Primary – dunkler Text auf Orange (WCAG AA: 5.4:1) */
.q-btn.mt-btn-primary { background: $accent$ !important; color: $bg$ !important; }
.q-btn.mt-btn-primary:hover { filter: brightness(1.15); }

/* Success – dunkler Text auf Grün */
.q-btn.mt-btn-success { background: $success$ !important; color: $bg$ !important; }
.q-btn.mt-btn-success:hover { filter: brightness(1.1); }

/* Danger */
.q-btn.mt-btn-danger { background: $danger$ !important; color: #fff !important; }
.q-btn.mt-btn-danger:hover { filter: brightness(1.1); }

/* Ghost */
.q-btn.mt-btn-ghost {
    background: $surface2$ !important;
    color: $text$ !important;
    border: 1px solid $border$ !important;
}
.q-btn.mt-btn-ghost:hover { border-color: $accent$ !important; }

/* Disabled state */
.q-btn.disabled, .q-btn[disabled] { opacity: 0.35 !important; }

/* ── Cards ─────────────────────────────────────────────────── */
.mt-card {
    background: $surface$ !important;
    border: 1px solid $border$ !important;
    border-radius: 8px !important;
}
.mt-card-header {
    background: $surface2$ !important;
    border-bottom: 1px solid $border$ !important;
    padding: 8px 14px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    color: $muted$ !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* ── Status Pills ──────────────────────────────────────────── */
.mt-pill {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    background: $surface2$;
    border: 1px solid $border$;
    color: $muted$;
    white-space: nowrap;
}
.mt-pill-info    { border-color: $accent$ !important; color: $accent$ !important; }
.mt-pill-success { border-color: $success$ !important; color: $success$ !important; }
.mt-pill-good    { border-color: $success$ !important; color: $success$ !important; }
.mt-pill-neutral { border-color: #a88a6a !important; color: $neutral$ !important; }
.mt-pill-danger  { border-color: $danger$ !important; color: $danger$ !important; }

/* ── Progress Bar ──────────────────────────────────────────── */
.mt-progress .q-linear-progress__track { background: $surface2$ !important; }
.mt-progress .q-linear-progress__model {
    background: linear-gradient(90deg, $accent$, $accent2$) !important;
}

/* ── Tables ────────────────────────────────────────────────── */
.mt-table .q-table { background: $surface$ !important; }
.mt-table .q-table thead tr th {
    background: $surface2$ !important;
    color: $muted$ !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    border-bottom: 1px solid $border$ !important;
}
.mt-table .q-table tbody tr td {
    color: $text$ !important;
    font-family: 'Menlo', 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    border-bottom: 1px solid #1f1916 !important;
}
.mt-table .q-table tbody tr:hover td { background: $surface2$ !important; }
.mt-table .q-table tbody tr:last-child td { border-bottom: none !important; }

/* ── Action Tags (Tabellen-Badges) ─────────────────────────── */
.mt-tag {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.mt-tag-compress { background: #3a2218; color: $accent$; }
.mt-tag-skip     { background: $surface2$; color: $muted$; }
.mt-tag-copy     { background: #2a2018; color: $neutral$; }

/* ── Rename Preview Rows ───────────────────────────────────── */
.mt-rename-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-bottom: 1px solid #1f1916;
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 11px;
}
.mt-rename-row:hover { background: $surface2$; }
.mt-rename-old { color: $muted$; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mt-rename-arrow { color: #6b5a48; }
.mt-rename-new { color: $success$; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Duplikat-Gruppen ──────────────────────────────────────── */
.mt-dupe-group {
    background: $surface$;
    border: 1px solid $border$;
    border-radius: 8px;
    overflow: hidden;
}
.mt-dupe-header {
    background: $surface2$;
    border-bottom: 1px solid $border$;
    padding: 7px 14px;
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 11px;
    color: $muted$;
}
.mt-dupe-row {
    padding: 8px 14px;
    border-bottom: 1px solid #1f1916;
    transition: background 0.1s;
}
.mt-dupe-row:hover { background: $surface2$; }
.mt-dupe-row:last-child { border-bottom: none; }
.mt-dupe-name {
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 12px;
    color: $text$;
}
.mt-dupe-path {
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 10px;
    color: $muted$;
}

/* ── Checkboxes ────────────────────────────────────────────── */
.q-checkbox__inner--truthy .q-checkbox__bg,
.q-checkbox__inner--indet  .q-checkbox__bg { background: $accent$ !important; border-color: $accent$ !important; }
.q-checkbox__bg { border-color: $border$ !important; }
.q-checkbox__label { color: $muted$ !important; font-size: 12px !important; }

/* ── Select / Number inputs ────────────────────────────────── */
.q-select .q-field__control { background: $surface2$ !important; }
.q-menu { background: $surface2$ !important; border: 1px solid $border$ !important; }
.q-item  { color: $text$ !important; }
.q-item:hover { background: $border$ !important; }

/* ── Helper text ───────────────────────────────────────────── */
.mt-hint { font-size: 11px; color: $muted$; }

/* ── Separator ─────────────────────────────────────────────── */
.q-separator { background: $border$ !important; }

/* ── Notifications ─────────────────────────────────────────── */
.q-notification { border-radius: 8px !important; font-size: 13px !important; }

/* ── Focus Ring ────────────────────────────────────────────── */
*:focus-visible { outline-color: $accent$ !important; }

/* ── Flammen-Spinner ──────────────────────────────────────── */
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
"""


def _build_css() -> str:
    css = _CSS_TEMPLATE
    for key, value in COLORS.items():
        css = css.replace(f"${key}$", value)
    unresolved = re.findall(r"\$\w+\$", css)
    assert not unresolved, f"Unresolved tokens: {unresolved}"
    return css


CSS = _build_css()


def apply() -> None:
    """CSS in die Seite injizieren. Einmalig in main() aufrufen."""
    ui.add_head_html(f"<style>{CSS}</style>")


def flame_spinner(size: int = 24) -> ui.html:
    """SVG-Flammen-Spinner. Caller setzt .visible = False."""
    svg = f"""
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
    </span>"""
    return ui.html(svg)


def pill(text: str, variant: str = "") -> None:
    """
    Rendert ein Status-Pill als inline HTML.
    variant: '' | 'info' | 'good' | 'success' | 'neutral' | 'danger'
    """
    cls = f"mt-pill mt-pill-{variant}" if variant else "mt-pill"
    ui.html(f'<span class="{cls}">{text}</span>')
