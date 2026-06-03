-- v3.10.5 ROLLBACK system_config
DROP POLICY IF EXISTS system_config_admin_all ON public.system_config;

DO $$
DECLARE snap RECORD;
BEGIN
  FOR snap IN SELECT polname, cmd, qual FROM public._rls_snapshot_v3108 WHERE tablename='system_config'
  LOOP
    BEGIN
      EXECUTE format(
        'CREATE POLICY %I ON public.system_config FOR %s TO authenticated USING (%s)',
        snap.polname, snap.cmd, COALESCE(snap.qual,'true')
      );
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END $$;
