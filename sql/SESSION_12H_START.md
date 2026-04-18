# EPKolar 12h-Session BASELINE — 18.04.2026

## Repo-Snapshot
- **HEAD**: `aaf1e26` (v3.5.141)
- **index.html**: 15.284 Zeilen
- **sw.js**: 73 Zeilen
- **Brackets**: `() -2, {} 0, [] 0` ✓
- **node --check**: OK ✓

## Code-Metriken
| Metric | Baseline |
|---|---|
| `setState`-Calls | 1708 |
| `setForm({...form,...})` non-functional | **58** |
| `setForm(prev=>...)` functional | 11 |
| Empty `try{}catch(_){}` | 83 |
| Empty `.catch(()=>{})` | 24 |
| `aria-label` Attribute | **0** |
| `useEffect.call` | 105 |
| `useMemo.call` | 8 |
| `addEventListener` | 16 |
| `removeEventListener` | 12 |

**Auffällig**: 4 `addEventListener` mehr als `removeEventListener` — potentielle Cleanup-Lücken. 58 vs 11 functional-setForm — stale-closure-Risiko.

## Session-Plan (13 Iterationen, 12h)

### Phase 1 — CRITICAL Bug-Hunt (Iter 1-4)
- Iter 1: React-Invariants (setState-closures, missing deps, unstable keys, conditional hooks)
- Iter 2: IndexedDB-Transactions (weitere Read-Modify-Write-Races außerhalb SQ/PhotoQ)
- Iter 3: Fetch-Error-Handling (!r.ok swallowed, Server-500 vs Network-0)
- Iter 4: Auth-State-Machine (Race zwischen Expiry-Timer und aktivem Request)

### Phase 2 — Weitere Tiefen-Scans (Iter 5-7, statt Features)
- Iter 5: Component-Lifecycle-Leaks (timer/listener cleanup)
- Iter 6: Security-Härtung (XSS in HTML-generierung, Print-popup, PDF)
- Iter 7: Performance-Deep-Dive (unvirtualisierte Listen, teure Render-Berechnungen)

### Phase 3 — Dokumentation + Regressions-Harness (Iter 8-10)
- Iter 8: ARCHITECTURE.md (Globals, Flows, Mutex-Semantik)
- Iter 9: Testkonzept v5.0 (neue Kategorien TC-M/T/J/I)
- Iter 10: `_runAllTests()` erweitern um 6 CRITICAL-Regression-Checks

### Phase 4 — Polish + Close-out (Iter 11-13)
- Iter 11: A11y Quick-Wins (50 wichtigste Buttons aria-label)
- Iter 12: Mobile-Polish (iOS-zoom, overscroll, touch-action)
- Iter 13: FINAL HANDOFF_12H.md mit Delta-Analyse

## Garantien
- Brackets `() -2, {} 0, [] 0` + `node --check` bei jedem Push
- Self-Terminierung nach 3× Idle in Folge
- `HANDOFF_12H.md` garantiert geschrieben

Start-Zeit: dieser Commit-Zeitpunkt.
