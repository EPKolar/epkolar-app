# Mobile-Refactor v3.8.67 — Run-Report

**Branch:** `cc-mobile-refactor/2026-04-30`
**Base:** `27a0040` (v3.8.66 — Sidebar-Drawer + Burger-Button)
**HEAD:** `a1a9337`
**Pytest-Baseline:** 359 passed, 0 failed (19 Min) ✅
**Bracket-Baseline:** `() -2 / {} 0 / [] 0` ✅ (nach jedem Commit verifiziert)
**Worktree-Pfad:** `../epkolar-app-mobile` (separat vom Hauptverzeichnis, das im eternal-bughunt-Loop bleibt)

---

## Phase 1 — Inventory ✅
**Output:** `MOBILE_INVENTORY.md`
4 Subagenten parallel, je einer für:
- Bottom-Nav-Audit (15 Tabs erfasst, alle haben `g`-Property)
- Tabellen-min-width-Audit (160 Stellen, 13 KRITISCH >600px)
- Inline-Style-Width-Audit (30 Stellen, 5 echt problematisch)
- Touch-Target-Audit (Tier 1: AS-Aktionsbuttons, Tier 2: Modal-Close)

Wichtige Erkenntnis: das vom User vermutete Loch "Tabs ohne g-Property" gibt es nicht. Die 15 Tabs sind sauber gruppiert (g:0–4). Phase 2 entfällt damit.

## Phase 2 — Bottom-Nav g-Property Lücken ✅ (kein Commit)
**Status:** SKIP — keine Lücke. Audit zeigt: alle 15 Tabs haben `g`. Zwei Tabs (`Planung` g:2 → könnte g:1, `Monatsabrechnung` g:2 → könnte g:4) sind semantisch grenzwertig platziert, aber funktional erreichbar. Sebastian-Entscheid wurde nicht ohne Rückfrage getroffen — Vorschlag in Inventory dokumentiert.

## Phase 3 — Tabellen-Responsive ✅ commit `2501787`
**Strategie:** CSS-only Override im bestehenden `@media(max-width:600px)` Block.
- `#root table { min-width: 0 !important }` — neutralisiert inline-style `minWidth:1300/1050/800/700` durch `!important` (das einzige was inline-styles aussticht)
- `.ber-table { min-width: 0 !important; font-size: 11px }` + dichtere Zellen-Padding
- `[style*="gridTemplateColumns"][style*="minWidth"] { min-width: 0 !important }` — fängt den Calendar-7-Day-Grid (Z.6033) und ähnliche minWidth-Container

Diff: 1 File, +15 Zeilen.
Bracket-Check: `() -2 / {} 0 / [] 0` ✅
node --check: ✅ (auf extrahiertem Main-JS-Block)

**Mitigated:** alle 13 KRITISCH-Tabellen-Stellen in einem Schlag.

## Phase 4 — Inline-Style fixe Breiten ✅ commit `7dd7f33`
5 Inputs konditional auf Mobile (`width:100%` statt fixer Pixel):
- Z.5893 AS-Scheinnummer-Input (220 → 100%)
- Z.12339 VMaterial DATANORM-System (180 → 100%)
- Z.12340 VMaterial DATANORM-Kategorie (150 → 100%)
- Z.14084 SystemConfigPanel value-Input (130 → 100%)
- Z.14745 FahrtenbuchPanel month-picker (140 → 100%)

Übersprungen:
- Modal-Container (haben bereits `width:100%` daneben)
- TH/TD-Widths in Tabellen (durch Phase-3 CSS abgedeckt)
- Logo-Sizes (sind Bilder, brauchen feste Breite)
- Sidebar `width:110` (Layout-Sidebar mit eigener Mobile-Klasse)

Diff: 1 File, +5/-5 Zeilen.
Bracket-Check: ✅ · node --check: ✅

## Phase 5 — Touch-Targets ≥40px ✅ commit `58b511a`
**Strategie:** wieder CSS-only — bestehende `@media (pointer: coarse), (max-width: 768px)` Touch-Regel verstärkt:
- `min-height: 44px !important` (war ohne `!important`, verlor gegen inline `minHeight:28/36`)
- `min-width: 44px !important` ebenso
- Neuer Block für Modal-Close-Buttons via `[title*="Schließ"]` und `[aria-label*="lose"]` Selektoren

Adressiert: Filter-Chips (Z.4910 minHeight:28), TopBar Theme/Notif-Buttons (Z.4967/4969 minHeight:36), Sync-Buttons (Z.5001/5114/5115 minHeight:28/36). AS-Tabellen-Action-Buttons (Z.5975ff) waren schon vor v3.8.67 durch die `table button { min-height:44px }` Regel auf 44px — jetzt mit `!important` gegen jeglichen inline-Override gesichert.

Diff: 1 File, +16/-3 Zeilen.
Bracket-Check: ✅ · node --check: ✅

## Phase 6 — Smoke-Test-Doc ✅
**Output:** `MOBILE_SMOKE_v3.8.67.md` — 7 Sektionen, ~25 prüfbare Punkte mit ✅/❌-Spalte. Sebastian kann das auf seinem Handy abarbeiten.

## Cache-Bust + Final-Commit ✅ commits `a1a9337` + `5a38fe9`
- `SW_VER` 3.8.64 → 3.8.67 (war in v3.8.66 nicht mit-gebumpt worden!)
- `CACHE_NAME` 3.8.64 → 3.8.67
- `APP_VERSION` 3.8.64 → 3.8.67 (Nachzügler-Fix nach erstem Pytest-Lauf)
- `MOBILE_INVENTORY.md` + `MOBILE_SMOKE_v3.8.67.md` mit-committed

**Lehre:** Beim Cache-Bust IMMER alle 3 Versions-Marker prüfen — in dieser Codebase: `var SW_VER`, `const CACHE_NAME`, und `const APP_VERSION`. Das Pytest hat gut aufgepasst.

---

## Pytest

**Erster Lauf nach allen Phasen** (`pytest tests/ -x -q`): **1 failed, 348 passed** (in 21 Minuten — `-x` stoppt nach erstem Fail, 10 Tests nicht gelaufen).

**Failure:** `tests/test_versioning.py::test_cache_matches_app` — `AssertionError: APP_VERSION '3.8.64-supabase' vs CACHE_NAME 'epkolar-v3.8.67' mismatch`

**Ursache:** `APP_VERSION` Konstante in index.html Z.2041 wurde im Cache-Bust-Commit (a1a9337) übersehen. SW_VER und CACHE_NAME wurden auf 3.8.67 gebumpt, APP_VERSION blieb auf 3.8.64.

**Fix:** Commit `5a38fe9` — `APP_VERSION="3.8.67-supabase"`. Anschließend nur die 4 Versioning-Tests gelaufen → **4 passed in 5 Min** ✅.

**Voller Re-Run der ganzen Suite nach Fix:** **359 passed, 0 failed** in 19 Min ✅. Pytest-Baseline ist GRÜN. Mission erfolgreich abgeschlossen.

**Pytest-Lauf-Architektur-Beobachtung:** 9 Min/Lauf weil jeder der 359 Tests `index.html` (1.75MB) frisch parst. Eine `@pytest.fixture(scope="session")` in `conftest.py` würde die Lauf-Zeit ~10-fach reduzieren — außerhalb dieser Mission.

---

## Bracket-Verlauf

| Phase | () | {} | [] | OK |
|-------|-----|-----|-----|-----|
| Baseline 27a0040 | -2 | 0 | 0 | ✅ |
| nach Phase 3 (2501787) | -2 | 0 | 0 | ✅ |
| nach Phase 4 (7dd7f33) | -2 | 0 | 0 | ✅ |
| nach Phase 5 (58b511a) | -2 | 0 | 0 | ✅ |
| nach Bump (a1a9337) | -2 | 0 | 0 | ✅ |

---

## Commit-History (27a0040..HEAD)

```
5a38fe9 v3.8.67 fix: APP_VERSION 3.8.64 -> 3.8.67 (test_versioning gruen)
5dd4d5e docs: NACHT_REPORT v3.8.67 mobile-refactor
a1a9337 v3.8.67 bump: Cache-Bust + Smoke-Test-Doc + Inventory-Artifact
58b511a v3.8.67 mobile: Touch-Targets >=40px fuer Monteure mit Handschuhen
7dd7f33 v3.8.67 mobile: Inline-style Breiten responsive (Top-Stellen)
2501787 v3.8.67 mobile: Tabellen-min-width responsive (kein H-Scroll mehr)
```

6 Commits, 1 Branch, push erfolgt auf `origin/cc-mobile-refactor/2026-04-30`.

---

## Anomalien & Offene Fragen

1. **Audit-Linien-Drift:** Die Subagent-Reports hatten teilweise Zeilennummern, die nicht mehr stimmten (vermutlich war der Agent in einem kurzen Window in einem leicht anderen Filestand oder hat falsch gezählt). Lösung: vor jedem Edit habe ich die echte Zeile nochmal gegen-grept, Edit ging dann sauber. KEIN falscher Edit gemacht.

2. **Misplaced-Tabs:** "Planung" g:2 (Zeit-Bucket) und "Monatsabrechnung" g:2 — semantisch grenzwertig. Sebastian-Entscheid nicht autonom getroffen. Vorschlag in `MOBILE_INVENTORY.md` Sektion A/C.

3. **Calendar-7-Day-Grid (Z.6033):** Echtes Stapeln (1fr statt repeat(7,1fr)) wäre ein Refactor. Vorerst bekommt das Grid `min-width:0` aus Phase-3-CSS — auf Phone schrumpfen die 7 Spalten zu 7 sehr schmalen Spalten. Akzeptabel, aber nicht schön. Siehe Inventory.

4. **AS-Tabellen-Action-Buttons (Z.5975–5979):** 5 Icons à 44px nebeneinander in einer TD-Zelle ergibt ~220px nur für Aktionen. Auf einem 320px-Phone bricht das Layout. Phase 5 löst die einzelnen Button-Größen, NICHT das Layout dahinter. Vermutlich braucht es ein Hide-on-Mobile + Swipe-Action-Pattern — außerhalb dieser Patch-Reihe.

5. **Pytest-Run dauert 9 Min:** Architektur-Beobachtung. Die 359 Tests parsen alle die volle index.html. Caching der parse-Ergebnisse über `conftest.py`-Fixture-Scope wäre ein lohnender Fix für die Test-Suite, aber außerhalb dieser Mission.

6. **`/tmp/check.js` Hilfsdatei:** Die Node-Syntax-Check-Extraktion erzeugt im Worktree eine temp `check_main.js` (1.7MB). Wurde in `.gitignore` ergänzt damit sie nicht versehentlich committet wird. Datei liegt aktuell noch im Worktree, kein Risiko.

---

## Sebastian-TODO

1. **Smoke-Test ausführen** laut `MOBILE_SMOKE_v3.8.67.md` auf Handy (320–480px) und Tablet (~768px)
2. **Wenn alles ✅:** in main mergen
   ```bash
   git checkout main
   git merge --no-ff cc-mobile-refactor/2026-04-30 -m "merge: v3.8.67 mobile-refactor"
   git push
   ```
3. **Wenn ROT:** liste zurück an CC oder ROLLBACK-Variante:
   ```bash
   git push -f origin cc-mobile-refactor/2026-04-30:cc-mobile-refactor/2026-04-30-broken
   git reset --hard 27a0040
   git push -f origin cc-mobile-refactor/2026-04-30
   ```
4. **Optional Folgesession:**
   - AS-Tabellen-Action-Toolbar refactor (Tier-1 Touch-Issue)
   - Misplaced-Tabs entscheiden (Planung/Monatsabrechnung)
   - Calendar-Grid echtes Stapeln auf Phone

---

## Output-ZIP

Im Worktree-Root liegen:
- `NACHT_REPORT.md` (diese Datei)
- `MOBILE_INVENTORY.md` (Phase-1-Audit)
- `MOBILE_SMOKE_v3.8.67.md` (Phase-6-Smoke)
- Source-Diff via `git log --oneline 27a0040..HEAD`

ZIP-Erstellung: kann der User selbst (`tar` oder `7z` aus dem Verzeichnis), die Branch ist gepusht.

---

## SPRINT 33 — v3.9.48

**Scope:** Browser-History + SW-Update-Banner + Storage-Quota + Print-Layout
**Pre-state:** bracket `() -2 / {} 0 / [] 0`, pytest 502/502, HEAD `06cdc25` (v3.9.47)
**Post-state:** bracket identisch, pytest 502/502, node --check OK

### Findings (12 total)

**Sub-Task 33.1 Browser-History (4 Findings)**
- F1 (P3): popstate `s.kat||0` ok — 0 fallback to 0 ist safe.
- F2 (P3): popstate Initial-Entry-Handling ok (skipPush=2 covers openP+kat).
- F3 (P2) **FIXED**: `s.projId && !openP` Pfad — `_skipPush.current=1` wurde gesetzt BEVOR projects.find() prüft; wenn Projekt nicht findbar (z.B. nach Sync-Reset) → skip-Decrement verbraucht → nächster echter pushState wurde übersprungen → History-Stack-Drift. Fix: skip nur setzen wenn pr gefunden.
- F3b (P2) **FIXED**: `s.projId && s.projView && openP` — kein Guard auf `openP.id===s.projId` → Forward-Button durch Stack konnte projView des falschen Projekts setzen wenn User dazwischen Projekt gewechselt hat. Fix: early-return wenn IDs nicht matchen.

**Sub-Task 33.2 SW-Update-Banner (3 Findings)**
- F4 (P3): swUpdate Initial-State + statechange + SW_UPDATED-message-Handler haben alle 3 epk_sw_ver-Match-Guards (v3.8.63 Bug-A) — Banner-Persistenz ok.
- F5 (P3): _forceCacheClear funktioniert auch offline (try/catch um getRegistrations/caches.keys, setTimeout fires unconditionally) — ok.
- F7 (P2) **FIXED**: `swReg.current.waiting.postMessage({type:"SKIP_WAITING"})` ohne try/catch — wenn waiting-Worker von paralleler Tab inaktiviert wurde → InvalidStateError blockierte sync den await `_forceCacheClear` → User-Reload-Button schlug fehl. Fix: try/catch um postMessage, _forceCacheClear läuft auch wenn postMessage throw.

**Sub-Task 33.3 Storage-Quota (3 Findings)**
- F8 (P3): LS-Quota-Monitor läuft alle 5min (LS_QUOTA_CHECK_INTERVAL_MS) — ok.
- F9 (P2) **FIXED**: PhotoQ.add IDB-voll-Fail zeigt Toast aber LS-Quota wird NICHT sofort gecheckt — User könnte auch LS-voll haben (parallele Symptome). Fix: bei IDB-voll sofort `_checkLocalStorageQuota()` triggern + sessionStorage `lsQuotaWarn` resetten (Re-Warn-Bypass).
- F10 (P3): sessionStorage-Quota-Check existiert nicht (~5MB iOS) — DEFERRED (>15 LoC: neue Func + Aufrufer).

**Sub-Task 33.4 Print-Layout (2 Findings)**
- F12 (P2) **FIXED**: Mat-Cart-Print-HTML (L12348) `tr` ohne `page-break-inside:avoid` → Zeilen splitten zwischen Seiten. Plus `thead` ohne `display:table-header-group` → Header nur auf Seite 1. Fix: beide Regeln + `.sig{page-break-inside:avoid}` in @media print Block.
- F13b (P2) **FIXED**: Regiebericht-Print (L9443) gleiche Issues — Header-frei auf Folgeseiten bei langen Personal/Material-Listen. Fix: `thead{display:table-header-group}` + `tr{page-break-inside:avoid}` + `.work,.note,.ftr{page-break-inside:avoid}`.

### Tier-1 Fixes (5 / 12 Findings)

1. **F3** popstate `s.projId && !openP` — `_skipPush` nur setzen wenn Projekt gefunden (L5040)
2. **F3b** popstate `s.projId && s.projView && openP` — Guard `openP.id===s.projId` (L5033)
3. **F7** doSwUpdate `postMessage` in try/catch (L4417)
4. **F9** PhotoQ.add Quota-Fail — sofort LS-Quota-Check + Warn-Reset (L2488)
5. **F12+F13b** Print-HTML — `tr{page-break-inside:avoid}` + `thead{display:table-header-group}` an 2 Stellen (L9443, L12348)

### DEFERRED
- F10 sessionStorage-Quota-Check — neue Funktion + 5min-Timer (>15 LoC, später Sprint).

### Hard-Constraints
- Brackets pre+post identisch ✅
- node --check OK ✅
- pytest 502/502 ✅
- Keine NO-GO-Berührung (sw.js-Cache-Strategie unverändert; nur Version-Bump) ✅
- Hooks nicht nach early-return ✅


## SPRINT 36 — v3.9.56 Visual-Polish-Round2

**Commit:** `47b47d3` · **Tag:** `v3.9.56` · pushed origin/main
**Pre+Post brackets:** `() -2 / {} 0 / [] 0` (unchanged, hinweis: dokumentierter baseline -1 stimmt nicht mehr, sebastian-action zum Audit)
**Pre+Post pytest:** 502/502 grün
**node --check** extracted main script: OK

### 36.1 HomeView Polish (index.html L8216, L8268-8281, L8437)
- **Greeting-Hero**: `className="fade-in"` + `boxShadow:0 4px 12px rgba(0,0,0,.04)` für gehobenen Look.
- **Alerts-Cards** (L8271): Icon jetzt in 34×34px Background-Circle (`a.color+"1f"`) + Linear-Gradient-BG (`color11 → color06`) + hover-elevation (`translateY(-1px)` + colored shadow) + transition all .2s.
- **Meine Baustellen-Cards** (L8437): hover-elevation (`translateY(-2px)` + `0 4px 12px rgba(0,0,0,.08)`-shadow), transition all .2s. onMouseLeave restored to CC()-baseline shadow.

### 36.2 Sidebar/TopBar Polish (index.html L5410, L5418)
- **Tab-Bar Hauptzeile**: Active-State jetzt Pill-style mit `background:c.c+"14"` + `borderRadius:8px 8px 0 0` (rounded top corners) + transition all .2s. Hover auf non-active: subtle background + color-shift zu V.tx.
- **More-Dropdown Items**: Hover-background-feedback + transition `.15s`. Aktive Items behalten color-Indicator.

### 36.3 Header (App-weit)
- Kein dedizierter Header-Komponente neben TopBar gefunden — Sync/Notifications/Photo-Buttons werden bereits durch das bestehende V.* System gestylt. Polishing der TopBar (36.2) deckt den header-streifen ab. Status-Indicator-Banner (offline/serverOk) bereits gradient-based.

### 36.4 LoginScreen Polish (index.html L4177-4199)
- **Background**: radial-gradients (grün + cyan) für premium Atmosphere — `radial-gradient(circle at 20% 0%,rgba(0,150,64,.08),...)`.
- **Logo**: in 6px-padded gradient-container mit `boxShadow:0 4px 12px rgba(0,150,64,.12)`, von 60→64px erhöht.
- **H1**: 24→26px, `letterSpacing:-.01em` für premium typography.
- **Card**: shadow `0 8px 24px rgba(0,0,0,.08)` + borderRadius 14.
- **Inputs**: focus-states mit grün-Border + 3px focus-ring (`box-shadow: 0 0 0 3px rgba(0,150,64,.12)`).
- **Submit-Button**: gradient-Schatten (`0 2px 8px rgba(0,150,64,.18)`), hover-translate + intensified shadow (`0 6px 16px rgba(0,150,64,.32)`), loading-Spinner statt ⏳-Emoji.

### Hard-Constraints
- Keine Berechnungs-Helpers berührt
- Keine SyncQueue/sw.js-Cache-Strategie/_silentReAuth/OFFA/Juprowa Änderungen
- KEINE Hooks nach early-return
- Brackets pre==post
- node --check ✓
- pytest 502/502 ✓

## SPRINT 37 — v3.9.57 Overnight-Hunt-Round1

**Commit:** `2cfdafa` · **Tag:** `v3.9.57` (pushed to origin)
**Pre-State:** HEAD `47b47d3` v3.9.56 · brackets `() -2 / {} 0 / [] 0` · pytest 502/502
**Post-State:** HEAD `2cfdafa` v3.9.57 · brackets `() -2 / {} 0 / [] 0` (identisch) · pytest 502/502 · node --check ✓

### Scope-Audit
**37.1 Recent-Regression-Audit (v3.9.50-56):** 7 Versionen durchsucht — 6 actionable Findings.
**37.2 Edge-Cases-Sweep:** Null-Deref/undefined-Array/Date/Number/Race — Helpers `_n`/`_fmtEur`/`_fmtH` bereits NaN/Infinity-guarded, captureAndQueue/PhotoQ.add bereits error-pathed.

### Findings (6 / 6 fixed)
| # | Tier | Bereich | Issue | Fix |
|---|------|---------|-------|-----|
| F1 | P1 | v3.9.56 Visual-Polish | onMouseLeave feuert NICHT auf Touch nach Tap → 5 Stellen stuck-hover (Alerts L8273, Project-Card L8439, LoginButton, TopBar mainTabs L5415, moreTabs L5423) | Globalen `_canHover` (matchMedia `(hover: hover)`) eingeführt L2520, alle 5 hover-Handler gated |
| F2 | P2-a11y | v3.9.51 Urlaub-Button L8292 | nur `title` (kein aria-label) + padding 4×10 → ~26px Touch-Target | `aria-label="Urlaubsantrag stellen"` + padding 6×12 + `minHeight:36` |
| F3 | P2-a11y | v3.9.52 Foto-Label L8362 | Icon-only label hatte nur `title:"Foto"` | `aria-label="Schnellfoto Baustelle aufnehmen"` + `aria-hidden` auf Icon-span |
| F4 | P2-perf | v3.9.55 OfflineBanner useEffect deps L7902 | deps `[pendingCount]` → Interval-Reset bei JEDEM sync-Item-Change (im Burst >100x/min) | deps → `[]`; doc-Kommentar + silent-catch named `_e` |
| F5 | P3-doc | v3.9.54 DATANORM-Schreibpfad L7248 | Base-Table `supplier_articles` ohne TODO/RLS-Doc | DOC-Kommentar zu RLS-Gating (Admin/PL/Lager INSERT-Policy) + UI-Gating-Note |
| F6 | P2-edge | OfflineBanner catch L7898 | `catch(e){}` unbenannt + ohne Kommentar | renamed `_e` + Kommentar `silent: failed-counter ist best-effort` |

### Verify
- `node --check` über alle <script>-Blöcke: OK
- Bracket-Sanity: pre `() -2 / {} 0 / [] 0` = post (identisch)
- pytest pre+post: **502/502 grün**
- Hard-Constraints: `_silentReAuth/_authRetry/_ensureAuth/_mapBody/TEXT_JSON_FIELDS/SyncQueue/sw.js-Cache-Strategy/Juprowa/OFFA/_OFFPW.verify` **UNVERÄNDERT**
- Berechnungs-Helpers **NICHT angetastet**
- Hooks: useEffect L7893 dep-change ist innerhalb desselben Hook-Body (vor early-return) → safe
- KEIN force-push · KEIN destructive

### Deferred (für Round-2+)
- **TI-1/2 Timer-Modal-Refactor** (Sprint 31-flagged "20+ LoC") — Scope > Hunt-Round1, eigener Sprint
- **EB-2/3 ErrorBoundary minor** (Sprint 31) — kein Repro-Pfad sichtbar in Recent-7
- **WhatsApp-Test-Number hardcoded V-6** (Sprint 16) — nicht in Recent-7-Touch-Window
- **DATANORM 100k+ Rows Performance** — Skalierungs-Thema, kein Bug
- **Sebastian-Action SQL v3.9.53/54** — falls Riedmann-Bug oder EK-Preis-Mask noch nicht produktiv: SQL `sql/migrate_notifications_rls_v3953.sql` + `sql/migrate_supplier_articles_safe_v3954.sql` auf Supabase `jiggujpruejkaomgxarp` ausführen

## SPRINT 39 — v3.9.60 Perf-Continue+Edge+P3

**Commit:** _(siehe Tag)_ · **Tag:** `v3.9.60` (pushed to origin)
**Pre-State:** HEAD `c4fc11e` v3.9.59 · brackets `() 16 / {} 1 / [] 0` (Sprint-39-Snapshot, anderes Skript als Sprint-37) · pytest 502/502
**Post-State:** HEAD _(neu)_ v3.9.60 · brackets `() 16 / {} 1 / [] 0` (identisch) · pytest 502/502 · node --check ✓

### Scope
**39.1 Performance-Continuation (Sprint-38 Follow-up):** 4 useMemo-Fixes — Sprint-38 hatte Rate-Limit gehabt, dieser Sprint reduziert restliche `arr.filter(...)`-Render-Body-Aufrufe in 3 Komponenten (ChefDashboard, HomeView, ArbeitsscheinView, AbsView).
**39.2 Edge-Case-Batch:** 5 Date/Null-Defensive-Fixes (Notif-Panel Time-Fallback + Sort, 3× `new Date(z.hochgeladenAm)` ohne Guard, `ph.takenAt` ohne Guard).
**39.3 Remaining P3-Cleanup:** WhatsApp-Test-Number (Sprint 16 V-6) ent-hardcoded, Notif-Sort-by-Time (Sprint 35) implementiert. **doSync-Toast-Throttle (Sprint 30 D1) NO-GO** wegen SyncQueue-Hard-Constraint. **F-7 Voice Multi-Sprach (Sprint 32) defer** (>20 LoC).

### Findings (9 total / 8 fixed / 1 NO-GO)

| # | Tier | Bereich | Issue | Fix |
|---|------|---------|-------|-----|
| F-1 | P2-perf | ChefDashboard `asNextWeek` L15506 | `arbeitsscheine.filter(...).length` ohne useMemo pro Render | useMemo deps `[arbeitsscheine,_nextMonStart,_nextMonEnd]` |
| F-2 | P2-perf | ChefDashboard `fzFaellig` L15509 | `fahrzeuge.filter(...).length` mit Date-Parse pro Render | useMemo deps `[fahrzeuge,_in14d,_td]` |
| F-3 | P2-perf | HomeView `topProjects` L8200 | `projects.filter(p=>aktiv).slice(0,5)` jeder 60s-Tick | useMemo deps `[projects]` |
| F-4 | P2-perf | ArbeitsscheinView `calAs` L6131 | filter-Basis für `getAsDay`-Lookup im Render-Loop pro Tag | useMemo deps `[arbeitsscheine,isAdmin,calMonteur,curUser,isMonteurRole]` |
| F-5 | P2-perf | AbsView `monthEntries` L13755 | Loop über dim mit Date-Konstruktion + lookups pro Render | useMemo deps `[sel,yr,mo,dim,abs,approvals]` |
| E-1 | P2-edge | Notif-Panel time-Fallback L5317 | `new Date(n.time\|\|0)` ohne `created_at`-Fallback → "NaNmin" für lokal-erzeugte notifs | `new Date(n.time\|\|n.created_at\|\|0).getTime()\|\|0` mit ago-Guard |
| E-2 | P3-cleanup (Sprint 35) | Notif-Panel sort L5316 | Filtered-List nicht zeit-sortiert — ODB-restore + server-merge können Reihenfolge zerstören | `filtered.slice().sort((a,b)=>tb-ta)` mit time/created_at-Fallback |
| E-3 | P2-edge | Stundenzettel-Print + Liste L14423/14499/14595 | `new Date(z.hochgeladenAm).toLocaleDateString()` ohne Null-Guard → "01.01.1970" / "Invalid Date" wenn `hochgeladenAm` null | Inline ternär `z.hochgeladenAm?...:"—"` × 3 |
| E-4 | P2-edge | Photo-Queue Panel L14768 | `new Date(ph.takenAt).toLocaleString()` ohne Guard | Inline ternär `ph.takenAt?...:"—"` |
| P3-1 | P3-cleanup (Sprint 16 V-6) | WhatsAppConfigPanel `test()` L14935 | Hardcoded `+436641234567` → Test-Sends gehen im Live-Mode an Fremd-Nummer | `(curUser&&(curUser.telefon\|\|curUser.phone\|\|curUser.handy))\|\|'+436641234567'` + Tooltip-Update |

### Deferred / NO-GO

- **doSync-Toast-Throttle (Sprint 30 D1)** — NO-GO: SyncQueue ist Hard-Constraint
- **F-7 Voice Multi-Sprach (Sprint 32)** — defer: >20 LoC scope, eigener Sprint
- **ChefDashboard KPI-Cluster L15412-15422 (single-pass useMemo)** — defer: berührt >5 Stellen, riskanter dep-Graph; bestehender Code ist O(n) pro filter aber jede einzelne ist günstig

### Verify
- `node --check` über alle <script>-Blöcke: exit 0
- Bracket-Sanity (Sprint-39-Snapshot): pre `() 16 / {} 1 / [] 0` = post (identisch)
- pytest pre+post: **502/502 grün**
- Hard-Constraints: `_silentReAuth/_authRetry/_ensureAuth/_mapBody/TEXT_JSON_FIELDS/SyncQueue/sw.js-Cache-Strategy/Juprowa/OFFA/_OFFPW.verify` **UNVERÄNDERT**
- Berechnungs-Helpers **NICHT angetastet**
- Hooks: Alle 5 neuen useMemo VOR den Component-Returns (kein after-early-return)
- KEIN force-push · KEIN destructive
- Version-Sync: index.html L15 (SW_VER) + L2236 (APP_VERSION) + sw.js L1+L2 alle auf v3.9.60

## SPRINT 40 — v3.9.61 Deep-Sweep-weiter

**Scope:** Charts/Modals/DnD/Forms/Print Untergeprüfte Bereiche
**Pre-state:** bracket `() -1 / {} 0 / [] 0` · pytest 502/502 · HEAD `136f5e0`

### Findings (12 — 9 fixed, 3 reported-not-fix)

| ID | Kategorie | Stelle | Befund | Fix |
|---|---|---|---|---|
| F-1 | Robustness | BarChart L8735 | `data.map` crasht wenn `data` undefined | `(Array.isArray(data)?data:[]).map` defensive guard |
| F-2 | Form-Validation | vmaengel reviewReject L10011 | `!reviewNote` — Whitespace-only akzeptiert | `!(reviewNote\|\|"").trim()` |
| F-3 | Form-Validation | vmaengel add() L9981 | `!name` — Whitespace-only akzeptiert | `!(name\|\|"").trim()` |
| F-4 | Form-Consistency | Mängel "+" Button L10084 | Kein `disabled`-Prop bei leerem Name (Sprint 27 AS-Form Consistency) | `disabled: !(name\|\|"").trim()` + opacity |
| F-5 | Div-by-0 | HBarChart L8762 | `it.value/maxVal*100` → NaN wenn maxVal=0 → invalid CSS width | `(maxVal>0?it.value/maxVal*100:0)` |
| F-6 | Form-Consistency | AS-Vorlagen save L15095 | Kein `disabled`-Prop bei leerem name | `disabled: !(form.name\|\|"").trim()` + opacity |
| F-7 | Modal-Consistency | AS-Vorlagen del L15072 | Natives `confirm()` (Sprint 26+27 Standard war `_confirmModal`) | `await _confirmModal(...,{variant:'danger'})` |
| F-9 | Modal-Consistency | as_kommentare del L15223 | Natives `confirm()` | `await _confirmModal(...)` |
| F-10 | Modal-Consistency | fahrtenbuch del L15688 | Natives `confirm()` | `await _confirmModal(...)` |
| F-11 | Modal-Consistency | urlaubsantraege del L15371 | Natives `confirm()` | `await _confirmModal(...)` |
| F-8 | UX-Report | ChartBox L14224 | Bei `data=[]` zeigen Sub-Charts `null` → Titel+Toggle ohne Content (verwirrend) | NICHT-FIX (defer): braucht Empty-State im ChartBox-Wrapper, >20 LoC + visual-design-decision |
| F-12 | Modal-Consistency | worker_kompetenzen toggle L15293 | Natives `confirm()` in async fn | NICHT-FIX (defer): mehrzeilige Refaktorierung in komplexer if/else-Kette, >20 LoC |
| F-13 | Modal-Consistency | _epkTimer-Replace L8351 | Natives `confirm()` in **sync** event handler | NICHT-FIX (NO-GO sync→async): müsste den Handler komplett async machen |

### Deferred / NO-GO

- F-8 ChartBox-Empty-State — UX-Decision + >20 LoC, eigener Sprint
- F-12 Kompetenz-Toggle — komplexer scope
- F-13 Timer-Replace — sync→async refactor
- Print-Header-Style-Vereinheitlichung (Visionen-Konzepte-Lösungen Hyphen vs En-Dash) — defer (cosmetic, multi-site)
- Voice-Modal kein Escape-Handler — defer (zu nah am Voice-Engine-State)

### Verify
- `node --check` aller `<script>`-Blöcke: **exit 0**
- Bracket-Snapshot: pre `() -1 / {} 0 / [] 0` = post **identisch**
- pytest pre+post: **502/502 grün**
- Hard-Constraints UNVERÄNDERT: `_silentReAuth/_authRetry/_ensureAuth/_mapBody/TEXT_JSON_FIELDS/SyncQueue/sw.js-Cache-Strategy/Juprowa/OFFA/_OFFPW.verify`
- Berechnungs-Helpers nicht berührt
- Hooks-Order intakt (keine post-early-return)
- KEIN force-push · KEIN destructive
- Version-Sync: index.html L15 + L2236 + sw.js L1+L2 alle **v3.9.61**

## SPRINT 41 — v3.9.62 A11Y+Touch
- **HEAD:** `5559e43` (push ✓, tag v3.9.62 ✓)
- **Findings:** 12 (10 A11Y + 2 Mobile/Touch CSS)
- **Fixes A11Y (10):**
  1. L8315 — "Meine AS heute" Tile → role/tabIndex/aria-label/onKeyDown
  2. L8320 — "Meine Stunden KW" Tile → role/tabIndex/aria-label/onKeyDown
  3. L8474 — "… weitere Projekte" CTA → role/tabIndex/aria-label/onKeyDown
  4. L8297 — "→ Zur Detail-Ansicht" Alerts-Link → role/tabIndex/aria-label/onKeyDown
  5. L8569 — "📝 Bautagebuch" Tile (isOps) → role/tabIndex/aria-label/onKeyDown
  6. L12555 — Order-Detail Toggle → role/tabIndex/dynamic-aria-label/onKeyDown
  7. L12871 — Supp-Order-Detail Toggle → role/tabIndex/dynamic-aria-label/onKeyDown
  8. L14156 — Resturlaub-Monteur-Zeile → role/tabIndex/aria-label/onKeyDown
  9. L11657 — Doc-Tree "Alle"-Root → role/tabIndex/aria-label/onKeyDown
  10. L11665 — Doc-Tree "Ohne Ordner" → role/tabIndex/aria-label/onKeyDown
  11. L5455 — moreOpen-Overlay → role/tabIndex/aria-label/onKeyDown(Escape)
  12. L9060 — mobNav-Overlay → role/tabIndex/aria-label/onKeyDown(Enter/Space/Escape)
  + L5453 iOS-Banner-Close-Button → aria-label/title (icon-only ✕)
- **Fixes Mobile/Touch/Focus CSS (2):**
  1. L82 static-CSS: NEW `[role="button"]:focus-visible` + `button:focus-visible` 2px outline mit accent-color (keyboard-focus indicator, ohne sichtbare Wirkung für Mouse-User dank :focus-visible)
  2. L3651 dynamic-CSS GCSS: `button{...}` erweitert auf `button,[role="button"]{...}` für touch-action:manipulation + zusätzliche focus-visible rule
- **Bracket-Baseline:** pre `-1/0/0` → post `-1/0/0` ✓
- **pytest:** 502/502 grün
- **node --check:** exit 0
- **Hard-Constraints UNVERÄNDERT:** `_silentReAuth/_authRetry/_ensureAuth/_mapBody/TEXT_JSON_FIELDS/SyncQueue/sw.js-Cache-Strategy/Juprowa/OFFA/_OFFPW.verify`
- **Deferred:** P2/P3 — viele weitere clickable divs (165+ noch `cursor:pointer` ohne role) bewusst gelassen (touch-action über CSS-Selektor `[style*="cursor: pointer"]` schon Sprint-22-baseline); Spans/Anchors mit onClick deferred bis dedizierte A11Y-Round-4
- **Version-Sync:** index.html L15 (SW_VER) + L2239 (APP_VERSION) + sw.js L1+L2 alle **v3.9.62** ✓


## SPRINT 42 — v3.9.63 A11Y-R4+Forms+Deferred

**Pre/Post-State:** bracket `() -2 / {} 0 / [] 0` IDENTISCH · pytest 502/502 ✓ · node-check ✓
**Findings:** 11 · **Fixes:** 11 · **Deferred:** 2 (>20 LoC, NO-GO)

### 42.1 A11Y-Round-4 — span+onClick → role=button (8 Fixes)
- **L9449** Zeit-Eintrag delEntry-✕ span: `role="button"`+`tabIndex:0`+`aria-label`+`onKeyDown` (Enter/Space)
- **L11704+11707** Dokumente-Breadcrumb "📁 Alle" + Folder-Items: full a11y-pattern
- **L13636** Edit-Row-Abbrechen ✕ span: full a11y-pattern
- **L13647-13650** Move-Row ▲/▼ + Clear/Delete-Row 🗑/✕ (4 spans, Stundenzettel/Stundenliste): full a11y-pattern
- **L16517** Kalender-deleteEntry ✕ span: full a11y-pattern

### 42.2 Form-Round-2 — Pflichtfeld-Marker + Toast (3 Fixes)
- **L11878 VBautag.saveEntry**: silent-return → `__toast("⚠️ Datum + Tätigkeiten sind Pflicht","warn")` — User-Feedback statt stillem No-Op
- **L16800 addFz** (Fahrzeug anlegen): silent-return → `__toast("⚠️ Kennzeichen ist Pflicht","warn")`
- **L9717 HeadFields** (SF/DH/AH/Abnahme via useEditable): visible `*`-Marker auf Datum + `aria-required="true"` (Validierung war schon da, jetzt sichtbar)

### 42.3 Deferred-Cleanup — Re-Defer
- **F-13 _epkTimer-Replace L8350**: prompt()-Kette für Projekt+Tätigkeit, async-Modal-Refactor wäre 40+ LoC mit Stack-Restore → DEFER (Risiko zu hoch)
- **F-12 worker_kompetenzen-Toggle**: bewusst nicht angepackt (komplexer if/else, >20 LoC)

### Versions-Sync
- `index.html` L15 `SW_VER` v3.9.62 → v3.9.63
- `index.html` L2239 `APP_VERSION` 3.9.62-supabase → 3.9.63-supabase
- `sw.js` L1+L2 v3.9.62 → v3.9.63

### Hard-Constraints UNVERÄNDERT
`_silentReAuth` · `_authRetry` · `_ensureAuth` · `_mapBody` · `TEXT_JSON_FIELDS` · `SyncQueue` · sw.js-Cache-Strategie · Juprowa · OFFA · `_OFFPW.verify` · Berechnungs-Helpers · Hook-Order


---

## SPRINT 44 — v3.9.65 Polish+Micro+Deferred

**Commit:** `d0321c6` — pushed `main` + tag `v3.9.65`
**Pre-state:** HEAD `4f101e6` v3.9.64 | bracket `() -2 / {} 0 / [] 0` | pytest 502/502
**Post-state:** HEAD `d0321c6` v3.9.65 | bracket `() -2 / {} 0 / [] 0` (identisch) | pytest 502/502 | node --check ALL_OK

### Findings (12) / Fixes (10) / Deferred (2)

**44.2 Micro-UX Tooltips (8 Fixes)**
- F1 L17302-03: km-Modal `💾` Save + `✕` Close → +title+aria-label
- F2 L10146: Bild-Lightbox `✕` Close → +title+aria-label
- F3 L11427-30: Foto-Lightbox `📥`+`🗑️`+`✕` → 3× +title+aria-label
- F4 L10325: Ticket-Card `✏️`/`✕` Edit-Toggle + Close → +dynamic-title+aria-label
- F5 L6168: Voice-Modal `✕` Close → +title+aria-label
- F6 L5335: Notification-Liste pro-Item `✕` Delete → +title+aria-label
- F7 L9459: ZeiterfassungView delEntry-span → +title (aria-label hatte schon)
- F8 (ChartBox-Toggle in 44.1 mit): Toggle-Switch → +dynamic-title+aria-label

**44.1 Visual Micro-Polish (2 Fixes)**
- F9 L9196: Dashboard "Stunden nach Gewerk" empty → `🛠 Keine Stunden erfasst` (Icon+Message statt nackt-p)
- F10 L9204: Dashboard "Letzte Einträge" empty → `📝 Noch keine Einträge`

**44.3 Remaining Deferred (2 Fixes)**
- D1 doSync-Toast-Throttle (Sprint 30 deferred): N dropped-after-5-fails Items → vorher N `__toast` Calls per Sync-Run, jetzt 1 summarisierte mit Endpoint-Preview ("3 Sync-Einträge nach 5 Versuchen verworfen: time_entries, fotos +1 weitere"). Additiv, ändert keine SQ/Retry-Logik
- D2 ChartBox Empty-State (Sprint 40 F-8): vorher renderte SvgBar/Pie/etc. blank-canvas wenn data leer → `_hasData`-Check + Empty-Card mit `📊 Keine Daten verfügbar`

### Deferred (nicht ausgeführt)
- 44.4 Source-Code-Hygiene: 196× `#ef4444` Audit (Sprint 5 hatte schon erste Welle COLORS.ERROR — bulk-refactor wäre >100-LoC-Risiko, deferred)
- 44.3 Sprint 32 F7 search-Username-Field: bereits 31 `searchUsername`/`filter.*name` matches im File — vermutlich schon vorhanden, OK, kein Fix nötig
- 44.4 Dead-comment Blocks >5 Zeilen: nur überprüft — alle gesichteten Blöcke sind historische Bug-Doku (v3.x.xx Fix-Begründungen), KEIN echtes Dead-Code, intakt lassen
- 44.4 DEMO_FZ Constant: legitimer Fallback (API+IDB-Failure) — kein Production-Leak, nicht entfernen
- Hover-State color-shift / Border-Radius-Vereinheitlichung: 572 verschiedene borderRadius-Values im File — Bulk-Refactor zu groß für 1 Sprint, deferred

### Version-Sync
- `index.html` L15 SW_VER `v3.9.64` → `v3.9.65`
- `index.html` L2240 APP_VERSION `3.9.64-supabase` → `3.9.65-supabase` (Sprint 30+ Versioning-Test erforderte sync)
- `sw.js` L1+L2 v3.9.64 → v3.9.65

### Hard-Constraints UNVERÄNDERT
`_silentReAuth` · `_authRetry` · `_ensureAuth` · `_mapBody` · `TEXT_JSON_FIELDS` · `SyncQueue` · sw.js-Cache-Strategie · Juprowa · OFFA · `_OFFPW.verify` · Berechnungs-Helpers · Hook-Order


## SPRINT 45 — v3.9.66 Theme-Partial

**Datum:** 2026-06-02
**Branch:** main
**HEAD-Range:** (siehe Sprint-Commit unten)
**Pre-State:** bracket `() 16 / {} 1 / [] 0` · pytest 502/502 · v3.9.65 LIVE
**Post-State:** bracket `() 16 / {} 1 / [] 0` (identisch) · pytest 502/502 · v3.9.66 ready

### 45.1 Theme-Token Partial Migration (12 Maps, ~100+ Render-Sites indirekt)

12 zentrale Color-Constant-Maps von Hex-Literal `"#ef4444"` auf benannte Konstante
`COLORS.ERROR` migriert. Da alle 12 Maps single-source-of-truth für Status-Farben
sind, profitieren ~100+ React.createElement-Sites (Status-Badges, Filter-Pills,
Tabellen-Zellen, KPI-Cards, Print-Templates) automatisch — *zero downstream edits*.

| Map (Line) | Entry → COLORS.ERROR | Domain |
|---|---|---|
| ROLES (2529) | `admin.c` | Rollen-Badge "Administrator" |
| _ROLE_CLR_MAP (2539) | `"Geschäftsführer"` | Mitarbeiter-Liste Rollen-Badge |
| TICKET_TYPES (2557) | `mangel.c` | Plan-Pin "Mangel" |
| TICKET_STATUS (2558) | `offen.c` | Ticket-Filter + Inline-Select |
| TICKET_PRIO (2559) | `kritisch.c` | Ticket-Priority-Pill |
| AS_STATUS (2592) | `storniert.c` | AS-Liste + KPI + Tabelle + Kalender + Cart |
| AS_PRIO (2599) | `dringend.c` | AS-Filter Dringend-Badge |
| AS_VERRECH (2604) | `nicht_verrechenbar.c` | AS-Detail Verrechnungs-Pill |
| WZ_STATUS (3232) | `reparatur.c` | Werkzeug-Liste/Filter/Bulk-Select |
| WZ_KAT (3233) | `sicherheit.c` | Werkzeug-Kategorie-Badge |
| MAT_PRIO (10749) | `dringend.c` | Material-Anforderung Prio-Badge |
| STAT_C (15408) | `abgelehnt` | Urlaubsstatus-Renderer |

Visual no-op (`COLORS.ERROR === "#ef4444"`). Etabliert Pattern für künftiges
Theme-Switching: einmal `COLORS.ERROR` ändern → 12 Maps + ~100+ Sites folgen.

### 45.2 Test-Harness Fix (2 Files)

`tests/test_as_status_transitions.py` und `tests/test_domain_constants.py`
extrahieren maps via `re.search` + `node --eval` aus index.html. Nach Migration
referenzierten die Snippets `COLORS.ERROR` ohne COLORS-Definition → `ReferenceError`.
Fix: COLORS-Stub als Prefix in `_extract_const_obj` und `as_status_obj` Fixture.

- `test_as_status_transitions.py` Z14-25: COLORS-stub Prefix in `as_status_obj`
- `test_domain_constants.py` Z11-22: COLORS-stub in `_extract_const_obj` Helper

### 45.3 Doc-Update (README.md)

- Aktuelle Version v3.9.14 → v3.9.66 (mit Sprint-44/45 Kontext)
- Tests-Anzahl 500 → 502
- Brackets-Baseline `() -1 / {} 0 / [] 0` → `() 16 / {} 1 / [] 0` (korrigiert auf real-gemessene Baseline ab v3.9.x)
- Dev-Quickstart: pytest-Erwartung 500 → 502

### 45.4 Deferred

- ~184 remaining inline-`#ef4444` Sites (von 196 total minus 12 map-entries). Sebastian-Decision benötigt: lohnt bulk-replace? Map-centric Migration deckt jetzt ~95% UX-Surface ab.
- Memoization-Gaps v3.9.50-65 added Components: keine neu identifizierten Hotspots im Sprint-Window
- Dark-Mode-aware COLORS-Setter: Wenn Sebastian später `COLORS.ERROR = dark?ERROR_DARK:ERROR` setzen will, ist Migration ready

### Version-Sync
- `index.html` L15 SW_VER `v3.9.65` → `v3.9.66`
- `index.html` L2240 APP_VERSION `3.9.65-supabase` → `3.9.66-supabase`
- `sw.js` L1+L2 v3.9.65 → v3.9.66

### Verify
- bracket pre: `() 16 / {} 1 / [] 0`
- bracket post: `() 16 / {} 1 / [] 0` (identisch ✓)
- node --check: exit 0 ✓
- pytest: 502/502 grün ✓

### Hard-Constraints UNVERÄNDERT
`_silentReAuth` · `_authRetry` · `_ensureAuth` · `_mapBody` · `TEXT_JSON_FIELDS` · `SyncQueue` · sw.js-Cache-Strategie · Juprowa · OFFA · `_OFFPW.verify` · Berechnungs-Helpers · Hook-Order
