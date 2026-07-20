# Handoff 2026-07-20 NACHT (autonomer Durchlauf) — v3.9.775 → 782 live

**Arbeitsklon** `C:\repos\epkolar-app`, alles gepusht + deployed (raw + github.io auf **3.9.782**).
Modus: autonom, Multi-Agent (große Bauten an Subagenten delegiert, ICH jeden Bau selbst verifiziert:
grep 0-Ref · node_check · `_bracket_check` (Baseline `() -1`) · `_check_version` · voller pytest · Headless-Mount).
pytest zuletzt **1860 passed, 13 skipped**.

## Was live ging (jede eigene Version, volle Gates)
| Ver | Inhalt | Verifiziert |
|---|---|---|
| **775** | Entfernungszulage-Vergabe als Outlook-Kalender (Etappe 3+4): `EZKalender` Monat/Woche, Semantik „Vorbelegung gilt, Flag korrigiert" (`_ezEffTage`), lohnrelevante Menge = eff-Tage × 11,71 | Live-Check Sebastian grün |
| **776** | PZE-Monatsblatt (FinkZeit) als **PDF** = Lohnverrechner-Export, ersetzt CSV. `_pzePdf`/`_pzeBuildRows` (eine Zeilenquelle, DST→März 31). EZ-Fuß aus `_ezEffTage` | Headless-Mount + node-eval Riedmann [8, 93.68] |
| **777** | EZ-Kalender-UX: Heute-Fix (Ursache: rohes `new Date()` + fehlender Marker → Sprung unsichtbar) via `_ezHeuteISO()` (Wiener) + Heute-Ring; Kachel-Infos (Std + Status-Label statt Punkt); Legende | Headless: Heute-Ring, Std, „vorbelegt" |
| **778** | PZE-PDF auf **Querformat** (landscape, PW 297, Spalten 273 mm, Umbruch y>188) | node_check + pytest |
| **779** | Nav-Tab + 3 Überschriften „Urlaub" → **„Abwesenheiten"** (4 UI-Stellen; perm/Fachbegriffe unberührt) | grep-Sweep + pytest |
| **780** | manueller **OFFA-Import-Flow komplett entfernt** (Button+importOffa+importRef+commitImport+Vorschau-Modal+States+`_parseOffaPdf`); 0 lebende Refs; Export unberührt | grep 0-Ref + pytest |
| **781** | **Chef-Portal (ChefDashboard) auf Sub-Tabs** (5 Tabs, localStorage; Muster v771) | Headless: 5 Tabs + Persistenz |
| **782** | Dead-Code-Mini: `_stReadLog` entfernt (0 Aufrufer seit v769) + StempelTafel-Kommentar auf RPC-Realität | grep 0-Ref + pytest |

## SICHTPRÜFLISTE für Sebastian (kein statisches Gate deckt das ab)
1. **PZE-PDF öffnen** (Zulagen-Tab → „📄 PZE-PDF (Lohnverrechner)"): ist **quer** (v778), FinkZeit-Spalten Datum|Tag|Von/Bis|Fehlgrund|Gesamt|Soll|Pause|+/-|Notiz|Projektzeit, EZ-Fußzeile „N Tage × 11,71 € = X".
2. **EZ-Kalender**: „Heute"-Button springt + Heute-Ring sichtbar; Kacheln zeigen Std + Status („✓ vergeben / vorbelegt / ✕ abgewählt"). Ring nutzt EP-Grün (nah am „vergeben"-Grün) — falls zu ähnlich, sag Bescheid (Blau als Alternative).
3. **Nav-Tab** heißt „Abwesenheiten"; **OFFA-Import-Button weg**, „📊 OFFA Excel" noch da.
4. **Chef-Portal** hat 5 Tabs (Überblick/Projekte/Arbeit/Personal/Ressourcen), merkt den letzten.

## Geflaggt / offen (NICHT autonom entschieden)
- **`OFFA_SB_MAP`** ist seit v780 toter Code (nur der entfernte Import nutzte es) — bewusst behalten (im Auftrag als „nicht anfassen" markiert). Kandidat für die **Dead-Code-Nachtsession**.
- **Etappe 3 (EZ-Menge = geflaggte Tage) ist LIVE und lohnrelevant** (Sebastian freigegeben, €-Beispiel Riedmann 93,68 €). Der Lohnverrechner bleibt maßgeblich; die App-Zahl ist Vorschau/Übergabe.
- **Stempeluhr-RPC** (`sql/STEMPEL_TERMINAL_RPC_v3.sql`) + `entfernungszulage_tage` sind angelegt; die Stempeluhr-Stufe-2 (PZE als FinkZeit-Ablösung, Gleitzeitpool) bleibt spätere Runde.

## Gotchas dieser Nacht (für die nächste Session)
- **sw.js-Truncate-Falle:** `open('w').write(open().read())` in EINEM Ausdruck leert die Datei vor dem Lesen (das äußere `open('w')` truncatet zuerst) → sw.js war kurz leer. Immer getrennt lesen/schreiben. Via `git checkout sw.js` gerettet.
- **Regex-frisst-Decorator:** ein `re.sub(...(?=\ndef ))` beim Test-Umschreiben verschluckte den `@pytest.mark.skip`-Decorator der Folge-Funktion → ein obsoleter Test wurde wieder aktiv. Bei Funktions-Ersatz in Testdateien den nächsten Decorator im Blick behalten.
- **Subagent-Bracket-Zählung:** zwei Subagenten meldeten `() 12` als Baseline; das Projekt-Skript `scripts/_bracket_check.py` gibt konsistent `() -1`. Immer dem Projekt-Skript trauen, Subagent-Report gegenprüfen.
- **Playwright-MCP** verklemmte zwischendurch (Profil-Lock „already in use"); löste sich später von selbst. `rm`/PowerShell-Kill waren geblockt.
