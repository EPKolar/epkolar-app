# Auth-Inventory · 24.04.2026 (Phase 0 der v3.8.47-Auth-Hardening-Session)

**Zweck:** Vollständiger Lese-Durchgang des Auth-Codes in `index.html` vor Code-Änderung.
**Ergebnis:** Architektur fundamental anders als im Session-Plan angenommen → STOPP per H8.
**HEAD:** `73b0c86` (v3.8.46), unverändert.

---

## 1 · In-Memory-State (L342)

```js
let _authToken=null, _authRefreshToken=null, _authRefreshTimer=null;
```

- `_authToken` — aktueller Access-Token (JWT, 1h Lifetime)
- `_authRefreshToken` — aktueller Refresh-Token (7d Supabase-Default)
- `_authRefreshTimer` — Handle für one-shot setTimeout(refresh, expires_in-60s)

---

## 2 · Storage-Keys (wer liest/schreibt)

| Key | Schreiber | Leser | Inhalt |
|---|---|---|---|
| `epkolar_auth` | `_storeAuth` L1178 | `_restoreAuth` L1188, visibility-handler L1197 | `{at, rt, exp}` JSON-Blob |
| `epkolar_token` | `_storeAuth` L1179 | Smoke-Tests (T-100er Reihe) | roher access_token (für Debug) |
| `epkolar_refresh` | `_storeAuth` L1179 | keine direkte Nutzung (wird via `_authRefreshToken` bereits in-memory gehalten) | roher refresh_token |
| `epkolar_gc` | (entfernt v3.8.35) | — | war base64-plaintext-PW, Sicherheitsrisiko |
| `epkolar_user` | L1889 Login | L1828 Logout-Cleanup | User-Objekt-Cache |
| `epkolar_auth_backup_preforce` | `_forceToken` L772 | `_restoreToken` L780 | Debug-Backup |

**Key-Befund:** Entgegen Session-Plan-Annahme wird `epkolar_refresh` **durchaus genutzt** — indirekt via `epkolar_auth.rt` beim Bootstrap-Restore (L1190) → setzt `_authRefreshToken` → den wiederum `_sbAuthRefresh` verwendet (L1150).

---

## 3 · Auth-Funktionen (alle vorhanden)

### 3.1 `_sbAuthLogin(email, password)` · L1129
- POST `/auth/v1/token?grant_type=password`
- Return: Response-JSON (enthält `access_token`, `refresh_token`, `expires_in`)
- Fehlerbehandlung: error_description/msg/message-Extraction

### 3.2 `_sbAuthRefresh()` · L1145 ★ SINGLETON
- **Singleton via `_authRefreshInflight` Flight-Promise** (L1144, L1146)
- POST `/auth/v1/token?grant_type=refresh_token`
- Bei Erfolg: ruft `_storeAuth(d)` → setzt Token + schedulet nächsten Timer
- Bei Fehler (kein `_authRefreshToken` oder 4xx): fällt auf `_silentReAuth()` zurück
- 5-Parallele-Calls teilen denselben Promise (Thundering-Herd-Protection, dokumentiert L1203)

### 3.3 `_silentReAuth()` · L1158 ★ STUB (bewusst, v3.8.35)
- Ursprünglich: via `epkolar_gc` (base64-PW-Cache) re-login
- **Entfernt v3.8.35** weil base64 reversibel → effektiv Klartext-PW in localStorage
- Aktuell: nur Warning + `_authToken=null; _authRefreshToken=null;`
- Refresh-Token hat 7d Lifetime — überbrückt die meisten realen Szenarien
- Bei echtem Ablauf: User muss neu einloggen (normale Web-UX)

### 3.4 `_sbAuthLogout()` · L1168
- POST `/auth/v1/logout` (best-effort, wenn JWT-Shape gültig)
- Clearing: `_authToken`, `_authRefreshToken`, `_authRefreshTimer`
- localStorage-Cleanup: `epkolar_auth`, `epkolar_gc`, `epkolar_token`, `epkolar_refresh`

### 3.5 `_storeAuth(d)` · L1174 ★ TIMER-SCHEDULING
- JWT-Shape-Guard (L1176): lehnt garbage ab
- Schreibt `_authToken`, `_authRefreshToken`, alle 3 localStorage-Keys
- **Schedulet one-shot Refresh-Timer** L1183: `setTimeout(_sbAuthRefresh, Math.max((expSec-60)*1000, 30000))`
- Default `expires_in` Fallback: 3600s

### 3.6 `_restoreAuth()` · L1187 ★ BOOTSTRAP
- Läuft genau einmal am App-Start (L1195)
- Parst `epkolar_auth` aus localStorage
- Bei valid + exp>now: setzt `_authToken`, `_authRefreshToken`, schedulet Timer 60s vor exp
- Bei exp<now aber rt vorhanden: feuert `_sbAuthRefresh()` sofort
- Bei ungültig: `_silentReAuth()` (= Token-Nullify)

### 3.7 `_ensureAuth()` · L1088 (auf window exponiert)
- Opt-in Preflight-Check
- Parst `_authToken.payload.exp`
- Trigger `_sbAuthRefresh()` wenn exp < 300s OR role='anon'
- Returns boolean (Token da nach dem Call)

### 3.8 `_sbH(extra)` · L1108 ★ ANON-DETECT
- Header-Builder für Supabase-REST
- Detect anon-JWT role → triggert async non-blocking `_sbAuthRefresh()` (Throttle 5s via `_sbHLastRefreshAt`)
- JWT-Shape-Validator vor Bearer-Injection (verhindert PGRST301 "Expected 3 parts")

### 3.9 `_sbRH()` · L1126 · Reader-Header (Range 0-4999)
### 3.10 `_sbWH(prefer)` · L1127 · Writer-Header (Content-Type + Prefer)

### 3.11 `_authRetry(fn)` · L1206 ★ 401-RETRY
- Wrapped fetch-Caller
- Bei 401/403: ruft `_sbAuthRefresh()`, dann retry einmal
- Bei 2×401: `_onAuthFail()` (Toast + Flag)
- Last-Line-of-Defense für Token-Drift

### 3.12 `_sbGet/Post/Patch/Delete/Upsert/GetOrder/GetUsersSafe` · L1452ff
- **Alle async, alle nutzen `_authRetry`**
- Kein direkter Refresh-Call nötig — via Header + Retry gedeckt

---

## 4 · Listener-Registrierungen

### 4.1 `visibilitychange` · L1197 ★ AUTH-REFRESH
```js
document.addEventListener("visibilitychange",()=>{
  if(document.visibilityState==="visible"&&_authToken){
    try{
      const s=JSON.parse(localStorage.getItem("epkolar_auth")||"null");
      if(!s||!s.exp||s.exp-Date.now()<120000){_sbAuthRefresh();}
    }catch(_){_sbAuthRefresh();}
  }
});
```
- Triggert Refresh wenn Tab visible UND exp < 120s

### 4.2 `online`/`offline` · L4350/4351 (React-useEffect, Dep `[curUser]`)
- Triggert `doSync()`, `PhotoQ.flush()` und Service-Worker-Sync-Registrierung
- **KEIN Auth-Refresh-Call drin** — das wäre ein purer additiver Mehrwert

### 4.3 `online`/`offline` · L7211 (zweiter Listener, anderes Scope)
- Connection-Banner-State

---

## 5 · Was "fehlt" laut Session-Plan vs. Realität

| Session-Plan-Annahme | Realität |
|---|---|
| "FEHLEND: `_refreshToken`" | `_sbAuthRefresh` EXISTIERT (L1145), Singleton |
| "FEHLEND: `_tokenWatchdog`" | One-shot setTimeout via `_authRefreshTimer` existiert (60s vor exp) — **kein 60s-Interval, aber timer-basiert** |
| "FEHLEND: `_getTokenExpiry`" | `_ensureAuth()` + inline JWT-parsing in mehreren Funktionen |
| "epkolar_refresh NIE VERWENDET zum Refreshen" | **FALSCH** — wird indirekt via `epkolar_auth.rt` beim Bootstrap gelesen → `_authRefreshToken` → `_sbAuthRefresh` |
| "visibility-Handler fehlt" | L1197 existiert mit 120s-Threshold |
| "online-Handler fehlt" | L4350 existiert (für Sync), KEIN Auth-Refresh drin — einziger valider Additiv |
| "`_silentReAuth` ist halbimplementiert" | **Absichtlich Stub seit v3.8.35** (Sicherheitsentscheidung — Klartext-PW) |

---

## 6 · Was wirklich ergänzend wäre (Additive, NICHT Session-Plan-Scope)

1. **Backup-Watchdog (setInterval 60s)** — falls `_authRefreshTimer` silent dies (z.B. throttle durch Browser bei Tab-Sleep), hätte ein Interval als Backstop Sinn.
2. **`online`-Event-Auth-Refresh** — in L4350 einen Aufruf von `_sbAuthRefresh()` (oder `_ensureAuth()`) ergänzen.
3. **`__authLog`-Telemetrie** — Ring-Buffer mit `refresh_ok/fail/attempt/gc_fallback`-Events für Debug-Support (keine Token-Werte).
4. **Preflight in `_sbGet/Post/Patch/Delete`** — derzeit relies on `_authRetry` (reaktiv). Preflight wäre proaktiver, aber der 401-Retry-Pfad funktioniert (bewiesen durch `_s8_107c` Thundering-Herd-Test L1226).

**Skala des Additivs:** ~50-100 Zeilen Code, 4 Commits, 2-3h. **Aber keine der 4 Punkte ist "kritisch" — alle sind Defense-in-Depth.**

---

## 7 · Empfehlung

Die ursprüngliche Session-Annahme "Token-immer-gültig-Garantie fehlt noch" ist **nur teilweise richtig**:
- Für Tab-Sleep 12h: Visibility-Handler ✅ (wenn Tab visible wird + exp < 120s → refresh)
- Für 8h-Offline-Wiederkommen: Fehlt (online-Handler refresh-t aktuell nicht)
- Für Password-Wechsel via Admin-Panel: Wird vom nächsten 401 via `_authRetry` gefangen, aber User sieht kurzen UX-Hickser

**Konkrete Lücken, die wirklich Mehrwert bringen:**
1. `online`-Event triggert `_sbAuthRefresh` in L4350 (1-Zeile-Fix)
2. Backup-`setInterval(60s)`-Watchdog für Timer-Resilienz

**Alles andere (Preflight in `_sbGet/Patch/...`, `__authLog`, `_ensureFreshToken`) duplizert existierende Mechanismen oder ist reine Telemetry.**

Sebastian sollte entscheiden ob die 2 additiven Fixes jetzt (Mini-Session <30min) oder nach Urlaub gemacht werden. **Eine vollwertige Auth-Hardening-Session-v3.8.47 wie geplant ist NICHT nötig.**
