-- ═══════════════════════════════════════════════════════════════════════════
-- ENTFERNUNGSZULAGE_TAGE_v1.sql  ·  Etappe 2 der EZ-Vergabe (Kalender-Klick)
-- IDEMPOTENT · Human-Run-Gate · Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp)
-- ═══════════════════════════════════════════════════════════════════════════
-- MODELL (Sebastian, 20.07.2026): Die Entfernungszulage wird kuenftig PER KLICK
-- pro Mitarbeiter-Tag vergeben (Kalender, Etappe 4), statt automatisch aus
-- >6h-Tagen. Diese Tabelle haelt das Tages-Flag — exakt analog zum bewaehrten
-- montagezulage_tage (PK worker_id+datum, is_staff()-RLS, kein Auth-Bezug).
--
-- WICHTIG: NUR die Tabelle. Die RECHNUNG liest diese Flags erst nach Etappe 3
-- (lohnrelevant, eigene Freigabe mit €-Beispiel). Bis dahin bleibt die
-- Entfernungszulage automatisch (>6h aus time_entries) — die App schreibt die
-- Flags feature-detect-tolerant (42P01 -> still), sie wirken noch nicht.
--
-- €/Lohn: das blosse Anlegen der Tabelle aendert KEINE abgerechnete Zahl.
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.entfernungszulage_tage (
  worker_id   text        NOT NULL,
  datum       date        NOT NULL,
  aktiv       boolean     NOT NULL DEFAULT true,
  created_by  text,
  created_at  timestamptz DEFAULT now(),
  PRIMARY KEY (worker_id, datum)
);

ALTER TABLE public.entfernungszulage_tage ENABLE ROW LEVEL SECURITY;

-- RLS: nur Staff (admin/buero/projektleiter) — analog montagezulage_tage.
-- is_staff() ist SECURITY DEFINER/STABLE (users.role IN ('admin','buero','projektleiter')).
DROP POLICY IF EXISTS entfernungszulage_tage_select_staff ON public.entfernungszulage_tage;
CREATE POLICY entfernungszulage_tage_select_staff ON public.entfernungszulage_tage
  FOR SELECT USING (is_staff());

DROP POLICY IF EXISTS entfernungszulage_tage_insert_staff ON public.entfernungszulage_tage;
CREATE POLICY entfernungszulage_tage_insert_staff ON public.entfernungszulage_tage
  FOR INSERT WITH CHECK (is_staff());

DROP POLICY IF EXISTS entfernungszulage_tage_update_staff ON public.entfernungszulage_tage;
CREATE POLICY entfernungszulage_tage_update_staff ON public.entfernungszulage_tage
  FOR UPDATE USING (is_staff()) WITH CHECK (is_staff());

DROP POLICY IF EXISTS entfernungszulage_tage_delete_staff ON public.entfernungszulage_tage;
CREATE POLICY entfernungszulage_tage_delete_staff ON public.entfernungszulage_tage
  FOR DELETE USING (is_staff());

-- VERIFY (read-only, nach dem Run):
--   SELECT count(*) FROM public.entfernungszulage_tage;                    -- 0
--   SELECT policyname, cmd FROM pg_policies
--     WHERE schemaname='public' AND tablename='entfernungszulage_tage';    -- 4x is_staff()
