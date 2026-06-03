-- ═══════════════════════════════════════════════════════════
-- v3.10.5 P0-3 urlaubskontingent Hardening (Sebastian-Spec)
-- ═══════════════════════════════════════════════════════════
--
-- BEFUND: Monteur(barger) liest ALLE Kontingente + kann PATCH eigenes Kontingent hochsetzen.
-- FIX: SELECT nur eigene (worker_id-Match) oder büro/admin alle.
--      UPDATE/INSERT/DELETE nur büro/admin (HR).

-- Snapshot
CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3106 (
  ts timestamptz DEFAULT now(), tablename text, polname text, roles text[],
  cmd text, qual text, with_check text
);
INSERT INTO public._rls_snapshot_v3106 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename='urlaubskontingent';

-- Helper: is_hr() = admin OR büro
CREATE OR REPLACE FUNCTION public.is_hr() RETURNS boolean AS $$
  SELECT EXISTS(
    SELECT 1 FROM public.users
    WHERE auth_user_id = auth.uid()
      AND role IN ('admin','buero','projektleiter')
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Drop offene Policies
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='urlaubskontingent'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.urlaubskontingent', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
  END LOOP;
END $$;

-- SELECT: eigene Zeile + HR
CREATE POLICY urlaubskontingent_select_own_or_hr
  ON public.urlaubskontingent FOR SELECT TO authenticated
  USING (
    is_hr()
    OR worker_id IN (
      SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid()
    )
    OR worker_id IN (
      SELECT id FROM public.users WHERE auth_user_id = auth.uid()
    )
  );

-- INSERT/UPDATE/DELETE: nur HR
CREATE POLICY urlaubskontingent_modify_hr
  ON public.urlaubskontingent FOR ALL TO authenticated
  USING (is_hr())
  WITH CHECK (is_hr());

-- VERIFY:
-- 1. barger SELECT /urlaubskontingent → nur eigene Zeile
-- 2. barger PATCH /urlaubskontingent?id=eq.<own> body:{stunden:9999} → 403
-- 3. schober (buero) SELECT → alle Zeilen
-- 4. schober PATCH → 200

-- ROLLBACK siehe _ROLLBACK.sql
