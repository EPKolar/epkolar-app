# EPKolar CC · 10h-PLAN v3.8.18 → v3.8.19
# =========================================
# STARTZEIT: NOW. BUDGET: 8-10h. AUTONOM.
# REPO: T:\03_Repos\epkolar-app (main, HEAD ≥ e6c9498)
# PHILOSOPHIE: "Nicht übertreiben und ehrlich bleiben." — Sebastian 19.04.2026

---

## WARUM DIESER PLAN ANDERS IST ALS DER VORGÄNGER

Ein Claude-Chat hat am 19.04 Nacht-2 Chrome-MCP gegen Supabase gefahren und **echte Baseline-Daten** geholt — keine Vermutungen mehr. Das hat 3 Konsequenzen:

1. **B-021 ist CLOSED** per Business-Entscheidung (Status Quo). Details: `B021_DECISION_19042026_NACHT2.md`. Kein Rebuild, kein Owner-Check-RLS.
2. **Smoke-Basis 0-2 ist grün** (DB_VER=7, APP_VERSION v3.8.18, `_curUser`/`_b017check`/`_selfTest` alle PASS).
3. **8 Baseline-Sektionen sind durchgelaufen** — echte Zahlen siehe unten. Block C/D aus dem vorigen Plan wird dadurch deutlich entlastet.

### Die echte DB-Baseline (Stand 19.04 Nacht-2)

🟢 **OK:**
- 45 Tabellen, alle RLS enabled, alle mit Policies (CC hatte Gaps vermutet — keine da)
- users.username UNIQUE ✅
- supplier_articles(supplier_id, art_nr) UNIQUE ✅
- 3 FKs sauber mit NOT NULL (bautagebuch/material_items/material_orders → projects)
- 0 echte Duplikate irgendwo
- 0 NULL-Werte in App-kritischen Spalten
- 0 Orphan-Rows in photos/time_entries
- Performance <130 ms auf allen 9 perfBench-Queries

🟡 **Idempotent fixbar:**
- `users.email` kein UNIQUE (aber 0 Dupes)
- `arbeitsscheine.juprowa_id` kein UNIQUE (aber 0 Dupes)
- 0 CHECK-Constraints im Schema (keine Enum-Validierung)
- 5 App-kritische Spalten nullable (aber 0 NULL-Werte)

🔴 **Echter Daten-Gap (Entscheidung nötig):**
- **12 Arbeitsscheine mit `monteur`-Wert der auf keinen Worker zeigt** (historische Daten, vermutlich gelöschte Monteure wie u4)

ℹ️ **Korrektur:** `login_audit`-Tabelle existiert gar nicht. CC hatte sie als "Wachstum unbekannt" gelistet — der Tabellenname ist falsch.

---

## KERNREGELN (HART)

- Commit nach JEDEM Block. Push nach JEDEM Commit.
- Bracket-Baseline: `() delta=-2` (Template-Literal False-Positive bleibt), `{}=0`, `[]=0`.
- `node --check` bestehen. Sonst Block revertieren.
- Juprowa Phase-1-Pull (`_juprowaSanitize`, `_juprowaPull`) NIE anfassen.
- `_authRetry` Core NICHT anfassen (`_sbUploadFile` ist in v3.8.15 bereits wrapped).
- DB-Migration → SQL-File unter `sql/` + HANDOFF-Eintrag. NUR wo explizit gesagt selbst ausführen.
- Bei Unsicherheit: konservativ > elegant. Liegen lassen > Raten.
- Kein fake-Bumping. NOT-A-BUG ist ein legitimes Ergebnis.

---

## PRIORISIERUNG

| Prio | Blocks | Budget | Netto-Thema |
|---|---|---|---|
| **P0** | A, B | 60 min | Baseline-Fixes + 12-Orphans-Entscheidung |
| **P1** | C, D, E | 300 min | Chef-Seite v2 + RLS-Reconcile + Mobile-UX |
| **P2** | F, G | 120 min | Smoke-Rest + Logging-Cleanup |
| **P3** | H, I | 120 min | Index-Effect + Testkonzept v5.0 |
| **FINAL** | Bump | 30 min | v3.8.19 |
| **Summe** | | **630 min = 10.5h** | |

P0+P1 (Muss) = 6h. P0+P1+P2 (Soll) = 8h. Plus P3 = 10h. Final extra 30 min.

---

## BLOCK 0 · PRE-FLIGHT (15 min, implizit, nicht im Budget)

```powershell
cd T:\03_Repos\epkolar-app
git fetch origin main
git reset --hard origin/main
git log -3 --oneline
# HEAD muss e6c9498 oder neuer zeigen.

node sql/_check_brackets.js | Tee-Object -FilePath baseline_v3.8.19_start.txt
node sql/_check_syntax.js
(Get-Item index.html).Length
```

Init `HANDOFF_NACHT_v3.8.19.md` mit Timestamp + Start-HEAD.
Commit: `"v3.8.19-wip pre-flight"`

---

# P0 · KRITISCH (60 min)

## BLOCK A · BASELINE-FIXES SELEKTIV (30 min)

### A.1 Datei `sql/BASELINE_FIX_v3.8.sql` erstellen

```sql
-- BASELINE-FIX v3.8.19 — Idempotent, 0 Datenrisiko, nur DDL
-- FIX 1: UNIQUE auf users.email (0 Dupes aktuell → sicher)
CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique_idx
  ON public.users (lower(email))
  WHERE email IS NOT NULL AND email <> '';

-- FIX 2: UNIQUE auf arbeitsscheine.juprowa_id (0 Dupes → sicher)
CREATE UNIQUE INDEX IF NOT EXISTS arbeitsscheine_juprowa_id_unique_idx
  ON public.arbeitsscheine (juprowa_id)
  WHERE juprowa_id IS NOT NULL AND juprowa_id <> '';

-- FIX 3: CHECK-Constraints auf Enums (NOT VALID, schützt neue Rows)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_scheinstatus_chk') THEN
    ALTER TABLE public.arbeitsscheine ADD CONSTRAINT arbeitsscheine_scheinstatus_chk
      CHECK (scheinstatus IS NULL OR scheinstatus IN ('neu','bearbeitung','abgeschlossen','storniert')) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_prioritaet_chk') THEN
    ALTER TABLE public.arbeitsscheine ADD CONSTRAINT arbeitsscheine_prioritaet_chk
      CHECK (prioritaet IS NULL OR prioritaet IN ('niedrig','mittel','hoch','kritisch')) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='users_role_chk') THEN
    ALTER TABLE public.users ADD CONSTRAINT users_role_chk
      CHECK (role IS NULL OR role IN ('admin','buero','monteur','projektleiter')) NOT VALID;
  END IF;
END$$;

-- FIX 4: NOT NULL auf kritischen Spalten (0 NULLs aktuell → sicher)
-- NICHT arbeitsscheine.monteur (12 Orphans — Block B)
-- NICHT photos.uploaded_by (Backfill-Status unklar)
DO $$
BEGIN
  IF (SELECT count(*) FROM public.photos WHERE project_id IS NULL) = 0 THEN
    ALTER TABLE public.photos ALTER COLUMN project_id SET NOT NULL;
  END IF;
  IF (SELECT count(*) FROM public.time_entries WHERE worker_id IS NULL) = 0 THEN
    ALTER TABLE public.time_entries ALTER COLUMN worker_id SET NOT NULL;
  END IF;
  IF (SELECT count(*) FROM public.time_entries WHERE project_id IS NULL) = 0 THEN
    ALTER TABLE public.time_entries ALTER COLUMN project_id SET NOT NULL;
  END IF;
EXCEPTION WHEN others THEN
  RAISE NOTICE 'NOT NULL fix skipped: %', SQLERRM;
END$$;
```

### A.2 Verify-Query `sql/BASELINE_FIX_VERIFY_v3.8.sql`

```sql
SELECT 'users_email_unique' as check_item, EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='users_email_unique_idx') as applied
UNION ALL SELECT 'arbeitsscheine_juprowa_id_unique', EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='arbeitsscheine_juprowa_id_unique_idx')
UNION ALL SELECT 'arbeitsscheine_scheinstatus_chk', EXISTS(SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_scheinstatus_chk')
UNION ALL SELECT 'arbeitsscheine_prioritaet_chk', EXISTS(SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_prioritaet_chk')
UNION ALL SELECT 'users_role_chk', EXISTS(SELECT 1 FROM pg_constraint WHERE conname='users_role_chk')
UNION ALL SELECT 'photos_project_id_notnull', (SELECT attnotnull FROM pg_attribute WHERE attrelid='public.photos'::regclass AND attname='project_id')
UNION ALL SELECT 'time_entries_worker_id_notnull', (SELECT attnotnull FROM pg_attribute WHERE attrelid='public.time_entries'::regclass AND attname='worker_id')
UNION ALL SELECT 'time_entries_project_id_notnull', (SELECT attnotnull FROM pg_attribute WHERE attrelid='public.time_entries'::regclass AND attname='project_id');
```

### A.3 CC-Aktion
CC baut beide Dateien, checkt SQL-Syntax (keine DB-Ausführung möglich — CC hat keine DB-Schreibrechte), dokumentiert in HANDOFF dass **Sebastian selbst ausführen muss**.

Commit: `"v3.8.19-wip BASELINE_FIX_v3.8 (4 idempotent fixes, manual run required)"`

---

## BLOCK B · 12-ORPHAN-ARBEITSSCHEINE (30 min)

### B.1 Details-Query

```sql
SELECT a.id, a.nummer, a.monteur, a.scheinstatus, a.kunde_name, a.created_at
FROM public.arbeitsscheine a
WHERE a.monteur IS NOT NULL 
  AND NOT EXISTS(SELECT 1 FROM public.workers WHERE id = a.monteur)
ORDER BY a.created_at DESC;
```

### B.2 Kategorisieren
Für jede der 12 Rows: Leerstring '' oder Value? Ex-Worker (z.B. "w4" = historischer u4)? Juprowa-Monteur-Code ohne worker-Match?

### B.3 Drei Aktionen (CC entscheidet anhand B.2)
- **(a)** Alle Leerstrings → UPDATE SET monteur=NULL
- **(b)** Gelöschter Worker → worker mit aktiv=false neu anlegen
- **(c)** Gemischt → Sebastian einbinden

Output: `sql/B_12_ORPHANS_ANALYSIS.md` mit Liste + Kategorie + Empfehlung + SQL-Staging (NICHT ausführen).

Commit: `"v3.8.19-wip 12-orphan-arbeitsscheine analysis (decision pending)"`

---

# P1 · MUSS (300 min)

## BLOCK C · CHEF-SEITE v2 (150 min) · HIGH-VALUE

Chef-Seite v1 hat: KPI-Kacheln, Auslastung-Woche, Projekt-Ampeln, Überfällig-Liste.
Sebastian: "besser werden, aber nichts doppelt was ich schon sehe."

### C.2 · Sorgenkind-Widget (70 min) — NEU zwischen Projekt-Ampeln und Überfällig-Liste
```
🚨 Handlungsbedarf
├── AS ohne Monteur zugewiesen: N
├── AS ohne Termin: N
├── Juprowa Push-Stau (push_pending=true): N
├── Projekt ohne Aktivität >14 Tage: [Namen]
└── Monatsabrechnung nicht freigegeben: [Namen mit worker_id resolve]
```
Datenbasis: `arbeitsscheine WHERE monteur IS NULL OR ''`, `WHERE termin IS NULL AND scheinstatus NOT IN (...)`, `WHERE push_pending = true`, `projects` vs activity_log 14d, `monatsabrechnungen WHERE NOT freigegeben AND jahr=2026`.

### C.3 · Trend-Pfeile neben KPI-Kacheln (50 min)
Jede der 5 Kacheln bekommt ↑/↓ + Diff zur Vorwoche unten. Offene/Überfällig ↑ = rot, ↓ = grün. Aktive Projekte / Monteure-heute: kein Trend (zu volatil).

Beispiel-Query:
```sql
WITH diese_kw AS (SELECT count(*) c FROM arbeitsscheine WHERE scheinstatus NOT IN ('abgeschlossen','storniert')),
     letzte_kw AS (SELECT count(*) c FROM arbeitsscheine 
                   WHERE created_at < date_trunc('week', now()) 
                     AND (abschluss_datum IS NULL OR abschluss_datum > date_trunc('week', now()))
                     AND scheinstatus NOT IN ('abgeschlossen','storniert'))
SELECT (SELECT c FROM diese_kw) - (SELECT c FROM letzte_kw) as delta;
```

### C.4 · Nächste-Woche-Preview (30 min) — NEUE Sektion am Ende
```
📅 Nächste Woche
├── Geplante AS: N
├── Abwesend: [Namen aus absences von/bis in next week]
└── Fahrzeuge mit Service/Pickerl fällig in 14 Tagen: N  ← Aggregate-Count, KEINE Detail-Liste
```

### C.5 Test
- Mobile-Viewport iPhone 12
- Permissions: Chef-Seite nur für admin (NICHT monteur/buero)
- Alle neuen Queries <200 ms

Commit: `"v3.8.19-wip feat(chef): v2 — Sorgenkind-Widget + Trend-Pfeile + Nächste-Woche-Preview"`

---

## BLOCK D · RLS-RECONCILE DOKU (60 min) · LIGHT

Status schon verifiziert: 45 Tabellen, alle RLS+Policies. CC muss nur dokumentieren.

```sql
SELECT c.relname as table_name,
  (SELECT count(*) FROM pg_policy WHERE polrelid = c.oid) as policy_count,
  (SELECT string_agg(polname, ', ' ORDER BY polname) FROM pg_policy WHERE polrelid = c.oid) as policies
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r'
ORDER BY c.relname;
```

Output: `sql/RLS_RECONCILE_v3.8.md` — Matrix pro Tabelle: policy_count, policies, intended_role_pattern (aus App-Code), verdict OK/REVIEW. **photos als bewusst permissiv markieren** (B-021 Business-Entscheidung, nicht als Finding).

Commit: `"v3.8.19-wip Block10 RLS-reconcile 45-tables documented (0 gaps)"`

---

## BLOCK E · MOBILE-UX TOUCH-TARGETS (90 min)

Selftest zeigt 14 too-small Touch-Targets + 1 horizOverflow (Desktop-Viewport). In iPhone 12 (390×844) mehr. Chrome DevTools Device-Toolbar → iPhone 12 → `await window._selfTest()` erneut.

### E.3 Global CSS in `<style>`:
```css
@media (pointer: coarse), (max-width: 768px) {
  button, [role="button"], .clickable, a.btn, 
  input[type="checkbox"], input[type="radio"], input[type="submit"] {
    min-height: 44px; min-width: 44px;
  }
  .icon-btn, button.icon-only { padding: 10px; }
}
```
Plus gezielte Fixes für Top-5 kritischste Stellen.

### E.4 Verify
- `_selfTest()` iPhone-Viewport: `tooSmallTouch` <5
- Screenshots `docs/mobile_ux_v3.8.19_before.png` / `_after.png`

Commit: `"v3.8.19-wip Block13 mobile touch-targets + global 44px media rule"`

---

# P2 · SOLL (120 min)

## BLOCK F · SMOKE-REST (60 min)

Schon grün (Claude Nacht-2): DB_VER=7, APP_VERSION, _curUser, _b017check, _selfTest.

### Was CC noch smoken muss:

**4 UI-Fixes visuell (v3.8.0):**
1. Mitarbeiter-Dropdown: 9 Einträge (nicht 18)
2. Monatsabrechnung-Kachel: Namen (nicht nur Zahl)
3. 38,5h-Auslastung: 38,5h = 100% (nicht 96,25%)
4. Riedmann-Nav: `riedmann` Login → nur Monteur-Tabs

**Photos-Upload (B-021 Status Quo):**
1. paschinger/test1234 Login (falls GoTrue fail: auf schober ausweichen)
2. AS → Foto aufnehmen → POST 201 Created
3. `SELECT uploaded_by FROM photos ORDER BY uploaded_at DESC LIMIT 1` = 'w1'
4. Cross-User-Sichtbarkeit IST NICHT TEIL DES TESTS (B-021 Status Quo)

**Cross-User-Cleanup (v3.8.10/11):**
1. User-A Timer → Logout verwerfen
2. User-B Login
3. Console: `epk_timer===null`, `epkolar_user=User-B`, `_syncDiag().total===0`
4. IDB: user-data-Stores leer oder nur User-B-Daten

**Login-Regression:** admin (✅ schon), schober, riedmann, lindhuber. 5 nie-eingeloggte (paschinger/barger/cracana/pinger/schmid) = Sebastian-Aufgabe, OUT-OF-SCOPE.

Output: `SMOKE_LOG_v3.8.18.md` mit ✅/❌ pro Test + Notizen.
Commit: `"v3.8.19-wip smoke v3.8.18 rest: UI-fixes + photos-upload + cross-user + login"`

**Rot-Regel:** Irgendwo rot → v3.8.19-wip-hotfix nur für diese Stelle, dann Block G.

---

## BLOCK G · LOGGING + SILENT-CATCH (60 min)

### G.1 Logging-Cleanup (30 min)
```powershell
$before = (Select-String -Path index.html -Pattern "console\.log" | Measure-Object).Count
```
DEBUG-Flag:
```javascript
const DEBUG = (typeof window !== 'undefined' && window.DEBUG === true) || localStorage.getItem('DEBUG')==='1';
const dlog = (...a) => { if (DEBUG) console.log(...a); };
```
Max 50 Stellen hinter dlog(). `console.warn`/`console.error` bleiben. Bei >100: nur hochfrequente (Sync/Auth/API-Dumps), Rest als v3.8.20-followup.

### G.2 Silent-Catch-Audit (30 min)
CC hat 3x den gleichen Fehler gefixt (v3.8.7/8/18). Global-Scan:
```powershell
Select-String -Path index.html -Pattern 'catch\s*\([^)]*\)\s*\{\s*\}' -Context 2,1
Select-String -Path index.html -Pattern '\.catch\(\s*\(?\s*[a-z_]*\s*\)?\s*=>\s*\{\s*\}\s*\)' -Context 2,1
Select-String -Path index.html -Pattern 'supabase\.auth\.(signUp|updateUser|resetPassword|setSession|admin)' -Context 3,5
```
Output: `sql/SILENT_CATCH_AUDIT.md` mit File:Line, Kontext, Vorschlag. **Nicht pauschal fixen** — nur dokumentieren, Sebastian genehmigt Einzelfixe.

Commit: `"v3.8.19-wip logging-cleanup + silent-catch audit"`

---

# P3 · KANN (120 min, nur wenn nach 8h noch Zeit)

## BLOCK H · INDEX-EFFECT (60 min)
Claude-Nacht-2 perfBench: alle 9 Queries <130 ms → Low-Priority.
```sql
SELECT indexname, tablename FROM pg_indexes 
WHERE schemaname='public' AND indexname NOT LIKE '%_pkey' AND indexname NOT LIKE '%_unique_idx'
ORDER BY tablename, indexname;
```
Top-7: `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` mit + ohne Index (`SET enable_indexscan = off;`). Delta + Speedup. Verdict KEEP/REVIEW/DROP.

Output: `sql/INDEX_EFFECT_v3.8_RESULTS.md`. Bei <2x Speedup kleine Tabellen: REVIEW/DROP bei Wachstum. Keine Schönrechnerei.
Commit: `"v3.8.19-wip Block9 index-effect real EXPLAIN-ANALYZE"`

## BLOCK I · TESTKONZEPT v5.0 (60 min)
Abgleich v5.0 mit Session 19 + Nacht-2-Findings (B-021, B-020 4/9, _selfTest-Baseline, Mobile-Count, 12-Orphans). Merge falls nicht da. v4.5-DELTA archivieren falls v5.0 enthält.
Reality-Check: welche Tests tatsächlich gelaufen? Ehrlich listen.
Commit: `"v3.8.19-wip Testkonzept v5.0 + Nacht-2-Findings merge"`

---

# FINAL · v3.8.19 BUMP (30 min)

### FINAL.1 Voraussetzung
Mindestens P0+P1 komplett (6h). Sonst: kein Bump, `v3.8.18.x-wip` bleibt.

### FINAL.2 Bump (4 Strings)
```javascript
const APP_VERSION = '3.8.19-supabase';
const SW_VER = 'epkolar-3.8.19-supabase';
const CACHE_NAME = 'epkolar-3.8.19-supabase';
```
+ `sw.js` entsprechend.

### FINAL.3 HANDOFF_NACHT_v3.8.19.md Endabschnitt

```
## EHRLICHKEITS-BILANZ

### Was gemacht wurde (wirklich)
- Block 0, A, B, C, D, E, F, G, (H), (I): status pro Block

### Was NICHT gemacht wurde
- (ehrlich auflisten)

### Zeit: Plan 8-10h / Ist Xh

### Kritische Follow-ups für Sebastian
1. BASELINE_FIX_v3.8.sql auf Supabase laufen lassen (P0!)
2. B_12_ORPHANS_ANALYSIS.md reviewen + Entscheidung
3. B-020 Login-Smoke 5 User (paschinger/barger/cracana/pinger/schmid)
4. sync_supplier Edge Function CLI-Deploy
5. FinkZeit-API falls gewünscht: Typ/Endpoints/Auth/Schema/Richtung

### Follow-ups CC v3.8.20
1. Chef-Seite Umsatz-Widget (braucht FinkZeit-API)
2. Feature 12 WhatsApp
```

### FINAL.4 Commit + Tag
```powershell
git add index.html sw.js HANDOFF_NACHT_v3.8.19.md
git commit -m "v3.8.19 full bump: chef-v2 + baseline-fixes + RLS-doc + mobile-UX + smoke + logging"
git push
git tag v3.8.19
git push --tags
```

### FINAL.5 QA
Reload `?t=NEW` → Version `3.8.19-supabase`. Chef-Seite neue Widgets rendern.

---

# ABSCHLUSS-REGEL

Keine Embellishments. Nur echte Findings. NOT-A-BUG ist legitim.
P0+P1 first. P2 nur wenn P0+P1 sauber. P3 nur wenn echt Zeit.

---

*Ende Plan v3.8.18→v3.8.19.*
