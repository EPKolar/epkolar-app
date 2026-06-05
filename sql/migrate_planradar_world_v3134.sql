-- v3.9.134 PlanRadar World-Container Phase 1 — normalisierte Pin-Koordinaten (nx/ny ∈ 0..1)
-- AUSFÜHRUNG: Chat-Claude im Supabase SQL-Editor (CC führt KEINE Migration aus). Snapshot empfohlen.
-- Hintergrund: Pins NIE wieder in Bildschirm-/Canvas-Pixeln. Kanonisch = nx/ny (Bruchteil der
-- Plan-Intrinsic-Größe). Render multipliziert ×100 → left:nx*100%% im world-div; GPU trackt Pins.

BEGIN;

-- Pin-Koordinaten + Seite
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS nx   DOUBLE PRECISION;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS ny   DOUBLE PRECISION;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS page INTEGER DEFAULT 1;

-- Plan-Intrinsic-Maße + Seitenzahl
ALTER TABLE plans ADD COLUMN IF NOT EXISTS intrinsic_w DOUBLE PRECISION;
ALTER TABLE plans ADD COLUMN IF NOT EXISTS intrinsic_h DOUBLE PRECISION;
ALTER TABLE plans ADD COLUMN IF NOT EXISTS page_count  INTEGER DEFAULT 1;

-- Backfill nx/ny: bevorzugt aus x_pct/y_pct (v3.9.133, 0..100), sonst aus Pixel x/y ÷ plans.width/height.
UPDATE tickets ti SET nx = (ti.x_pct / 100.0)
 WHERE ti.nx IS NULL AND ti.x_pct IS NOT NULL;
UPDATE tickets ti SET ny = (ti.y_pct / 100.0)
 WHERE ti.ny IS NULL AND ti.y_pct IS NOT NULL;
UPDATE tickets ti SET
  nx = CASE WHEN pl.width  > 0 THEN (ti.x::double precision / pl.width ) END,
  ny = CASE WHEN pl.height > 0 THEN (ti.y::double precision / pl.height) END
FROM plans pl
WHERE ti.plan_id = pl.id AND ti.nx IS NULL AND ti.x IS NOT NULL AND ti.y IS NOT NULL;

-- page default 1 für bestehende Pins
UPDATE tickets SET page = 1 WHERE page IS NULL;

-- VERIFY vor COMMIT:
--   SELECT id, round(nx::numeric,3) AS nx, round(ny::numeric,3) AS ny, page FROM tickets WHERE nx IS NOT NULL;
--   (nx/ny müssen im Bereich 0..1 liegen und der Pin-Position entsprechen.)

COMMIT;

-- ════════════ ROLLBACK ════════════
-- BEGIN;
--   ALTER TABLE tickets DROP COLUMN IF EXISTS nx;
--   ALTER TABLE tickets DROP COLUMN IF EXISTS ny;
--   -- page / plans.intrinsic_*/page_count bei Bedarf ebenfalls droppen.
-- COMMIT;
