# HANDOFF · v3.8.42 Auto-Push · 2026-04-24

**Baseline:** `443444b` (v3.8.41)
**End-State:** `3f1eab1` · tag `v3.8.42` · origin/main synced

## Commits

| SHA | Subject |
|---|---|
| `3cdc7da` | docs: Auto-Push Analyse (v3.8.42 prep) |
| `3f1eab1` | v3.8.42 feat(juprowa): Auto-Push nach AS-Save (2-Layer) |

## Delta

### Layer 1 · Save-Hooks (4 Pfade)

| Line | Pfad | Vorher | Nachher |
|---:|---|---|---|
| 5139 | `save` (AS-Edit-Form) | `_juprowaPushAll()` (4-Min-Timeout) | `_juprowaPush(editId)` fire-and-forget |
| 5140 | `storno` | kein Push | neuer Auto-Push-Hook |
| 5142 | `verschieben` | kein Push | neuer Auto-Push-Hook |
| 5143 | `updAs` | kein Push | neuer Auto-Push-Hook |

Pattern pro Hook:
```js
try{if(<juprowa-guard>&&navigator.onLine&&typeof _juprowaPush==="function"){
  _juprowaPush(id).then(r=>{
    if(!r||(!r.ok&&r.error))console.warn('[AUTOPUSH]',id,(r&&r.error)||'unknown');
  }).catch(e=>console.warn('[AUTOPUSH-EXC]',id,e&&e.message||e));
}}catch(_){}
```

### Layer 2 · Auto-Sync-Drain

- Neue `async function _juprowaDrainPending(maxBatch=10)`:
  - `navigator.onLine`-Guard
  - `_sbGet('arbeitsscheine','push_pending=eq.true&juprowa_id=not.is.null&select=id&limit=10')`
  - `for-of` sequenziell, kein `Promise.all`
  - Returns `{drained, failed, batch}` (oder `{error,drained:0}`)
- Integration in `_juprowaSync` vor dem `return result`:
  ```js
  try{const _dr=await _juprowaDrainPending(10);
      if(_dr&&(_dr.drained>0||_dr.failed>0))console.log('[JP-DRAIN]',_dr);
  }catch(e){console.warn('[JP-DRAIN-EXC]',e&&e.message||e);}
  ```
- `_juprowaStartAutoSync`: Legacy `_juprowaPushAll()`-Call entfernt (Drain läuft jetzt intern).

## Tests

- **101/101 grün** (90 → 101, +11 netto)
- `tests/test_autopush_hook.py` · 11 Invariants:
  - Layer 2 (7): definiert, online-guard, for-of, `_juprowaPush(row.id)`-call, default-10, `_juprowaSync`-integration, AutoSync-no-pushall-direct-call
  - Layer 1 (4): AUTOPUSH-Marker, online-guard, `.then()` fire-and-forget, AUTOPUSH-EXC console.warn

## H5 Final-Check

- `node sql/_check_syntax.js` → `syntax OK`
- `node sql/_check_brackets.js` → `brackets () -2 {} 0 [] 0`
- `node sql/_check_version.js` → `✓ versions synced: 3.8.42`
- `pytest tests/ -q` → `101 passed`
- `git status` → clean
- `git log --oneline -3` → Commit-Messages konkret (H8)

## Sebastian-Verifikation (manuell, 5 Min)

1. **Cache-Bust**: DevTools → Application → Service Workers → "Unregister" + F5
2. **Version**:
   ```js
   fetch('/index.html',{cache:'no-store'}).then(r=>r.text())
     .then(t=>console.log(t.match(/APP_VERSION\s*=\s*"([^"]+)"/)[1]))
   ```
   Erwartet: `3.8.42-supabase`
3. **AS editieren + aktualisieren** → Push-Badge (`☁️↑`/`⚠↻`) sollte binnen 2-3 s verschwinden
4. **OFFA-Log nach 5 Min**: Änderung da, weiter kein "Länderkürzel von 'A' auf ''"
5. **Network-Tab** nach AS-Save: 1× PATCH + 1× `rpc/juprowa_push_worksheet` innerhalb Sekunden

## Known Limits / Follow-ups

- Fire-and-forget: Push-Fehler landen nur in Console, kein User-Toast.
- Backlog > 10: mehrere Sync-Zyklen nötig (je 5 Min Intervall). Akzeptabel.
- `_juprowaPushAll` bleibt als Helper-Definition (nicht mehr aufgerufen), kann später entfernt werden wenn `_juprowaDrainPending` sich bewährt hat.

## Sleep-Prevention (für Urlaubs-Woche)

- `powercfg -change` Timeouts auf 0 (Admin-less ausführbar, einzelne Variante lief durch).
- `powercfg /requests` Admin-gated, konnte ich nicht verifizieren.
- KeepAwake-Script aktiv (Scroll-Lock-Toggle, PID 22056, Fenstertitel "EPKolar-KeepAwake").

## Nächster Step

**Sebastian verifiziert v3.8.42 live.** Danach Freigabe "Urlaubs-Modus an" → H9-H16 aktiv ab Mo 28.04 09:00 Lokalzeit.

Bis dahin: passiv warten, nichts weiter tun.
