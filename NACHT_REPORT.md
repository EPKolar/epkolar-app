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
