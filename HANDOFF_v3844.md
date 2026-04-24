# HANDOFF · v3.8.44 Bug-Hunt-Safety-Fixes · 2026-04-24

**Baseline:** `a187e47` (admin_reset_password recovery SQL)
**End-State:** `af555fd` · tag `v3.8.44` · origin/main synced

## TL;DR

5 von 6 geplanten Bug-Hunt-Findings gefixt, 1 geskipped (H1-Zone). Pytest 184 → 203 (+19). Brackets stabil über alle Fixes. Single-commit-pro-Fix + 1 Bump-Commit.

## Commits (6 + 1 Bump)

| SHA | Subject | Finding |
|---|---|---|
| `b80610c` | fix(safety): _safeJsonParse helper + migrate 5 sites | S2.1 |
| `5ad9b04` | fix(safety): SpeechRec length-guard | S2.4 |
| `caec859` | refactor(time): TIME_* constants + migrate 22 magic-numbers | S1.3 |
| `d1eadf2` | docs: inline comment for password_hash deref safety | S2.2 |
| `b910ce2` | docs: inline comment for deleteLayer persistence note | S3.3 |
| `af555fd` | v3.8.44 bump after bughunt-safety fixes | — |

## Delta per Finding

### S2.1 · `_safeJsonParse` Helper ✅
- Helper definiert bei L1285 (nach `_storagePath`, vor `_toSnake`).
- Behavior: null/undefined/leerer String → fallback; parse-fail → fallback; success → value.
- **5 Sites migriert** (non-H1):
  - L4014 `wp.data||'[]'` (Wochenplan)
  - L6764 `a.details||'{}'` (Activity-Log Detail)
  - L6941 `log.details||'{}'` (Activity-Log Filter)
  - L7285 `d.data||'{}'` (FinkZeit stats)
  - L12802 `d.data||'{}'` (FinkZeit fetch)
- **Nicht migriert:** 46 weitere Sites (H1-Zonen Auth/Juprowa, komplexe Fallback-Logik mit Array-Check, Inline-Boolesche Fallbacks).
- Tests: +10 (`tests/test_safejsonparse_helper.py`).

### S2.4 · SpeechRec Length-Guard ✅
- L3264 vorher: `rec.onresult=e=>{const t=e.results[e.results.length-1][0].transcript;…}`
- Jetzt dreistufige Prüfung (`e/e.results/e.results.length` → `last` → `last[0]/transcript`).
- Race-Condition bei Speech-Cancel kann keine TypeError mehr werfen.
- L5460 war bereits defensive (for-loop mit length-check) — unberührt.

### S1.3 · TIME-Konstanten ✅
- `TIME_SECOND=1000` · `TIME_MINUTE=60*TIME_SECOND` · `TIME_HOUR` · `TIME_DAY` · `TIME_WEEK`
- Platzierung direkt vor `window._fmtDate` (L501).
- **22 Magic-Numbers migriert** via bulk-replace:
  - 5× `3600000` → `TIME_HOUR` (Timer-Display, hAlt-Calculations)
  - 17× `86400000` → `TIME_DAY` (Pickerl/Service-Fristen, Calendar-Math)
- `_fmtRelative` (Sekunden-Math) NICHT migriert — "Sekunden pro Stunde" ist etablierte Idiomatic.
- Tests: +9 (`tests/test_time_constants.py`).

### S2.2 · password_hash-Kommentar ✅
- Inline-Kommentar an L1904 vor `compareSync`-Aufruf.
- Dokumentiert dass `users[0].password_hash` durch vorausgehende Guards (L1896 length, L1900 null-check) garantiert ist.

### S3.3 · deleteLayer-Kommentar ✅
- Inline-Kommentar an L9369.
- Dokumentiert dass layers aktuell UI-only sind (kein SQ.push), mit Hinweis für zukünftige Persistenz (canDo-Guard).

### S2.3 · OFFA-PDF-Datum-NaN-Guard ⛔ SKIPPED
- **Grund:** `_parseOffaPdf` ist in H1-Schutzzone (OFFA-Parser).
- In URLAUB_STATUS + nächste Non-H1-Session dokumentiert.

## Tests

- Gesamt: **203/203 grün** (184 → 203, +19 netto)
- `tests/test_safejsonparse_helper.py` neu (10 Tests)
- `tests/test_time_constants.py` neu (9 Tests)
- Alle anderen Test-Files unverändert.

## Brackets

`() -2 {} 0 [] 0` stabil über alle 5 Code-Modifikationen + 1 Bump.

## Nicht in dieser Session (Remaining)

- **S2.3** OFFA-PDF-Datum-Guard — H1-Zone, separate Session nötig (mit Sebastian-Input zu OFFA-Flow)
- **S3.4** `delFolder` Guard-Audit — nicht inspiziert
- **S3.5** `delPhoto` canDo-Audit — nicht inspiziert
- **46 weitere JSON.parse-Sites** — Bulk-Migration riskiert Logging-Verluste, pro-Section wenn angefasst
- **S7.2** Modal-`_confirmModal`-Helper (UX-Konsistenz) — separater 1.5 h Task

## H-Rules-Bilanz

- **H0 Pfad-Lock:** ✅ alle Commits aus T:\05_Claude\...\epkolar-app
- **H1 Kritische Zonen:** ✅ Auth/Juprowa/SyncQueue/_mapBody/OFFA-Parser unberührt (S2.3 SKIP deshalb)
- **H2 Kein Supabase-Write:** ✅
- **H3 Bracket-Drift:** n/a (kein Drift aufgetreten)
- **H4 Bump am Ende:** ✅ ein v3.8.44-Bump nach allen 5 Fixes
- **H5 Triade nach jedem Fix:** ✅ syntax + brackets + pytest grün
- **H6 2× Skip-Regel:** n/a (nur 1 Skip)
- **H8 Ehrlich:** ✅ S2.3 klar als SKIP deklariert

## Sebastian-Empfehlung

- **Live-Smoke** v3.8.44: AS editieren, Push funktioniert weiter (keine Juprowa-Änderung); Console prüfen auf neue Warnungs-Breadcrumbs.
- **Nächste Code-Session**: S2.3 OFFA-PDF, S3.4/S3.5 Folder/Photo-Delete-Guards.
- **Langfrist**: 46 verbleibende JSON.parse-Sites pro Session schrittweise migrieren wenn sowieso angefasst.

## KeepAwake

War bei Tag-6-Cleanup beendet; für diese Session nicht neu gestartet (interaktiv, kurz).
