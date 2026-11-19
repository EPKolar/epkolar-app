-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_2_gesperrt_v1056_ROLLBACK.sql  —  Rueckweg zu AUTH_HAERTUNG_2_gesperrt_v1056_ENTWURF.sql
-- STATUS: ENTWURF — nur durch Sebastian ueber das Tor. Originale aus public._auth_haertung_v1056_sicherung.
-- Bricht ab, solange noch eine Policy ist_aktiver_benutzer() nutzt (dann zuerst AUTH_HAERTUNG_4 zuruecknehmen).
-- =====================================================================================

BEGIN;

DO $$
DECLARE v_n int;
BEGIN
  IF to_regclass('public._auth_haertung_v1056_sicherung') IS NULL THEN
    RAISE EXCEPTION 'Keine Sicherung vorhanden - AUTH_HAERTUNG_2 wurde nie angewendet (nichts zu tun)'; END IF;
  SELECT count(*) INTO v_n FROM pg_policies
   WHERE (coalesce(qual,'') || ' ' || coalesce(with_check,'')) ILIKE '%ist_aktiver_benutzer%';
  IF v_n > 0 THEN
    RAISE EXCEPTION '% Policies nutzen noch ist_aktiver_benutzer() - zuerst AUTH_HAERTUNG_4 zuruecknehmen', v_n; END IF;
END $$;

-- 1. Helfer: Original zurueck, Basis weg
DO $$
DECLARE v_name text; v_def text;
BEGIN
  FOREACH v_name IN ARRAY ARRAY['auth_role','current_user_role','is_staff','is_hr','is_logged_in'] LOOP
    SELECT definition INTO v_def FROM public._auth_haertung_v1056_sicherung WHERE objekt = 'funktion:public.'||v_name||'()';
    IF v_def IS NULL THEN RAISE NOTICE '%() ohne Sicherung - uebersprungen', v_name; CONTINUE; END IF;
    EXECUTE v_def;
    EXECUTE format('DROP FUNCTION IF EXISTS public.%I()', '_'||v_name||'_basis_v1056');
    DELETE FROM public._auth_haertung_v1056_sicherung WHERE objekt = 'funktion:public.'||v_name||'()';
    RAISE NOTICE '%() zurueck auf Original', v_name;
  END LOOP;
END $$;

-- 2. ist_aktiver_benutzer und Index (keine Policy nutzt sie mehr, siehe Vorpruefung)
DROP FUNCTION IF EXISTS public.ist_aktiver_benutzer();
DROP INDEX IF EXISTS public.users_auth_user_id_idx_v1056;

COMMIT;
