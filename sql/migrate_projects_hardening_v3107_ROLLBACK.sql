-- v3.10.5 ROLLBACK projects
DROP POLICY IF EXISTS projects_select_authenticated ON public.projects;
DROP POLICY IF EXISTS projects_insert_admin_pl ON public.projects;
DROP POLICY IF EXISTS projects_update_admin_pl ON public.projects;
DROP POLICY IF EXISTS projects_delete_admin_pl ON public.projects;

DO $$
DECLARE snap RECORD;
BEGIN
  FOR snap IN SELECT polname, cmd, qual FROM public._rls_snapshot_v3107 WHERE tablename='projects'
  LOOP
    BEGIN
      EXECUTE format(
        'CREATE POLICY %I ON public.projects FOR %s TO authenticated USING (%s)',
        snap.polname, snap.cmd, COALESCE(snap.qual,'true')
      );
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END $$;
