# EPKolar-App — Handoff für neue CC-Session (2026-06-08)

## Stand
- main HEAD `eb74968` = **v3.9.182** live (https://epkolar.github.io/epkolar-app/), 726 pytest grün, Working-Tree sauber.
- Repo: `T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app` (UNC, single-file `index.html` ~19k Zeilen, transpiled React `React.createElement` + `_optionalChain`).
- Supabase `jiggujpruejkaomgxarp` — **CC hat DB-Zugriff** via `mcp__plugin_supabase_supabase__*` (execute_sql/apply_migration/get_logs/get_advisors). DB ist **sauber** (heute 13 Junk/Orphan-Records gelöscht).

## Verifikations-Triade (pro index.html-Änderung, PFLICHT)
1. `python scripts/_bracket_check.py index.html` → Baseline `() -1 / {} 0 / [] 0`.
2. node --check auf das größte inline `<script>` (siehe frühere Bash-Snippets).
3. `python -m pytest tests/ -q` → **726 passed** (UNC zäh, ~3-5 min; Foreground-sleep BLOCKIERT → Monitor-Tool nutzen).
4. Version-Bump 4 Stellen: `var SW_VER='epkolar-vX'`, `const APP_VERSION="X-supabase"`, sw.js header + CACHE_NAME.
Wenn ein Test ein altes Code-Muster assertet, das du bewusst geändert hast → Test nachziehen (kein Test-Gaming).

## ⚠️ OFFENE AUFGABEN (User-Wunsch "fix alle Bugs + Vignette")

### 1. VIGNETTE-Feature (DB-Spalten BEREITS angelegt, Frontend fehlt)
DB (Sebastian-freigegeben, schon da): `fahrzeuge.vignette_typ text` + `fahrzeuge.vignette_bis text`.
TODO Frontend (FahrzeugView, function bei ~17251):
- `nf`-State (17498) + Edit-Form-Felder (Pickerl/Versicherung @17884 + @18046): Vignette-Typ-Select
  (keine/Jahresvignette/2-Monats/10-Tage/Digital) + `vignette_bis` (gültig-bis, date).
- Detail-Anzeige: "🛣️ Vignette: <typ>, gültig bis <bis>" + Ablauf-Warnung (rot wenn `vignette_bis < heute`, analog Pickerl).
- POST/PUT-Body (fahrzeuge anlegen/speichern) um `vignette_typ`/`vignette_bis` ergänzen; `_mapFahrzeug` (Load) durchreichen.
- fahrzeuge HAT updated_at → kein plans-PUT-Bug (PUT funktioniert normal).

### 2. RESTLICHE BUG-HUNT-FUNDE (Agenten 2026-06-08, contained, noch offen)
- **Projekte#2 [MITTEL]** `deleteP` (9222): kaskadiert lokalen State NICHT → verwaiste tickets/maengel/plans/docs/entries.
  Fix: lokale Collections mitfiltern (entries.p, maengel/tickets/plans per pid, material_orders/Fotos per project_id)
  + serverseitige FK-Cascade prüfen/sicherstellen (sonst DB-Waisen wie heute aufgeräumt).
- **Projekte#3 [NIEDRIG]** Portal-Code-Gen (9274): keine Uniqueness-Prüfung. Fix: gegen `projects.some(p=>p.portalCode===c)`
  würfeln; optional DB-UNIQUE auf portal_code.
- **Projekte#4 [NIEDRIG]** Double-Submit-Guard (9209/9219): synchron gesetzt+zurückgesetzt = wirkungslos. Fix: Button
  während `_savingProject.current` disabled ODER Guard erst nach Async-Ende reset.
- **Pläne#6 [NIEDRIG]** page-Sync (10900): bei `selectedTicket.page > pageCount` zentriert auf nicht-existente Seite.
  Fix: `setPageNum(Math.min(_pg,pageCount))` clampen.
- **Pläne#4 [MITTEL, GRÖSSER]** Layer-Definitionen nur In-Memory (toggleLayer/addLayer/updateLayer/deleteLayer ~11251,
  kein SQ.push) → nach Reload Default-Layer, Tickets zeigen auf verwaiste Layer-IDs. Braucht DB-Persistenz
  (eigene Spalte/Tabelle, z.B. JSON am Projekt/Plan) — DESIGN-Entscheidung mit Sebastian.

### 3. PIN-DRAG-Reposition (halb fertig)
- x/y im updateTicket-PUT ist DRIN (v3.9.182). TODO: Drag-Handler in PlanViewerCanvas (`_startPinDrag` per
  pointerdown/move/up, %-Position via `canvasRef.getBoundingClientRect()` wie handleCanvasClick 10914) + Marker
  onPointerDown (10759, statt onClick) + `onPinMove`-Prop → `updateTicket({...t,x,y,xPct:x,yPct:y})`. Click-vs-Drag
  per 4px-Threshold. Funktioniert dann auch mobil (Pointer-Events).

## HEUTE GELIEFERT (v3.9.162→182, PlanRadar-Marathon — siehe Memory `epkolar-app-hunt-marathon-2026-06-04`)
Viewer-Transformation (Direkt-Flow Tap→Formular, immersiv, EP-grüne Pins + kanonische Pin-Nummer, Mobile-Sheet,
Geschosse), Tickets (Fotos im Create+QuickEditPin, Journal/Kommentare in DB, **comments-Spalte** angelegt),
3 kritische Persistenz-Fixes (Load-Mapping, JSON-Parse, **plans-PUT updated_at-PGRST204**), Back-Navigation-Fix
(useBackLayer), DB-Cleanup, Projekte+Pläne-Bug-Hunt.

## GOTCHAS
- **DB-DDL/DELETE:** AskUserQuestion-Freigabe nötig (Auto-Mode-Klassifizierer blockt sonst). DELETE per **exakter ID**
  (breites `ILIKE '%test%'` wird geblockt).
- **plans hat KEINE updated_at-Spalte** → generischer PUT-Handler ist für plans in der No-updated_at-Blacklist (2158).
- **Playwright + React onBlur:** synthetisches `blur`-Event triggert React nicht — `FocusEvent('focusout',{bubbles:true})` nutzen.
- **MCP-Browser** fällt bei langen Flows zu → vor jedem Lauf chrome killen (mcp-chrome-82c465c) + neu navigieren (`?cachebust`).
- **git auf UNC:** index.lock-Hänger → git.exe killen + lock löschen (Snippet in Bash-History).
- Edit "file changed since read" oft False-Trigger nach git/bump → Read-refresh + retry.

## NEUSTART
Neue CC-Session im Repo-Verzeichnis starten. First-read: dieses Doc + Memory `epkolar-app-hunt-marathon-2026-06-04`.
