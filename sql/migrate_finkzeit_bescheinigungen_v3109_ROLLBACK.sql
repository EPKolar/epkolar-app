-- v3.10.5 ROLLBACK finkzeit + bescheinigungen
DROP POLICY IF EXISTS finkzeit_select_own_or_hr ON public.finkzeit;
DROP POLICY IF EXISTS finkzeit_insert_hr ON public.finkzeit;
DROP POLICY IF EXISTS finkzeit_modify_hr ON public.finkzeit;
DROP POLICY IF EXISTS finkzeit_delete_hr ON public.finkzeit;
DROP POLICY IF EXISTS bescheinigungen_select_own_or_hr ON public.bescheinigungen;
DROP POLICY IF EXISTS bescheinigungen_modify_hr ON public.bescheinigungen;

DO $$
DECLARE snap RECORD;
BEGIN
  FOR snap IN SELECT tablename, polname, cmd, qual FROM public._rls_snapshot_v3109
    WHERE tablename IN ('finkzeit','bescheinigungen')
  LOOP
    BEGIN
      EXECUTE format(
        'CREATE POLICY %I ON public.%I FOR %s TO authenticated USING (%s)',
        snap.polname, snap.tablename, snap.cmd, COALESCE(snap.qual,'true')
      );
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
  END LOOP;
END $$;
