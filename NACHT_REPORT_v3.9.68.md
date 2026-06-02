# NACHT_REPORT v3.9.68 — SPRINT 48 Gewerk-Filter (Sebastian-Bug-Fix)

## SPRINT 48 — v3.9.68 Gewerk-Filter (Sebastian-Bug-Fix)

### Bug-Report (Sebastian)
> "elektriker sieht immer noch sanitär und heizung bei materialbestellung"

### Root-Cause
`renderWarenkorb` (L12374) liest `epk_user_gewerk` aus `localStorage` mit Default `"beide"` (= alles anzeigen). Das v3.8.49 Logout-Cleanup (L5021) entfernt diesen Key explizit beim Logout (Cross-User-Leak-Fix). → Nach jedem Login eines Monteurs ist der Key **unset** → Default `"beide"` → Elektriker sieht Sanitär+Heizung+Klima.

Der bestehende Settings-Page-Dropdown (L14854) erlaubt manuelle Auswahl, aber Monteure müssen das aktiv anklicken — Sebastian-Bug ist ein **fehlender Default**.

### Fix (3-stufige Priorität)
**index.html L12374-12387** — neue Auto-Detect-Kaskade in `renderWarenkorb()`:
1. **localStorage `epk_user_gewerk`** (höchste Prio, expliziter User-Wunsch)
2. **`curUser.gewerk`** (DB-column override, Forward-Compat für SQL-Migration)
3. **role-based**: admin/projektleiter/buero → `"beide"`, sonst → `"elektro"` (EP Kolar primär)

Filter erweitert auch um `"sanitaer"` und `"heizung"` als eigenständige Werte (vorher nur `"installateur"`-Sammelbegriff).

### Visual-Indicator
Badge oben in VMaterial Warenkorb-Tab:
- `"🔧 Anzeige: ⚡ Elektro · 3/12 Kataloge (auto)"` für auto-detected
- `"🔧 Anzeige: ⚡ Elektro · 3/12 Kataloge"` für explizit gewählt
- `title`-Hover erklärt: "Gewerk auto-erkannt aus Rolle · Einstellungen → Mein Profil zum Ändern"

Admin/Buero/PL sehen weiterhin **alle** Kataloge (kein Badge sichtbar) — Sebastian-Wunsch: "Admin sieht alles".

### Filter-Logic (vollständig)
```js
const _gp =
  localStorage.getItem("epk_user_gewerk")   // 1. expliziter Override
  || curUser.gewerk                          // 2. DB-Spalte (Sebastian-Action SQL)
  || (isAdminLike ? "beide" : "elektro");    // 3. role-based fallback

_kataAllowed(g):
  beide      → true
  elektro    → g==="elektro" || g==="allgemein"
  installateur → g in {sanitaer, heizung, klima, allgemein}
  sanitaer   → g in {sanitaer, heizung, klima, allgemein}
  heizung    → g in {heizung, sanitaer, klima, allgemein}
```

### SQL-Migration (Sebastian-Action)
**File:** `sql/migrate_user_gewerk_v3968.sql`
- `ALTER TABLE users ADD COLUMN IF NOT EXISTS gewerk text` (idempotent)
- `ALTER TABLE workers ADD COLUMN IF NOT EXISTS gewerk text` (conditional, falls Tabelle existiert)
- Backfill: admin/projektleiter/buero → `"beide"`, monteur → `"elektro"`, Lagerleitung → `"beide"`
- Check-Constraint: gewerk IN ('elektro','sanitaer','heizung','installateur','klima','beide','allgemein')
- Rollback-Block dokumentiert (optional)
- **Status: DRAFT — Sebastian-Action via Supabase SQL-Editor**

### Verify
- **Bracket pre/post:** `() -2 / {} 0 / [] 0` (identisch zu Baseline)
- **node --check** inline-script-bundle (1.84MB): ✓ OK
- **pytest:** 502/502 ✓ (160s)

### Files
- `index.html` (L15 SW_VER, L2242 APP_VERSION, L12374-12387 Filter-Logic, L12383 Badge)
- `sw.js` (L1+L2 v3.9.68)
- `sql/migrate_user_gewerk_v3968.sql` (NEW — DRAFT)
- `NACHT_REPORT_v3.9.68.md` (this)

### Constraints Honored
- ✓ Kein `_silentReAuth`/`_authRetry`/`_ensureAuth`/`_mapBody`/`TEXT_JSON_FIELDS`/SyncQueue/sw.js-Cache-Strategie/Juprowa/OFFA/`_OFFPW.verify` touched
- ✓ Keine Berechnungs-Helpers angefasst
- ✓ Hooks-Order unverändert (Edit innerhalb existierender `renderWarenkorb` function)
- ✓ Material-Anforderung Workflow intakt (`sendOrder` nutzt `catalogs` weiter, nicht `_filteredCatalogs` — kein Funktions-Regress, nur UI-Filter)
- ✓ Bracket-Baseline identisch
- ✓ Kein force-push

### Sebastian-Actions
1. **SQL-Migration apply:** `sql/migrate_user_gewerk_v3968.sql` via Supabase SQL-Editor
2. **Smoke-Test Elektriker-Login:** Norbert/Sorin/Ian → Material → Warenkorb → erwartet: Mepla/Silent-PP/Mapress NICHT sichtbar (sanitaer/heizung versteckt)
3. **Smoke-Test Admin-Login:** Sebastian → Material → Warenkorb → erwartet: alle Kataloge sichtbar, kein Badge
4. Optional: Spezifischen Installateur-User in DB anlegen → `UPDATE users SET gewerk='installateur' WHERE username='...'`
