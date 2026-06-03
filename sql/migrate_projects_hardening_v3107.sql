-- ═══════════════════════════════════════════════════════════
-- v3.10.5 P0-4 projects Hardening (Sebastian-Spec)
-- ═══════════════════════════════════════════════════════════
--
-- BEFUND: Monteur(barger) PATCH projects = 200.
-- FIX: UPDATE/INSERT/DELETE nur projektleiter/admin. SELECT bleibt für authenticated offen.
-- Note: anon-Portal-SELECT bleibt unverändert (v3.10.3 lockdown).

-- Snapshot
CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3107 (
  ts timestamptz DEFAULT now(), tablename text, polname text, roles text[],
  cmd text, qual text, with_check text
);
INSERT INTO public._rls_snapshot_v3107 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename='projects';

-- Drop offene authenticated-Write-Policies
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='projects'
      AND cmd IN ('ALL','UPDATE','INSERT','DELETE')
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.projects', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
  END LOOP;
END $$;

-- SELECT bleibt offen (authenticated darf alle Projekte sehen, App-Layer filtert)
CREATE POLICY IF NOT EXISTS projects_select_authenticated
  ON public.projects FOR SELECT TO authenticated
  USING (true);

-- WRITE: nur admin/PL
CREATE POLICY projects_insert_admin_pl
  ON public.projects FOR INSERT TO authenticated
  WITH CHECK (is_admin_or_pl());

CREATE POLICY projects_update_admin_pl
  ON public.projects FOR UPDATE TO authenticated
  USING (is_admin_or_pl())
  WITH CHECK (is_admin_or_pl());

CREATE POLICY projects_delete_admin_pl
  ON public.projects FOR DELETE TO authenticated
  USING (is_admin_or_pl());

-- VERIFY:
-- 1. barger SELECT /projects → 200, alle Projekte (App-Layer filtert via monteurProjekte)
-- 2. barger PATCH /projects?id=eq.X body:{name:'x'} → 403
-- 3. pinger (PL) PATCH /projects → 200
-- 4. anon Portal-Login bleibt unverändert
