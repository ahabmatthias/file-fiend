"""
Zentrales Design-System für Media Tools.
Einbinden mit: theme.apply()
"""

import re

from nicegui import ui

# ── Design-Tokens – Kalte Palette + Logo-Rot ─────────────────────────────────
COLORS = {
    # Surfaces
    "bg": "#0e1015",  # Seiten-Hintergrund
    "surface": "#161920",  # Header, Tab-Bar, Karten
    "surface2": "#1c2028",  # Inputs, Hover
    "border": "#262b36",  # Separator, Rahmen
    # Text
    "text": "#e4e7ec",  # Primärtext (15.3:1 auf bg)
    "muted": "#7f8694",  # Sekundärtext (5.2:1 auf bg)
    # Semantic
    "accent": "#f63138",  # Logo-Rot, Primary Buttons
    "success": "#22c55e",  # Bestätigung
    "danger": "#f87171",  # Destruktiv
    "danger_filled": "#dc2626",  # Confirm-Dialog Hintergrund
    # Derived
    "row_border": "#161920",  # = surface
    "pill_neutral_border": "#3a4050",  # abgedunkeltes Border
    "tag_compress_bg": "rgba(246,49,56,0.12)",  # accent-dim
    "tag_copy_bg": "rgba(127,134,148,0.12)",  # muted-dim
    "rename_arrow": "#555d6e",  # gedämpftes Grau
}

_CSS_TEMPLATE = """
/* ── Quasar Brand-Farben überschreiben ─────────────────────── */
:root {
    --q-primary: $accent$;
    --q-secondary: $muted$;
    --q-positive: $success$;
    --q-negative: $danger$;
    --q-info: $accent$;
}

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

/* ── Header Sub-Row (Mit Unterordnern) ────────────────────── */
.mt-header-sub {
    border-top: 1px solid $border$;
    padding: 6px 20px !important;
    min-height: auto !important;
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
/* Shared base – body prefix beats Quasar's .bg-primary specificity */
body .q-btn.mt-btn-primary,
body .q-btn.mt-btn-success,
body .q-btn.mt-btn-danger,
body .q-btn.mt-btn-ghost {
    border-radius: 6px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 0 14px !important;
    height: 32px !important;
    box-shadow: none !important;
}

/* Primary – dunkler Text auf Rot */
body .q-btn.mt-btn-primary { background: $accent$ !important; color: #fff !important; }
body .q-btn.mt-btn-primary:hover { filter: brightness(1.15); }

/* Success – dunkler Text auf Grün */
body .q-btn.mt-btn-success { background: $success$ !important; color: $bg$ !important; }
body .q-btn.mt-btn-success:hover { filter: brightness(1.1); }

/* Danger – immer Outline, nie gefüllt (Unterscheidung zu Primary-Rot) */
body .q-btn.mt-btn-danger {
    background: transparent !important;
    color: $danger$ !important;
    border: 1px solid $danger$ !important;
}
body .q-btn.mt-btn-danger:hover { background: rgba(248,113,113,0.1) !important; }

/* Ghost */
body .q-btn.mt-btn-ghost {
    background: $surface2$ !important;
    color: $text$ !important;
    border: 1px solid $border$ !important;
}
body .q-btn.mt-btn-ghost:hover { border-color: $accent$ !important; }

/* Disabled state */
body .q-btn.disabled, body .q-btn[disabled] { opacity: 0.35 !important; }

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
.mt-pill-neutral { border-color: $pill_neutral_border$ !important; color: $muted$ !important; }
.mt-pill-danger  { border-color: $danger$ !important; color: $danger$ !important; }

/* ── Progress Bar ──────────────────────────────────────────── */
.mt-progress .q-linear-progress__track { background: $surface2$ !important; }
.mt-progress .q-linear-progress__model {
    background: $accent$ !important;
    transition: none !important;
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
    border-bottom: 1px solid $row_border$ !important;
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
.mt-tag-compress { background: $tag_compress_bg$; color: $accent$; }
.mt-tag-skip     { background: $surface2$; color: $muted$; }
.mt-tag-copy     { background: $tag_copy_bg$; color: $muted$; }

/* ── Rename Preview Rows ───────────────────────────────────── */
.mt-rename-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-bottom: 1px solid $row_border$;
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 11px;
}
.mt-rename-row:hover { background: $surface2$; }
.mt-rename-old { color: $muted$; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mt-rename-arrow { color: $rename_arrow$; }
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
    border-bottom: 1px solid $row_border$;
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

/* ── Glut-Ring-Spinner ─────────────────────────────────────── */
.mt-ember-spinner {
    display: inline-block;
    width: 22px;
    height: 22px;
    vertical-align: middle;
    flex-shrink: 0;
}

.mt-ember-ring {
    display: block;
    width: 22px;
    height: 22px;
    box-sizing: border-box;
    border: 2px solid rgba(246, 49, 56, 0.15);
    border-top-color: $accent$;
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(246, 49, 56, 0.35);
    animation: mt-ember-spin 0.8s linear infinite;
    will-change: transform;
}

@keyframes mt-ember-spin {
    to { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
    .mt-ember-ring { animation: none !important; opacity: 0.6; }
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
    ui.colors(
        primary=COLORS["accent"],
        positive=COLORS["success"],
        negative=COLORS["danger"],
        accent=COLORS["accent"],
    )
    ui.add_head_html(f"<style>{CSS}</style>")


def ember_spinner() -> ui.element:
    """Glut-Ring-Spinner. Caller setzt .visible = False."""
    with ui.element("span").classes("mt-ember-spinner") as wrap:
        ui.element("span").classes("mt-ember-ring")
    return wrap


def pill(text: str, variant: str = "") -> None:
    """
    Rendert ein Status-Pill als inline HTML.
    variant: '' | 'info' | 'good' | 'success' | 'neutral' | 'danger'
    """
    cls = f"mt-pill mt-pill-{variant}" if variant else "mt-pill"
    ui.html(f'<span class="{cls}">{text}</span>')
