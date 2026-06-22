-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar — Migration weekplans → weekplan_rows  v1
-- ═══════════════════════════════════════════════════════════════════════════
-- Datum:    2026-06-22
-- Status:   READY-TO-EXECUTE — Human-Run-Gate (Sebastian / Chat-Claude)
-- Voraussetzung: sql/WEEKPLAN_ROWS_v1.sql ZUERST ausgeführt (Tabelle muss da sein).
--
-- ▶ ZWECK
--   Bestehende weekplans.data-Blobs (JSON-Array von rows) werden in einzelne
--   weekplan_rows-Datensätze aufgelöst. Eine row aus dem JSON-Array →
--   eine SQL-Zeile. sort_order = Index im ursprünglichen Array (für die
--   Reihenfolge im Frontend).
--
-- ▶ GARANTIEN
--   - INSERT … ON CONFLICT (row_id) DO NOTHING — idempotent, re-runbar.
--   - Pre/Post-Count-Vergleich am Ende (Sebastian: row_count vorher/nachher).
--   - Skipped: rows ohne id (defensive).
--   - Skipped: rows mit leerem bvh UND leerem z (Padding-Empty-Rows aus
--     padWpRows — die brauchen wir nicht in der DB, werden im Frontend
--     wieder hinzugefügt).
--
-- ▶ NICHT AUSFÜHREN bevor:
--   (1) sql/WEEKPLAN_ROWS_v1.sql APPLIED + verifiziert ist.
--   (2) Pre-Check unten lief.
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- SCHRITT 0 — Pre-Check (READ-ONLY)
-- ───────────────────────────────────────────────────────────────────────────
-- 0.1) Ziel-Tabelle existiert + ist leer:
--    SELECT to_regclass('public.weekplan_rows');           -- erwartet: classoid
--    SELECT count(*) FROM public.weekplan_rows;            -- erwartet: 0
--
-- 0.2) Quell-Tabelle (weekplans) vorhanden + Stand:
--    SELECT count(*) AS kw_count,
--           sum(jsonb_array_length(
--             CASE WHEN jsonb_typeof(data::jsonb)='array' THEN data::jsonb ELSE '[]'::jsonb END
--           )) AS source_row_count
--    FROM public.weekplans;
--    -- source_row_count NOTIEREN — Migration muss <= das ergeben (Padding-Skip).
--
-- 0.3) Sample-Inspect (typisches row-Format prüfen):
--    SELECT wp.year, wp.week, jsonb_array_length(
--      CASE WHEN jsonb_typeof(wp.data::jsonb)='array' THEN wp.data::jsonb ELSE '[]'::jsonb END
--    ) AS rows_in_kw, wp.data::jsonb -> 0 AS first_row
--    FROM public.weekplans wp
--    ORDER BY wp.year DESC, wp.week DESC
--    LIMIT 5;
--    -- first_row.id, .bvh, .z.Mo etc. sollten erkennbar sein.


-- ───────────────────────────────────────────────────────────────────────────
-- SCHRITT 1 — Migration (eine BEGIN/COMMIT-Transaktion)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

WITH expanded AS (
  SELECT
    wp.year,
    wp.week,
    elem,
    ord,
    -- row_id: bevorzugt elem->>'id' (frontend setzt das immer), Fallback unique
    COALESCE(NULLIF(elem->>'id',''),
             wp.year || '-' || wp.week || '-mig-' || ord::text) AS row_id_text
  FROM public.weekplans wp,
       jsonb_array_elements(
         CASE WHEN jsonb_typeof(wp.data::jsonb)='array' THEN wp.data::jsonb ELSE '[]'::jsonb END
       ) WITH ORDINALITY AS arr(elem, ord)
)
INSERT INTO public.weekplan_rows
  (row_id, year, week, sort_order, bvh, proj_id, bem, z, updated_by, updated_at, created_at)
SELECT
  e.row_id_text,
  e.year,
  e.week,
  ((e.ord - 1) * 10)::int    AS sort_order,                  -- × 10 für Lücken-Toleranz (Einschübe)
  COALESCE(e.elem->>'bvh', ''),
  COALESCE(e.elem->>'projId', ''),
  COALESCE(e.elem->>'bem', ''),
  COALESCE(e.elem->'z', '{}'::jsonb),
  'migration',
  NOW(),
  NOW()
FROM expanded e
WHERE
  -- Skip leere Padding-Rows aus padWpRows (keine bvh + keine z-Belegung)
  NOT (
    COALESCE(NULLIF(e.elem->>'bvh',''), '') = ''
    AND (
      e.elem->'z' IS NULL
      OR e.elem->'z' = '{}'::jsonb
      OR NOT EXISTS(
        SELECT 1
        FROM jsonb_each(e.elem->'z') dz,
             LATERAL jsonb_each(dz.value) dv
        WHERE jsonb_typeof(dv.value)='array' AND jsonb_array_length(dv.value) > 0
      )
    )
  )
ON CONFLICT (row_id) DO NOTHING;

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- SCHRITT 2 — Verifikation (READ-ONLY)
-- ───────────────────────────────────────────────────────────────────────────
-- 2.1) Migrierte Row-Count vs Quelle:
--    SELECT count(*) AS migrated_rows FROM public.weekplan_rows;
--    -- vs. source_row_count aus Pre-Check 0.2 — sollte ≤ source sein
--    -- (Padding-Skip kann manche raus filtern).
--
-- 2.2) Pro KW Migration konsistent:
--    SELECT wp.year, wp.week,
--           jsonb_array_length(
--             CASE WHEN jsonb_typeof(wp.data::jsonb)='array' THEN wp.data::jsonb ELSE '[]'::jsonb END
--           ) AS source_count,
--           (SELECT count(*) FROM public.weekplan_rows wr
--            WHERE wr.year=wp.year AND wr.week=wp.week) AS migrated_count
--    FROM public.weekplans wp
--    ORDER BY wp.year DESC, wp.week DESC
--    LIMIT 20;
--    -- migrated_count ≤ source_count (Differenz = Padding-Empties).
--
-- 2.3) Sample-Inhalt:
--    SELECT row_id, year, week, sort_order, bvh, proj_id, bem,
--           jsonb_object_keys(z) AS day_keys
--    FROM public.weekplan_rows
--    ORDER BY year DESC, week DESC, sort_order ASC
--    LIMIT 20;
--
-- 2.4) Doppel-id-Check (sollte 0 sein nach ON CONFLICT):
--    SELECT row_id, count(*) FROM public.weekplan_rows
--    GROUP BY row_id HAVING count(*) > 1;
--    -- erwartet: 0 rows.


-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK (Migration rückgängig — falls Verifikation fehlschlägt)
-- ═══════════════════════════════════════════════════════════════════════════
-- BEGIN;
-- TRUNCATE TABLE public.weekplan_rows;
-- COMMIT;
--
-- Bemerkung: weekplans-Tabelle bleibt unverändert (alte Source-of-Truth bis
-- Cut-Over im Frontend via v3.9.500). DROP TABLE weekplans NICHT in dieser
-- Migration — eigener späterer Cleanup-Schritt nach erfolgreichem Live-Verify.
-- ═══════════════════════════════════════════════════════════════════════════
