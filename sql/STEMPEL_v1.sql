-- ═══════════════════════════════════════════════════════════════════
-- STEMPEL_v1.sql — Fundament Stempeluhr (App v3.9.638, DORMANT)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — Human-Run-Gate.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Grundsatz: stempel_log.ts speichert IMMER den ROHEN, ungerundeten
-- Zeitpunkt. Rundung (5-min-Raster) + Pausenabzug passieren NUR im
-- Client bei der Auswertung, NIE in der DB.
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) NFC-Chip-UID am Mitarbeiter ──────────────────────────────────
ALTER TABLE public.workers ADD COLUMN IF NOT EXISTS nfc_uid text;
-- Eindeutige UID (partieller Unique-Index: beliebig viele NULL erlaubt).
CREATE UNIQUE INDEX IF NOT EXISTS workers_nfc_uid_uidx
  ON public.workers (nfc_uid) WHERE nfc_uid IS NOT NULL;

-- ── 2) Roh-Stempel-Log ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.stempel_log (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id  text NOT NULL,
  ts         timestamptz NOT NULL DEFAULT now(),   -- roh/ungerundet
  direction  text NOT NULL CHECK (direction IN ('kommen','gehen')),
  device     text,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS stempel_log_worker_ts_idx
  ON public.stempel_log (worker_id, ts);

-- ── 3) RLS: vorerst NUR Staff (is_staff()) ──────────────────────────
-- Kiosk-Rollen-Policy (eigene Terminal-Rolle fuer das Stempel-Terminal)
-- folgt bei Aktivierung. Bis dahin bucht der Kiosk als eingeloggter
-- Admin/Staff (App-Gate ?screen=stempel ist admin-only).
ALTER TABLE public.stempel_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS stempel_log_select_staff ON public.stempel_log;
CREATE POLICY stempel_log_select_staff ON public.stempel_log
  FOR SELECT USING (is_staff());

DROP POLICY IF EXISTS stempel_log_insert_staff ON public.stempel_log;
CREATE POLICY stempel_log_insert_staff ON public.stempel_log
  FOR INSERT WITH CHECK (is_staff());

DROP POLICY IF EXISTS stempel_log_update_staff ON public.stempel_log;
CREATE POLICY stempel_log_update_staff ON public.stempel_log
  FOR UPDATE USING (is_staff()) WITH CHECK (is_staff());

DROP POLICY IF EXISTS stempel_log_delete_staff ON public.stempel_log;
CREATE POLICY stempel_log_delete_staff ON public.stempel_log
  FOR DELETE USING (is_staff());

-- ── 4) Pausenregeln-Seed (OPTIONAL) ─────────────────────────────────
-- Der Client hat einen In-Memory-Fallback {"buero":0,"default":60} und
-- funktioniert ohne diesen Key. Die sichtbare Konfig-UI kommt als eigene
-- App-Version (Mitarbeiter-Verwaltung, Gate isWAdm). Zum Vorbelegen
-- diesen Block auskommentieren:
-- INSERT INTO public.system_config (key, value)
--   VALUES ('stempel_pause_rules', '{"buero":0,"default":60}')
--   ON CONFLICT (key) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════════
-- ROLLBACK (manuell, NICHT Teil des Vorwaerts-Laufs):
--   DROP POLICY IF EXISTS stempel_log_select_staff  ON public.stempel_log;
--   DROP POLICY IF EXISTS stempel_log_insert_staff  ON public.stempel_log;
--   DROP POLICY IF EXISTS stempel_log_update_staff  ON public.stempel_log;
--   DROP POLICY IF EXISTS stempel_log_delete_staff  ON public.stempel_log;
--   DROP TABLE  IF EXISTS public.stempel_log;
--   DROP INDEX  IF EXISTS public.workers_nfc_uid_uidx;
--   ALTER TABLE public.workers DROP COLUMN IF EXISTS nfc_uid;
--   DELETE FROM public.system_config WHERE key='stempel_pause_rules';
-- ═══════════════════════════════════════════════════════════════════
