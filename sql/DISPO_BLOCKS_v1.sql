-- ═══════════════════════════════════════════════════════════════════
-- DISPO_BLOCKS_v1.sql — Fundament "blockierbare Tage" in der Dispo (App v3.9.747, Register #1)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — Human-Run-Gate (Sebastian).
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Zweck (Sebastian #1 / P1-e Teil 2): Buero/PL/Admin kann einen Monteur-Tag
-- in der Dispo SPERREN (z.B. Schulung, Urlaub-Rest, Werkstatt-Tag) -> der
-- Tag zaehlt in der Vorschlagsplanung als Kapazitaet 0 (harte Wand, 🚫).
-- Die App liest die Sperren 42P01-tolerant: existiert die Tabelle noch nicht,
-- laeuft die Dispo unveraendert weiter (keine Sperren). Kein OFFA/Juprowa-
-- Bezug, kein Push — reine Dispo-Planungssperre.
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) Sperre je Monteur-Tag ────────────────────────────────────────
-- PK (worker_id, datum): eine Sperre PRO TAG. grund = optionaler Klartext.
CREATE TABLE IF NOT EXISTS public.dispo_blocks (
  worker_id  text NOT NULL,
  datum      date NOT NULL,
  grund      text,
  created_by text,
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (worker_id, datum)
);

-- ── 2) RLS: NUR Staff (is_staff()) darf lesen + setzen ──────────────
ALTER TABLE public.dispo_blocks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS dispo_blocks_select_staff ON public.dispo_blocks;
CREATE POLICY dispo_blocks_select_staff ON public.dispo_blocks
  FOR SELECT USING (is_staff());

DROP POLICY IF EXISTS dispo_blocks_insert_staff ON public.dispo_blocks;
CREATE POLICY dispo_blocks_insert_staff ON public.dispo_blocks
  FOR INSERT WITH CHECK (is_staff());

DROP POLICY IF EXISTS dispo_blocks_update_staff ON public.dispo_blocks;
CREATE POLICY dispo_blocks_update_staff ON public.dispo_blocks
  FOR UPDATE USING (is_staff()) WITH CHECK (is_staff());

DROP POLICY IF EXISTS dispo_blocks_delete_staff ON public.dispo_blocks;
CREATE POLICY dispo_blocks_delete_staff ON public.dispo_blocks
  FOR DELETE USING (is_staff());

-- ── 3) Kiosk-RESTRICTIVE: der Kiosk/Monteur-Pfad hat NIE Zugriff ────
-- Restriktive Policy schneidet zusaetzlich ab (AND-Verknuepfung): selbst
-- wenn eine kuenftige permissive Policy breiter waere, bleibt der Kiosk-
-- Rollenpfad aussen vor. (Muster wie bei den Kiosk-Whitelist-Tabellen.)
DROP POLICY IF EXISTS dispo_blocks_no_kiosk ON public.dispo_blocks;
CREATE POLICY dispo_blocks_no_kiosk ON public.dispo_blocks
  AS RESTRICTIVE FOR ALL
  USING (is_staff()) WITH CHECK (is_staff());

-- ═══════════════════════════════════════════════════════════════════
-- ROLLBACK (manuell, NICHT Teil des Vorwaerts-Laufs):
--   DROP POLICY IF EXISTS dispo_blocks_select_staff ON public.dispo_blocks;
--   DROP POLICY IF EXISTS dispo_blocks_insert_staff ON public.dispo_blocks;
--   DROP POLICY IF EXISTS dispo_blocks_update_staff ON public.dispo_blocks;
--   DROP POLICY IF EXISTS dispo_blocks_delete_staff ON public.dispo_blocks;
--   DROP POLICY IF EXISTS dispo_blocks_no_kiosk     ON public.dispo_blocks;
--   DROP TABLE  IF EXISTS public.dispo_blocks;
-- ═══════════════════════════════════════════════════════════════════
