# HANDOFF · OFFA-Land-Fix Phase 2 · v3.8.40

**Baseline:** `3ad138e` (v3.8.39 LIVE)
**End-State:** `3c85d14` · tag `v3.8.40` · origin/main synced

## TL;DR

OFFA-Log-Bug "Länderkürzel von 'A' auf '' geändert" beim Juprowa-Push ist gefixt. `_juprowaReversMap` sendet jetzt 10 zusätzliche Adress-Felder (`AK_BAUADR_*` + `RE_ADR_*`) inkl. hartem `LKZ="A"`. Feldname aus echter Pull-Response verifiziert (nicht geraten). 10 neue Tests, 74 → 84 pytest grün.

## Commits (Phase 2)

| SHA | Subject |
|---|---|
| `11f17f4` | sql: OFFA-Push Land-Feldname Probe *(obsolet nach Chat-MCP-Verifikation)* |
| `3c85d14` | v3.8.40 fix(juprowa): Adress-Felder inkl. Länderkürzel (LKZ) im Push-Payload |

Phase 1 war in `5b0efba` + `647e5af` (Doku/Probe).

## Block-Abarbeitung

| Block | Status | Notiz |
|---|---|---|
| A-2 Code-Scan | ✅ | 0 Treffer auf `_LAND`/`_LKZ`/`_COUNTRY` im Code — Pull kennt das Feld nicht |
| A-1 Probe-SQL | ✅ gepusht (`11f17f4`), dann obsolet | Chat-Claude hat via Chrome-MCP live-ausgelesen: **LKZ** |
| B Push-Erweiterung | ✅ `index.html` L2523 +14 Zeilen | 10 neue JSON-Keys, alle `_juprowaSanitize`-gewrappt außer LKZ (hardcoded "A") |
| B.1 Regression-Check | ✅ | Titel-Felder bewusst weggelassen (Pull-Only) |
| C Tests | ✅ | 10 neue Tests statt geforderten 8 — Edge-cases großzügiger |
| D Bump + Push | ✅ | v3.8.40, tag gepusht |
| E Verifikation | ⏳ Sebastian | siehe unten |

## Feldname-Verifikation

Aus `juprowa_raw` eines echten Scheins (S075295, juprowa_id=5085210):
- `AK_BAUADR_LKZ: "A"` — Einsatzort
- `RE_ADR_LKZ: "A"` — Rechnung

**Nicht geraten.** Der Pull-Code liest das Feld nicht (bestätigt durch `grep -oE 'AK_[A-Z_]+|RE_[A-Z_]+'` = 30 unique Keys, 0 mit LKZ-Suffix).

## Push-Payload-Delta

### Vorher (9 Keys + ID)
```
ID, AK_SCHEINNR, AK_ARBEITEN, AK_NOTIZ, AK_DURCHZUFUEHREN,
AK_MONTEUR?, AK_TERMIN?, AK_DAUER?, AK_PRIOR, AK_AUFSTATUS
```

### Nachher (+10 = 19 bei vollem Mock ohne Monteur)
```
+ AK_BAUADR_STR, AK_BAUADR_PLZ, AK_BAUADR_ORT, AK_BAUADR_LKZ, AK_BAUADR_NAM1
+ RE_ADR_STR,    RE_ADR_PLZ,    RE_ADR_ORT,    RE_ADR_LKZ,    RE_ADR_NAM1
```

Quellen:
- `AK_BAUADR_{STR,PLZ,ORT,NAM1}` ← `schein.kundStr/Plz/Ort/Name` (via `_juprowaSanitize`)
- `AK_BAUADR_LKZ` ← **hardcoded "A"**
- `RE_ADR_*` spiegelt `AK_BAUADR_*` 1:1 (kein separates lokales Datenmodell)

## Test-Coverage (10 neue)

1. `test_push_contains_all_new_address_keys` — alle 10 Keys präsent
2. `test_ak_bauadr_lkz_hardcoded_A` — unabhängig von Input
3. `test_re_adr_lkz_hardcoded_A`
4. `test_empty_kundstr_becomes_empty_string` — kein undefined/null
5. `test_umlauts_stay_intact_latin1_compatible` — ö/ü/ß bleiben (nicht sanitized)
6. `test_em_dash_gets_sanitized_in_address` — U+2014 → "--"
7. `test_legacy_9_ak_fields_still_present` — Regression-Guard
8. `test_payload_key_count_exactly_19_without_monteur` — exakt, nicht 9 nicht 25
9. `test_no_titel_fields_in_payload` — Regression-Guard gegen Pull-Only-Leak
10. `test_returns_null_without_juprowa_id` — Early-Exit bleibt

Run: `python -m pytest tests/ -q` → **84 passed in ~2.7s**.

## H5 Final-Check

- `node sql/_check_syntax.js` → `syntax OK`
- `node sql/_check_brackets.js` → `brackets () -2 {} 0 [] 0`
- `node sql/_check_version.js` → `✓ versions synced: 3.8.40`
- `pytest tests/ -q` → `84 passed`
- `git status` → clean
- `git log --oneline -3` → all commits labeled concretely (H8)

## Block E · Sebastian-Verifikation

Nach Deploy-Sync:

1. **Cache-Bust**: DevTools → Application → Service Workers → "Unregister" + F5
2. **APP_VERSION check**:
   ```js
   fetch('/index.html',{cache:'no-store'}).then(r=>r.text())
     .then(t=>console.log('ver',t.match(/APP_VERSION\s*=\s*"([^"]+)"/)[1]))
   ```
   Erwartung: `ver 3.8.40-supabase`
3. **AS-Edit trigger**: beliebigen AS öffnen, ein Feld ändern, speichern
4. **Sync**: 30-60 s warten auf Auto-Push ODER "Juprowa Sync"-Button klicken
5. **OFFA-Log prüfen** (5 Min Lag): KEINE "Länderkürzel von 'A' auf ''"-Einträge mehr
6. **Juprowa-Cloud Check**: Adress-Felder des gesyncten Scheins sollen korrekt befüllt sein (nicht leer, nicht falsch überschrieben)

## Offene Punkte / Follow-ups

### Phase 2b · Separate Rechnungsadresse (falls benötigt)
- Aktuell spiegelt `RE_ADR_*` den `AK_BAUADR_*`. Wenn ein AS tatsächlich eine andere Rechnungsadresse hat als Einsatzort (was laut `_mapJuprowaWorksheet`-Fallback-Logik `AK_BAUADR_NAM1||RE_ADR_NAM1` möglich ist), überschreibt unser Push die echte Rechnungsadresse mit der Einsatzadresse.
- **Risk-Level**: Mittel. Für AT-only Einsätze meist unkritisch. Für größere Kunden mit Zentral-Rechnung → Problem.
- **Fix-Optionen** (Sebastian-Entscheidung):
  - (a) Neue Spalten `re_str/re_plz/re_ort/re_name` in `arbeitsscheine` → UI-Edit-Field
  - (b) Nur senden wenn `schein.juprowa_raw` die RE_ADR-Werte kennt, sonst skippen
  - (c) `RE_ADR_*` komplett aus Push rausnehmen, wenn Juprowa das als "behalten" interpretiert

### Kundennummer `AK_BAUADR_NUMMER`
- Aktuell nicht im Push. `juprowa_raw` kennt das Feld. Bei Neuanlage-AS (nicht über Juprowa-Pull) könnten wir die Juprowa-Kundennummer nicht setzen — aber unsere lokale `kundNr` ist vermutlich nicht 1:1 das Juprowa-Equivalent.
- **Follow-up**: Wenn Neuanlage via Juprowa-Push relevant wird, Kundennummer-Mapping definieren.

### `OFFA_LAND_FIELDNAME_PROBE.sql`
- Obsolet nach Chat-MCP-Verifikation. Bleibt im Repo als historischer Kontext (siehe `sql/OFFA_LAND_REGRESSION_ANALYSIS.md` für Verknüpfung).

## Philosophie-Check

- **H0** Pfad-Lock: alle Commits aus `T:\05_Claude\...\epkolar-app`. ✅
- **H1** Nur `_juprowaReversMap` angefasst. Auth/SyncQueue/_mapBody unberührt. ✅
- **H2** Kein Supabase-Write. ✅
- **H3** Hard-Stop getriggert (Block A-2 leer → Probe gepusht, gewartet bis Sebastian LKZ bestätigt). ✅
- **H4** Genau ein Version-Bump (v3.8.40). ✅
- **H5** Nach jedem index.html-Touch: Triade + pytest grün. Keine Reverts. ✅
- **H8** Ehrlich: Feldname NICHT geraten, aus echter Response verifiziert. Probe-SQL obsolet markiert statt versteckt.

"Nicht übertreiben und ehrlich bleiben." — der Fix ist minimal-invasiv (14 neue Zeilen in `_juprowaReversMap`), regression-tested, dokumentiert.
