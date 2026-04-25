-- DEPRECATED v3.8.59: tickets-Schema bleibt bei x/y (Pixel). NICHT AUSFÜHREN.
-- Begründung: DB-Schema-Verifikation 25.04.2026 18:00 (Sebastian) zeigt keine xPct/yPct/page-Spalten in tickets.
-- Migration würde leere Spalten erzeugen + die Auto-Migration in v3.8.57 hat silent gefailt.
-- Phase 1 v3.8.59 hat den Auto-Migration-Code entfernt. Component konvertiert beim Render.
-- Alternativer Weg für Multi-Page-Support: B034_tickets_page_column.sql (nur "page"-Spalte).

-- ORIGINAL CONTENT (NICHT AUSFÜHREN):

-- B-033 Pixel→%-Migration für tickets-Tabelle
-- Datum: 25.04.2026
-- Annahme: tickets-Tabelle hat x, y, plan_id Spalten.
-- xPct/yPct/page werden ggf. erst hinzugefügt.

-- Schritt 1: Spalten hinzufügen wenn noch nicht da
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS "xPct" numeric;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS "yPct" numeric;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS page integer DEFAULT 1;

-- Schritt 2: Pre-Check
SELECT COUNT(*) AS to_migrate FROM tickets
WHERE ("xPct" IS NULL OR "yPct" IS NULL) AND x IS NOT NULL AND y IS NOT NULL;

-- Schritt 3: Migration via JOIN auf plans (nutzt width/height für Skalierung)
UPDATE tickets t
SET
  "xPct" = (t.x::numeric / NULLIF(p.width, 0)) * 100,
  "yPct" = (t.y::numeric / NULLIF(p.height, 0)) * 100
FROM plans p
WHERE t.plan_id = p.id
  AND (t."xPct" IS NULL OR t."yPct" IS NULL)
  AND t.x IS NOT NULL
  AND t.y IS NOT NULL
  AND p.width > 0 AND p.height > 0;

-- Schritt 4: Verify
SELECT
  COUNT(*) FILTER (WHERE "xPct" IS NOT NULL) AS with_pct,
  COUNT(*) FILTER (WHERE "xPct" IS NULL) AS without_pct,
  COUNT(*) AS total
FROM tickets;
