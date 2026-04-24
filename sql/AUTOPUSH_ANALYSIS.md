# Auto-Push Analyse · v3.8.42 Prep · 2026-04-24

**Baseline:** `443444b` (v3.8.41).
**Problem:** Chrome-MCP-Capture zeigt Auto-Sync pullt, aber pusht nicht. 48× PATCH, 0× Push-RPC in 33 Min. Monteure klicken manuell — UX-Risiko für Urlaubs-Woche.

## Save-Pfade identifiziert (alle in AS-Komponente, L~5137+)

| Line | Pfad | push_pending-Setter | Juprowa-Push heute |
|---:|---|---|---|
| 5137 | `save` (AS-Edit-Form) | ✅ `push_pending:_isPush?true` | 🔴 `_juprowaPushAll()` (4-Min-Timeout!) |
| 5140 | `storno` | ✅ `push_pending:isJup?true` | ❌ kein Push-Call |
| 5142 | `verschieben` | ✅ `push_pending:pp?true` | ❌ kein Push-Call |
| 5143 | `updAs` (generic) | ✅ `push_pending:pp?true` | ❌ kein Push-Call |

## Helper-Inventar

- `_juprowaPush(scheinId: string)` L2566 — funktioniert, single-id, schnell.
- `_juprowaPushAll()` L2610 — lädt alle `push_pending`-Rows, pusht sequenziell. Hängt bei großen Queues (4-Min-Timeout laut Capture).
- `_juprowaMarkEdited(scheinId, updates)` L2623 — setzt DB-seitig `push_pending:true`.
- `_juprowaSync(arbeitsscheine, setArbeitsscheine, silent)` L2364 — Pull-Zyklus, kein Push-Drain am Ende.

## Fix-Strategie v3.8.42

### Layer 1 · Save-Hook (Instant-Push)

An JEDEM der 4 Save-Pfade nach `_juprowaMarkEdited()` (bzw. SQ.push bei L5139):

```js
if (editId && _finalForm.juprowa_id && navigator.onLine && typeof _juprowaPush === 'function') {
  _juprowaPush(editId).then(r => {
    if (!r || (!r.ok && r.error)) console.warn('[AUTOPUSH]', editId, (r && r.error) || 'unknown');
  }).catch(e => console.warn('[AUTOPUSH-EXC]', editId, e && e.message || e));
}
```

- **Fire-and-forget:** kein `await` → UI blockiert nicht.
- **Guard:** nur online + nur Juprowa-gebundene AS.
- **Ersetzt L5139 `_juprowaPushAll()`**: single-id eliminiert den 4-Min-Timeout.

### Layer 2 · Auto-Sync-Drain (Safety-Net)

Neue Funktion `_juprowaDrainPending(maxBatch=10)` nach `_juprowaPushAll` L2620:

```js
async function _juprowaDrainPending(maxBatch=10){
  if(!navigator.onLine) return{drained:0,skipped:'offline'};
  try{
    const pending=await _authRetry(()=>_sbGet('arbeitsscheine','push_pending=eq.true&juprowa_id=not.is.null&select=id&limit='+maxBatch));
    if(!Array.isArray(pending)||pending.length===0) return{drained:0,batch:0};
    let ok=0,fail=0;
    for(const row of pending){
      try{const r=await _juprowaPush(row.id);if(r&&r.ok)ok++;else fail++;}catch(e){fail++;}
    }
    return{drained:ok,failed:fail,batch:pending.length};
  }catch(e){return{drained:0,error:e&&e.message||String(e)};}
}
```

Integration in `_juprowaSync` direkt vor dem `finally{_juprowaSyncing=false;}`-Block:

```js
try{
  const drainResult = await _juprowaDrainPending(10);
  if(drainResult.drained>0||drainResult.failed>0) console.log('[JP-DRAIN]', drainResult);
}catch(e){console.warn('[JP-DRAIN-EXC]', e && e.message || e);}
```

**WARUM max-Batch 10:** Limitiert Runtime bei Backlog, bleibt innerhalb des Sync-Timeouts, aufeinanderfolgende Sync-Zyklen draincasten progressiv ab.

**Unterschied zu `_juprowaPushAll`:**
- `_sbGet(... select=id)` statt ganzer Row → weniger Payload.
- Limit 10 statt alles.
- `_authRetry`-gewrappt.
- Return ist nicht ok/failed sondern `drained/failed/batch` für klareres Logging.

## Erwartung nach v3.8.42

- Nach AS-Save bei Juprowa-AS + online: Push-Badge verschwindet binnen ~1-2 s (Netzwerk-Latenz abhängig).
- Manueller `doSinglePush`-Button bleibt als Fallback.
- Bei Offline: `push_pending` bleibt gesetzt, drain beim nächsten Online-Sync.

## Bekannte Grenzen

- Fire-and-forget bedeutet: Push-Fehler sind nur in Console (kein Toast). Bewusst so wegen UI-Blockier-Vermeidung.
- Backlog >10: mehrere Sync-Zyklen nötig. Akzeptabler Trade-off.

## Nicht in v3.8.42

- Toast-Feedback bei Push-Fail
- Retry-Backoff bei 429/503 von Juprowa
- Batch-Progress-Indicator im UI
