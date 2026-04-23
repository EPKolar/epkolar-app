# B-021 Silent-Re-Auth · Verify-Playbook · 19.04.2026

## Implementation-Status

**B-021 ist substantiell schon vor dieser Session komplett gewesen.** Der Mechanismus existiert seit v3.5.112 (_authRefreshInflight Thundering-Herd-Schutz) und v3.5.137 (_isJwtShape + _authRetry-Verwendung in allen _sb*-Wrappers).

v3.5.178 Strengthening:
- 2nd-round-401-Detection: Wenn nach Silent-Re-Auth der Retry ERNEUT 401 liefert, wird _onAuthFail jetzt auch dort gefeuert (vorher: silent).
- Success-Logging: `console.log('[Auth] Silent re-auth OK → request recovered')`

## Wrapper-Architektur (schon gut)

- **`_authRetry(fn)`** (line 641) — Kern-Wrapper. Alle `_sb*`-Wrappers gehen durch.
- **`_sbAuthRefresh`** (line 585) — Rotate refresh_token. Hat `_authRefreshInflight` Promise-Guard (line 584, v3.5.112).
- **`_silentReAuth`** (line 598) — Fallback via `epkolar_gc` (base64-gespeicherte Login-Creds). Wenn refresh_token tot: re-login mit password-grant.

## Alle `_sb*` Wrappers nutzen `_authRetry`

| Wrapper | Line | Verwendung |
|---|---|---|
| `_sbGet` | 827 | ✓ _authRetry |
| `_sbGetOrder` | 835 | ✓ _authRetry |
| `_sbPost` | 843 | ✓ _authRetry |
| `_sbUpsert` | 848 | ✓ _authRetry |
| `_sbPatch` | 853 | ✓ _authRetry |
| `_sbDelete` | 858 | ✓ _authRetry |
| `_sbGetUsersSafe` | 865 | ✓ _authRetry |
| _api (legacy bridge) | 389-407 | ✓ _authRetry |

**Nicht-wrapped Fetches** (bewusst): Diagnose-Logger (line 331/334), Smoke-Tests (470-478), Fire-and-forget activity_log (1294/15336), Admin-User-Test (3294), Juprowa-RPCs (5600+). Alle entweder lesen-only oder best-effort-write.

## Verifikations-Script für Sebastian (Browser-Console)

### Smoke-Test 1: `_authRetry` ist aktive Funktion
```js
// Erwartung: function
console.log(typeof _authRetry);
```

### Smoke-Test 2: Force 401, dann Recovery
```js
// ACHTUNG: nur in dev/test. _authToken gezielt corruptem → Request soll
// automatisch 401 bekommen, refresh triggern, mit neuem Token retryen.
const _saved=_authToken;
_authToken='eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.invalid_sig_xxx'; // gefälschter JWT
// Jetzt irgendeinen _sb*-Call: sollte 401 kriegen, dann refresh/silentReAuth,
// dann erfolgreich werden.
const r=await _sbGet('users','limit=1');
console.log('Ergebnis:', r, '_authToken neu:', _authToken!==_saved);
// Erwartung in Console: '[Auth] Silent re-auth OK → request recovered (200)'
```

### Smoke-Test 3: Thundering-Herd
```js
// 5 parallele Requests mit kaputt-Token
_authToken='broken.broken.broken';
const results=await Promise.all([
  _sbGet('users','limit=1').catch(e=>'err'),
  _sbGet('projects','limit=1').catch(e=>'err'),
  _sbGet('arbeitsscheine','limit=1').catch(e=>'err'),
  _sbGet('monteure','limit=1').catch(e=>'err'),
  _sbGet('fahrzeuge','limit=1').catch(e=>'err')
]);
// Erwartung: _sbAuthRefresh wird nur EINMAL tatsächlich aufgerufen
// (dank _authRefreshInflight). Alle 5 Requests retry nach erfolgreicher Refresh.
console.log('Alle 5 erfolgreich?', results.every(r=>Array.isArray(r)));
```

### Smoke-Test 4: Refresh-Token auch tot (doppelter Fail)
```js
// _authToken UND refresh_token kaputt → _silentReAuth Fallback
// Erwartung: Toast "⚠️ Sitzung abgelaufen — bitte neu anmelden"
_authToken='x.y.z';_authRefreshToken='broken';
localStorage.removeItem('epkolar_gc'); // verhindert silentReAuth-Fallback
await _sbGet('users','limit=1'); // silent 401
// Browser-DOM: Toast sichtbar? Wenn ja → _onAuthFail feuert korrekt.
```

## Edge-Case-Matrix

| Szenario | Erwartet | Status |
|---|---|---|
| JWT valid, Request OK | 200, no retry | ✓ |
| JWT expired, refresh_token valid | 401 → refresh → retry → 200 | ✓ |
| JWT expired, refresh_token tot, gc-Backup vorhanden | refresh-fail → silentReAuth(password-grant) → 200 | ✓ |
| JWT expired, alle Auth-Pfade tot | refresh-fail → silentReAuth-null → _onAuthFail Toast | ✓ |
| 5 parallele 401 | 1 tatsächlicher Refresh, alle 5 retry | ✓ (v3.5.112 Flight-Guard) |
| Retry liefert ERNEUT 401 (sehr selten) | _onAuthFail Toast auch in 2nd-round | ✓ v3.5.178 neu |
| POST Retry bei 401 → Gefahr doppeltes Schreiben | NEIN — 401 bedeutet "Request wurde NICHT verarbeitet" | ✓ (server-seitig sicher) |

## Nicht gefixt (bewusste Entscheidung)

- **Juprowa RPC-Calls (5600+, 5601+)**: bleiben außerhalb _authRetry. Admin-only, Fail-toast wird vom UI sauber gehandled. Keine Silent-Retry nötig.
- **Fire-and-forget activity_log (1294, 15336)**: bewusst "drop on 401". Kein User-Impact.
- **Diagnose + Smoke-Tests (331-478)**: Dev-Pfade, werden nach Bedarf ausgelöst.

## Bekannter Randfall

Wenn `_silentReAuth` Password aus `epkolar_gc` nutzt und Password auf Server geändert wurde (z.B. per SQL):
- refresh-Token fail → silentReAuth → password-grant → GoTrue antwortet 400 ("invalid credentials")
- _authToken=null → Retry ohne Bearer → RLS blockt 401 → _onAuthFail Toast
- User muss sich manuell neu einloggen. Korrekt.
