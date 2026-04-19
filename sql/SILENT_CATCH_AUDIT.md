# Silent-Catch-Audit v3.8.19 · Block G.2

**Stand**: 2026-04-19 (v3.8.19 Block G)
**Ziel**: Alle `catch(e){}` / `.catch(()=>{})` Sites scannen + bewerten.
**Nicht** pauschal fixen — nur dokumentieren + Sebastian genehmigt Einzelfixe.

## Zahlen

| Pattern | Count |
|---|---|
| `catch (_) { }` oder `catch (e) { }` (empty body) | 170 |
| `.catch(() => {})` (promise arrow empty) | 24 |
| **Gesamt** | ~194 |

Davon historisch bereits gefixt (Iter-7/8/18 — Observability added):
- `admin_reset_password` in createUser (v3.8.7)
- `admin_reset_password` in Passwort-Reset-Button (v3.8.8)
- `_SB_AUTH+"/user"` PUT password in changePassword (v3.8.18)

Die restlichen 191 sind größtenteils **defensive Wrapper** (localStorage-Safari-private,
quota-exceeded, vibrate-API-fail). Nicht kritisch.

---

## Klassifikation der 194 Sites

### Kategorie 1 · Defensive-Safe (nicht fixen)

Lokale I/O + Browser-API-Fallbacks — silent-catch ist angemessen.

| Count | Muster | Beispiele |
|---|---|---|
| ~80 | `localStorage.setItem/removeItem` | L350, L365, L1160, L1166 etc. |
| ~6 | `navigator.vibrate([...])` | L354-359 |
| ~15 | `JSON.parse(localStorage.getItem(...)\|\|'null')` | L850, L1017 etc. |
| ~10 | `indexedDB` ODB read/write innerhalb Mutex | L1988, L2001 etc. |

**Verdict**: OK. Browser-API-Flakiness ist legitime silent-catch.

### Kategorie 2 · Logging/Diagnostic-Sites (nicht fixen)

Test-Helper die im Fehlerfall einfach nicht outputten:

| Count | Beispiele |
|---|---|
| ~15 | _selfTest-Substeps `try{...}catch(_){}` |
| ~4 | activity_log-Fire-and-Forget (L1800, L2341, L2460) |

**Verdict**: OK. Activity-Log-Failures sollen UI nicht blockieren.

### Kategorie 3 · RPC/REST-Calls (selektiv fixen)

Hier lohnt Observability. Liste mit Context:

| Line | Call | Status | Action |
|---|---|---|---|
| L1157 | `_SB_AUTH+"/logout"` POST | silent | P3 — server-side refresh-token bleibt 1h gültig. Im Logout-Flow akzeptabel, localStorage wird nachfolgend gecleart. **LIEGEN LASSEN**. |
| L1837 | `_SB_AUTH+"/signup"` POST | silent (bcrypt-fallback-Pfad) | P3 — Fallback-Path bei Legacy-User-Migration. Wenn signup fehlt, bleibt gotrue=false, catch-Handler greift später. **LIEGEN LASSEN**. |
| L1876 | `_SB_AUTH+"/user"` PUT pw | ✅ **gefixt** v3.8.18 | — |
| L6262 | `admin_reset_password` createUser | ✅ **gefixt** v3.8.7 | — |
| L6308 | `juprowa_get_config` | silent `catch(e){}` | P3 — wenn fetch fail, bleibt setJupCfg(undefined). UI-Indikator fehlt. **KANDIDAT** für Iter v3.8.20. |
| L2486 | `juprowa_push_worksheet` | innerhalb try-Block mit Error-Patch ✅ | OK. |
| L2315 | `juprowa_fetch_worksheets` | innerhalb try mit detailed Error-Handler ✅ | OK. |

**Empfehlung**: 1 Kandidat für späteren Iter (L6308 juprowa_get_config Observability).
Kein P1/P2 Silent-Catch mehr in der RPC-Schicht.

### Kategorie 4 · Fire-and-Forget (nicht fixen)

| Count | Beispiele |
|---|---|
| ~5 | `SQ.push(...).catch(()=>{})` — Fallback wenn IDB write kracht |
| ~3 | `_sbPost("activity_log",...).catch(()=>{})` — Audit-Log best-effort |
| ~8 | `_sbPatch(...).catch(()=>{})` in Juprowa-Push-Path für error-field Update |

**Verdict**: OK. Diese Calls dürfen fehlschlagen ohne User-UX-Impact.

---

## Top-Kandidat für v3.8.20

### L6308 · `juprowa_get_config` silent-catch

```js
const fetchJupConfig=async()=>{
  setJupCfgLoading(true);
  try{
    const rpcH=_authToken?_sbWH():{apikey:SUPABASE_KEY,"Content-Type":"application/json"};
    const r=await fetch(SB_REST+"/rpc/juprowa_get_config",_fT({method:"POST",headers:rpcH,body:"{}"},15000));
    if(r.ok){const d=await r.json();setJupCfg(d);}
  }catch(e){}  // ← silent
  setJupCfgLoading(false);
};
```

**Problem**: Wenn RPC 500 wirft, sieht User nur den "Config-Loading-Spinner" der nach
Timeout weggeht — **kein Fehler-Toast, kein Retry**. Admin kann Juprowa-Konfiguration
nicht sehen und weiß nicht warum.

**Fix (für v3.8.20)**:
```js
}catch(e){
  console.error('[juprowa_get_config]',e);
  if(window.__toast)window.__toast('❌ Juprowa-Config fehlgeschlagen: '+(e.message||e),'error',10000);
}
```

---

## Summary

- **194 Silent-Catch-Sites gefunden**
- **Davon 3 bereits gefixt** in v3.8.7/8/18 (Iter-Loop-Historie)
- **~190 sind defensiv-OK** (localStorage/vibrate/ODB/Fire-and-Forget-Audit)
- **1 Kandidat** (L6308) für v3.8.20 Observability

**Verdict**: Silent-Catch-Audit ist **nicht der Bottleneck**. Die historisch
wiederholten Silent-Catch-Bugs (v3.8.7/8/18) betrafen alle die GoTrue-Auth-Ops,
und dort ist jetzt durchgängig Observability dran. Andere Sites sind OK.
