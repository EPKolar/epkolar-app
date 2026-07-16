# Handoff 16.07.2026 (langer Nachtlauf, ABSCHLUSS) — Dispo Register 0–31, Stand v3.9.754

**Arbeitsklon:** `C:\repos\epkolar-app`. Push `git push origin main`. Verify curl raw + github.io.
**HEAD:** **v3.9.754** (`6bf300b`). **pytest 1768 grün.** Working tree clean, alles gepusht & live.
In diesem Lauf **v731→v754 gebaut (34 Versionen)** + P0-Hotfix + P1-Fixes. Details im Memory `project_epkolar_dispo_register`.

> **Pflicht-Gates je Push:** `python scripts/node_check.py index.html` (0) · `python scripts/_bracket_check.py index.html`
> (`() -1`) · `node sql/_check_version.js` · voller `python -m pytest tests/ -q` **NACH dem Versions-Bump** ·
> **Headless-DispoPanel-Mount** (s.u.). Kein `?.`. Deutsche `„…"` in JS nur mit `'…'` innen. 4-Stellen-Version.

## LIVE durch (Register)
`#1(Teil1) #2 #3 #4 #5 #14 #15 #16 #17 #18 #19 #20 #21 #22 #23 #24 #25 #26 #27 #29(a–d) #30(a–e) #31(f,c) · Horizont=4W`

## Architektur (Wiederaufnahme)
- **Pure //@DISPO** (node-eval + window): `_dispoBuildInput(...,geoMap,distMatrix,blocksMap)`, `_dispoAblauf(items,startMin,puffer,takt,{anchors,endMin,noLunch})` = **First-Fit in Lücken** (Anker=fixe-mit-Zeit + Mittagspause), `_dispoAblaufBuendel` (atomare Bündel), `_dispoZeitkonflikte`, `_dispoDropOk`+`_dispoAblehnGrund` (Wand=Tagesnorm, Eigengewicht raus, Grund beziffert), `_dispoScheinPlz/_dispoTextPlz/_dispoOrtPlz/_dispoFold` (#24), `_dispoParseDauer`(HH:MM:SS!)/`_dispoDauer`(Regeln V2+Menge+Median)/`_dispoMengeFaktor`/`_dispoMedianJeKlasse`, `_absNotifOk`, `_dispoMonteurUebertragbar`.
- **EIN Schreibgesetz:** Prop `onDrop → updAs {terminBestaetigt,terminZeit,dauer}` (#22a); Chip-Render `_chipBox(kind,...)`; Ansicht read-only (test).
- `JUPROWA_WORKER_MAP` += P026 Kiener (mpxpwdhrht1b) / P028 Aliti (mqyxfca35x6i).

## ⚠️ GATE-LEKTIONEN
1. **Headless-DispoPanel-Mount ist PFLICHT** — Boot-Smoke rendert das Panel nie (ein `onReschedule`-ReferenceError killte v740 live = P0). Im geladenen Browser: `ReactDOM.flushSync(()=>ReactDOM.createRoot(div).render(React.createElement(DispoPanel,{arbeitsscheine:[1 fixer Termin morgen + 1 Vorschlag], monteure:[{id:'m1',n:'A',r:'Monteur'}], wpHistory:{},abs:{},onUebernehmen:()=>{},onOpenSchein:()=>{},onDrop:()=>{}})))` → kein Throw. Statisch: `test_dispo_panel_callbacks_v741.py`.
2. **Vollen pytest NACH dem Bump** — Prosa mit `[720,780)`/`1)` bricht `test_invariants` (Roh-Baseline -7/0/0). Zeile 2854 (APP_VERSION-Chain) via Python-Script ändern (zu groß für Edit).

## ⏳ OFFENER BACKLOG (Reihung)
- **30f** Datenfrische: visibilitychange/Tab-Fokus → arbeitsscheine neu ziehen + Plan neu rechnen (gecacht); Panel-Kopf „Stand HH:MM · ↻"; #26-Assertion erweitern (Re-Fetch = 0 Writes).
- **#28 Planungskern V2:** 28a MINUTEN statt km (plz_distanz-min in Score/`_dispo2opt`/Ablauf; Haversine-min via `DISPO_TEMPO_LANDSTRASSE`); 28b Nachbarschafts-Bonus (gleiche PLZ / Matrix-min < `DISPO_NAH_MIN=15` → Score-Bonus zwischen Adress-Bündel und Wochen-Malus; **Topf schlägt Bonus, Test pinnt**); 28c erledigt (via #29d); **28d Panel-Kopf Vollbilanz** „N offen: X fix · Y Vorschläge (KW…) · Warteliste · nicht-unterbringbar" — **Invariante als Test: Summe == alle offenen Scheine, nie ein Loch**; leere Zellen „— noch 3,5h frei" (Fr 4,0h).
- **#31a** Monteur-Guard (`updAs` `_isMt`) gegen `public.workers` prüfen, NIE ID-Muster (Random-IDs erste Klasse; users/Auth TABU); **#31b** Pull-Echo-Schutz (Monteur ohne Code → Feld NICHT aus Cloud zurückspiegeln, dauerhaft feldweise); **#31e** Schreibstellen-Inventar (6 direkte `_sbPatch/_sbPost` auf arbeitsscheine: 1 Drain legitim, 5 auf `updAs` umziehen) + **statisches Gate** (Vorbei-Schreiber-Zahl == Whitelist). *Juprowa = reine Maschinen-Brücke App↔OFFA; Push = Abrechnungs-Lebensader → 31e wichtigste Zusicherung.*
- **#1 Teil 2** 🚫-Toggle-UI (SQL `DISPO_BLOCKS_v1.sql` gelaufen ✓): `onToggleBlock`-Prop (Büro/PL/Admin) schreibt `dispo_blocks`.
- **#18b** (re-eval) · **#19b** Geo-Selbstnachzieh (Nominatim max 1/s nur Misses → INSERT plz_geo +ort; OSRM /table neue PLZ nur gegen Firma 3470 + offene-Scheine-PLZ, **≤80 Ziele/Request**; CSP connect-src += GENAU 2 Hosts, Test pinnt Zeile; nie hängen).
- **#6 E2-🚛-UI** · **#7 Büro-Extras A5** · **#8–#13** (Cleaning: `_dispoDropFeedback`/`_dispoCanResched` tot).

## Sebastian-Gates offen
`AS_FZ_BEDARF`-SQL · E4b-Live-Abnahme · PAT workflow-scope · Alt-Codes P024 Barger/P022 Cracana per GET gegen Cloud prüfen · Alii/Aliti-Namensfrage.
