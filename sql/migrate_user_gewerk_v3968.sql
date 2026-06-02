-- ════════════════════════════════════════════════════════════════════════════
-- migrate_user_gewerk_v3968.sql
-- SPRINT 48 / v3.9.68 — Gewerk-Filter VMaterial
-- ────────────────────────────────────────────────────────────────────────────
-- ZIEL: Server-side User-Gewerk-Spalte als persistenter Override für
--       VMaterial Katalog-Filter (statt nur localStorage epk_user_gewerk).
--
-- Sebastian-Bug ("Elektriker sieht immer noch Sanitär und Heizung bei
-- Materialbestellung") wurde clientseitig bereits in v3.9.68 gefixt durch
-- Auto-Detect aus role: Monteur ohne expliziten Override → Default 'elektro'.
--
-- Diese Migration ergänzt eine *optionale* DB-Spalte für Cross-Device-
-- Persistenz (curUser.gewerk wird in renderWarenkorb als Override gelesen,
-- bevor der role-basierte Fallback greift).
--
-- IDEMPOTENT: kann mehrfach laufen ohne Fehler / Datenverlust.
-- DESTRUCTIVE: nein (nur ADD COLUMN + UPDATE bestehender Zeilen)
-- ────────────────────────────────────────────────────────────────────────────
-- Status: DRAFT (Sebastian-Action — review + apply via Supabase SQL-Editor)
-- ════════════════════════════════════════════════════════════════════════════

BEGIN;

-- ──────────────────────────────────────────────────────────────────────────
-- 1. users.gewerk — Profile-Override für Material-Katalog-Filter
-- ──────────────────────────────────────────────────────────────────────────
-- Werte (matched mit MAT_KATALOG.gewerk und renderWarenkorb _kataAllowed):
--   'elektro'      → nur elektro + allgemein
--   'sanitaer'     → sanitaer + heizung + klima + allgemein
--   'heizung'      → heizung + sanitaer + klima + allgemein
--   'installateur' → sanitaer + heizung + klima + allgemein (alias)
--   'beide'        → alle Gewerke (admin/buero/projektleiter Default)
-- NULL = client-side auto-detect (Default 'elektro' für Monteur,
--        'beide' für admin/projektleiter/buero).
-- ──────────────────────────────────────────────────────────────────────────

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS gewerk text;

COMMENT ON COLUMN public.users.gewerk IS
  'Material-Katalog-Filter-Override für VMaterial (v3.9.68). Werte: elektro|sanitaer|heizung|installateur|beide. NULL = client-side auto-detect aus role.';

-- ──────────────────────────────────────────────────────────────────────────
-- 2. Optional: workers.gewerk (Monteur-Stammdaten)
-- ──────────────────────────────────────────────────────────────────────────
-- Falls workers-Tabelle existiert (MONT-Mirror), Spalte ergänzen für
-- konsistenten Datenfluss user.monteurId → workers.gewerk.
-- ──────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='workers') THEN
    EXECUTE 'ALTER TABLE public.workers ADD COLUMN IF NOT EXISTS gewerk text';
    EXECUTE $cmt$COMMENT ON COLUMN public.workers.gewerk IS 'Material-Katalog-Filter (v3.9.68). Werte: elektro|sanitaer|heizung|installateur|beide.'$cmt$;
  END IF;
END $$;

-- ──────────────────────────────────────────────────────────────────────────
-- 3. Backfill bestehender User basierend auf role
-- ──────────────────────────────────────────────────────────────────────────
-- EP Kolar ist primär Elektroinstallationsbetrieb → Monteur-Default 'elektro'.
-- Admin/Projektleiter/Backoffice/Lagerleitung → 'beide' (sehen alle Kataloge).
-- ──────────────────────────────────────────────────────────────────────────

UPDATE public.users
SET gewerk = 'beide'
WHERE gewerk IS NULL
  AND role IN ('admin','projektleiter','buero');

UPDATE public.users
SET gewerk = 'elektro'
WHERE gewerk IS NULL
  AND role = 'monteur';

-- Optional: Lagerleitung sieht alles für Bestellabwicklung
UPDATE public.users u
SET gewerk = 'beide'
WHERE gewerk IS NULL
  AND EXISTS (
    SELECT 1 FROM public.workers w
    WHERE w.id = u.monteurId
      AND w.r ILIKE '%lager%'
  );

-- Catch-all: alle restlichen NULL → 'elektro' (EP Kolar Default)
UPDATE public.users
SET gewerk = 'elektro'
WHERE gewerk IS NULL;

-- ──────────────────────────────────────────────────────────────────────────
-- 4. Check-Constraint für valide Werte
-- ──────────────────────────────────────────────────────────────────────────

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.constraint_column_usage
    WHERE table_schema='public' AND table_name='users' AND constraint_name='users_gewerk_check'
  ) THEN
    ALTER TABLE public.users
      ADD CONSTRAINT users_gewerk_check
      CHECK (gewerk IS NULL OR gewerk IN ('elektro','sanitaer','heizung','installateur','klima','beide','allgemein'));
  END IF;
END $$;

-- ──────────────────────────────────────────────────────────────────────────
-- 5. Verify
-- ──────────────────────────────────────────────────────────────────────────

SELECT
  role,
  gewerk,
  COUNT(*) AS user_count
FROM public.users
GROUP BY role, gewerk
ORDER BY role, gewerk;

COMMIT;

-- ════════════════════════════════════════════════════════════════════════════
-- ROLLBACK (nur falls Sebastian die Spalte wieder entfernen will):
--   BEGIN;
--   ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_gewerk_check;
--   ALTER TABLE public.users DROP COLUMN IF EXISTS gewerk;
--   ALTER TABLE public.workers DROP COLUMN IF EXISTS gewerk;
--   COMMIT;
-- ════════════════════════════════════════════════════════════════════════════
