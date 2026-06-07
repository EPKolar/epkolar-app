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

## 🧪 Verhaltens-Test (echter Laufzeit-Beweis, nicht nur pytest) — `scripts/verify_sync_behavior.cjs`
Node-Harness repliziert die ECHTE doSync-Loop (index.html:5135-5166 v3.9.159) + PhotoQ.flush (2540-2553 v3.9.160)
VERBATIM mit gemockten Calls. **Ergebnis 2026-06-07: ALLE GRÜN (exit 0)** — beide Fixes bewiesen, kein Revert:
- **A (403-Wedge):** [403, ok1, ok2] → Run1: ok1+ok2 durchgelaufen, 403 bleibt mit _retries=1 (kein break-Wedge);
  nach 5 Runs → 403 in `syncQueueFailed`, Queue leer. ✅
- **B (transient):** [5xx, ok3] → 5xx bricht ab, ok3 NICHT verarbeitet, beide bleiben, nichts gedroppt (Queue hält+retryt). ✅
- **C (401):** [401, ok4] → 401 break, ok4 nicht verarbeitet, 401 bleibt (Re-Auth-Pfad unverändert). ✅
- **D (PhotoQ):** [kaputt, gut1, gut2] → gut1+gut2 hochgeladen, kaputtes='error' (sichtbar), KEIN break. ✅
- **E (PhotoQ transient):** [offline, gut3] → break, gut3 nicht hochgeladen, offline='error'. ✅
Reproduzierbar: `node scripts/verify_sync_behavior.cjs`.

## ✅ Fix-Status 2026-06-07 (eng begrenzte Fixes, je eigener Commit, Triade grün)
- **FIX 1 — 403-Wedge: ✅ GEFIXT** v3.9.159 (`109c24b`). doSync breakt nur noch bei 401; 403 (RLS-Denial) fällt in
  Retry/Drop wie permanenter 4xx → blockiert die Queue nicht mehr. Transiente Fehler stoppen weiterhin. Kein _juprowaPush.
- **FIX 2 — PhotoQ-Block: ✅ GEFIXT** v3.9.160 (`d41f2e8`). Kaputtes Foto → status:"error" (sichtbar) + skip; nur
  transiente Fehler (offline/5xx/408/429) stoppen den Lauf. Nachfolgende Fotos laufen weiter.
- **FIX 3 — POST-Idempotenz: ⛔ GATED → NICHT angewendet, dokumentiert.** Grund (H6): Der saubere Idempotenz-Fix
  (Upsert auf der geteilten `_sbPost`-Schreibhilfe) würde den Pfad anfassen, den **`_juprowaPush` ebenfalls nutzt**
  (`index.html:~3116` `_sbPost('activity_log',...)`). Per Gate-Regel daher nicht gefixt. **Empfohlener Fix für
  dedizierten Sprint:** (a) read-modify-write-Handler serviceheft/tank/km id-Dedupe vor `arr.push`
  (`if(!arr.some(x=>x.id===body.id))arr.push(body)`) — berührt _juprowaPush NICHT, wäre der sichere Teil; (b) doSync
  409 (Row existiert bereits) als Erfolg behandeln statt Retry/Drop → kein falscher „verworfen"-Alarm. Beide getrennt
  + getestet, ohne `_sbPost` global umzustellen.
- **KRIT Fahrzeug Dual-Storage: dokumentiert** → `docs/handoff/FAHRZEUG-DUAL-STORAGE-DESIGN.md` (Ist-Zustand,
  fz_schaeden/fz_termine LEER = eingebettete JSON-Spalten de-facto Quelle, Option A/B, Migrationspfad+Backup+Risiken,
  Pre-Live-Task). Kein Code/keine Migration jetzt.
