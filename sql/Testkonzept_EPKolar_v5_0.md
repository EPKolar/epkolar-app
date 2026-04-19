# Testkonzept EPKolar — v5.0
**Stand:** 18.04.2026 · **App-Version:** v3.5.144 · **Vorgänger:** v4.0

## Was ist neu gegenüber v4.0

- Neue Kategorie **TC-M** (Mutex-Serialisierung SQ/PhotoQ)
- Neue Kategorie **TC-T** (Timezone local-date-string TZ-Fix v3.5.108/109)
- Neue Kategorie **TC-J** (JWT-Shape-Validation v3.5.137/142)
- Neue Kategorie **TC-I** (IndexedDB-Migration non-destructive v3.5.133)
- Erweiterte Regression-Tests für alle CRITICAL-Bugs der Session v3.5.108-144
- Automatisierte `_runAllTests()`-Integration (im Code)

## TC-M: Mutex-Serialisierung (v3.5.139-141)

### TC-M-01 — SQ.push Lost-Update
**Vorbedingung:** App geladen, gültiger Login
**Test:**
```js
await SQ.clear();
await Promise.all(Array.from({length:100},(_,i)=>SQ.push({url:'/api/t',method:'POST',body:{n:i}})));
const q=await SQ.getAll();
console.assert(q.length===100,'Expected 100, got '+q.length);
```
**Pass:** `q.length === 100` ✓ (bevor v3.5.139 wären 30-70 verloren gegangen)

### TC-M-02 — PhotoQ.add Lost-Update
Analog mit 50 parallelen adds.

### TC-M-03 — Concurrent Remove + Add
```js
await SQ.clear();
await SQ.push({url:'/a',method:'POST'});
await SQ.push({url:'/b',method:'POST'});
const q1=await SQ.getAll();
await Promise.all([SQ.remove(q1[0].id), SQ.push({url:'/c',method:'POST'})]);
const q2=await SQ.getAll();
console.assert(q2.length===2 && q2.some(x=>x.url==='/c'),'Mutex serial should leave [/b, /c]');
```

## TC-T: Timezone local-date-string (v3.5.108/109)

### TC-T-01 — _ymd local CET
```js
console.assert(_ymd(new Date(2026,0,4))==="2026-01-04", 'Should be local Jan 4, not UTC Jan 3');
console.assert(_ymd(new Date(2026,5,15))==="2026-06-15", 'Should be local Jun 15');
```

### TC-T-02 — kwD local days
```js
const kw16=kwD(2026,16);
console.assert(kw16[0]==="2026-04-13", 'Monday of KW16 2026 should be April 13 local');
```

### TC-T-03 — td2 matches form-date-input
```js
// form-date-input liefert "2026-04-18" (local). td2() sollte matchen.
const today=new Date().toISOString().split('T')[0];  // alt
const localToday=td2();                               // neu
// In der Nacht um 00:30 CET würden die DIFFERENT sein:
// - alt: "2026-04-17" (UTC-Vortag)
// - neu: "2026-04-18" (local heute)
```

## TC-J: JWT-Shape-Validation (v3.5.137/142)

### TC-J-01 — Valid JWT akzeptiert
```js
console.assert(_isJwtShape(SUPABASE_KEY)===true, 'SUPABASE_KEY must be valid JWT');
```

### TC-J-02 — Non-JWT abgelehnt
```js
console.assert(_isJwtShape("supabase-session")===false);
console.assert(_isJwtShape("bcrypt-fallback")===false);
console.assert(_isJwtShape("")===false);
console.assert(_isJwtShape(null)===false);
console.assert(_isJwtShape("a.b.c")===false, 'too short to be real JWT');
```

### TC-J-03 — _sbH Fallback bei invalid Token
```js
const bakup=_authToken;
_authToken="garbage";
const h=_sbH();
console.assert(h.Authorization==="Bearer "+SUPABASE_KEY, 'Should fall back to anon-key');
_authToken=bakup;
```

## TC-I: IndexedDB-Migration non-destruktiv (v3.5.133)

### TC-I-01 — Upgrade preserves stores
**Manueller Test (nicht via Console automatisierbar):**
1. Vor Deploy: `await ODB.save("testStore","value1")`
2. Deploy neue Version mit `DB_VER=7`
3. Nach Reload: `await ODB.load("testStore")` → muss `"value1"` liefern
**Pass:** Wert bleibt nach Version-Bump erhalten

### TC-I-02 — Neue Stores werden angelegt
1. `DB_VER=7` mit STORES = [...old, "newStore"]
2. Nach Upgrade: `await ODB.save("newStore","x")` → kein Fehler
3. `await ODB.load("newStore")` → `"x"`

## Bestehende Testfälle (von v4.0, unverändert)

- TC-A (Auth) 1-5
- TC-R6 (B-006) — ✅ CLOSED
- TC-R7 (B-007) — ✅ CLOSED (22 Policies verifiziert)
- TC-H (Home/Timer) 1-5
- TC-AS (Arbeitsscheine) 1-8
- TC-P (Projekte) 1-3
- TC-S (Search) 1-3
- TC-U (Urlaubsantrag) 1-5
- TC-F (Fahrtenbuch) 1-5
- TC-O (Offline/Sync) 1-4
- TC-CD (ChefDashboard) 1-3
- TC-X (Excel) 1-3
- TC-N (Null-Safety-Regression-Pack) 1-4

## Smoke-Test-Checkliste v5 (nach jedem Deploy)

- [ ] `APP_VERSION` in Console zeigt erwartete Version
- [ ] `SW_VER` matched
- [ ] Login admin + schober funktioniert
- [ ] AS-Liste lädt (Admin=54, Schober<54 via B-007)
- [ ] OfflineBanner: Network-Offline → sichtbar, Online → weg
- [ ] Timer Start/Stop speichert time_entry mit `hours ≥ 0`
- [ ] `_runAllTests()` Console — 15+ Tests grün
- [ ] **NEU v5:** Alle TC-M/T/J-Tests oben grün
- [ ] Service-Worker-Controller != null
- [ ] AS-PDF-Export → keine "undefined" Strings
- [ ] OFFA-Export → keine XSS in mitarbeiterName
- [ ] Foto-Download → Datei erscheint (iOS Safari-Test!)

## Regressions-Pack (neu in v5 via Code)

Siehe `_runAllTests()` Erweiterung in v3.5.145 (nächste Iter 10):
- `_test_ymd_cet` — TC-T-01 automatisiert
- `_test_uuid_shape` — UUID-Format-Check
- `_test_jwt_shape` — TC-J-01/02 automatisiert
- `_test_sq_mutex` — TC-M-01 automatisiert
- `_test_idb_nondestructive` — TC-I-01 (semi-auto)
- `_test_timeout` — _fT AbortSignal fires

---

# v5.1 Merge · Session 19 + Nacht-2 + v3.8.19 (2026-04-19)

Dieser Abschnitt merged die Delta aus `Testkonzept_EPKolar_v4_4_DELTA.md` (Session 16/17/18)
und ergänzt die neuen Test-Anforderungen aus Session 19 + Nacht-2-Messung.

## TC-B: Business-Entscheidungen (Session 19)

### TC-B-021 · Photos Cross-User-Sichtbarkeit (Status Quo)
**Entscheidung**: Nicht fixen. Photos-RLS bleibt permissiv.
**Referenz**: `B021_DECISION_19042026_NACHT2.md`
**Nicht-Ziel**: Kein Test erwartet Cross-User-Isolation in photos.
**Ziel**: `uploaded_by` korrekt gesetzt (v3.8.12 captureAndQueue fix) → testbar.

### TC-B-020 · Login-Regression 4/9 User
**Stand**: 4 User testbar in CC-Scope (admin, schober, riedmann, lindhuber),
5 nie-eingeloggte paschinger/barger/cracana/pinger/schmid = Sebastian-Aufgabe OOF.
**Test**: `SMOKE_LOG_v3.8.18.md` Abschnitt 4.

## TC-C: Chef-Seite v2 (v3.8.19 Block C)

### TC-C-01 · Sorgenkind-Widget rendert
**Voraussetzung**: admin-Login, Chef-Tab sichtbar.
**Test**: Chef-Seite scrollen. Zwischen "Projekt-Ampeln" und "Kritisch überfällige AS"
erscheint gelbes "🚨 Handlungsbedarf"-Widget mit 5 Indikatoren.
**Pass**: Widget sichtbar mit ≥1 Indikator (wenn Prod-Daten Sorgenkinder haben).

### TC-C-02 · Trend-Pfeile an 3 KPI-Kacheln
**Test**: Chef-Seite KPI-Grid inspizieren.
**Pass**: Offene AS, Heutige AS, Überfällig zeigen ↑/↓ + Delta. Aktive Projekte + Monteure heute ohne Pfeil.

### TC-C-03 · Nächste-Woche-Preview am Ende
**Test**: Chef-Seite ganz nach unten scrollen.
**Pass**: Blaues "📅 Nächste Woche"-Widget mit Geplante AS / Abwesend (Namen) / Fahrzeuge fällig.

### TC-C-04 · Permissions Chef-only
**Test**: monteur-Login → Chef-Tab NICHT sichtbar. buero-Login → Chef-Tab NICHT sichtbar.
**Pass**: perm='_chef' nur für role='admin' (Line 4375).

## TC-S: Self-Test-Baseline (v3.8.18)

### TC-S-01 · _selfTest({mode:'quick'}) grün
**Test**: admin-Login → Console `await window._selfTest({mode:'quick'})`.
**Pass**: `summary.failed === 0`.

### TC-S-02 · _b017check leak-free
**Test**: `window._b017check()`.
**Pass**: `summary.leaked === 0` (admin-Debug-Helper sind nicht mehr auf window nach Logout).

### TC-S-03 · _s8Suite auth-flow
**Test**: `await window._s8Suite()`.
**Pass**: T-B020/T-107c/T-B021 alle grün, _selfTest mit echter role statt 'none'.

## TC-M-UX: Mobile Touch-Targets (v3.8.19 Block E)

### TC-M-UX-01 · 44px Minimum auf touch-Geräten
**Test**: DevTools Device-Emulation iPhone 12 → `await window._selfTest()`.
**Pass**: `results.mobile.tooSmallTouch < 5` (von 14 in Baseline).

### TC-M-UX-02 · CSS Global-Rule greift
**Test**: DevTools → Computed Styles auf beliebigem Button → `min-height: 44px`, `min-width: 44px`.
**Pass**: Beide Properties applied bei Viewport <768px oder pointer:coarse.

## TC-D: DB-Integrität (v3.8.19 Block A + B)

### TC-D-01 · BASELINE_FIX_v3.8 deployed
**Test**: Supabase SQL-Editor → `BASELINE_FIX_VERIFY_v3.8.sql` laufen lassen.
**Pass**: 8 Rows, alle `applied=TRUE`.

### TC-D-02 · 12 Orphan-Arbeitsscheine resolved
**Test**: Sebastian führt Details-Query aus `B_12_ORPHANS_ANALYSIS.md` aus + wählt Aktion pro Row.
**Pass**: Nach Aktion: `remaining_orphans = 0`.

### TC-D-03 · Keine neuen Dupes seit UNIQUE-Deploy
**Test**: `SELECT email, count(*) FROM users GROUP BY email HAVING count(*)>1;` — leer.
**Pass**: Leere Result-Menge. Analog für `arbeitsscheine.juprowa_id`.

## TC-CL: Cross-User-Cleanup (v3.8.19 nachgewiesen)

### TC-CL-01 · Logout cleart SQ + PhotoQ + ODB-Stores
**Test**: `SMOKE_LOG_v3.8.18.md` Abschnitt 3.
**Pass**: alle 4 Sub-Checks grün.

### TC-CL-02 · localStorage user-prefs cleart
**Test**: User A Login → `localStorage.setItem('epkolar_default_sb','GÜNTHER')` → Logout → User B Login → `localStorage.getItem('epkolar_default_sb')` === null.
**Pass**: Key gelöscht. Analog für `epk_autonotif_cd`, `epk_dash_vis`.

---

## Reality-Check · Was tatsächlich gelaufen ist (ehrlich, 2026-04-19 22:xx)

| Kategorie | Status |
|---|---|
| TC-M (Mutex) | ❓ nie gemessen seit v3.5.145-Plan — wurde `_runAllTests()` je erweitert? TBD Sebastian. |
| TC-T (Timezone) | ❓ same |
| TC-J (JWT-Shape) | ✅ implizit durch B-017 Tests + `_s8Suite` v3.6.7 |
| TC-I (IDB non-destructive) | ✅ v3.5.133 geprüft, v3.8.16 DB_VER Bump hat nix zerstört |
| TC-B-021 | ✅ Status Quo per Business-Entscheidung, kein weiterer Test |
| TC-B-020 | 🟡 4/9 User testbar (CC), 5 Sebastian-OOF |
| TC-C (Chef v2) | ✅ Code-deployed v3.8.19, visuelles Prüfen Sebastian-TODO |
| TC-S (Self-Test) | ✅ Nacht-2 grün |
| TC-M-UX | 🟡 CSS deployed, iPhone-Verify Sebastian-TODO |
| TC-D (DB-Integrität) | 🟡 SQL bereit, Deploy+Verify Sebastian-TODO |
| TC-CL (Cross-User) | ✅ Code-verified, Browser-Test Sebastian-TODO |

**Zusammenfassung**: Code-Level-Qualität hoch (✅ oder 🟡 Code-bereit), operationelle
Tests überwiegend Sebastian-Browser-Tasks. Kein bekannter ❌.

