# HANDOFF · v3.8.20 Cleanup-Sweep · 2026-04-23

**Start-HEAD**: `40198da` (v3.8.19.4 Bug-Hunt Iter-22)
**End-HEAD**: `11566d6` (v3.8.20 full bump)
**Tag**: `v3.8.20` (lokal, push offen bis Sebastian OK)
**Modus**: vollautonom ausgeführt via `CC_COMMAND_v3.8.20_AUTO.md`

---

## 🆕 Update 2026-04-23 Abend · LIVE-STAND

Seit v3.8.20 wurden folgende "v3.8.21-Kandidaten" aus diesem Handoff abgearbeitet:

| Punkt | Status | Ref |
|---|---|---|
| Iter-23 AS-Filter L5009 (`!t` → `!_hasTermin(t)`) | ✅ **DONE v3.8.21** | `fc381ae` |
| `${z.dateiName}` FinkZeit-Footer L12765 `_e()`-wrap | ✅ **DONE v3.8.21** | `fc381ae` |
| Audit-UI Filter-Dropdown (5 → 17 Optionen + Entity-Filter) | ✅ **DONE v3.8.22** | `41e50ae` |
| Block 8 AS-Signature-Close-Flow | ✅ bereits in v3.8.7 umgesetzt (TODO war stale) | — |
| Block 13 Audit-Log-UI | ✅ bereits in v3.8.7 umgesetzt (TODO war stale) | — |
| Feature 12 WhatsApp UI | 🔵 blockiert auf Sebastian (Schema+Seeds-Deploy) | — |
| AS-PDF v2 (jsPDF statt HTML) | 🔵 deferred v3.8.23+ | — |

**Aufräumen 2026-04-23 Abend** (`7034ecf` + `e776e76`):
- 38 historische Files (Handoffs, Baselines, closed-Bug-Artefakte, superseded Docs) nach `_archiv/` bzw. `_archiv/sql/`
- Neue `.gitignore` (.env, node_modules, OS-/Editor-Kram, `CC_COMMAND_*_AUTO.md`)
- Neue `README.md` (Root) + `_archiv/README.md` + `sql/README.md` neu geschrieben

**Neuer Helper** (`sql/_check_version.js`): verifiziert dass `APP_VERSION` (index.html) und `CACHE_NAME` + Header-Kommentar (sw.js) synchron sind. Exit 1 bei Mismatch — tauglich für pre-push Hook.

**Aktueller HEAD**: siehe `git log -1` (während OFFA-Sync-Parallel-Session in Bewegung).

Sebastians Action-Items aus der "Offen"-Liste unten sind **weiterhin offen** — v3.8.21+22 waren pure Frontend-Fixes ohne DB-Touch.

---

## Block-Status-Tabelle

| Block | Thema | Status | Commit | Notiz |
|---|---|---|---|---|
| 0 | Pre-Flight | ✅ DONE | — | `baseline_v3.8.20_start.txt` geschrieben |
| 1 | Iter-23 Sentinel-Date-Fix | ✅ DONE | `4d73842` | `_hasTermin` Helper + 3 Chef-Stellen |
| 2 | R-3 Warenkorb-Print XSS | ✅ DONE | `8247bc8` | Lokales `_e` in Print-onClick |
| 3 | R-6 FinkZeit-Print `<iframe>`/`<img src>` | ✅ DONE | `da00d9f` | 3 Attr-Interpolationen gewrappt |
| 4 | R-4 Weather-API `_fT` | ⚠️ SKIPPED | — | Bereits erledigt (siehe unten) |
| 5 | `B_12_ORPHANS_ANALYSIS.md` Doc-Fix | ✅ DONE | `e86e874` | 4 Edits, SQL + Live-Count |
| 6 | v3.8.20 Version-Bump + Tag | ✅ DONE | `11566d6` | APP_VERSION + CACHE_NAME |
| 7 | Handoff + Push | 🔵 IN PROGRESS | — | Push erfolgt nach Handoff-Commit |

---

## Ehrlichkeits-Bilanz — was wirklich gemacht wurde

### Block 1 · Iter-23 Sentinel-Date-Fix ✅

- **Helper eingezogen** direkt nach `function _fT` (L1235):
  ```js
  const _hasTermin = t => !!(t && t > '1900-01-01');
  ```
- **3 ChefDashboard-Stellen gefixt** (nicht 2, wie im Command-Text vermutet):
  - L13647 `const ueberfaellige=...` (Chef-v2 Überfällig-Zähler)
  - L13653 `const ueberfaellige_vor7d=...` (Trend-Berechnung)
  - L13675 `const topOver=...` (Kritisch-Überfällig-Widget)
- **L13818 nicht extra angefasst**: `topOver.map(...)` iteriert bereits gefilterte Items, 739728d-Bug dort nicht mehr möglich.
- **L5008-5009 nicht angefasst**: Das ist der AS-Filter (`quickFilter==="ueberfaellig"`), nicht Chef-Scope — hat aber dasselbe Sentinel-Problem. Siehe "TODO v3.8.21" unten.
- Juprowa-Push-Code (`juprowa_push_worksheet`, `AK_TERMIN`) unberührt — dort ist Sentinel bewusst.
- Verify: syntax OK, brackets `() -2 {} 0 [] 0`, `_hasTermin` erscheint 4× (1 def + 3 Verwendungen).

### Block 2 · R-3 Warenkorb-Print XSS-Härtung ✅

- Scope: `renderWarenkorb` (L10780 – 10909) — konkret der Print-Button-`onClick`-Handler (L10888).
- **Lokales `_e`** am Anfang des Handlers eingeführt (wie in druckAnsicht L12708, Etiketten-Druck L2846).
- **Gewrappt** (alle Template-Literal-Interpolationen im Print-HTML):
  - `p.nr`, `p.name` (Title + H2, inkl. bestehendes `.replace(/"/g,"")`)
  - `curUser.name` (Meta-Zeile)
  - `i.artNr`, `i.name`, `i.dim`, `i.menge`, `i.einheit`, `i.katalog` (Tabellen-Rows)
- **Alte ad-hoc Patches entfernt**: `.replace(/</g,"&lt;")` ersetzt durch `_e(...)`.
- `items.length` (Zahl) unberührt — kein XSS-Risiko.

### Block 3 · R-6 FinkZeit-Print iframe/img src Attribut-Escape ✅

- Scope: `druckAnsicht` (L12704+) innerhalb FinkZeit-Komponente. `_e` dort bereits lokal definiert (L12708).
- **Gewrappt** (3 Stellen in L12750, L12756):
  - `<iframe src="${z.datei}">` → `<iframe src="${_e(z.datei)}">`
  - `<img src="${z.datei}" alt="Stundenzettel">` → `<img src="${_e(z.datei)}" ...>`
  - `<img src="${z.unterschrift}" alt="Unterschrift">` → `<img src="${_e(z.unterschrift)}" ...>`
- **`${z.dateiName}`** (L12765) nicht angefasst — Command-File erwähnt es nicht; konservative Option.
- AS-Signature-Blöcke (L2652, L5164, L5217, L5223, L8493-8494, L8557-8558) unberührt, wie vorgegeben.

### Block 4 · R-4 Weather-API `_fT` Timeout ⚠️ SKIPPED

- Beide open-meteo-fetches sind **bereits gewrappt**:
  - L7157 (cached-weather): `fetch(\`...\`, _fT({}, 10000))`
  - L10315 (autoFill Bautagebuch-Wizard): `fetch(url, _fT({}, 10000))`
- Command-File verlangte `_fT(8000, fetch(...))` — das passt **nicht** zur tatsächlichen `_fT(init, ms)`-Signatur (L1235, wraps fetch-init-object mit `AbortSignal.timeout`, NICHT Promise).
- 8000 ms vs. 10000 ms: beide aktuellen Calls verwenden 10s; konservative Entscheidung ist, das **nicht** zurückzudrehen (mehr Toleranz gegen langsame Mobile-Verbindung ist safer).
- Keine Änderung notwendig. Handoff statt Commit.

### Block 5 · B_12_ORPHANS_ANALYSIS.md Doc-Fix ✅

4 Edits wie spezifiziert:
1. L31 `a.kunde_name` → `a.kund_name` (42703-Fix)
2. Nach Frontmatter-Box (vor erstem `---`): neue Section "Stand 2026-04-23 (Claude-Chat-Live-Check)" mit Live-Count-Tabelle (0 NULL / 11 EMPTY_STRING / 0 orphans / 61 total)
3. In Section "Action (a)": neuer ausführbarer SQL-Block **vor** dem Original (konservative Option — Original bleibt als Referenz)
4. Vor Action (b), (c), (d): jeweils `> **⚠ N/A am 2026-04-23**`-Warnblock

Keine Code-Änderungen. Sebastian führt das `UPDATE`-SQL manuell aus (siehe offen-Liste).

### Block 6 · v3.8.20 Version-Bump ✅

- `index.html` L1909: `APP_VERSION="3.8.19-supabase"` → `"3.8.20-supabase"`
- `sw.js` L1-2: Kommentar + `CACHE_NAME` → `"epkolar-v3.8.20"`
- `sw.js` hat **kein** `SW_VER`-Symbol — nur `CACHE_NAME`. Command-File-Hinweis "SW_VER" war inkorrekt; konservativ: nichts Neues einführen.
- Syntax+Bracket-Check grün, `node --check sw.js` OK.
- Tag lokal: `v3.8.20` mit Annotation.

---

## Abweichungen vom Command-File (transparent)

| Stelle | Command-File sagte | Reality | Entscheidung |
|---|---|---|---|
| Block 1 Helper-Insertion | "nach `const _fT`" | Ist `function _fT` | Nach der `function _fT`-Zeile eingefügt (gleicher Effekt) |
| Block 1 Anzahl Stellen | "2 ChefDashboard-Stellen" | 3 relevante Stellen | Alle 3 gefixt (im Skip-Limit ≤5) |
| Block 4 `_fT`-Signatur | `_fT(ms, fetch())` | `_fT(init, ms)` | Block SKIP, Begründung dokumentiert |
| Block 6 sw.js | "`SW_VER`" | Symbol existiert nicht | Nur `CACHE_NAME` + Header-Kommentar bumped |

---

## Offen — Sebastian

- [ ] **Push**: `git push origin main && git push origin v3.8.20` (CC hat noch nicht gepusht — wartet auf Freigabe oder autonome Push-Entscheidung am Ende des Handoffs; siehe Block 7 unten).
- [ ] **Orphan-UPDATE-SQL** (Block 5, live-verifiziert): in Supabase SQL-Editor ausführen
  ```sql
  BEGIN;
  UPDATE public.arbeitsscheine SET monteur = NULL WHERE monteur = '';
  SELECT COUNT(*) FROM public.arbeitsscheine WHERE monteur = '';    -- erwarte 0
  SELECT COUNT(*) FROM public.arbeitsscheine WHERE monteur IS NULL; -- erwarte 11
  COMMIT;
  ```
- [ ] **BASELINE_FIX_v3.8** (seit 20.04 offen): `sql/BASELINE_FIX_v3.8.sql` + `BASELINE_FIX_VERIFY_v3.8.sql` manuell auf Supabase
- [ ] **B-020 Login-Smoke** für 5 User: paschinger, barger, cracana, pinger, schmid
- [ ] **Chef-v2 Regression-Check** nach Deploy: Überfällig-Widget zeigt jetzt 0–8 AS statt 8+ mit 739728d?

## Offen — CC v3.8.21-Kandidaten

- **Iter-23 AS-Filter-Erweiterung**: L5008–5009 (`quickFilter==="ueberfaellig"`) hat dasselbe Sentinel-Problem wie Chef-Scope. Konservativ ausgeklammert (Command-File sagte ChefDashboard-Scope). Simpler `_hasTermin(t)`-Einzug.
- **`${z.dateiName}`** (L12765 FinkZeit-Print) ebenfalls ungeescapt — kleine Ergänzung zu R-6.
- Feature 12 **WhatsApp UI** (braucht Schema+Seeds-Deploy durch Sebastian vorher)
- **AS-Signature-Close-Flow** (Block 8 aus TODO_MORGEN)
- **Audit-Log-UI** (Block 13 aus TODO_MORGEN)

---

## Metrics

- Commits: **5** (+ Handoff-Commit)
- index.html: `() -2 {} 0 [] 0`, `syntax OK`
- sw.js: `node --check` OK
- Dauer: ca. 6 Min (autonomer Run)
