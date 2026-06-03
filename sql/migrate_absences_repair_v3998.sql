-- ============================================================================
-- B-A absences-Reparatur (v3.9.98-data) — Sebastian-Service-Role-Run im SQL-Editor
-- ============================================================================
-- KONTEXT (Chat-Claude live + CC-Code-Analyse v3.9.101):
--   Die 30 kaputten absences-Rows stammen vom Kalender-Schreibpfad (tog(), index.html
--   ~Z13960): schreibt from_date/to_date + worker_id + type + note. Daher:
--     - from_date/to_date BEFÜLLT, von/bis LEER (by design des Writers)
--     - worker_id = NAME (Altlast pre-v3.9.100; aktueller Code löst wX via monteure.find)
--     - hours=0 / tage=0 (AKTIVER Bug: KEIN Writer setzt hours — Code-Fix separat in App)
--   Urlaubs-ANTRÄGE laufen über separate Tabelle `urlaubsantraege` (von/bis/art) — hier NICHT betroffen.
--
-- ENTSCHEIDUNG (Sebastian 2026-06-03): KANONISCH = from_date/to_date.
--   Diese Migration: (1) worker_id NAME→wX, (2) hours aus from_date/to_date (7,7h/Tag),
--   (3) worker_name aus workers.name backfillen, (4) von/bis aus from_date/to_date spiegeln
--       (Transit-Sicherheit für Reader die noch von/bis lesen, bis Code-Unification live ist).
--
-- SICHERHEIT: idempotent, NUR kaputte Rows, in Transaktion. Vorher Snapshot.
-- 38,5h-Woche → 7,7h/Tag. Halbtags: KEIN Flag in Schema gefunden → volle Tage gerechnet.
--   ⚠️ Falls einzelne Einträge Halbtage sind, nach der Migration manuell korrigieren
--      (Liste der betroffenen IDs gibt die VERIFY-Query unten aus).
-- ============================================================================

BEGIN;

-- ---- 0) Snapshot für Rollback-Referenz -------------------------------------
DROP TABLE IF EXISTS public._absences_snapshot_v3998;
CREATE TABLE public._absences_snapshot_v3998 AS TABLE public.absences;

-- ---- 1) worker_id: NAME → wX ----------------------------------------------
-- Primär: explizites Mapping (Sebastian-verifiziert, robust gegen workers.name-Format).
UPDATE public.absences a SET worker_id = m.wx
FROM (VALUES
  ('Günther','w6'), ('Schmid','w5'), ('Pinger','w4'), ('Paschinger','w1')
) AS m(nm, wx)
WHERE a.worker_id = m.nm
  AND a.worker_id NOT LIKE 'w%';   -- nur noch nicht-migrierte Rows

-- Fallback: generischer Join über workers.name (fängt evtl. weitere Namen ab).
UPDATE public.absences a SET worker_id = w.id
FROM public.workers w
WHERE a.worker_id = w.name
  AND a.worker_id NOT LIKE 'w%';

-- ---- 2) worker_name backfillen (Display / oder später deprecaten) -----------
UPDATE public.absences a SET worker_name = w.name
FROM public.workers w
WHERE a.worker_id = w.id
  AND (a.worker_name IS NULL OR a.worker_name = '');

-- ---- 3) von/bis aus kanonischen from_date/to_date spiegeln (Transit) --------
UPDATE public.absences
SET von = from_date
WHERE (von IS NULL OR von = '') AND from_date IS NOT NULL;
UPDATE public.absences
SET bis = to_date
WHERE (bis IS NULL OR bis = '') AND to_date IS NOT NULL;

-- ---- 4) hours/tage aus from_date/to_date berechnen (7,7h/Tag) ---------------
-- Inklusive Endtag: (to_date - from_date + 1) Kalendertage. Nur wo hours fehlt/0.
UPDATE public.absences
SET tage  = (to_date::date - from_date::date) + 1,
    hours = ((to_date::date - from_date::date) + 1) * 7.7
WHERE from_date IS NOT NULL AND to_date IS NOT NULL
  AND (hours IS NULL OR hours = 0);

-- ---- VERIFY (vor COMMIT prüfen!) -------------------------------------------
-- a) Keine NAME-worker_id mehr:
--    SELECT count(*) FROM public.absences WHERE worker_id NOT LIKE 'w%';   -- erwartet 0
-- b) Keine hours=0 mehr bei gültigem Zeitraum:
--    SELECT count(*) FROM public.absences WHERE from_date IS NOT NULL AND (hours IS NULL OR hours=0);  -- 0
-- c) Halbtags-Kandidaten (1-Tag-Einträge — manuell prüfen ob ganztags):
--    SELECT id, worker_id, type, from_date, to_date, hours FROM public.absences
--    WHERE from_date = to_date ORDER BY from_date;
-- d) Plausi Gesamt:
--    SELECT worker_id, type, sum(hours) FROM public.absences GROUP BY 1,2 ORDER BY 1,2;

COMMIT;

-- Nach erfolgreichem VERIFY: DROP TABLE public._absences_snapshot_v3998;  (optional aufräumen)
