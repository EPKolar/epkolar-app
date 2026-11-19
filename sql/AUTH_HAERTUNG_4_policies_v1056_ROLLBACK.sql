-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_4_policies_v1056_ROLLBACK.sql  —  alte Bedingungen zurueck (aus public._auth_haertung_v1056_sicherung)
-- STATUS: ENTWURF — nur durch Sebastian ueber das Tor.
-- =====================================================================================

BEGIN;

DO $$
DECLARE r record; v_sql text; v_n int := 0; v_tab text; v_pol text; v_cmd text;
BEGIN
  IF to_regclass('public._auth_haertung_v1056_sicherung') IS NULL THEN
    RAISE EXCEPTION 'Keine Sicherung vorhanden - AUTH_HAERTUNG_4 wurde nie angewendet (nichts zu tun)'; END IF;
  FOR r IN SELECT objekt, extra FROM public._auth_haertung_v1056_sicherung WHERE objekt LIKE 'policy4:%' LOOP
    v_tab := r.extra->>'tabelle'; v_pol := r.extra->>'policy'; v_cmd := r.extra->>'cmd';
    IF to_regclass('public.'||v_tab) IS NULL
       OR NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename=v_tab AND policyname=v_pol) THEN
      RAISE NOTICE 'Policy %.% gibt es nicht mehr - uebersprungen', v_tab, v_pol;
    ELSE
      v_sql := format('ALTER POLICY %I ON public.%I', v_pol, v_tab);
      IF r.extra->>'qual' IS NOT NULL AND v_cmd <> 'INSERT' THEN v_sql := v_sql || ' USING (' || (r.extra->>'qual') || ')'; END IF;
      IF r.extra->>'with_check' IS NOT NULL AND v_cmd NOT IN ('SELECT','DELETE') THEN
        v_sql := v_sql || ' WITH CHECK (' || (r.extra->>'with_check') || ')'; END IF;
      IF v_sql <> format('ALTER POLICY %I ON public.%I', v_pol, v_tab) THEN EXECUTE v_sql; v_n := v_n + 1; END IF;
    END IF;
    DELETE FROM public._auth_haertung_v1056_sicherung WHERE objekt = r.objekt;
  END LOOP;
  RAISE NOTICE 'Policies zurueck: %', v_n;
END $$;

DROP POLICY IF EXISTS workers_kein_kiosk_v1056 ON public.workers;

COMMIT;
