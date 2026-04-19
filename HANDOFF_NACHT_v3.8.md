# HANDOFF NACHT v3.7.0 → v3.8.0 · 14h-Run · 2026-04-19 16:22

## Start
- HEAD: `879c535` (v3.7.0)
- Baseline-Brackets: `() -2 {} 0 [] 0` (siehe `baseline_v3.8_start.txt`)
- `node --check`: OK

## Vorherige Findings (aus BUG_HUNT.md v3.7.0)

- **M-1 P2** `_isJwtShape`-Härtung: atob/JSON.parse im `_isJwtShape` kann bei garbage werfen. Fix: try/catch wrap.
- **M-2 P1** photos-Tabelle RLS: möglicherweise keine RLS-Policy → 25k Fotos anon-readable.
- **M-3 P3** `_authRefreshInflight` 50ms-race hypothetisch.
- **M-4 P2** localStorage `epkolar_gc` speichert base64-encoded Password.

## DB-State vor Run-Start (bereits geschlossen)
- **B-020 DB-Teil**: 9×OK verified am 19.04 ~14:00 (Sebastians Check). `sql/B020_FIX.sql` alle Schritte ausgeführt. In Block 0.3 NICHT re-executed.

## Blocks

