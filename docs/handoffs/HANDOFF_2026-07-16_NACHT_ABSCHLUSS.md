# Handoff 16.07.2026 (Nacht, ABSCHLUSS) — Dispo-Überarbeitung Register 0–26, Stand v3.9.748

**Arbeitsklon:** `C:\repos\epkolar-app`. Push `git push origin main`. Remote-Verify per curl raw + github.io.
**Stand HEAD:** **v3.9.748** (`21ec27d`). **pytest 1743 grün.** Working tree clean, alles gepusht & live.
**Resume-Wahrheit:** dieser Handoff + `git log` + Memory `project_epkolar_dispo_register`.

> **Pflicht-Gates je Push (unverkürzt):** `python scripts/node_check.py index.html` (0) ·
> `python scripts/_bracket_check.py index.html` (**`() -1`**, {} 0, [] 0) · `node sql/_check_version.js` ·
> voller `python -m pytest tests/ -q` **NACH dem Versions-Bump** · **Headless-DispoPanel-Mount** (s.u.).
> Kein optional chaining (`?.`). Deutsche `„…"` in JS-Strings nur mit `'…'` innen. Version 4 Stellen.

## MATRIX 0–26 (bei jedem Push führen)
`0✔724 1◑747(Teil1) 2✔723 3✔723 4✔723 5✔748 6– 7– 8– 9– 10– 11– 12– 13– 14✔725 15✔726 16✔732 17✔727 18✔728 19✔729 20✔733 21✔738 22✔741 23✔742 24✔744 25✔746 26✔745 · Horizont=4 Wochen`

## Diese Session gebaut & LIVE (v731–748, alle TDD + Headless-verifiziert)
| Ver | Register | Inhalt |
|---|---|---|
| 731 | #16a-Rest | Warteliste ziehbar (⠿), Live-Drop-Feedback grün/rot (`_dispoDropOk` seit v740), KW-Tab-Hover-600ms |
| 732→733 | #16b→#20 | Dauer-Griff → **Kalender-Kachel** (Höhe∝Dauer, Uhrzeit rechts, unterer Rand=Höhen-Griff) + **Startzeiten** (`_dispoAblauf`, 15-min-Takt ab 07:00) |
| 734 | — | Fixe Termine per Drag zwischen Tagen umterminieren (→ v740 in onDrop aufgegangen) |
| 735 | — | Mittagspause 12–13 + Freitag-Feierabend 11:30 in `_dispoAblauf` (opts.noLunch) |
| 736/737 | — | Text-Markierung bei Drag ENDGÜLTIG weg (selectstart-Blocker auf document + pointercancel-Restore, beide Gesten) |
| 738 | #21 | AS-Sub-Tab heißt **„Dispo"** (Tab + Panel-Titel) |
| 739 | **P1** | **Aktuelle Woche fehlte** — Anker KW+1→KW+0; vergangene Tage geblockt „vergangen" |
| 740 | **#22a** | **EIN Schreibgesetz**: jede Geste schreibt `{terminBestaetigt,terminZeit,dauer}` via `onDrop`→updAs (byte-gleich Übernehmen) + OFFA-Push; harte Wand `_dispoDropOk`; Kaskaden-Push-Verbot |
| 741 | **#22b + P0** | **P0-HOTFIX** `onReschedule`-Render-Crash (killte AS-Tab); **Pin-Mechanik entfernt** (v730 tot); Gate-Härtung |
| 742/743 | #23 / — | **Chip-Parität** (gemeinsame `_chipBox`); **4-Wochen-Horizont** |
| 744 | #24 | **km-Wahrheit**: PLZ aus Arbeitstext (Verwalter-Kunden, 69km→~2km); `_dispoScheinPlz`/`_dispoTextPlz`/`_dispoOrtPlz`/`_dispoFold`; geoMap führt `ort` |
| 745 | #26 | **Ansicht read-only** — statisch + Headless bewiesen (Mount/KW/Neu-berechnen = 0 Writes) |
| 746 | #25 | Vereinbarte (fett) vs. geplante Zeit (`~HH:MM geplant`, `_chipBox` geplant-Flag; `_abFix`) |
| 747 | **#1 Teil 1** | Blockierbare Tage: gesperrter Tag = Kap 0 + 🚫 (`blocksMap`); `dispo_blocks` 42P01-tolerant; **SQL gestaged** |
| 748 | #5 | Phantom-Krankmeldung: Absence-Poll Union-Merge + Plausi-Guard + `_absNotifOk` (from_date≥heute-3) |

## Architektur (für Wiederaufnahme)
- **Reine //@DISPO-Funktionen** (node-eval, window-Export): `_dispoPlan`, `_dispoBuildInput(...,geoMap,distMatrix,blocksMap)` (KW+0-Anker; vergangene Tage + gesperrte Tage kurzgeschlossen im Kap-Loop), `_dispoAblauf(items,startMin,pufferMin,taktMin,opts)` (Mittagspause 720–780, opts.noLunch=Freitag), `_dispoDropOk(dragMid,cellMid,hardBlock,restMin,dauerMin)`, `_dispoScheinPlz/_dispoTextPlz/_dispoOrtPlz/_dispoFold` (#24), `_dispoDauerSnap`, `_dispoScheinPlz`, `_absNotifOk`. Tot (Cleanup #12): `_dispoDropFeedback`, `_dispoCanResched`.
- **EIN Schreibgesetz:** Prop **`onDrop`** (Callsite in ArbeitsscheinView) → `updAs({terminBestaetigt,terminZeit,dauer})`. Kein Pin, kein zweiter Schreibweg. `_chipBox(kind,...)` rendert fix+Vorschlag identisch.
- **Zelle** exponiert `data-cap` (echte Rest-Kap) + `data-hardblock` (Urlaub/Krank/🚫/vergangen); Live-Feedback = Write-Wand (grün=speichert/rot=nicht).

## ⚠️ GATE-LEKTIONEN (teuer gelernt — unbedingt einhalten)
1. **Headless-DispoPanel-Mount ist PFLICHT.** Der Browser-Boot-Smoke lädt die App, **rendert das DispoPanel aber nie** → ein `onReschedule`-ReferenceError im Chip killte v740 live den ganzen AS-Tab (P0). DispoPanel ist eine globale Funktion (klassisches Script). Verifikation:
   ```js
   // im geladenen Browser (http-server auf Repo-Root)
   const div=document.createElement('div');
   ReactDOM.flushSync(()=>ReactDOM.createRoot(div).render(React.createElement(DispoPanel,{
     arbeitsscheine:[/* 1 fixer Termin (terminBestaetigt=morgen) + 1 Vorschlag */], monteure:[{id:'m1',n:'A',r:'Monteur'}],
     wpHistory:{},abs:{},onUebernehmen:()=>{},onOpenSchein:()=>{},onDrop:()=>{}})));
   // -> kein Throw; fixe + Vorschlags-Kachel im aktuellen KW-View rendern
   ```
   Statischer Backstop: `test_dispo_panel_callbacks_v741.py` (jeder `on*`-Prop-Callback in DispoPanel muss in der Signatur stehen).
2. **Vollen pytest IMMER NACH dem Versions-Bump** laufen. Prosa-Kommentare mit ungematchten `)`/`[` (z.B. `[720,780)`, Listen `1)`/`2)`) brechen `test_invariants` (Roh-Bracket-Baseline **-7/0/0**). Der Code-Bracket-Check (`() -1`) sieht das nicht.
3. **Ansicht ist read-only** (`test_dispo_readonly_view_v745.py`): DispoPanel hat keinen `updAs`/`SQ.push`; nur echte Gesten schreiben.

## ⏳ OFFEN — Reihung
- **#1 Teil 2 — 🚫-Toggle-UI** (nach SQL-Run): `onToggleBlock`-Prop (Gate Büro/PL/Admin), Toggle je Monteur×Tag schreibt `dispo_blocks` (insert grund / delete). DispoPanel bleibt sonst read-only. Prio-1/fixer Termin auf geblocktem Tag → Konflikt-Badge. **Voraussetzung: `sql/DISPO_BLOCKS_v1.sql` von Sebastian ausgeführt.**
- **#18b** — im v728-Handoff als „nicht möglich" markiert (kein Worksheet-Einzel-GET client-seitig). Re-Eval nötig.
- **#19b — Geo-Selbstnachzieh** (Sebastian-Command liegt vor): bei fehlender PLZ Nominatim-Lookup (max 1 req/s, nur Misses) → INSERT `plz_geo` (+ `ort` aus display_name, Teil 2); Paar fehlt → OSRM `/table` (router.project-osrm.org), **neue PLZ nur gegen Firma 3470 + PLZ der OFFENEN Scheine, gebatcht ≤80 Ziele/Request** (Kundenstamm 439 PLZ, OSRM-Limit ~100) → INSERT `plz_distanz`. Danach denselben Lauf neu rechnen (Selbstheilung). **CSP `connect-src` um GENAU 2 Hosts** erweitern (`nominatim.openstreetmap.org` + `router.project-osrm.org`), Test pinnt die Zeile wörtlich. Dienst down → Kaskade wie gehabt, nie hängen (kurzer Timeout, Session-Merker gegen Retry-Sturm).
- **#6 E2-🚛-UI** · **#7 Büro-Extras A5** · **#8–#13** (Team-Kachel, Material, Perf, Bug-Hunt, Cleaning `_dispoDropFeedback`/`_dispoCanResched`, Handoff+Endreport).

## Sebastian-Gates (offen)
**`sql/DISPO_BLOCKS_v1.sql` ausführen** (schaltet #1 scharf) · geo-Befüllung (plz_geo/plz_distanz; #19b füllt auto) · `AS_FZ_BEDARF`-SQL · E4b-Live-Abnahme (Diff belegt, Test grün) · PAT workflow-scope · **P2** Störungsdienst-Bonus zieht Routinearbeit an (Bonus nur `_dispoTopf(s)===0`?) · **P3** Vorab+Teilabwesenheit `max()` statt Summe.

## Live-Abnahme (Chat/Sebastian)
Auf Zuruf EINE kontrollierte E4b-Übernahme am echten Schein. Drag-Gesten sind headless nicht simulierbar (nur pure Kerne + Struktur + Render getestet) — die Gesten testet Sebastian live (bestätigt: Verschieben & Kalender-Kachel funktionieren).
