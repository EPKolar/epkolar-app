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
