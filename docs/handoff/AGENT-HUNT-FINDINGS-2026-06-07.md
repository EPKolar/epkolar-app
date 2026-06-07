# Overnight-Agenten-Bug-Hunt — Funde 2026-06-07 (Welle 1)

3 read-only Audit-Agenten. **GEFIXT:** KW-ISO-Wochenjahr (s.u.). **Die folgenden sind strukturell/größer → NICHT blind
gefixt, brauchen Sebastian-Entscheidung/Freigabe** (jeweils mit Datei:Zeile + Fix-Vorschlag).

## ✅ GEFIXT v3.9.158 — KW-Key Off-by-one an Jahresgrenzen (BWB-Export)
`getProjectData`/Filter mischten Kalenderjahr (`getFullYear`) mit ISO-Wochennummer (`_kwFromDate`) → an
Jahreswechseln falsche KW-Beschriftung + falscher `_kwDates`-Datumsbereich im Bauwochenbericht (Kunden+ÖBA).
Fix: `_kwYearFromDate()` (ISO-Wochenjahr) + an allen 9 Stellen (1 Key `-`, 1 Key `-KW`, 7 Filter) ersetzt.
Node-Repro verifiziert: 2024-12-30→`2025-01`, 2027-01-01→`2026-53`, 2022-01-01→`2021-52` (alle range-contains true).

## Sync-Queue / Offline-Sync (Agent 1) — sync-core, delikat
1. **[HOCH] 403-Wedge** `index.html:~1810/5141`: `_isAuthErr` behandelt 401 UND 403 als Session-Fehler →
   `doSync` macht `break`. Ein permanentes 403 (RLS-Denial, z.B. Monteur darf Zeile nicht schreiben) bleibt
   ewig vorn in der Queue + blockiert ALLE nachfolgenden Syncs (Banner steckt, pendingCount>0 permanent).
   Fix: 403 nach erfolglosem Refresh = permanenter Client-Fehler → Retry-Zähler + `continue` statt `break`.
2. **[HOCH] POST nicht idempotent** `index.html:~5151/1811`: `_sbPost` reiner POST. Server-Write erfolgreich,
   aber Response-Read scheitert transient (flakiges Mobilnetz) → Item bleibt → Re-POST. PK-Routen → 409 →
   falscher „verworfen"-Alarm trotz gespeicherter Daten; read-modify-write-Routen (serviceheft 1986, tank_log
   2003, km_log 2008/2026) → **echtes Duplikat** im Protokoll. Fix: `_sbUpsert` statt `_sbPost` (Client-id da)
   + id-Dedupe vor `arr.push`.
3. **[HOCH] Kein Backoff** `index.html:5135-5151`: Retry-Zähler ohne Zeit-Backoff → vergiftetes Item dreht
   Hot-Loop bei jedem Trigger, brennt 5 Versuche in Sekunden → verfrühter Datenverlust-Alarm. Fix: `_nextRetryAt`
   exp. Backoff (cap 60s).
4. **[HOCH] PhotoQ.flush break-on-any-error** `index.html:2547`: ein kaputtes Foto blockiert Upload aller
   nachfolgenden Fotos (bis 10× gescheitert). Fix: bei permanentem Fehler `continue`, `break` nur offline/5xx.
5. **[MITTEL/strukturell] worker_projects Lost-Update** `index.html:2082/5868`: DELETE-then-UPSERT ganze Liste
   = last-write-wins; 2 Geräte togglen parallel → überschreiben sich komplett. Fix: feingranulare INSERT/DELETE
   einzelner Zeilen statt „Liste ersetzen".

## Fahrzeuge / Werkzeuge (Agent 3) — Sub-Daten-Clobber + Dual-Storage (war als Architektur-Entscheidung gemerkt)
1. **[KRITISCH] Voll-Objekt-PUT clobbert Sub-Arrays** `index.html:17298` (`upd`): jede Feldänderung sendet ganzes
   `{...f}` per PUT → generischer PATCH (2153-2159) überschreibt `serviceheft/schaeden/termine` last-write-wins,
   keine Optimistic-Concurrency. Clobbert sogar single-device aus stale Closures. Fix: nur Delta-Feld patchen
   ODER Whitelist erlaubter Top-Level-Felder im Spezial-Handler (1995); Sub-Arrays nie aus Voll-PUT schreiben.
2. **[KRITISCH] Termine Dual-Storage** `fz_termine`-Tabelle (17288/17294) vs `fahrzeuge.termine`-Spalte
   (18021/18022): zwei Quellen, nie synchronisiert. Fix: `fz_termine` kanonisch, Spalte deprecaten, Buttons auf
   `togTermin(t.id)`/`delTermin(t.id)` (wie 18109/18110).
3. **[HOCH] Schäden Dual-Write + Half-Write** `addSchaden` 17376 (Spalte) + 17380 (`fz_schaeden`-Tabelle);
   Status-Änderung 18126 nur Spalte → `fz_schaeden` veraltet „offen". Fix: eine Quelle vereinheitlichen.
4. **[HOCH] Werkzeug save() Voll-PUT** `index.html:18326` überschreibt `serviceheft` mit stale `openEdit`-Snapshot
   (vs debounced `_pushWzSh` 18221). Fix: `serviceheft`/`fotos` aus `save()`-body strippen.
5. **[MITTEL] Generischer PATCH ohne Field-Whitelist** `index.html:2153-2159`: schreibt alle Body-Felder inkl.
   `_mapFahrzeug`-Defaults (kmStand:0) → potenzielle Null/Default-Overwrites. Fix: Whitelist skalarer Stammdaten.

**Sauber bestätigt (kein Bug):** Zeit/Stunden-Mathematik+Rundung (Agent 2), JSON-Parse-Pfade defensiv, tank/km-Log
korrekt read-modify-write, Mutex-Disziplin `_serial` (v3.9.149).

> Empfehlung: 403-Wedge (#1 Sync) + PhotoQ-break (#4 Sync) sind eng begrenzt + hoher User-Impact → gute Kandidaten
> für einen gezielten Fix mit Freigabe. Die Fahrzeug-Dual-Storage-Familie ist ein größerer Umbau (wie YachtLog
> Track-Unification) — Daten-Modell-Entscheidung.
