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
-- SICHERHEIT: idempotent, NUR kaputte Rows (hours NULL/0/7,7), in Transaktion. Vorher Snapshot.
-- STUNDEN-LOGIK (Sebastian-Payroll-Bestätigung 2026-06-03): Mo-Do 8,5h · Fr 4,5h · Sa/So 0 ·
--   AT/NÖ-Feiertag 0. NICHT flat 7,7h/Tag. Feiertage bewiesen relevant (Pfingstmontag 25.5.2026
--   zählte fälschlich 8,5h → Günther 98,5h statt 90,0h). Halbtags: KEIN Flag im Schema →
--   ⚠️ etwaige Halbtage nach Migration manuell halbieren (1-Tag-Einträge per VERIFY-Query prüfen).
-- ============================================================================

BEGIN;

-- ---- 0) Snapshot für Rollback-Referenz -------------------------------------
DROP TABLE IF EXISTS public._absences_snapshot_v3998;
-- Supabase-DB-Größe: NUR die Spalten sichern, die diese Migration ändert (nicht SELECT *).
CREATE TABLE public._absences_snapshot_v3998 AS
  SELECT id, worker_id, worker_name, von, bis, hours, tage FROM public.absences;

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

-- ---- 4) hours/tage nach kanonischer stdVonTag-Logik (Sebastian-Payroll-Bestätigung) -------
-- Mo-Do = 8,5h, Fr = 4,5h, Sa/So = 0, AT/NÖ-Feiertag = 0. tage = Werktage (hours>0).
-- NICHT flat 7,7h/Tag (das war falsch je Einzeltag). Pro Tag im Zeitraum summiert.
-- AT/NÖ-Feiertage 2025-2027 (fix + Oster-basiert); bei Bedarf weitere Jahre ergänzen.
WITH feiertage(d) AS (VALUES
  (DATE '2026-01-01'),(DATE '2026-01-06'),(DATE '2026-04-06'),(DATE '2026-05-01'),
  (DATE '2026-05-14'),(DATE '2026-05-25'),(DATE '2026-06-04'),(DATE '2026-08-15'),
  (DATE '2026-11-01'),(DATE '2026-12-08'),(DATE '2026-12-25'),(DATE '2026-12-26'),
  (DATE '2025-01-01'),(DATE '2025-01-06'),(DATE '2025-04-21'),(DATE '2025-05-01'),
  (DATE '2025-05-29'),(DATE '2025-06-09'),(DATE '2025-06-19'),(DATE '2025-08-15'),
  (DATE '2025-11-01'),(DATE '2025-12-08'),(DATE '2025-12-25'),(DATE '2025-12-26'),
  (DATE '2027-01-01'),(DATE '2027-01-06'),(DATE '2027-03-29'),(DATE '2027-05-01'),
  (DATE '2027-05-06'),(DATE '2027-05-17'),(DATE '2027-05-27'),(DATE '2027-08-15'),
  (DATE '2027-11-01'),(DATE '2027-12-08'),(DATE '2027-12-25'),(DATE '2027-12-26')
),
calc AS (
  SELECT a.id,
    SUM(CASE
      WHEN EXTRACT(DOW FROM g.d) IN (0,6) THEN 0
      WHEN g.d::date IN (SELECT d FROM feiertage) THEN 0
      WHEN EXTRACT(DOW FROM g.d) IN (1,2,3,4) THEN 8.5
      WHEN EXTRACT(DOW FROM g.d) = 5 THEN 4.5
      ELSE 0 END) AS soll_hours,
    SUM(CASE
      WHEN EXTRACT(DOW FROM g.d) IN (0,6) THEN 0
      WHEN g.d::date IN (SELECT d FROM feiertage) THEN 0
      ELSE 1 END) AS soll_tage
  FROM public.absences a
  CROSS JOIN LATERAL generate_series(a.from_date::date, a.to_date::date, INTERVAL '1 day') AS g(d)
  WHERE a.from_date IS NOT NULL AND a.to_date IS NOT NULL
  GROUP BY a.id
)
UPDATE public.absences a
SET hours = c.soll_hours, tage = c.soll_tage
FROM calc c
WHERE a.id = c.id
  AND (a.hours IS NULL OR a.hours = 0 OR a.hours = 7.7);  -- nur Fehlwerte (inkl. v3.9.103-7,7); manuelle Korrekturen bleiben

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

-- ⚠️ Supabase-DB-Größe: Snapshot NACH erfolgreichem Smoke wieder droppen!
--    DROP TABLE public._absences_snapshot_v3998;
