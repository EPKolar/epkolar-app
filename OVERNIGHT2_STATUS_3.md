# OVERNIGHT #2 · STATUS · Block 3 · Test-Expansion

**Baseline:** `9212cc9`
**End-State:** (nach Block 3 commit)
**Ergebnis:** pytest **34 → 74** (+40 Tests). Target 60+ übertroffen.

## Sub-Tasks

| ID | Theme | Tests | Status |
|---|---|---:|---|
| 3-1 | `_n()` Roundtrip | 10 | ✅ Node-Behavior |
| 3-2 | `kunde_freigabe` Integer-Coercion | 3 | ✅ Structural |
| 3-3 | `_juprowaSanitize` Latin-1 | 11 | ✅ Node-Behavior |
| 3-4 | `EP_AUTO_FILTER` Zählung | 3 | ✅ Structural (77 Gruppen bestätigt) |
| 3-5 | Datum-Parsing | 2 | ✅ Structural (ISO + DE.Pattern) |
| 3-6 | `_mapBody` Whitelist | 3 | ✅ Structural |
| 3-7 | 38.5h vs 40h | 2 | ✅ Structural |
| extra | `_juprowaSanitize` Body-Check | 2 | ✅ |
| extra | MONT-Tabelle | 1 | ✅ |
| extra | TEXT_JSON_FIELDS Doku-Guard | 3 | ✅ |

## Bugfix während Block 3

`run_node_snippet` hatte auf Windows cp1252-stdout-decode → Double-Encoding von UTF-8 Bytes. Fix: explizites `encoding="utf-8"` + `errors="replace"` in `subprocess.run`. Verhindert Regression bei Umlauts-/Em-Dash-Tests.

## Encoding-Lessons learned

Windows-Python schreibt/liest Test-Files teilweise in cp1252. Workaround: für non-ASCII Test-Inputs `\uXXXX` Escape-Sequences in Python Source-Code statt Literal-Chars. Generator-Script in `$TEMP/make_*_test.py` mit `encoding="ascii"` garantiert, dass auch auf fremden Systemen portabel lesbar.

## Run

```bash
python -m pytest tests/ -q
# => 74 passed in ~2s
```

## Keine index.html-Berührung

H1-konform. Alle Änderungen in `tests/` + `conftest.py`.

## Nächster Block

Block 4 (15h→11h im Plan): Safe index.html Fixes. Version-Bumps erlaubt (H4).
- 4-1 console.log/debug Sweep
- 4-2 _n() Sweep für toFixed (partiell durch Overnight #1 v3.8.33 already)
- 4-3 Button disabled-Audit (Doku only)
- 4-4 alt-Attribute Sweep
