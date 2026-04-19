# `window._selfTest()` Usage · v3.7.4

Orchestrator für alle Self-Test-Helpers. Spart das manuelle Einzelausführen der 5 Helper.

## Modes

| Mode | Was läuft | Dauer |
|---|---|---|
| `'full'` (default) | perfBench + mobileCheck + b017check + rlsAudit + s8Suite | 5-15s je nach Netzwerk |
| `'quick'` | Wie full, aber OHNE s8Suite (keine Auth-Tests) | 3-8s |
| `'security'` | NUR b017check + rlsAudit (keine Perf/Mobile) | <2s |

## Aufruf (Browser-Console, eingeloggt)

```js
// Standard — alles rein
await window._selfTest()

// Schnell ohne S8
await window._selfTest({mode:'quick'})

// Nur Security-Audits (am schnellsten)
await window._selfTest({mode:'security'})
```

## Ergebnis

1. **Console.group**: farbkodiert rot (fail) oder grün (all green) mit Total-Zeit
2. **Console.table**: pro Helper `{ok, ms}`
3. **localStorage**: `selftest_last_run` JSON mit vollen Results
4. **Toast**: `SelfTest: N/M ✅/⚠ (Tms)`

## Regression-Test-Workflow

Vor einem Release (oder v-Bump):
```js
// Pre-Change Baseline:
const before = await _selfTest({mode:'quick'});
// Code-Change...
// Re-Test:
const after = await _selfTest({mode:'quick'});
// Beide summary.failed vergleichen. Wenn after.failed > before.failed → Regression.
```

## Rollen-Matrix (pro Run ausführen)

Sebastian als **admin** + **monteur (schober/paschinger)** + **büro** + **projektleiter (pinger)**:
- Unterschiede in `rlsAudit`-Results zeigen ob RLS-Policies greifen
- `s8Suite` T-B020 prüft Token+User-Konsistenz pro Rolle
- `b017check` zeigt Window-Exposures (Admin=Helpers, Non-Admin=nichts)

## Troubleshooting

**Fehler: "function is not a function"**: ein Sub-Helper fehlt (noch nicht deployed oder gelöscht). Self-Test überspringt ihn, läuft trotzdem durch.

**Toast warn aber console grün**: Check localStorage `selftest_last_run.results` — dort steht pro Helper der err.

**Dauer >30s**: perfBench misst DB-Latenz. Wenn 9× >1000ms: INDEX_AUDIT_v3.6+7 deployen.
