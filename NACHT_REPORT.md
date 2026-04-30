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
