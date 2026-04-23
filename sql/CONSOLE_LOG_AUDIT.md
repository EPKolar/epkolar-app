# console.log Audit · 2026-04-25 (Overnight #2 Block 4-1)

**Scope:** `index.html`. 31 Treffer analysiert. **Kein Code-Fix notwendig** — alle Treffer sind in Dev-Helfern oder legitimen Loggern.

## Klassifikation

| # | Line | Kontext | Typ |
|---:|---:|---|---|
|  1 | 375 | `_runSmokeTests` Inline-Logger | DEV-HELPER |
|  2 | 384 | `_checkIntegrity` Inline-Logger | DEV-HELPER |
|  3 | 461 | Kommentar-Beispiel (`_log` usage) | Doku |
|  4 | 479 | `window._setLogLevel` Bestätigung | User-Action-Log |
|  5 | 486 | `dlog` Wrapper (gated durch DEBUG-Flag) | Dev-only-Helper |
|  6 | 539 | `window._runSmokeTests` Header | DEV-HELPER |
|  7 | 541 | `_runSmokeTests` Inline-Logger | DEV-HELPER |
|  8 | 584 | `_runSmokeTests` Summary | DEV-HELPER |
|  9 | 614 | `window._mobileCheck` Threshold-Info | DEV-HELPER |
| 10-14 | 625,650-654 | `window._rlsAudit` Expect-Vorgabe | DEV-HELPER |
| 15-16 | 687-688 | `window._perfBench` Baseline-Info | DEV-HELPER |
| 17-19 | 768-769, 778 | `_forceExpireToken`/`_restoreToken` Dev-Flow | DEV-HELPER (dev-gated) |
| 20 | 837 | `_thunderTest` Results | DEV-HELPER (dev-gated) |
| 21-23 | 877-909 | `_a11yCheck` Summary | DEV-HELPER |
| 24-27 | 909-916 | `_syncDiag` Output | DEV-HELPER |
| 28 | 1024 | `_s8Suite` Summary | DEV-HELPER |
| 29 | 1059 | `_b017check` Output | DEV-HELPER |
| 30-31 | 1235-1236 | `S8-107c` Timing | DEV-HELPER |

## Ergebnis

**Keine Production-Noise-Logs.** Alle 31 Treffer sind in manuell aufrufbaren `window._*` Dev-Helpers. Die `dlog`-Funktion (L486) ist bereits mit `DEBUG`-Flag gegated.

## Pattern-Konsistenz

Der Code-Style ist sauber:
- User-Feedback läuft über `window.__toast`
- Errors über `console.error` (Block-D XSS-Audit v3.8.37 erhöht)
- Warnings über `console.warn`
- Info-Logs nur in Dev-Helpers (oder via `dlog` gated)

## Keine Aktion

Gemäß H1/H5: Code nicht anfassen. Block 4-1 damit closed als "Audit, kein Fix nötig".
