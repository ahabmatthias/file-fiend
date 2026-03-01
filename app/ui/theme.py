"""
Zentrales Design-System für Media Tools.
Einbinden mit: theme.apply()
"""

import re

from nicegui import ui

# ── Design-Tokens (spiegeln den Mockup) ───────────────────────────────────────
COLORS = {
    "bg": "#0f1117",
    "surface": "#161b27",
    "surface2": "#1e2535",
    "border": "#2a3147",
    "accent": "#4f8ef7",
    "accent2": "#6c63ff",
    "green": "#34d399",
    "red": "#f87171",
    "neutral": "#7dd3fc",
    "muted": "#64748b",
    "text": "#e2e8f0",
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

/* Primary */
.q-btn.mt-btn-primary { background: $accent$ !important; color: #fff !important; }
.q-btn.mt-btn-primary:hover { filter: brightness(1.15); }

/* Success */
.q-btn.mt-btn-success { background: $green$ !important; color: $bg$ !important; }
.q-btn.mt-btn-success:hover { filter: brightness(1.1); }

/* Danger */
.q-btn.mt-btn-danger { background: $red$ !important; color: #fff !important; }
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
.mt-pill-good    { border-color: $green$ !important; color: $green$ !important; }
.mt-pill-neutral { border-color: #3b82c4 !important; color: $neutral$ !important; }
.mt-pill-danger  { border-color: $red$ !important; color: $red$ !important; }

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
    border-bottom: 1px solid #1a2033 !important;
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
.mt-tag-compress { background: #1e3a5f; color: $accent$; }
.mt-tag-skip     { background: $surface2$; color: $muted$; }
.mt-tag-copy     { background: #1e2a3f; color: $neutral$; }

/* ── Rename Preview Rows ───────────────────────────────────── */
.mt-rename-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-bottom: 1px solid #1a2033;
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 11px;
}
.mt-rename-row:hover { background: $surface2$; }
.mt-rename-old { color: $muted$; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mt-rename-arrow { color: #3b4a63; }
.mt-rename-new { color: $green$; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

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
    border-bottom: 1px solid #1a2033;
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


def pill(text: str, variant: str = "") -> None:
    """
    Rendert ein Status-Pill als inline HTML.
    variant: '' | 'info' | 'good' | 'neutral' | 'danger'
    """
    cls = f"mt-pill mt-pill-{variant}" if variant else "mt-pill"
    ui.html(f'<span class="{cls}">{text}</span>')
