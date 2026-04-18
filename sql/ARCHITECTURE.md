# EPKolar App Architecture — Developer Reference

**Current live version:** v3.5.144 · **Single-file React app:** ~15.300 Zeilen `index.html`

## Top-Level Globals (alle in `<script>`-Scope, funktionen hoisted)

### Supabase-Client-Layer
| Name | Datei-Zeile | Zweck |
|---|---|---|
| `SUPABASE_URL` | 292 | REST-API-Basis (`https://jiggujpruejkaomgxarp.supabase.co`) |
| `SUPABASE_KEY` | 298 | Anon-JWT (zeitlich begrenzt gültig bis 2036) |
| `SB_REST` | 294 | SUPABASE_URL + "/rest/v1" |
| `_SB_AUTH` | 302 | SUPABASE_URL + "/auth/v1" |

### Auth
| Name | Zeile | Typ | Zweck |
|---|---|---|---|
| `_authToken` | 300 | let string | Current access_token (JWT). Set via `_storeAuth`/`_restoreAuth`, nulled by `_sbAuthLogout`/`_silentReAuth`-fail |
| `_authRefreshToken` | 300 | let string | Current refresh_token |
| `_authRefreshTimer` | 300 | let number | setTimeout-ID für automatischen Refresh (min. 30s bevor Expiry) |
| `_authRefreshInflight` | 559 | let Promise | **Flight-Promise-Guard** (v3.5.112): parallele Refreshes teilen sich Promise |
| `_sbHLastRefreshAt` | 530 | let number | Throttle für proaktiven anon-JWT-Refresh in `_sbH()` |
| `_authFailShown` | 615 | let bool | Verhindert Toast-Spam bei 401-Kaskaden |
| `_isJwtShape(t)` | 606 | fn | **JWT-Shape-Validator** (v3.5.137): `t.split('.').length===3 && t.length>20` |

### HTTP-Helper
| Name | Zeile | Zweck |
|---|---|---|
| `_sbH(extra?)` | 532 | Headers-Object mit apikey + Bearer (Auto-Fallback auf SUPABASE_KEY wenn `_authToken` keine JWT-Shape). Auch `window._sbH` für Console |
| `_sbRH()` | 548 | Read-Headers mit Range |
| `_sbWH(prefer?)` | 549 | Write-Headers mit Prefer |
| `_fT(init, ms=30000)` | 611 | **Timeout-Wrapper** (v3.5.102): fügt `AbortSignal.timeout(ms)` in init, Feature-detect für ältere Browser |
| `_authRetry(fn)` | 599 | Führt `fn` aus, bei 401/403 → refresh + einmal retry |

### REST-Layer
| Name | Zeile | Scope | Methoden |
|---|---|---|---|
| `_sbGet/Post/Patch/Delete` | 777-813 | module | Low-level REST mit `_fT` Timeout + `_authRetry` |
| `_sbGetAnon` | 837 | module | Anon-only (B-006 nach Fix = immer []), mit Timeout |
| `_sbUpsert` | 793 | module | POST mit `resolution=merge-duplicates` |
| `_api.get/post/patch/delete` | 384-408 | module | Higher-level, ruft `_ensureAuth` + `_fT` + throws bei !ok |
| `window._ensureAuth` | 510 | global | Garantiert gültigen Token (refresh bei anon-JWT oder <5min exp) |

### Offline-Sync
| Name | Zeile | Zweck |
|---|---|---|
| `ODB.get/set/del/getAll/clear/save/load` | 1323-1331 | IndexedDB-Wrapper. DB-Handle gecacht (v3.5.101), non-destruktive Migration (v3.5.133) |
| `SQ.push/clear/remove/removeMany/count/getAll` | 1366-1390 | Offline-Action-Queue. **Shared Mutex `_serial()`** (v3.5.140) serialisiert alle Read-Modify-Write |
| `PhotoQ.add/remove/update/clear/count/getAll/flush` | 1393-1435 | Offline-Foto-Queue. Gleicher Mutex-Pattern. Flush hat zusätzlich `_flushing` Concurrency-Guard + Max-Retry (10) |
| `_translateAndExec` | 886 | Übersetzt alte `/api/xxx`-Paths auf Supabase REST |

### Utils
| Name | Zeile | Zweck |
|---|---|---|
| `_ymd(d)` | 2041 | **TZ-safe** (v3.5.108) — `YYYY-MM-DD` aus lokalen Date-Komponenten (NIE `toISOString.split`!) |
| `td2()` | 2043 | `_ymd(new Date())` für "heute" |
| `dk` | Alias auf `_ymd` |
| `fdt(d)` | 2044 | "YYYY-MM-DD" → "DD.MM.YYYY" (cached) |
| `uid()` | 2040 | Non-crypto-UUID (Date.now + Math.random slice) |
| `_uuid()` | 2044 | **RFC4122 v4** mit `crypto.getRandomValues` Fallback (v3.5.111, iOS <15.4 compat) |
| `_jp(s)` | 692 | Safe JSON.parse (string → parsed, object → pass-through, errors → []) |
| `_mapBody(obj)` | 639 | camelCase → snake_case für Supabase-Writes |
| `_dl(blob, filename)` | 2049 | **Mobile-safe Download** (v3.5.116) — anker zu DOM + 2s-delayed revoke |
| `_n(v, d?)` | 2093 | NaN-safe parseFloat + optional toFixed |

### Error-Handling
| Name | Zeile | Zweck |
|---|---|---|
| `window.__EP_ERRORS` | 1259 | Ring-Buffer (cap 50) mit allen JS-Errors |
| `window.onerror` | 1260 | Globaler Handler: logt in activity_log + __EP_ERRORS + User-Toast bei bekannten Mustern |
| `window.onunhandledrejection` | 1280 | Unhandled Promise-Rejections dito |
| `EpkErrorBoundary` | 15254 | React Error-Boundary wraps `<App>` mit Retry + Reload Buttons |

### Toast + Haptic
| Name | Zeile | Zweck |
|---|---|---|
| `window._showToast(msg, type?, duration?)` | 366 | Queue-basiert, Cap bei 20 Items (v3.5.135), Colors nach Type |
| `window.__toast` | 2973 | React-Toast (App-mount) — ruft addToast in React-Liste |
| `window._haptic.{success, error, warning, tap, confirm, tick}` | 315 | navigator.vibrate-Pattern |

### Timer
| Name | Zeile | Zweck |
|---|---|---|
| `window._epkTimer.{start, stop, get}` | 321 | Projekt-Timer in localStorage, `Math.max(0,...)` Schutz gegen Systemuhr-Rücksprung (v3.5.89) |

### Sync
| Name | Zeile | Zweck |
|---|---|---|
| `window._epkSyncInflight` | 3331 | **Sync Flight-Flag** (v3.5.138) — synchrones Guard zusätzlich zu syncStatus.syncing React-state |
| `window.__doSync` | 3386 | Globaler Entry-Point für SQ-flush, gesetzt von App-mount |

## Auth-Flow-Diagramm

```
User-Login                     GoTrue                       Storage
─────────────────────────────────────────────────────────────────────
API.login(user, pw)  ───>  RPC login_lookup ───>  users-row
        │                         │                    │
        └─> _sbAuthLogin ──────> /token?grant_type=password
                                       │
                                       ├─> 200 OK {access_token, refresh_token, expires_in}
                                       │       │
                                       │       └─> _storeAuth(d)   
                                       │            ├─ _authToken = d.access_token (JWT-Shape validated!)
                                       │            ├─ localStorage.epkolar_auth = {at,rt,exp}
                                       │            ├─ localStorage.epkolar_token = at
                                       │            ├─ localStorage.epkolar_refresh = rt
                                       │            └─ setTimeout(_sbAuthRefresh, expires_in-60s)
                                       │
                                       └─> 500 error (B-016 info@/office@ Scenario)
                                               │
                                               └─> bcrypt-Fallback (local hash-compare)
                                                   └─> localStorage.epkolar_token = 'bcrypt-fallback' (sentinel)

App-Reload
─────────
_restoreAuth()   // sync at module-init, line 612
    ├─ JSON.parse(localStorage.epkolar_auth)
    ├─ _isJwtShape(s.at) check
    │   ├─ Valid + not-expired → _authToken = s.at, setTimeout refresh
    │   ├─ Valid + expired → _sbAuthRefresh()
    │   └─ Invalid / empty → _silentReAuth (tries epkolar_gc creds)

Refresh (triggered by timer, API-401, or visibility)
────────────────────────────────────────────────────
_sbAuthRefresh()   // Flight-Promise-Guard: concurrent calls share one Promise
    ├─ POST /token?grant_type=refresh_token
    │    ├─ 200 → _storeAuth(d)
    │    └─ 4xx/5xx → _silentReAuth
    └─ 50ms TTL damit nachfolgende Calls den resolved Promise bekommen
```

## Sync-State-Maschine

```
Action (z.B. AS-Save)
    │
    ├─ setArbeitsscheine(prev=>...) // Optimistic UI update
    │
    └─ SQ.push({url,method,body})  // via _serial mutex
          │
          └─ ODB.save("syncQueue", [...old, newAction])
                │
                └─ setTimeout(__doSync, 1500ms) // Auto-batch-timer
                      │
                      └─ doSync() [if (navigator.onLine && _authToken)]
                            │
                            ├─ _epkSyncInflight = true  (v3.5.138 sync-guard)
                            │
                            ├─ Auth-Refresh-Preflight (if anon/near-expiry)
                            │
                            ├─ queue = SQ.getAll()
                            │
                            └─ for item of queue:
                                  try: _translateAndExec(item.url, method, body)
                                       └─ on success: okIds.push(id)
                                  catch(Auth-error): break [await re-login]
                                  catch(Network-error): break [retry on next online]
                                  catch(Other): item._retries++;
                                                if (retries >= 5): skipIds.push + push to syncQueueFailed
                            │
                            ├─ SQ.removeMany([...okIds, ...skipIds])
                            ├─ Update retry counters (v3.5.141 via _serial)
                            ├─ setSyncStatus(syncing:false, lastSync)
                            └─ finally: _epkSyncInflight = false

PhotoQ-Flush analog, aber:
    - Foto in Storage hochladen, URL erhalten
    - Separaten Photos-Row in DB anlegen
    - PhotoQ.remove(id)
    - retries >= 10 → skip permanent
```

## Mutex-Semantik (v3.5.139-141)

```js
SQ._mutex = Promise.resolve()       // initial resolved
SQ._serial(fn) {                    // jede read-modify-write-op
    SQ._mutex = SQ._mutex.then(fn)  // kettet an, serialisiert
                .catch(() => {})    // swallow damit keine Kette bricht
    return SQ._mutex                // caller kann awaiten
}
```

**Zweck:** Verhindert Read-Modify-Write Lost-Update-Race wenn 2+ parallele Push/Remove/Update/Clear-Calls die gleiche Queue anfassen.

**Gilt für:** `SQ.push`, `SQ.remove`, `SQ.removeMany`, `SQ.clear`, doSync's Retry-Update. Analog für PhotoQ.

**Gilt NICHT für:** `getAll`, `count` (read-only, keine Kontaminationsgefahr).

## Forbidden Zones

Per CLAUDE.md nicht zu modifizieren:
- **Juprowa Phase-1-Pull** (`_juprowaSync`, `_juprowaFetch_worksheets`, `_juprowaFresh`, Lines 1494-1662)
- Diese werden mit service_role-Key aus Supabase-Edge-Function betrieben und sind produktiv seit Monaten

## Race-Test-Anleitung

Nach Deploy in DevTools-Console:

```js
// Test 1: Mutex SQ.push — 100 parallele Pushes
(async()=>{
  await SQ.clear();
  await Promise.all(Array.from({length:100},(_,i)=>SQ.push({url:'/api/test',method:'POST',body:{n:i}})));
  const all=await SQ.getAll();
  console.log('Expected 100, got:',all.length);
})();

// Test 2: Mutex PhotoQ.add — 50 parallele Adds
(async()=>{
  await PhotoQ.clear();
  await Promise.all(Array.from({length:50},(_,i)=>PhotoQ.add({entityType:'test',entityId:i,dataUrl:'data:,'})));
  const all=await PhotoQ.getAll();
  console.log('Expected 50, got:',all.length);
})();

// Test 3: TZ-Shape — lokal date string matches
console.log(_ymd(new Date(2026,0,4))==="2026-01-04" ? 'TZ OK' : 'TZ BROKEN');

// Test 4: JWT-Shape
console.log(_isJwtShape(SUPABASE_KEY)===true ? 'JWT-Shape OK' : 'BROKEN');
console.log(_isJwtShape('bcrypt-fallback')===false ? 'Non-JWT rejected OK' : 'BROKEN');

// Test 5: _dl creates proper anchor
const b=new Blob(['test'],{type:'text/plain'});
_dl(b,'test.txt'); // sollte Download triggern + nach 2s cleanup
```
