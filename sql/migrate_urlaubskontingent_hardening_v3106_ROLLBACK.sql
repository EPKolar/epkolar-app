-- v3.10.5 ROLLBACK urlaubskontingent
DROP POLICY IF EXISTS urlaubskontingent_select_own_or_hr ON public.urlaubskontingent;
DROP POLICY IF EXISTS urlaubskontingent_modify_hr ON public.urlaubskontingent;

-- Restore original permissive (aus Snapshot)
DO $$
DECLARE snap RECORD;
BEGIN
  FOR snap IN SELECT polname, cmd, qual FROM public._rls_snapshot_v3106
    WHERE tablename='urlaubskontingent'
  LOOP
    BEGIN
      EXECUTE format(
        'CREATE POLICY %I ON public.urlaubskontingent FOR %s TO authenticated USING (%s)',
        snap.polname, snap.cmd, COALESCE(snap.qual,'true')
      );
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END $$;

-- Fallback wenn Snapshot leer
DO $$ BEGIN
  IF NOT EXISTS(SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='urlaubskontingent') THEN
    CREATE POLICY urlaubskontingent_fallback_all ON public.urlaubskontingent
      FOR ALL TO authenticated USING (true) WITH CHECK (true);
  END IF;
END $$;
