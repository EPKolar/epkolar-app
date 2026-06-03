-- v3.10.5 P0-5 system_config Hardening (Sebastian-Spec)
-- BEFUND: Monteur liest system_config (Schreibtest offen).
-- FIX: SELECT + ALL nur admin.

CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3108 (
  ts timestamptz DEFAULT now(), tablename text, polname text, roles text[],
  cmd text, qual text, with_check text
);
INSERT INTO public._rls_snapshot_v3108 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename='system_config';

-- Drop offene Policies
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='system_config'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.system_config', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
  END LOOP;
END $$;

-- Nur Admin
CREATE POLICY system_config_admin_all
  ON public.system_config FOR ALL TO authenticated
  USING (is_admin())
  WITH CHECK (is_admin());

-- VERIFY:
-- 1. barger SELECT /system_config → 403 oder leeres Array
-- 2. admin SELECT/PATCH/POST → 200
