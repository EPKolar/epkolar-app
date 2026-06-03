-- ============================================================================
-- ROLLBACK zu migrate_absences_repair_v3998.sql — Sebastian-Service-Role
-- ============================================================================
-- Stellt absences exakt aus dem Pre-Migrations-Snapshot wieder her.
-- Voraussetzung: _absences_snapshot_v3998 wurde von der Forward-Migration erzeugt
-- und noch NICHT gedroppt.
-- ============================================================================
BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                 WHERE table_schema='public' AND table_name='_absences_snapshot_v3998') THEN
    RAISE EXCEPTION 'Snapshot _absences_snapshot_v3998 fehlt — Rollback nicht möglich (kein Restore-Punkt).';
  END IF;
END $$;

-- Spaltenweises Restore über den PK (id) — verändert nur die migrierten Felder zurück.
UPDATE public.absences a
SET worker_id   = s.worker_id,
    worker_name = s.worker_name,
    von         = s.von,
    bis         = s.bis,
    hours       = s.hours,
    tage        = s.tage
FROM public._absences_snapshot_v3998 s
WHERE a.id = s.id;

COMMIT;

-- Optional: DROP TABLE public._absences_snapshot_v3998;   (erst wenn Rollback bestätigt)

-- ============================================================================
-- ERWARTUNGSWERTE / VERIFY-VORLAGE (für Chat-Claude nach Forward-Migration)
-- ============================================================================
-- hours-Formel: hours = ((to_date - from_date) + 1) * 7,7   (38,5h-Woche, ganztags)
--   1 Tag  → 7,7 h
--   2 Tage → 15,4 h
--   5 Tage → 38,5 h (volle Woche)
-- Diese Query GENERIERT die Soll-Werte pro Eintrag zum Abgleich gegen die migrierten Ist-Werte:
--
--   SELECT id, worker_id, type, from_date, to_date,
--          ((to_date::date - from_date::date) + 1)            AS soll_tage,
--          ((to_date::date - from_date::date) + 1) * 7.7      AS soll_hours,
--          tage AS ist_tage, hours AS ist_hours,
--          CASE WHEN tage = ((to_date::date - from_date::date) + 1)
--                AND hours = ((to_date::date - from_date::date) + 1) * 7.7
--               THEN 'OK' ELSE 'ABWEICHUNG (Halbtag? manuell prüfen)' END AS status
--   FROM public.absences
--   ORDER BY worker_id, from_date;
--
-- Resturlaub-Plausibilität pro MA (gegen erwartete Salden in der App):
--   SELECT worker_id, sum(CASE WHEN type='urlaub' THEN hours ELSE 0 END)        AS urlaub_h,
--                     sum(CASE WHEN type='zeitausgleich' THEN hours ELSE 0 END) AS za_h,
--                     sum(CASE WHEN type='krankenstand' THEN hours ELSE 0 END)  AS krank_h
--   FROM public.absences GROUP BY worker_id ORDER BY worker_id;
