# HANDOFF · v3.8.47 Auth-Hardening · 2026-04-24

**Baseline:** `4e5f6fb` (v3.8.46 + Abort-Inventory-Docs)
**End-State:** `cd797dc` · tag `v3.8.47` · origin/main synced
**Rollback-Target:** `v3.8.46-pre-auth-refresh` tag (entspricht `4e5f6fb`)
**Rollback-Kommando:** `git reset --hard v3.8.46-pre-auth-refresh && git push -f origin main`

## TL;DR

Nach Phase-0-ABORT der ursprünglichen Session (Inventar zeigte existing Refresh-Architektur) hat die Fortsetzung-Session 3 konkrete Bugs im bestehenden System gefixt statt ein paralleles zu bauen. pytest 211 → 227 (+16). Brackets stabil über 5 Commits.

## Commits (5)

| SHA | Subject | Fix |
|---|---|---|
| `072c67a` | fix(auth): G1 network-error preserves _authRefreshToken + __authLog | G1 + Telemetry |
| `76e6a4b` | fix(auth): G2 online-event triggers _sbAuthRefresh | G2 |
| `254fde8` | fix(auth): G3 localStorage fallback in auto-login catch | G3 |
| `72c0f1f` | test(auth): v3.8.47 hardening meta-tests (16 neu) | Tests |
| `cd797dc` | v3.8.47 bump: auth-hardening minimal-invasive fixes | Bump |

## Phase A · Deep-Dive-Befund

Die vorherige Session hatte korrekt gestoppt weil die Session-Plan-Annahme "App hat keine Refresh-Logik" falsch war. Vollständiges Inventar in `sql/AUTH_INVENTORY_20260424.md`. Existing Komponenten:

- `_sbAuthRefresh` L1145 mit `_authRefreshInflight` Singleton-Guard
- `_silentReAuth` L1158 (seit v3.8.35 absichtlicher Stub)
- `_storeAuth`/`_restoreAuth` mit 60s-vor-exp `_authRefreshTimer`
- `visibilitychange`-Handler L1197 mit 120s-Threshold
- `_sbH` mit anon-JWT-Detect + Refresh-Trigger (5s-Throttle)
- `_authRetry` mit 401/403-Retry + `_onAuthFail`
- `_ensureAuth` Preflight (window-exposed, 300s-Threshold)
- epkolar_auth/token/refresh/user Storage-Keys

Diese Architektur deckt ~95% der Szenarien. 3 konkrete Bugs blieben offen:

## Phase B · Gap-Analyse

| ID | Bug | Scope | Severity |
|---|---|---|---|
| G1 | `_sbAuthRefresh` nukt `_authRefreshToken` auf NETZWERK-Fehler (nicht nur bei 4xx) | Cascade-Failure nach single Network-Blip | HOCH |
| G2 | `onOnline`-Handler triggert Sync aber keinen Auth-Refresh | 401-Spam nach 8h Offline | MITTEL |
| G3 | Auto-Login-catch hat keinen localStorage-Fallback zwischen ODB-Miss und Session-Kill | Matcht Sebastians curUser=null-Symptom | HOCH |
| G4 | Keine strukturierte Auth-Telemetry | Debug-Blindflug | NIEDRIG (in G1 mit gelöst) |

## Phase C · Root-Cause-Fixes

### G1: Network-Error-Distinction · Commit `072c67a`

**Vorher** (`_sbAuthRefresh` L1153):
```js
catch(e){console.warn("[Auth] Refresh error:",...);return await _silentReAuth();}
```
Jeder thrown Error → `_silentReAuth` → `_authToken=null; _authRefreshToken=null;`.
Konsequenz: Single fetch-Netzwerk-Hiccup zerstört Refresh-Mechanismus bis Reload.

**Nachher:**
```js
catch(e){
  // v3.8.47 G1-Fix: Netzwerk-/Timeout-Fehler NUKEN _authRefreshToken NICHT.
  console.warn("[Auth] Refresh network error (token kept):",...);
  _authLog('refresh_fail',{status:'network',...});
  return null;
}
```
Nur `!r.ok` (4xx von Supabase) → `_silentReAuth`. Transiente Network-Fails preservieren Tokens für nächsten Versuch.

**Bonus:** `window.__authLog` Ring-Buffer (100 Events, keine Token-Inhalte) für DevTools-Debug.

### G2: Online-Event triggert Refresh · Commit `76e6a4b`

**Vorher** (`onOnline` L4355):
```js
const onOnline=async()=>{
  setSyncStatus(...);
  _optionalChain([window.__toast("📶 Verbindung wiederhergestellt")]);
  // Register background sync
  if(swReg.current.sync) sync.register("epkolar-sync");
  const cnt=await SQ.count();
  // Sync-Flush triggered
```
Nach 8h Offline: `_authToken` abgelaufen, Sync-Flush feuert mit totem Token → 3× 401 + Toast-Spam.

**Nachher:** Nach Toast, vor Sync:
```js
try{if(_authToken&&_authRefreshToken){_authLog('wake_online',{});await _sbAuthRefresh();}}catch(_){}
```
Singleton via `_authRefreshInflight` garantiert: parallele Sync-Starts lösen nur 1 Refresh aus. G1-Fix macht das Network-Safe.

### G3: localStorage-Fallback · Commit `254fde8`

**Vorher** (Auto-Login-useEffect-catch L3965-3972):
```js
catch(e){
  try{const u=await ODB.get("meta","lastUser");if(u){...setCurUser(u);...return;}}catch(ex){}
  API.setToken(null);  // <-- kill session
}
```
Wenn `API.me()` + ODB-Lookup fail → Session gekillt, obwohl `_authToken` noch Valid + `localStorage.epkolar_user` existiert. Matcht Sebastians beobachtetes Symptom.

**Nachher:** Dritter Fallback zwischen ODB-Miss und `API.setToken(null)`:
```js
if(_authToken&&_isJwtShape(_authToken)){
  const _p=JSON.parse(atob(_authToken.split('.')[1]));
  if(_p.exp&&_p.exp*1000>Date.now()+60000){
    const _lsU=_safeJsonParse(localStorage.getItem('epkolar_user'),null);
    if(_lsU&&_lsU.id){
      _authLog('curuser_ls_recover',{reason:...});
      _fixAdminName(_lsU);
      setCurUser(_lsU);setAppLoading(false);return;
    }
  }
}
API.setToken(null);
```
Guards: JWT-Shape + 60s-Validity + `_safeJsonParse` + `_lsU.id`-Check + `_fixAdminName`-Hook.

### Warum NICHT die Prompt()-Migration?

L6711 Admin-PW-Reset verwendet natives `prompt()` das den JS-Thread blockt. Das triggert plausibel Race-Conditions während prompt-Blocking. Eine vollwertige Migration auf Promise-basiertes Modal (analog `_confirmModal` v3.8.46) wäre >50 LOC (input-field + focus-mgmt + validation) und fällt aus dem "minimal-invasive"-Scope. Empfehlung: eigene Mini-Session nach Urlaub.

## Tests

- **227/227 grün** (211 → 227, +16 in `tests/test_auth_v3847.py`)
- Alle anderen Test-Files unverändert
- Brackets `() -2 {} 0 [] 0` stabil über alle 5 Commits

## H-Rules-Bilanz

- **H0 Pfad-Lock:** ✅ `T:\05_Claude\...\epkolar-app`
- **H1 Unantastbar:** ✅ Juprowa/_mapBody/SyncQueue/OFFA/DATANORM/_OFFPW/sw.js-außer-Version unberührt
- **H2 Tag:** ✅ `v3.8.46-pre-auth-refresh` vor Commit 1 gesetzt + gepusht
- **H3 Signaturen:** ✅ `_sbAuthRefresh()`/`_silentReAuth()`/`_authRetry(fn)` unverändert (Test verifiziert)
- **H4 <50 LOC NET-ADD pro Commit:** ✅ G1 +21/-4, G2 +4/-0, G3 +17/-0 (alle unter 50)
- **H5 Triade nach jedem Commit:** ✅ Brackets + syntax + pytest nach jedem Edit
- **H6 Bracket-Drift:** n/a (kein Drift)
- **H7 H-CANARY:** ✅ Commit 1 enthält `ROOT-CAUSE-CANARY`-Marker im Body
- **H8 Kein Zweifel:** ✅ keine spekulativen Fixes, nur code-bestätigte Bugs

## Out-of-Scope (dokumentiert, nicht gefixt)

- **Prompt()-Migration** in Admin-PW-Reset (L6711): Würde ~80 LOC brauchen für Promise-based Input-Modal. Separate Session nötig.
- **Cross-Tab-Sync:** Tab A refresht Token → Tab B hat stale `_authRefreshToken` in-memory → nächster Refresh in Tab B scheitert mit 4xx → G1-Fix fängt jetzt nur Network-Errors ab, 4xx-Fall weiterhin nukt Tokens. Storage-Event-Listener würde das lösen.
- **Admin-triggered Password-Change:** Wenn Admin das PW eines aktiven Users ändert, invalidiert Supabase den refresh_token. `_sbAuthRefresh` bekommt 4xx → `_silentReAuth` → User landet auf LoginScreen. Akzeptabel.
- **Token-Storage-Konsolidierung:** 4 Storage-Keys (auth/token/refresh/user) sind redundant. Cleanup-Ticket post-Urlaub.

## Sebastian-Smoke-Test-Anleitung

Nach Cache-Bust + Reload in Browser:

1. **Baseline:** Home-Kacheln voll, curUser gesetzt, keine 401 in Console.
2. **__authLog check:** DevTools → `window.__authLog` → Array mit Events sichtbar (zumindest `refresh_attempt`/`refresh_ok` beim Boot-Refresh).
3. **G1 Netzwerk-Blip:** DevTools → Network → "Offline" für 10s → "Online" → kein _authToken=null im Console-Log.
4. **G2 Online-Wake:** Offline 30s → Online → `window.__authLog` zeigt `wake_online` + ggf. `refresh_ok`.
5. **G3 PW-Reset-Szenario:** Admin-Tab → User → "🔑 Passwort zurücksetzen" → ESC/Cancel auf prompt() → Home-Tab wechseln → curUser bleibt gesetzt, keine 401-Spam.
6. **G3 ODB-Miss:** IndexedDB manuell in DevTools leeren → Reload → wenn `epkolar_user` in localStorage UND Token valid → Session wird recovered (sichtbar als `curuser_ls_recover`-Event in `__authLog`).

## Nicht in dieser Session (Remaining)

- `HANDOFF_v3847_ABORT.md` wird in Doc-Commit (folgt) entfernt — Abort wurde übersteuert.
- Prompt()-Migration L6711 (eigene Session, 1.5-2h).
- 46 verbleibende `JSON.parse`-Sites (pro Section bei Code-Touch).
- Bug-Hunt-Findings mittel/niedrig-Severity aus `sql/BUGHUNT_REPORT_20260428.md`.

## KeepAwake

Nicht relevant in dieser kurzen Session (<90 min).
