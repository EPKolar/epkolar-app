-- v3.9.132 PlanRadar Phase 1 — Daten-Konsistenz Plan/Ticket-Felder
-- AUSFÜHRUNG: Chat-Claude im Supabase SQL-Editor (CC führt KEINE Migration aus).
-- Snapshot vor COMMIT empfohlen. Alle Schritte sind additiv/idempotent.

BEGIN;

-- 1a) is_pdf bei bestehenden Plänen korrekt setzen (Endung .pdf, case-insensitive).
--     Frontend setzt is_pdf ab v3.9.132 beim Upload; dieser Backfill fixt die 2 Altpläne.
UPDATE plans SET is_pdf = TRUE
 WHERE is_pdf IS DISTINCT FROM TRUE
   AND (lower(coalesce(filename,'')) LIKE '%.pdf' OR lower(coalesce(file_url,'')) LIKE '%.pdf');
UPDATE plans SET is_pdf = FALSE
 WHERE is_pdf IS NULL
   AND NOT (lower(coalesce(filename,'')) LIKE '%.pdf' OR lower(coalesce(file_url,'')) LIKE '%.pdf');

-- 1b) Ticket-Doppelfelder konsolidieren: KANONISCH gewerk + assignee.
--     'layer' und 'assigned_to' bleiben als DEPRECATED erhalten (NICHT droppen).
--     Backfill nur wo kanonisches Feld leer ist (kein Überschreiben echter Werte).
UPDATE tickets SET gewerk = layer
 WHERE (gewerk IS NULL OR gewerk = '') AND layer IS NOT NULL AND layer <> '';
UPDATE tickets SET assignee = assigned_to
 WHERE (assignee IS NULL OR assignee = '') AND assigned_to IS NOT NULL AND assigned_to <> '';

-- VERIFY (vor COMMIT prüfen):
--   SELECT count(*) FILTER (WHERE is_pdf) AS pdf, count(*) FILTER (WHERE NOT is_pdf) AS img FROM plans;
--   SELECT count(*) FILTER (WHERE gewerk<>'' ) AS mit_gewerk, count(*) FILTER (WHERE coalesce(gewerk,'')='') AS ohne FROM tickets;

COMMIT;

-- ════════════ ROLLBACK (nur Datenwerte; Spalten bleiben) ════════════
-- BEGIN;
--   -- is_pdf zurück auf NULL (Vorzustand war NULL bei beiden Altplänen):
--   UPDATE plans SET is_pdf = NULL;
--   -- gewerk/assignee-Backfill ist additiv (nur leere Felder gefüllt) — ein gezielter Rollback
--   -- müsste die vor dem Backfill leeren Zeilen kennen; Snapshot nutzen statt pauschal leeren.
-- COMMIT;
