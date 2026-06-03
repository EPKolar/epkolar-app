-- v3.10.5 P0-6 finkzeit + bescheinigungen Hardening (Sebastian-Spec)
-- BEFUND: Monteur liest beide.
-- FIX: SELECT nur eigene (worker_id-Match) + büro/admin.

CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3109 (
  ts timestamptz DEFAULT now(), tablename text, polname text, roles text[],
  cmd text, qual text, with_check text
);

INSERT INTO public._rls_snapshot_v3109 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename IN ('finkzeit','bescheinigungen');

-- ═══ FINKZEIT ═══
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='finkzeit'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.finkzeit', pol.polname);
  END LOOP;
END $$;

CREATE POLICY finkzeit_select_own_or_hr
  ON public.finkzeit FOR SELECT TO authenticated
  USING (
    is_hr()
    OR worker_id IN (
      SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid()
    )
  );

CREATE POLICY finkzeit_insert_hr
  ON public.finkzeit FOR INSERT TO authenticated
  WITH CHECK (is_hr());

CREATE POLICY finkzeit_modify_hr
  ON public.finkzeit FOR UPDATE TO authenticated
  USING (is_hr()) WITH CHECK (is_hr());

CREATE POLICY finkzeit_delete_hr
  ON public.finkzeit FOR DELETE TO authenticated
  USING (is_hr());

-- ═══ BESCHEINIGUNGEN ═══
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='bescheinigungen'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.bescheinigungen', pol.polname);
  END LOOP;
END $$;

CREATE POLICY bescheinigungen_select_own_or_hr
  ON public.bescheinigungen FOR SELECT TO authenticated
  USING (
    is_hr()
    OR worker_id IN (
      SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid()
    )
    OR user_id IN (
      SELECT id FROM public.users WHERE auth_user_id = auth.uid()
    )
  );

CREATE POLICY bescheinigungen_modify_hr
  ON public.bescheinigungen FOR ALL TO authenticated
  USING (is_hr()) WITH CHECK (is_hr());

-- VERIFY:
-- 1. barger SELECT /finkzeit → nur Rows mit worker_id=barger.monteur_id
-- 2. barger SELECT /bescheinigungen → nur eigene
-- 3. schober/admin → alle
