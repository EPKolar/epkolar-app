-- ═══════════════════════════════════════════════════════════════════
-- GPS_v1.sql — Flotte-Tab Fundament (App v3.9.645)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — Human-Run-Gate.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Schreibpfad kommt SPAETER: die Edge Function gps_ingest (Traccar-
-- Forwarding) schreibt fz_positions via service_role (umgeht RLS).
-- Darum hier BEWUSST keine insert/update/delete-Policy fuer anon/auth.
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) Tracker-IMEI am Fahrzeug ─────────────────────────────────────
ALTER TABLE public.fahrzeuge ADD COLUMN IF NOT EXISTS tracker_imei text;

-- ── 2) Positions-Log ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.fz_positions (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fahrzeug_id text NOT NULL,
  ts          timestamptz NOT NULL,
  lat         double precision NOT NULL,
  lon         double precision NOT NULL,
  speed       numeric,
  ignition    boolean,
  raw         jsonb,
  created_at  timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS fz_positions_fahrzeug_ts_idx
  ON public.fz_positions (fahrzeug_id, ts DESC);

-- ── 3) RLS: Lesen nur Staff (is_staff()); KEINE Schreib-Policy ──────
-- (service_role der Edge Function umgeht RLS → braucht keine Policy).
ALTER TABLE public.fz_positions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS fz_positions_select_staff ON public.fz_positions;
CREATE POLICY fz_positions_select_staff ON public.fz_positions
  FOR SELECT USING (is_staff());

-- lager_display hart geblockt (GPS = Kontrollmassnahme, Kiosk darf NIE lesen).
DROP POLICY IF EXISTS fz_positions_no_lager_display ON public.fz_positions;
CREATE POLICY fz_positions_no_lager_display ON public.fz_positions AS RESTRICTIVE
  FOR SELECT USING ( ((auth.jwt() -> 'app_metadata') ->> 'role') IS DISTINCT FROM 'lager_display' );

-- ═══════════════════════════════════════════════════════════════════
-- ROLLBACK (manuell, NICHT Teil des Vorwaerts-Laufs):
--   DROP POLICY IF EXISTS fz_positions_no_lager_display ON public.fz_positions;
--   DROP POLICY IF EXISTS fz_positions_select_staff    ON public.fz_positions;
--   DROP TABLE  IF EXISTS public.fz_positions;
--   DROP INDEX  IF EXISTS public.fz_positions_fahrzeug_ts_idx;
--   ALTER TABLE public.fahrzeuge DROP COLUMN IF EXISTS tracker_imei;
-- ═══════════════════════════════════════════════════════════════════
