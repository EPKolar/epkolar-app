# Fahrzeug/Werkzeug Dual-Storage — Design & Migrationsvorschlag (Pre-Live-Task)

**Status: NUR DESIGN. Kein Code, keine Migration angewendet.** Daten-Modell-Entscheidung für Sebastian.
Quelle: Overnight-Agenten-Hunt 2026-06-07 (`AGENT-HUNT-FINDINGS-2026-06-07.md` Findings Fahrzeug 1-4).

## Ist-Zustand (DB-verifiziert 2026-06-07)
Sub-Daten existieren DOPPELT — eingebettet als JSON-Spalte UND als eigene Tabelle:

| Sub-Daten | Eingebettet (genutzt) | Eigene Tabelle | Tabellen-Rows |
|---|---|---|---|
| Schäden | `fahrzeuge.schaeden` (JSON) | `fz_schaeden` (id, fahrzeug_id, datum, beschreibung, fotos, status, kosten, by_user, note, created_at) | **0** |
| Termine | `fahrzeuge.termine` (JSON) | `fz_termine` (id, fahrzeug_id, typ, datum, beschreibung, erledigt, created_at) | **0** |
| Serviceheft | `fahrzeuge.serviceheft` (JSON) | — (nur eingebettet) | — |
| Tank/KM-Log | `fahrzeuge.tank_log` / `km_log` (JSON) | — (nur eingebettet, korrekt read-modify-write) | — |
| Werkzeug-Serviceheft | `werkzeuge.serviceheft` (JSON) | — | — |

`fahrzeuge` = 17 Rows. **fz_schaeden/fz_termine sind LEER** → die eingebetteten JSON-Spalten sind die
**de-facto Quelle der Wahrheit**; die separaten Tabellen sind angelegt aber faktisch tot (Dual-Write läuft
ins Leere oder scheitert still).

## Wo es divergiert / bricht
1. **Voll-Objekt-PUT clobbert JSON-Sub-Arrays** (`index.html:17298` `upd`): jede Feldänderung sendet das ganze
   In-Memory-Fahrzeug per PUT → generischer PATCH überschreibt `schaeden/termine/serviceheft` last-write-wins,
   keine Optimistic-Concurrency. 2 Geräte / stale Closures → Sub-Eintrag geht verloren. **Kernursache.**
2. **Schäden Half-Write**: `addSchaden` schreibt eingebettet (17376) UND in `fz_schaeden` (17380, landet aber
   nicht → 0 Rows); Status-Änderung (18126) nur eingebettet. → wer je `fz_schaeden` liest, sieht nichts/„offen".
3. **Termine gespalten**: `addTermin/togTermin/delTermin` (17288/17294) gegen `fz_termine`-Tabelle (leer),
   aber UI rendert `selFz.termine` (18018, eingebettet) + Toggle/Delete (18021/18022) via Voll-PUT in die Spalte.
   Zwei Pfade, nie synchron.

## Vorschlag: EINE Quelle der Wahrheit (analog YachtLog Track-Unification)

### Option B (EMPFOHLEN) — separate Tabellen kanonisch
`fz_schaeden` / `fz_termine` werden die einzige Quelle; eingebettete Spalten deprecaten (Altdaten bleiben read-only).
Serviceheft analog in neue Tabelle `fz_serviceheft` (existiert noch nicht) auslagern. Werkzeug-Serviceheft → `wz_serviceheft`.
**Vorteil:** löst die Clobber-Kernursache strukturell — einzelne Rows statt JSON-Array im Voll-PUT, kein last-write-wins,
feingranulare INSERT/UPDATE/DELETE pro Eintrag, RLS pro Row möglich.
**Migrationspfad:**
1. **Datensicherung zuerst:** `CREATE TABLE _backup_fahrzeuge_subdata AS SELECT id, schaeden, termine, serviceheft, tank_log, km_log FROM fahrzeuge;` (+ analog werkzeuge.serviceheft). Export als SQL-Dump.
2. Fehlende Tabellen anlegen (`fz_serviceheft`, `wz_serviceheft`) + RLS analog is_staff/own-record.
3. **Backfill-Skript** (idempotent): pro Fahrzeug die JSON-Arrays auslesen, je Eintrag eine Row in die Zieltabelle
   (id beibehalten falls vorhanden, sonst gen_random_uuid; fahrzeug_id setzen). Dry-run + Count-Abgleich (JSON-Array-Länge == Row-Count) vor Commit.
4. **Frontend umstellen:** `upd` Voll-PUT auf Whitelist skalarer Stammdaten beschränken (NIE schaeden/termine/serviceheft
   im Voll-PUT); add/tog/del der Sub-Daten ausschließlich gegen die Tabellen (wie `togTermin(t.id)`/`delTermin(t.id)`
   es teilweise schon tun, 18109/18110); UI-Reads von den Tabellen (`getFzTermine` etc.).
5. Eingebettete Spalten 1-2 Releases als Fallback behalten (read-only), dann droppen.
**Risiken:** Backfill-Fehler (Mitigation: Backup + Dry-run + Count-Abgleich + idempotent); Frontend muss ALLE
Sub-Daten-Pfade konsistent umstellen (sonst neue Divergenz); Offline-Sync der granularen Ops über SQ testen.

### Option A (minimal) — eingebettet kanonisch
Eingebettete JSON-Spalten bleiben Quelle; tote Writes nach `fz_schaeden`/`fz_termine` entfernen; `upd` auf
Field-Whitelist beschränken (schaeden/termine/serviceheft NIE aus Voll-PUT). **Vorteil:** keine Daten-Migration
(Tabellen leer). **Nachteil:** Clobber-Risiko bleibt grundsätzlich (JSON-Array im selben Row), nur entschärft.

## Empfehlung
Da die separaten Tabellen LEER sind, ist der Migrationsaufwand für Option B **moderat** (Backfill aus 17 Fahrzeugen,
keine Konfliktauflösung mit bestehenden Tabellen-Daten). Option B löst die Kernursache strukturell → empfohlen als
**Pre-Live-Task**. Falls Zeitdruck: Option A als Zwischenschritt (Field-Whitelist im `upd`) entschärft sofort den
schlimmsten Clobber, ohne Migration.

> Out-of-scope dieser Aufgabe: kein Code/keine Migration jetzt. Erst nach Sebastian-Entscheidung A vs B + dediziertem,
> getestetem Sprint mit Backup.
