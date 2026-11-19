-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_1_users_v1056_ROLLBACK.sql  —  Rueckweg zu AUTH_HAERTUNG_1_users_v1056_ENTWURF.sql
-- STATUS: ENTWURF — nur durch Sebastian ueber das Tor. Liest die Originale aus public._auth_haertung_v1056_sicherung.
-- Nicht zurueckholbar: Sitzungen, die admin_reset_password nach dem Apply beendet hat; ein geleerter password_hash.
-- Reihenfolge, falls mehrere zurueck: 4 -> 3 -> 2 -> 1 (5 unabhaengig).
-- =====================================================================================

BEGIN;

DO $$
BEGIN
  IF to_regclass('public._auth_haertung_v1056_sicherung') IS NULL THEN
    RAISE EXCEPTION 'Keine Sicherung vorhanden - AUTH_HAERTUNG_1 wurde nie angewendet (nichts zu tun)'; END IF;
END $$;

-- 1. Admin-RPCs: Original zurueck (CREATE OR REPLACE auf dieselbe Funktion, Rechte bleiben), Basis entfernen
DO $$
DECLARE v_name text; v_def text; v_idargs text;
BEGIN
  FOREACH v_name IN ARRAY ARRAY['admin_create_user','admin_reset_password'] LOOP
    SELECT definition INTO v_def FROM public._auth_haertung_v1056_sicherung WHERE objekt = 'funktion:public.'||v_name;
    IF v_def IS NULL THEN RAISE NOTICE '% ohne Sicherung - uebersprungen', v_name; CONTINUE; END IF;
    EXECUTE v_def;
    SELECT pg_get_function_identity_arguments(oid) INTO v_idargs FROM pg_proc
     WHERE pronamespace='public'::regnamespace AND proname = '_'||v_name||'_basis_v1056';
    IF v_idargs IS NOT NULL THEN
      EXECUTE format('DROP FUNCTION public.%I(%s)', '_'||v_name||'_basis_v1056', v_idargs);
    END IF;
    RAISE NOTICE '% zurueck auf Original', v_name;
  END LOOP;
END $$;

-- 2. login_lookup: Original zurueck
DO $$
DECLARE v_def text;
BEGIN
  SELECT definition INTO v_def FROM public._auth_haertung_v1056_sicherung WHERE objekt = 'funktion:public.login_lookup(text)';
  IF v_def IS NOT NULL THEN EXECUTE v_def; RAISE NOTICE 'login_lookup zurueck auf Original'; END IF;
END $$;

-- 3. Trigger weg, Policies zurueck (users_update und ggf. eingeengte INSERT/DELETE-Policies)
DROP TRIGGER IF EXISTS zz_users_selbst_nur_harmlos ON public.users;
DROP FUNCTION IF EXISTS public._users_selbst_nur_harmlos();

DO $$
DECLARE r record; v_name text; v_rollen text;
BEGIN
  FOR r IN SELECT * FROM public._auth_haertung_v1056_sicherung WHERE objekt LIKE 'policy:public.users.%' LOOP
    v_name := substr(r.objekt, length('policy:public.users.') + 1);
    SELECT string_agg(CASE WHEN x = 'public' THEN 'public' ELSE quote_ident(x) END, ', ')
      INTO v_rollen FROM jsonb_array_elements_text(r.extra->'roles') x;
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.users', v_name);
    EXECUTE format('CREATE POLICY %I ON public.users AS %s FOR %s TO %s%s%s',
      v_name, r.extra->>'permissive', r.extra->>'cmd', coalesce(v_rollen,'public'),
      CASE WHEN r.extra->>'qual' IS NOT NULL THEN ' USING ('||(r.extra->>'qual')||')' ELSE '' END,
      CASE WHEN r.extra->>'with_check' IS NOT NULL THEN ' WITH CHECK ('||(r.extra->>'with_check')||')' ELSE '' END);
    RAISE NOTICE 'Policy % zurueck', v_name;
  END LOOP;
END $$;

-- 4. Leserecht wie vorher (Review 19.11. Fund 10): ERST alles SELECT weg (der Tabellen-REVOKE nimmt auch die
--    Spaltenrechte aus dem Entwurf mit), DANN exakt nach Sicherung neu vergeben - sonst bliebe einer Rolle, die vorher
--    kein Tabellen-SELECT hatte, das Spaltenrecht des Entwurfs.
DO $$
DECLARE v_x jsonb;
BEGIN
  SELECT extra INTO v_x FROM public._auth_haertung_v1056_sicherung WHERE objekt = 'grant:public.users:select';
  IF v_x IS NULL THEN RAISE NOTICE 'Keine Rechte-Sicherung - Rechte unveraendert'; RETURN; END IF;
  REVOKE SELECT ON public.users FROM anon, authenticated;
  IF (v_x->>'anon_tabelle')::boolean THEN GRANT SELECT ON public.users TO anon; END IF;
  IF (v_x->>'authenticated_tabelle')::boolean THEN GRANT SELECT ON public.users TO authenticated; END IF;
  IF has_table_privilege('anon','public.users','SELECT') IS DISTINCT FROM (v_x->>'anon_tabelle')::boolean
     OR has_table_privilege('authenticated','public.users','SELECT') IS DISTINCT FROM (v_x->>'authenticated_tabelle')::boolean THEN
    RAISE EXCEPTION 'Rueckweg: Tabellen-SELECT auf users weicht von der Sicherung ab (PUBLIC-Grant?) - melden'; END IF;
  RAISE NOTICE 'Leserecht users wie gesichert: anon=% authenticated=%', v_x->>'anon_tabelle', v_x->>'authenticated_tabelle';
END $$;

-- 5. Sicherungseintraege dieses Schritts entfernen (Tabelle bleibt, falls 2-4 sie noch brauchen)
DELETE FROM public._auth_haertung_v1056_sicherung
 WHERE objekt IN ('funktion:public.admin_create_user','funktion:public.admin_reset_password',
                  'funktion:public.login_lookup(text)','grant:public.users:select')
    OR objekt LIKE 'policy:public.users.%';

COMMIT;
