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
-- hours-Logik (KANONISCH, Sebastian 2026-06-03): pro Tag Mo-Do 8,5h · Fr 4,5h · Sa/So 0 ·
--   AT/NÖ-Feiertag 0. NICHT flat 7,7h/Tag.
--   1 Mo-Do-Tag → 8,5h · 1 Fr → 4,5h · volle Mo-Fr-Woche → 38,5h.
--   SOLL-Werte (Chat-Claude-verifiziert): w6 Günther Urlaub 90,0h / ZA 25,5h;
--     w5 Schmid ZA 25,5h / Sonder 17h; w4 Pinger Urlaub 34h / Kranken 17h; w1 Paschinger Sonder 8,5h.
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
