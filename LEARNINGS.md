# Learnings & Entscheidungen

Chronologisches Lerntagebuch – für mich zum Nachschlagen, nicht als Projektdoku.

---

## 2026-02 – Quality-Gate-Architektur

### Pre-commit Hooks
- Hooks sind **repo-lokal** – jeder neue Klon braucht `pre-commit install` einmalig
- Die Config-Datei (`.pre-commit-config.yaml`) ist im Repo, der eigentliche Hook liegt in `.git/hooks/` und wird nicht versioniert
- Hooks greifen bei **allen lokalen Commits**, egal von wem oder auf welchem Branch – nicht bei GitHub Web-UI oder CI

### mypy vs. ruff
- **ruff** ist schnell und findet Stil-Probleme, Unused Imports, unsichere Patterns
- **mypy** prüft Typen und findet andere Klassen von Bugs: falsche Rückgabetypen, Monkey-Patching auf Module, `Any`-Werte die als konkreter Typ behandelt werden
- Beide zusammen sinnvoll – sie überschneiden sich kaum

### Python-Versionen
- `int | None` Union-Syntax ist **Python 3.10+**, nicht 3.9
- CLAUDE.md hatte „3.9+" stehen, obwohl der Code bereits 3.10-Syntax nutzte und das venv auf 3.13 läuft → Versionsdoku war irreführend
- Lektion: Mindestversion immer am tatsächlichen Code messen, nicht an einer Wunschvorstellung

### Coverage
- 52% auf `app/core/` nach erster Test-Session
- Lücken: EXIF-Parsing (`_read_exif_year`, `_detect_camera`) braucht echte Testbilder mit Metadaten oder Mocks – aufwändiger als reine Logik-Tests
- `app/core/renamer.py` zeigt 0% weil Tests direkt `unified_media_renamer` importieren, nicht den Wrapper

### Legacy-Script-Integration (sys.path, install_packages)
- Legacy-Scripts im Projekt-Root (`unified_media_renamer.py`, `year_folder_script.py`) wurden ursprünglich mit `sys.path`-Hacks importiert
- `install_packages()` wurde beim Modulimport ausgeführt → blockiert UI beim Start
- Beides entfernbar wenn: (a) App immer aus Projekt-Root gestartet wird, (b) Packages in `requirements.txt` stehen

---

## 2026-02 – Projekt-Aufräumen: Legacy-Scripts entfernen

### Ausgangslage
Drei Root-Scripts (`unified_media_renamer.py`, `video_compress.py`, `year_folder_script.py`)
lagen im Projekt-Root, weil die App-Module ursprünglich nur Wrapper um diese Scripts waren.
Über die Zeit war die gesamte Logik aber in `app/core/` gewachsen – die Root-Scripts waren
nurmehr Ballast.

### Wrapper-Falle
`app/core/renamer.py` und `app/core/year_org.py` importierten aktiv aus den Legacy-Scripts.
Das sah harmlos aus (`from unified_media_renamer import collect_files`), bedeutete aber:
Löschen der Root-Scripts hätte die App sofort gebrochen. Der erste Schritt beim Aufräumen
muss immer sein: **Wo wird das tatsächlich noch importiert?**

```bash
grep -r "unified_media_renamer\|year_folder_script" app/
```

### Vorgehen
1. Core-Module neu schreiben (Logik direkt einbetten, Legacy-Import entfernen)
2. Test-Imports anpassen (Tests importierten z.T. noch direkt aus Root-Scripts)
3. Root-Scripts löschen
4. Tests laufen lassen – erst dann committen

### Was sonst noch weg kam
- `README.md` – veraltet, beschrieb noch die CLI-Scripts; wird am Projektabschluss neu geschrieben
- `requirements-dev.txt` – in `pyproject.toml` unter `[project.optional-dependencies]` konsolidiert;
  Dev-Tools (ruff, mypy, pytest) sind damit zentral an einer Stelle

### Muster: Branch für Aufräum-Arbeiten
Strukturelle Änderungen (viele Löschungen, Imports umschreiben) immer auf einem eigenen Branch –
falls Tests rot werden oder etwas unerwartet kaputt geht, kann man einfach zurück zu main.

---

## 2026-02 – Startup-Performance: Lazy Imports

### Problem
App startete in ~4 Sekunden. Ursache: Alle drei Tab-Module wurden beim Start vollständig
importiert, obwohl der Nutzer zunächst nur das Fenster sehen will.

Die Importkette beim Start:
- `renamer_tab.py` → `app.core.renamer` → `unified_media_renamer` → **`pymediainfo`** (lädt
  native C-Bibliothek `libmediainfo`) + `PIL`
- `year_org_tab.py` → `app.core.year_org` → `PIL`, **`pillow_heif.register_heif_opener()`**
  (Seiteneffekt auf Modul-Ebene!), `pymediainfo` (nochmal), `year_folder_script`

`pymediainfo` war der größte Einzelbrocken – es lädt beim Import eine native shared library.

### Fix: Lazy Imports in den Handler-Funktionen
Core-Module erst beim ersten Klick auf „Vorschau" importieren, nicht beim App-Start:

```python
# vorher (Modul-Ebene):
from app.core.renamer import collect_files, process_files

# nachher (innerhalb von do_preview()):
from app.core.renamer import collect_files, process_files  # noqa: PLC0415
```

Python cached Module – nach dem ersten Aufruf ist der Import instant.

### Ergebnis
Startzeit von ~4 Sekunden auf ~1 Sekunde reduziert. Die verbleibende Sekunde ist NiceGUI
selbst (uvicorn + pywebview), kaum optimierbar ohne Framework-Wechsel.

### Muster
Überall wo schwere C-Extensions (pymediainfo, pillow-heif, PIL) nur für bestimmte
Funktionen gebraucht werden: Import in die Funktion verschieben statt auf Modul-Ebene.
`# noqa: PLC0415` unterdrückt die ruff-Warnung für Import-not-at-top-of-file.

---

## 2026-02 – Phase 1b: UX-Verbesserungen & Shared State

### Shared State zwischen Tabs: Dict-Referenz statt Binding

Für einen gemeinsamen Ordner-Picker über den Tabs war der einfachste Ansatz ein
schlichtes Dict, das an die `build()`-Funktionen übergeben wird:

```python
shared = {"folder": ""}
```

Tabs lesen `shared["folder"]` beim Button-Klick aus – kein Reaktivitäts-Framework nötig,
weil der Wert immer zum Zeitpunkt des Klicks gelesen wird, nicht beim Build.

**NiceGUI-Parameter-Name:** `ui.input()` verwendet `on_change=`, nicht `on_value_change=`
(das existiert nicht und wirft einen `TypeError` erst zur Laufzeit).

### Zwei Picker vs. einer: Konsequent entscheiden

Erster Entwurf: globaler Picker oben + lokaler Picker in jedem Tab. Das ist redundant
und verwirrend – der Nutzer fragt sich, welcher gerade gilt.

Bessere Lösung: **lokale Picker komplett entfernen**. Einziger Picker oben, Tabs lesen
aus `shared`. Tabs verlieren keine Funktionalität – sie brauchen keinen eigenen Picker,
weil der globale alle Fälle abdeckt.

Ausnahme: Video-Tab mit getrenntem Quell- und Zielordner hat genuinen Bedarf für eigene
Picker – der bleibt unverändert.

### Pre-commit vs. `make lint`: Unterschiedliche mypy-Sichtbarkeit

Pre-commit läuft mypy nur auf **veränderten Dateien** – `make lint` prüft das ganze `app/`-
Verzeichnis. Fehler in Dateien, die man nicht angefasst hat, sieht der Hook nicht.

Konsequenz: `make lint` nach jeder Session als Pflicht, nicht nur verlassen auf den Hook.

### Mypy-Fehler: suppressen vs. fixen

Ersten Instinkt (Fehler mit `type: ignore` oder `[[tool.mypy.overrides]]` stumm schalten)
hinterfragen. In diesem Fall waren echte Fixes möglich und besser:

- `image._getexif()` → `image.getexif()` (öffentliche Pillow-API seit 6.0). Nebeneffekt:
  mypy sieht jetzt den Typ von `tag` als `str | int` statt `Any` → weiterer echter Fix nötig:
  `str(tag).lower()` statt `tag.lower()`
- `nicegui_app.native.main_window` kann laut Typing `None` sein → echten `None`-Guard
  einbauen statt das Typing zu ignorieren. Macht die Funktion auch robuster (Browser-Modus).

**Daumenregel:** `type: ignore` ist akzeptabel wenn das Typing schlicht falsch/unvollständig
ist und kein Fix existiert. Wenn ein echter Fix existiert, ist der immer vorzuziehen.

### Progress-Callbacks: Zwei-Stufen-Problem bei Duplikaten

`find_duplicates()` läuft in zwei Phasen: erst alle Dateien nach Größe gruppieren (sehr
schnell), dann nur die Kandidaten hashen (langsam). Die Kandidaten-Anzahl für die
Fortschrittsanzeige ist erst nach Phase 1 bekannt.

Lösung: `candidates_total` nach Phase 1 berechnen, dann in Phase 2 den Callback aufrufen.
Der Fortschrittsbalken zeigt nur den langsamen Teil – das ist genau was der Nutzer sehen will.

---

## 2026-02 – Kamera-Sortierung: Refactoring einer Querschnitts-Funktion

### Ausgangslage
Der Renamer schrieb den Kameranamen (`Lumix`, `Osmo`) als Token in den Dateinamen:
`2024-03-15_143022_Lumix_P1020123.jpg`. Das war gedacht, um Aufnahmen verschiedener Kameras
unterscheidbar zu machen. In der Praxis war das unübersichtlich und vermischte zwei Aufgaben:
_Datum_ und _Herkunft_ in einem einzigen Dateinamen-Schema.

### Entscheidung: Kamera als Ordner, nicht als Namensteil
Statt `year/datei` (mit Kamera im Namen) wird jetzt `year/camera/datei` als optionale Struktur
im Jahr-Ordner-Tool angeboten. Der Dateiname selbst ist sauber: `YYYY-MM-DD_HHMMSS_<stem>.<ext>`.

**Warum Ordner besser ist als Name:**
- Ordner ist filterbar im Finder ohne Suche
- Dateiname bleibt kürzer und maschinenlesbarer
- Kamera-Information liegt im EXIF – die braucht nicht im Namen redundant zu stehen
- Schema funktioniert auch für Kameras, die keinen Kamera-Token bekommen hätten

### Rückwärtskompatibilität bewusst weggelassen
Bereits umbenannte Dateien mit `_Lumix_` im Namen werden vom Renamer jetzt übersprungen statt
„korrigiert". Der Korrektur-Zweig war nur für eigene Altdateien nötig – externe Nutzer haben
keine Dateien im alten Format. Das vereinfacht `generate_filename()` und `process_files()`
erheblich.

### Wo `detect_camera()` jetzt lebt
Die Funktion existierte in `unified_media_renamer.py` und wurde in `app/core/year_org.py` neu
implementiert (als `_detect_camera()`). Bewusst _nicht_ importiert: Die Erkennungslogik für
den Renamer (der Dateinamen-Fallback für bereits umbenannte Dateien) ist anders als die für
die Jahr-Sortierung (EXIF-first, Dateiname nur als letzter Fallback). Getrennte Implementierung
ist hier klarer als ein gemeinsamer Import.

### Architektur-Muster: group_by_camera als Parameter
`scan_folder()` und `execute_organization()` bekamen einen `group_by_camera: bool = False`-
Parameter. Defaultwert `False` hält den normalen Workflow unverändert. Die UI-Checkbox setzt
diesen Wert und speichert ihn im Scan-Ergebnis (`_state["scan"]["group_by_camera"]`), damit
`do_execute()` exakt dieselbe Option nutzt wie die vorangegangene Vorschau.

### Tests haben den Merge abgesichert
28 Tests liefen nach dem Merge grün durch – darunter Tests für `scan_folder` und
`execute_organization`, die die Kernlogik abdecken. Die Kamera-Erkennung selbst (EXIF-Parsing)
ist noch nicht getestet, weil dafür echte Testbilder mit Metadaten nötig wären.

---

## 2026-02 – Video-Compress-Tab: Integration & UX-Iterationen

### Von Wrapper zu eigenständigem Modul
`app/core/video_compress.py` war ursprünglich ein Wrapper um das Root-Script `video_compress.py`.
Nach dem Aufräumen (Legacy-Scripts löschen) war der Import kaputt – der Video-Tab crashte.
Fix: Alle relevanten Funktionen (`Config`, `ProbeInfo`, `collect_files`, `ffprobe_json`,
`detect_videotoolbox`, `pick_target_bitrate`, `human_mb`, `should_skip_copy`, `build_ffmpeg_cmd`)
direkt in `app/core/video_compress.py` eingebettet – wie bei `renamer.py` und `year_org.py`.

### Pre-commit: ruff SIM108
ruff hat einen if/else-Block durch einen Ternary-Ausdruck ersetzt (SIM108). Kann direkt beim
Schreiben vermieden werden – bei `codec == "auto"` war die Ternary-Form tatsächlich lesbarer:
```python
use_vt = detect_videotoolbox() if codec == "auto" else codec == "hevc_videotoolbox"
```

### UX: Labels sind wichtiger als technische Bezeichnungen
Erste Version der Codec-Auswahl nutzte technische Namen: `"Auto (empfohlen)"`,
`"VideoToolbox (HW)"`, `"libx265 (SW)"`. Das sagt Nutzern ohne Encoding-Hintergrund nichts.

Überarbeitete Labels:
- `"Automatisch"` – beschreibt das Verhalten, nicht den Mechanismus
- `"Hardware (schnell)"` – der relevante Unterschied ist Geschwindigkeit
- `"Software (langsam)"` – ehrlich, keine Verschleierung

Gleiches Muster bei der Checkbox: `"Rekursiv"` → `"Unterordner einbeziehen"`. Fachbegriff
gegen direkte Beschreibung der Konsequenz austauschen.

**Merksatz für Labels:** Was passiert, wenn ich das aktiviere? Die Antwort ist der Label.

### UX-Block als bewusste Entscheidung
Design und Labels werden immer wieder angefasst – das ist kein Fehler, sondern sinnvoll.
Einzelne Korrekturen direkt mitzudenken spart später aufwändigere Refactorings. Ein
dedizierter UX-Review-Block (alle Tabs auf einmal) ist trotzdem geplant, um konsistente
Sprache und Verhalten über die gesamte App sicherzustellen.

---

## 2026-02 – Code Review vor Packaging: Opus als Reviewer

### Workflow: Sonnet baut, Opus reviewt
Nach vielen einzelnen Arbeitsblöcken mit Sonnet (Features, Refactoring, Tests) hatte sich
eine Reihe von Problemen angesammelt, die im Einzelkontext nicht aufgefallen sind:
- **Toter Import**: `video_compress.py` importierte noch aus dem gelöschten Root-Script –
  der Video-Tab war komplett kaputt, aber kein Test hat das abgedeckt
- **Operator-Precedence-Bug**: `or` vs `and` ohne Klammern im EXIF-Parsing (`renamer.py`)
- **Collision-Counter-Bug**: Bei Namenskollisionen entstand `foto_(1)_(2).jpg` statt `foto_(2).jpg`
- **Inkonsistente Patterns**: Jedes Modul hatte eigene Extension-Sets und eigenes Error-Handling

**Erkenntnis:** Sonnet ist produktiv für Feature-Arbeit in einzelnen Dateien, sieht aber
cross-file-Probleme und subtile Logikfehler nicht zuverlässig. Ein dedizierter Review-Pass
mit Opus (oder manuell) nach mehreren Sonnet-Sessions fängt genau diese Klasse von Fehlern ab.

### Konkrete Fixes
1. Video-Tab: Logik aus gelöschtem Root-Script direkt in `app/core/video_compress.py` eingebettet
2. Operator-Precedence: Explizite Klammerung in `renamer.py` EXIF-Parsing
3. Collision-Counter: `base_stem` wird vor der Schleife gesetzt, nicht in jedem Durchlauf neu
4. `stat()`-Crash in `duplicates_tab.py` mit `try/except` abgesichert
5. `_short_path` aus zwei Tabs in `app/ui/utils.py` dedupliziert
6. Extension-Sets in `app/core/constants.py` zentralisiert
7. Error-Handling in `renamer.py` auf strukturierte Dicts umgestellt (wie `year_org.py`)
8. Bestätigungsdialoge für "Löschen" und "Umbenennen" hinzugefügt

### Muster: Review-Checkliste für vor dem Packaging
- Jeden Tab in der laufenden App durchklicken
- `grep -r "from <gelöschtes_modul>" app/` – tote Imports finden
- `make check` (lint + test) – muss grün sein
- Operator-Precedence bei gemischten `and`/`or` immer explizit klammern

---

## 2026-02 – UX-Konsistenz-Pass

### Labels konsistent über Tabs halten
Beim Umbenennen-Tab hieß die Checkbox schon „Mit Unterordnern", beim Video-Tab noch
„Unterordner einbeziehen". Beides beschreibt dasselbe – unterschiedliche Formulierungen
ohne Grund verwirren. Konsequenz: eine App, eine Formulierung.

### Ausnahme-Entscheidungen regelmäßig hinterfragen
Phase 1b hatte den Video-Tab bewusst ausgenommen: „genuiner Bedarf für eigene Picker"
(Quell- und Zielordner). In der Praxis zeigte sich, dass der Quellordner immer der
globale Ordner ist – nur der Zielordner ist wirklich Video-spezifisch.
Der Quellordner-Picker im Tab war also doch redundant und wurde entfernt.

**Muster:** Ausnahmen beim nächsten Review-Pass aktiv in Frage stellen, nicht als
dauerhaft gesetzt betrachten.

### Tipp-Texte nur wenn wirklich nötig
„Tipp: Mindestens eine Kopie behalten!" im Duplikate-Tab war überflüssig – der
Bestätigungsdialog mit „Endgültig löschen" kommuniziert die Konsequenz bereits klar.
Doppelte Warnungen wirken bevormundend und stören den Fokus.

### Hinweis-Position und -Farbe: am bestehenden Muster orientieren
Backup-Hinweis im Duplikate-Tab wurde zuerst _vor_ dem Scannen-Button platziert (amber-Farbe).
Das war inkonsistent mit dem Renamer-Tab, wo derselbe Hinweis _nach_ dem Ausführen-Button steht
(text-slate-400). Designziel war immer „wie beim Renamer" – aber ohne direkten Vergleich war
die erste Umsetzung leicht daneben.

**Muster:** Bevor ein neues UI-Element platziert wird, vorhandene Tabs auf denselben
Elementtyp prüfen (`grep "Tipp"` o.ä.) und Position + Klassen 1:1 übernehmen.

### Codec-Select: „auto" entfernen, sinnvolle Defaults setzen
Erste Version hatte `"auto"` als Option und Default – das ist bequem beim Entwickeln,
aber für Nutzer bedeutungslos. Wenn `"auto"` ohnehin immer `hevc_videotoolbox` auf macOS
wählt, ist es klarer, direkt diesen Default zu setzen und `"auto"` wegzulassen.
Nutzer sehen, was tatsächlich passiert, und können bewusst abweichen.

---

## 2026-02 – Dark-Theme & UI-Redesign (feature/dark-theme)

### Warum ein eigenes Design-System
NiceGUI rendert alles als Quasar-Komponenten. Quasar setzt eigene Inline-Styles, die sich
nur mit `!important` überschreiben lassen. Statt in jedem Tab einzeln Tailwind-Klassen zu
verwenden, wurde ein zentrales `theme.py` eingeführt, das per `ui.add_head_html()` ein
komplettes Dark-Theme injiziert. Vorteile: eine Stelle für Farben und Abstände, Tabs
nutzen nur noch CSS-Klassen (`mt-btn-primary`, `mt-card`, `mt-dupe-group` etc.).

### Tab-Architektur vereinfacht
Vorher: `build(tab_panel, shared=None)` mit `with tab_panel:` im Body.
Nachher: `build(shared: dict)`, Panel-Wrapper liegt in `main.py` (`with ui.tab_panel(...): tab.build(shared)`).
Tabs rendern nur ihren Inhalt, nicht den Container – saubere Trennung.

### ui.element("div").text() existiert nicht
NiceGUI's `ui.element()` hat keine `.text()`-Methode. Der Aufruf wirft einen
`AttributeError`, der async Callbacks still abbricht – kein Fehler in der Konsole,
die UI zeigt einfach nichts an. Fix: `ui.html('<div class="...">Text</div>')` statt
`ui.element("div").classes("...").text("Text")`.

### Status-Pills statt ui.notify()
Nach Aktionen (Scan, Umbenennen, Komprimieren) zeigen jetzt farbige Pills direkt im Tab
das Ergebnis (`theme.pill()`). `ui.notify()` ist entfernt – Toasts verschwinden nach
wenigen Sekunden und der Nutzer verpasst das Feedback. Pills bleiben sichtbar bis zur
nächsten Aktion.

### HTML-Tabellen statt ui.table()
Die Video-Vorschau und Rename-Preview sind als `ui.html()` gebaut statt als `ui.table()`
oder `ui.row()`-Schleifen. Das gibt volle Kontrolle über das Styling (mt-table, mt-rename-row,
mt-tag-*) und vermeidet Quasar-Defaults, die im Dark-Theme durchschlagen.

### Info-Tooltips statt statische Hint-Labels
Erklärungstexte (Codec-Unterschied, EXIF-Hinweis) nahmen als `ui.label()` dauerhaft Platz
weg, obwohl sie nur einmal gelesen werden. `ui.icon("info_outline").tooltip("...")` ist
kompakter – der Hinweis erscheint bei Hover und stört den normalen Workflow nicht. Passt
zum Muster: sekundäre Information nicht im Layout konkurrieren lassen, sondern on-demand
zeigen.

### Video-Metadaten: encoded_date als Fallback
DJI-Dateien haben kein `recorded_date` in pymediainfo, nur `encoded_date`/`tagged_date`.
`get_metadata()` prüft jetzt alle drei Felder. Gleichzeitig wurde die Jahr-Erkennung
umpriorisiert: Metadaten zuerst (zuverlässiger), Dateiname nur als Fallback.

---

## 2026-01 – NiceGUI & UI-Integration

### tqdm/print in Legacy-Scripts
- Legacy-Scripts nutzen `tqdm` und `print` für Terminal-Output
- In der UI stört das: Output landet im Terminal statt in der UI, kann Logs zumüllen
- Fix: Im Wrapper-Modul `_renamer_module.tqdm` und `_renamer_module.print` nach Import überschreiben (Monkey-Patching)

### Async in NiceGUI
- NiceGUI-Event-Handler müssen `async def` sein wenn sie auf Ergebnisse warten
- Blocking-Code (Datei-Scan, Umbenennungen) in `ThreadPoolExecutor` auslagern mit `await loop.run_in_executor(...)`
- Sonst friert die UI ein

### HEIC-Support
- `pillow` öffnet HEIC-Dateien nicht nativ – braucht `pillow-heif` als Plugin
- Plugin muss vor dem ersten Öffnen registriert werden: `pillow_heif.register_heif_opener()`
- Optional halten: im `try/except ImportError` wrappen, damit die App auch ohne das Plugin startet
