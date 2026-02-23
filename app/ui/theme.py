"""
Zentrales Design-System für Media Tools.
Einbinden mit: theme.apply()
"""

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

CSS = """
/* ── Reset & Base ──────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

body, .q-page, .nicegui-content {
    background: #0f1117 !important;
    color: #e2e8f0 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif !important;
    font-size: 13px !important;
}

/* ── Scrollbar ─────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a3147; border-radius: 3px; }

/* ── Header / Folder Picker ────────────────────────────────── */
.mt-header {
    background: #161b27;
    border-bottom: 1px solid #2a3147;
    padding: 10px 20px;
}

/* ── Tabs ──────────────────────────────────────────────────── */
.q-tabs { background: #161b27 !important; border-bottom: 1px solid #2a3147; }
.q-tab  { color: #64748b !important; font-size: 12px !important; font-weight: 500 !important; }
.q-tab--active { color: #4f8ef7 !important; }
.q-tab__indicator { background: #4f8ef7 !important; }
.q-tab-panels, .q-tab-panel { background: #0f1117 !important; }

/* ── Inputs ────────────────────────────────────────────────── */
.q-field__control { background: #1e2535 !important; }
.q-field__native, .q-field__input { color: #e2e8f0 !important; }
.q-field--outlined .q-field__control::before {
    border-color: #2a3147 !important;
}
.q-field--outlined.q-field--focused .q-field__control::before {
    border-color: #4f8ef7 !important;
}
.q-field__label { color: #64748b !important; }

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
.q-btn.mt-btn-primary { background: #4f8ef7 !important; color: #fff !important; }
.q-btn.mt-btn-primary:hover { filter: brightness(1.15); }

/* Success */
.q-btn.mt-btn-success { background: #34d399 !important; color: #0f1117 !important; }
.q-btn.mt-btn-success:hover { filter: brightness(1.1); }

/* Danger */
.q-btn.mt-btn-danger { background: #f87171 !important; color: #fff !important; }
.q-btn.mt-btn-danger:hover { filter: brightness(1.1); }

/* Ghost */
.q-btn.mt-btn-ghost {
    background: #1e2535 !important;
    color: #e2e8f0 !important;
    border: 1px solid #2a3147 !important;
}
.q-btn.mt-btn-ghost:hover { border-color: #4f8ef7 !important; }

/* Disabled state */
.q-btn.disabled, .q-btn[disabled] { opacity: 0.35 !important; }

/* ── Cards ─────────────────────────────────────────────────── */
.mt-card {
    background: #161b27 !important;
    border: 1px solid #2a3147 !important;
    border-radius: 8px !important;
}
.mt-card-header {
    background: #1e2535 !important;
    border-bottom: 1px solid #2a3147 !important;
    padding: 8px 14px !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #64748b !important;
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
    background: #1e2535;
    border: 1px solid #2a3147;
    color: #64748b;
    white-space: nowrap;
}
.mt-pill-info    { border-color: #4f8ef7 !important; color: #4f8ef7 !important; }
.mt-pill-good    { border-color: #34d399 !important; color: #34d399 !important; }
.mt-pill-neutral { border-color: #3b82c4 !important; color: #7dd3fc !important; }
.mt-pill-danger  { border-color: #f87171 !important; color: #f87171 !important; }

/* ── Progress Bar ──────────────────────────────────────────── */
.mt-progress .q-linear-progress__track { background: #1e2535 !important; }
.mt-progress .q-linear-progress__model {
    background: linear-gradient(90deg, #4f8ef7, #6c63ff) !important;
}

/* ── Tables ────────────────────────────────────────────────── */
.mt-table .q-table { background: #161b27 !important; }
.mt-table .q-table thead tr th {
    background: #1e2535 !important;
    color: #64748b !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    border-bottom: 1px solid #2a3147 !important;
}
.mt-table .q-table tbody tr td {
    color: #e2e8f0 !important;
    font-family: 'Menlo', 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    border-bottom: 1px solid #1a2033 !important;
}
.mt-table .q-table tbody tr:hover td { background: #1e2535 !important; }
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
.mt-tag-compress { background: #1e3a5f; color: #4f8ef7; }
.mt-tag-skip     { background: #1e2535; color: #64748b; }
.mt-tag-copy     { background: #1e2a3f; color: #7dd3fc; }

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
.mt-rename-row:hover { background: #1e2535; }
.mt-rename-old { color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mt-rename-arrow { color: #3b4a63; }
.mt-rename-new { color: #34d399; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Duplikat-Gruppen ──────────────────────────────────────── */
.mt-dupe-group {
    background: #161b27;
    border: 1px solid #2a3147;
    border-radius: 8px;
    overflow: hidden;
}
.mt-dupe-header {
    background: #1e2535;
    border-bottom: 1px solid #2a3147;
    padding: 7px 14px;
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 11px;
    color: #64748b;
}
.mt-dupe-row {
    padding: 8px 14px;
    border-bottom: 1px solid #1a2033;
    transition: background 0.1s;
}
.mt-dupe-row:hover { background: #1e2535; }
.mt-dupe-row:last-child { border-bottom: none; }
.mt-dupe-name {
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #e2e8f0;
}
.mt-dupe-path {
    font-family: 'Menlo', 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #64748b;
}

/* ── Checkboxes ────────────────────────────────────────────── */
.q-checkbox__inner--truthy .q-checkbox__bg,
.q-checkbox__inner--indet  .q-checkbox__bg { background: #4f8ef7 !important; border-color: #4f8ef7 !important; }
.q-checkbox__bg { border-color: #2a3147 !important; }
.q-checkbox__label { color: #64748b !important; font-size: 12px !important; }

/* ── Select / Number inputs ────────────────────────────────── */
.q-select .q-field__control { background: #1e2535 !important; }
.q-menu { background: #1e2535 !important; border: 1px solid #2a3147 !important; }
.q-item  { color: #e2e8f0 !important; }
.q-item:hover { background: #2a3147 !important; }

/* ── Helper text ───────────────────────────────────────────── */
.mt-hint { font-size: 11px; color: #64748b; }

/* ── Separator ─────────────────────────────────────────────── */
.q-separator { background: #2a3147 !important; }

/* ── Notifications ─────────────────────────────────────────── */
.q-notification { border-radius: 8px !important; font-size: 13px !important; }
"""


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
