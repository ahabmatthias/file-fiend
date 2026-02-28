---
date: 2026-02-28
topics:
  - ux-fixes-fortschritt
  - video-zielordner
  - checkbox-spacing
  - unterordner-option
  - info-icon-placement
---

# UX-Fixes: Fortschrittsanzeige + Video-Zielordner

Drei kleine Beobachtungen aus dem täglichen Gebrauch. Kein großes Refactoring –
alle Fixes sind chirurgisch und unabhängig voneinander umsetzbar.

---

## Beobachtung 1 – Fortschrittswert als Dezimalzahl statt Prozent

### Problem

`ui.linear_progress` zeigt den gesetzten Rohwert an (`done / total` ergibt z. B. `0.9173`).
Das ist schwer lesbar – der Nutzer erwartet eine Ganzzahl wie `92 %`.

### Ursache

In allen Tabs wird der Progress-Wert direkt übergeben:

```python
# duplicates_tab.py, year_org_tab.py
progress_bar.set_value(done / total)  # → 0.9173
```

NiceGUI zeigt diesen Float-Wert unformatiert an, wenn `show_value=True` (Default).

### Lösung

**Option A – `show_value=False`, Prozent in `status_label` einblenden (empfohlen)**

```python
progress_bar = ui.linear_progress(value=0, show_value=False).classes("mt-progress")

async def _update_progress(value: float):
    progress_bar.set_value(value)
    status_label.set_text(f"Scanne … {int(value * 100)} %")
```

Vorteil: Status-Label und Fortschrittsbalken kommunizieren zusammen, kein zweites Widget nötig.

**Option B – Wert vor dem Setzen runden**

Zeigt dann `0.92` statt `0.9173` – immer noch kein `%`, daher schlechter als A.

**Entscheidung:** Option A.

### Betroffene Dateien

- `app/ui/duplicates_tab.py` – `_update_progress()`
- `app/ui/year_org_tab.py` – `_update_scan_progress()`, `_update_exec_progress()`

---

## Beobachtung 2 – Fortschrittsbalken erscheint an unterschiedlichen Positionen

### Problem

Der `progress_bar` steht in jedem Tab an einer anderen Stelle im Layout, was beim
Wechsel zwischen Tabs visuell inkonsistent wirkt.

### Ursache

- **Duplikate-Tab:** `spinner+status` → `progress_bar` → `results_col`
- **Jahr-Org-Tab:** Checkboxen → `spinner+status` → `pills_row` → `progress_bar`

Der Balken erscheint im Jahr-Org-Tab nach den Pills, im Duplikate-Tab davor.

### Lösung

Einheitliche Reihenfolge in allen Tabs:

```
[Filter / Optionen]
[Scan-Button]
[Spinner + Status-Label]
[Fortschrittsbalken]     ← immer direkt unter Status-Label
[Ergebnisse / Preview]
```

### Betroffene Dateien

- `app/ui/year_org_tab.py` – `progress_bar` vor `pills_row` verschieben

---

## Beobachtung 3 – Video-Tab: Zielordner automatisch vorausfüllen

### Problem

Der Zielordner im Video-Tab ist leer. Nutzer müssen ihn manuell setzen, obwohl der
naheliegende Default `<Quellordner>_compressed` wäre.

### Lösung

Beim Laden des Tabs einmalig prüfen ob `shared["folder"]` gesetzt ist, und den
Zielordner-Vorschlag automatisch eintragen:

```python
def _update_target_suggestion():
    src = shared.get("folder", "").strip()
    if src and not target_input.value:
        target_input.set_value(src + "_compressed")
```

**Verhalten:**
- Quellordner `/Users/ich/Videos` → Zielordner `/Users/ich/Videos_compressed`
- Nur wenn das Zielfeld noch leer ist – bereits gesetzte Werte werden nicht überschrieben
- Nutzer kann den Pfad danach frei editieren oder per Picker ersetzen

### Betroffene Dateien

- `app/ui/video_compress_tab.py`

---

## Priorisierung

| # | Fix | Aufwand | Priorität |
|---|-----|---------|-----------|
| 1 | Prozent-Anzeige | S (< 30 min) | Hoch |
| 2 | Balken-Position | S (< 30 min) | Mittel |
| 3 | Video-Zielordner | S (< 30 min) | Hoch |

Alle drei können in einem einzigen Commit erledigt werden.

## Nächste Schritte

→ `/workflows:plan` für den Implementierungsplan

---

# Checkbox-Spacing, „Mit Unterordnern" und Info-Icon

Beobachtungen zur Struktur und Logik der Optionsbereiche in den drei Haupt-Tabs.
Zwei davon sind direkte Fixes, einer erfordert eine Designentscheidung.

---

## Beobachtung 4 – Checkbox-Spacing im Duplikate-Tab uneinheitlich

### Problem

Die drei Checkboxen „Fotos", „Videos", „Audio" liegen in einer `ui.row()` mit `gap-4`,
jede Checkbox hat zusätzlich `.classes("mt-1")`. Das doppelte Margin führt zu leicht
ungleichmäßigen Abständen zwischen den Optionen.

### Ist-Zustand (`duplicates_tab.py:64–67`)

```python
with ui.row().classes("items-center gap-4 flex-wrap mt-1"):
    cb_fotos = ui.checkbox("Fotos", value=True).classes("mt-1")
    cb_videos = ui.checkbox("Videos", value=True).classes("mt-1")
    cb_audio = ui.checkbox("Audio", value=False).classes("mt-1")
```

Das `mt-1` auf den einzelnen Checkboxen ist redundant, da `gap-4` auf dem Row-Container
bereits den horizontalen Abstand regelt.

### Lösung

`mt-1` von den einzelnen Checkboxen entfernen; nur den Row-Container für das Spacing
verantwortlich machen. Gleiches Muster konsequent in allen Tabs anwenden.

### Betroffene Dateien

- `app/ui/duplicates_tab.py`
- Zur Konsistenz prüfen: `app/ui/renamer_tab.py`, `app/ui/year_org_tab.py`

---

## Beobachtung 5 – „Mit Unterordnern" fehlt in Duplikate- und Sortieren-Tab (TODO)

### Problem

Der Umbenennen-Tab hat bereits eine `cb_recursive`-Checkbox („Mit Unterordnern"), die steuert,
ob der Scan rekursiv in Unterordner geht. Den anderen beiden Tabs fehlt diese Option:

- **Duplikate-Tab:** Scannt aktuell immer rekursiv – keine Nutzersteuerung.
- **Sortieren-Tab:** Gleiches Problem.

### Lösung

`cb_recursive` in Duplikate- und Sortieren-Tab ergänzen, analog zum Umbenennen-Tab.
Die Core-Funktionen müssten einen `recursive`-Parameter erhalten oder nutzen ihn bereits.

### Status

**→ TODO** – Umsetzung in einem eigenen Commit, unabhängig vom Spacing-Fix.

### Betroffene Dateien

- `app/ui/duplicates_tab.py` – Checkbox hinzufügen, `recursive` an Core weitergeben
- `app/ui/year_org_tab.py` – Checkbox hinzufügen
- `app/core/duplicates.py` – `recursive`-Parameter prüfen/ergänzen
- `app/core/year_org.py` – `recursive`-Parameter prüfen/ergänzen

---

## Beobachtung 6 – Logische Trennung im Umbenennen-Tab (Designentscheidung)

### Problem

Im Umbenennen-Tab liegen zwei konzeptionell verschiedene Optionen in derselben Zeile:

```python
# renamer_tab.py:21–24
with ui.row().classes("items-center gap-4 flex-wrap"):
    cb_recursive = ui.checkbox("Mit Unterordnern", value=True)   # ← Scope
    cb_fotos     = ui.checkbox("Fotos", value=True)              # ← Typ-Filter
    cb_videos    = ui.checkbox("Videos", value=True)             # ← Typ-Filter
```

„Mit Unterordnern" ist eine **Scope-Option** (wie weit gesucht wird).
„Fotos" / „Videos" sind **Typ-Filter** (was gesucht wird).
Beide gleichgestellt zu zeigen ist irreführend.

Dasselbe Problem entsteht im Sortieren-Tab, sobald „Mit Unterordnern" dort ergänzt wird
(Beobachtung 5) – dann gibt es drei Gruppen, die alle unterscheidbar sein sollten:
Scope · Typ-Filter · Organisations-Option (Nach Kamera).

### Entscheidung: `ui.separator()` zwischen Gruppen

Dünne horizontale Linie zwischen jeder konzeptionellen Gruppe.
Kein Label-Overhead, sofort lesbar, minimal.

**Duplikate-Tab** (nach Ergänzung von Beobachtung 5):
```
☑ Mit Unterordnern
──────────────────
☑ Fotos   ☑ Videos   ☐ Audio
```

**Umbenennen-Tab:**
```
☑ Mit Unterordnern
──────────────────
☑ Fotos   ☑ Videos
```

**Sortieren-Tab** (nach Ergänzung von Beobachtung 5):
```
☑ Mit Unterordnern
──────────────────
☑ Fotos   ☑ Videos
──────────────────
☑ Nach Kamera sortieren  ⓘ
```

### Status

**→ Entschieden** – `ui.separator()` zwischen Gruppen, einheitlich in allen drei Tabs.

---

## Beobachtung 7 – Info-Icon im Sortieren-Tab falsch platziert

### Problem

Das Info-Icon mit Kamera-EXIF-Tooltip steht als loses Element nach `camera_checkbox`,
aber nicht in einer gemeinsamen `ui.row()` mit ihr:

```python
# year_org_tab.py:20–24
camera_checkbox = ui.checkbox("Nach Kamera sortieren").classes("mt-1")
ui.icon("info_outline").classes("text-[#4f8ef7] text-sm cursor-default").tooltip(...)
```

Ohne `items-center`-Container schweben Checkbox und Icon nicht auf derselben Grundlinie.
Logisch gehört das Icon direkt zur „Nach Kamera"-Option – das sollte auch visuell stimmen.

### Lösung

Checkbox und Icon in eine gemeinsame `ui.row()` wrappen:

```python
with ui.row().classes("items-center gap-2 mt-1"):
    camera_checkbox = ui.checkbox("Nach Kamera sortieren")
    ui.icon("info_outline").classes("text-[#4f8ef7] text-sm cursor-default").tooltip(
        "Kamera-Erkennung liest EXIF Make/Model aus den Dateien. "
        "Dateien ohne EXIF landen im Ordner 'Sonstige'."
    )
```

Direkt umsetzbar – kein Design-Vorlauf nötig.

### Betroffene Dateien

- `app/ui/year_org_tab.py` – Zeilen 20–24

---

## Gesamtübersicht

| # | Beobachtung | Typ | Status |
|---|-------------|-----|--------|
| 4 | Checkbox-Spacing Duplikate | Fix | Direkt umsetzbar |
| 5 | „Mit Unterordnern" fehlt in Duplikate + Sortieren | Feature | TODO |
| 6 | Logische Trennung via `ui.separator()` | Design | Entschieden ✓ |
| 7 | Info-Icon Platzierung Sortieren-Tab | Fix | Direkt umsetzbar |
