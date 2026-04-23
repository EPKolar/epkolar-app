# EPKolar Static Test-Suite

Pytest-based **static invariant tests** for `index.html` und `sw.js`. Läuft komplett offline — keine Browser-Instanz, keine Supabase, keine React-Rendering. Jeder Test ist eine Aussage über den Quelltext (Grep, Regex, Parse).

## Warum Python + Static?

- JS-Unit-Tests bräuchten ein Bundle + jsdom → viel Build-Infrastruktur für eine Single-File-App
- Viele Invarianten sind **strukturell** (Funktionen existieren, Patterns vorhanden, Versionen synced)
- CI-ready: `python -m pytest tests/` geht in ~1 s

## Scope

- ✅ Sanity-Checks: Datei existiert, Größe plausibel, Bracket-Baseline
- ✅ Versionierung: APP_VERSION ↔ CACHE_NAME ↔ sw.js-Header synced
- ✅ Helper-Präsenz: `_n`, `canDo`, `_authRetry`, `_OFFPW`, `ODB` definiert
- ✅ Security-Invariants: kein `eval()`, kein `document.write`, Offline-PW-Hash ≠ reines base64
- ✅ canDo Matrix: mind. N Actions erfasst
- ✅ Doku-Präsenz: Audit-Docs da (CANDO_MATRIX, _authretry_gaps, SMOKE_TESTS)

## Out of Scope

- Runtime-Behavior (UI, API-Calls)
- Supabase-RLS-Validierung (separate SQL-Tests)
- Visual Regression
- E2E / User-Journey

## Run

```bash
# Setup (einmalig)
cd tests && pip install -r requirements.txt && cd ..

# Run
python -m pytest tests/ -v
```

Erwartet: 25 / 25 passing.

## Struktur

- `conftest.py` — shared fixtures (load index.html, sw.js, etc.)
- `test_invariants.py` — Datei-Größen, Bracket-Baseline, Kernstruktur
- `test_versioning.py` — APP_VERSION ↔ CACHE_NAME Sync
- `test_helpers.py` — _n, canDo, _authRetry, _OFFPW, ODB Präsenz
- `test_security.py` — XSS-/Code-Injection-Sinks
- `test_cando.py` — canDo Matrix-Integrität
- `test_docs.py` — Audit-Doku-Präsenz

## Erweiterung

Neue Tests sollten:
1. Einen klaren Invarianten-Namen haben (`test_<was>`)
2. Schnell sein (<100 ms)
3. Keinen Internet-Zugriff
4. Kein Re-Run des SQL-Deploys
5. Aussagekräftig fehlschlagen (Message zeigt exakt was kaputt ist)
