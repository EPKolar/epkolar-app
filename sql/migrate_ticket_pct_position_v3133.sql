-- v3.9.133 PlanRadar Phase 3b — Pin-Position als kanonisches Prozent (zoom-/seiten-unabhängig)
-- AUSFÜHRUNG: Chat-Claude im Supabase SQL-Editor (CC führt KEINE Migration aus).
-- Hintergrund: tickets.x/y sind Pixel (normalisiert auf die PDF-Eigenbreite bei scale=1). Der Render
-- konvertierte bisher Pixel→%% via pageDims.baseWidth — funktioniert für Einzelseiten, ist aber bei
-- Mehrseiten-PDFs (Phase 2, je Seite andere Breite) fragil. NEU: echtes %% (0-100) wird persistiert.
-- Frontend ab v3.9.133 schreibt x_pct/y_pct beim Anlegen; Render bevorzugt sie, Fallback = Pixel/baseWidth.

BEGIN;

ALTER TABLE tickets ADD COLUMN IF NOT EXISTS x_pct DOUBLE PRECISION;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS y_pct DOUBLE PRECISION;

-- Backfill der bestehenden Pixel-Tickets → %%. Annahme: x/y wurden gegen plans.width/height (die beim
-- Upload gespeicherte Eigenbreite) gesetzt. Nur befüllen wo x_pct noch leer und Plan-Maße > 0.
UPDATE tickets ti SET
  x_pct = CASE WHEN pl.width  > 0 THEN (ti.x::double precision / pl.width  * 100) END,
  y_pct = CASE WHEN pl.height > 0 THEN (ti.y::double precision / pl.height * 100) END
FROM plans pl
WHERE ti.plan_id = pl.id
  AND ti.x_pct IS NULL
  AND ti.x IS NOT NULL AND ti.y IS NOT NULL;

-- VERIFY vor COMMIT:
--   SELECT id, x, y, round(x_pct::numeric,1) AS xp, round(y_pct::numeric,1) AS yp FROM tickets WHERE x_pct IS NOT NULL;
--   (xp/yp sollten im Bereich 0..100 liegen und der Pin-Position auf dem Plan entsprechen.)

COMMIT;

-- ════════════ ROLLBACK ════════════
-- BEGIN;
--   ALTER TABLE tickets DROP COLUMN IF EXISTS x_pct;
--   ALTER TABLE tickets DROP COLUMN IF EXISTS y_pct;
-- COMMIT;
