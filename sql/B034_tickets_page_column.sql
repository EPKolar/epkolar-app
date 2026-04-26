-- B-034 tickets.page Spalte für Multi-Page-PDF-Support
-- Datum: 26.04.2026 (v3.8.64 Phase 4.1)
-- Sebastian: nach Rückkehr im Supabase SQL-Editor ausführen.
--
-- Hintergrund: PlanViewerCanvas filtert Tickets nach plan_id + page (default 1).
-- DB-Schema (verifiziert 25.04 18:00) hat KEINE page-Spalte → Multi-Page-Pins
-- werden alle als page=1 gerendert. Diese Migration fügt die Spalte hinzu + Index.

-- 1. Spalte vorhanden?
SELECT column_name FROM information_schema.columns
WHERE table_name = 'tickets' AND column_name = 'page';

-- 2. Spalte hinzufügen + Default
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS page integer DEFAULT 1;
UPDATE tickets SET page = 1 WHERE page IS NULL;

-- 3. Index für plan_id + page (Pin-Filter-Performance)
CREATE INDEX IF NOT EXISTS idx_tickets_plan_page ON tickets(plan_id, page);

-- 4. Verify
SELECT
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE page IS NOT NULL) AS with_page,
  COUNT(*) FILTER (WHERE page = 1) AS on_page_1,
  MAX(page) AS max_page
FROM tickets;
