-- ============================================================
-- BASELINE-FIX v3.8.19 — Idempotent, 0 Datenrisiko, nur DDL
-- Sebastian führt manuell aus (Supabase SQL-Editor).
-- Verify danach mit BASELINE_FIX_VERIFY_v3.8.sql — 8 TRUE erwartet.
-- ============================================================
-- Voraussetzung: Baseline-Messung Nacht-2 (19.04.2026) zeigte:
--   · 0 Dupes in users.email und arbeitsscheine.juprowa_id
--   · 0 NULL-Werte in photos.project_id, time_entries.worker_id,
--     time_entries.project_id
-- Fixes sind daher risikolos und sofort deploybar.
-- ============================================================

-- FIX 1: UNIQUE auf users.email (0 Dupes aktuell → sicher)
CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique_idx
  ON public.users (lower(email))
  WHERE email IS NOT NULL AND email <> '';

-- FIX 2: UNIQUE auf arbeitsscheine.juprowa_id (0 Dupes → sicher)
CREATE UNIQUE INDEX IF NOT EXISTS arbeitsscheine_juprowa_id_unique_idx
  ON public.arbeitsscheine (juprowa_id)
  WHERE juprowa_id IS NOT NULL AND juprowa_id <> '';

-- FIX 3: CHECK-Constraints auf Enums (NOT VALID, schützt neue Rows)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_scheinstatus_chk') THEN
    ALTER TABLE public.arbeitsscheine ADD CONSTRAINT arbeitsscheine_scheinstatus_chk
      CHECK (scheinstatus IS NULL OR scheinstatus IN ('neu','bearbeitung','abgeschlossen','storniert')) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_prioritaet_chk') THEN
    ALTER TABLE public.arbeitsscheine ADD CONSTRAINT arbeitsscheine_prioritaet_chk
      CHECK (prioritaet IS NULL OR prioritaet IN ('niedrig','mittel','hoch','kritisch')) NOT VALID;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='users_role_chk') THEN
    ALTER TABLE public.users ADD CONSTRAINT users_role_chk
      CHECK (role IS NULL OR role IN ('admin','buero','monteur','projektleiter')) NOT VALID;
  END IF;
END$$;

-- FIX 4: NOT NULL auf kritischen Spalten (0 NULLs aktuell → sicher)
-- NICHT arbeitsscheine.monteur (12 Orphans — Block B)
-- NICHT photos.uploaded_by (Backfill-Status unklar)
DO $$
BEGIN
  IF (SELECT count(*) FROM public.photos WHERE project_id IS NULL) = 0 THEN
    ALTER TABLE public.photos ALTER COLUMN project_id SET NOT NULL;
  END IF;
  IF (SELECT count(*) FROM public.time_entries WHERE worker_id IS NULL) = 0 THEN
    ALTER TABLE public.time_entries ALTER COLUMN worker_id SET NOT NULL;
  END IF;
  IF (SELECT count(*) FROM public.time_entries WHERE project_id IS NULL) = 0 THEN
    ALTER TABLE public.time_entries ALTER COLUMN project_id SET NOT NULL;
  END IF;
EXCEPTION WHEN others THEN
  RAISE NOTICE 'NOT NULL fix skipped: %', SQLERRM;
END$$;

-- ============================================================
-- Ende BASELINE_FIX_v3.8.sql
-- ============================================================
