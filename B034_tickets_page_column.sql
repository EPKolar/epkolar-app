-- B-034 tickets.page Spalte für Multi-Page-PDF-Support
-- Datum: 25.04.2026 abends
-- Sebastian: nach Rückkehr im Supabase SQL-Editor ausführen.
-- Hintergrund: PlanViewerCanvas filtert Tickets nach plan_id + page (default 1).
-- DB-Schema (verifiziert 25.04 18:00) hat KEINE page-Spalte → Multi-Page-Pins
-- werden alle als page=1 gerendert. Diese Migration fügt die Spalte hinzu.

SELECT column_name FROM information_schema.columns
WHERE table_name = 'tickets' AND column_name = 'page';

ALTER TABLE tickets ADD COLUMN IF NOT EXISTS page integer DEFAULT 1;
UPDATE tickets SET page = 1 WHERE page IS NULL;

SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE page IS NOT NULL) AS with_page,
  COUNT(*) FILTER (WHERE page = 1) AS on_page_1
FROM tickets;
