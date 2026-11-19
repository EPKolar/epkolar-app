-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_1_users_v1056_ENTWURF.sql  —  public.users: Hash nicht lesbar, fremde Zeilen nicht aenderbar,
--                                              login_lookup nur noch E-Mail, Admin-RPCs ohne Kontouebernahme
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Pruefung durch Chat-Claude, Einspielen nur durch Sebastian ueber das Tor.
-- Zweig fix/auth-haertung (Basis release/v1054). Bericht: C:/repos/epk-auth-pruefung-2026-11-19.md (Funde 2, 5, 6, 13, 14).
--
-- REIHENFOLGE (WICHTIG):
--   0. Dashboard: "Allow new users to sign up" AUS (Fund 1, Sebastian, 1 Klick).
--   1. App >= v3.9.1056 ausliefern UND warten, bis ALLE Geraete sie haben (Tablets mit altem Service-Worker!).
--      Grund: (a) alte Apps lesen users mit select=* und bekommen nach Schritt 1 dieses Skripts 42501 fuer die
--      GANZE Tabelle (auch beim Schreiben, weil return=representation alle Spalten zurueckliest); (b) alte Apps
--      brauchen aus login_lookup die id - nach Schritt 3 meldet die alte Anmeldemaske "Benutzer nicht gefunden".
--      Pruefen: activity_log action='login' der letzten Tage, details enthaelt den User-Agent - oder jedes Tablet
--      einmal oeffnen und unten auf der Anmeldemaske die Version lesen.
--   2. AUTH_HAERTUNG_2_gesperrt (Helfer), 3. AUTH_HAERTUNG_3_waisen, 4. AUTH_HAERTUNG_4_policies,
--      5. AUTH_HAERTUNG_5_passwort_hilfe (unabhaengig, jederzeit; die App zeigt bis dahin den ehrlichen Text).
--   Dieses Skript (1) haengt NICHT von 2-5 ab.
--
-- WAS ES AENDERT
--   1. Spaltenrecht: anon/authenticated duerfen users.password_hash nicht mehr LESEN. Technisch: Tabellen-SELECT
--      weg, SELECT auf alle uebrigen Spalten (zur Laufzeit aus information_schema gebaut). FOLGE: eine kuenftig
--      NEU angelegte Spalte in users ist fuer die App erst lesbar, wenn sie ausdruecklich gegrantet wird
--      (GRANT SELECT (neue_spalte) ON public.users TO anon, authenticated;) - im Migrationsmuster vermerken.
--      SECURITY-DEFINER-Funktionen (login_lookup, auth_role, admin_*) sind nicht betroffen (laufen als Eigentuemer).
--   2. users_update: Nicht-Admin nur die EIGENE Zeile (auth_user_id = auth.uid()), Admin unveraendert alle.
--      Dazu Trigger zz_users_selbst_nur_harmlos: Nicht-Admin darf an der eigenen Zeile nur
--      last_login, login_count, updated_at, phone, avatar aendern (gemessen im Code: die App schreibt als
--      Nicht-Admin NUR last_login + login_count beim Anmelden; phone/avatar sind harmlos, falls es sie gibt).
--      name/email/username/active/locked/deactivate_at/role/permissions/password_hash/... nur Admin.
--      Der bestehende Trigger guard_users_privilege bleibt unangetastet.
--      Ausserdem: users-INSERT/-DELETE-Policies, die nur "angemeldet" pruefen, werden auf Admin eingeengt
--      (die App legt Benutzer nur als Admin an und loescht nur als Admin).
--   3. login_lookup: liefert NUR {"email": ...} und nur fuer aktive, nicht gesperrte, nicht ausgeschiedene
--      Konten mit E-Mail - sonst NULL. Keine id, kein Telefon, keine Rechte an anonyme Aufrufer.
--      (Ersetzt den nie angewendeten sql/fix_login_lookup_v3.9.213.sql - der gab noch id/role/locked heraus.)
--   4. admin_create_user / admin_reset_password: werden in eine HUELLE gelegt. Das Original bleibt byte-gleich als
--      _admin_create_user_basis_v1056 / _admin_reset_password_basis_v1056 erhalten (Kopie aus pg_get_functiondef,
--      kein Nachbau - der Rumpf liegt nicht im Repo) und ist nur noch fuer den Eigentuemer ausfuehrbar.
--      Die Huelle prueft VOR dem Original:
--        * Admin (auth_role() = 'admin'), sonst 42501 - damit erfaehrt ein Nicht-Admin auch nicht, ob es eine
--          E-Mail gibt;
--        * Passwort mindestens 8 Zeichen (App: PW_MIN_LEN = 8);
--        * create: gibt es die E-Mail schon in auth.users -> Abbruch 23505 (Fund 14: vorher wurde das Passwort des
--          vorhandenen Kontos still ueberschrieben, ein Tippfehler uebernahm ein fremdes Konto). Ausnahme nur:
--          das vorhandene Konto ist schon mit genau DIESEM Benutzernamen verknuepft (Wiederholung derselben Anlage).
--        * reset: NACH erfolgreichem Original alle Refresh-Tokens des Ziels widerrufen und seine Sitzungen loeschen
--          (Fund 13: vorher blieb ein Angreifer nach dem Reset angemeldet). Laufende Zugangs-Tokens gelten noch
--          hoechstens bis zu ihrem Ablauf (Standard 1 h).
--   5. (auskommentiert, nur mit Freigabe) users.password_hash leeren - die App >= v3.9.1056 liest und schreibt die
--      Spalte nicht mehr; offline gilt die PBKDF2-Ablage auf dem Geraet.
--
-- SICHERUNG: Originaldefinitionen und Policies landen beim ERSTEN Lauf in public._auth_haertung_v1056_sicherung
--   (nur Eigentuemer, RLS an, keine Rechte fuer anon/authenticated). Der Rueckweg liest dort:
--   sql/AUTH_HAERTUNG_1_users_v1056_ROLLBACK.sql
-- =====================================================================================

BEGIN;

-- 0. VORPRUEFUNG (bricht ab, wenn die Annahmen nicht stimmen — dann NICHT weiter, sondern melden)
DO $$
DECLARE v_t text; v_n int; v_liste text;
BEGIN
  IF to_regclass('public.users') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: public.users fehlt'; END IF;
  FOREACH v_t IN ARRAY ARRAY['password_hash','auth_user_id','username','email','role','active','locked','deactivate_at'] LOOP
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='users' AND column_name=v_t) THEN
      RAISE EXCEPTION 'Vorpruefung: users.% fehlt', v_t; END IF;
  END LOOP;
  SELECT data_type INTO v_t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='users' AND column_name='auth_user_id';
  IF v_t <> 'uuid' THEN RAISE EXCEPTION 'Vorpruefung: users.auth_user_id ist %, erwartet uuid', v_t; END IF;
  SELECT data_type INTO v_t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='users' AND column_name='deactivate_at';
  IF v_t NOT IN ('date','timestamp with time zone','timestamp without time zone') THEN
    RAISE EXCEPTION 'Vorpruefung: users.deactivate_at ist %, erwartet date/timestamp', v_t; END IF;
  IF to_regprocedure('public.auth_role()') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: public.auth_role() fehlt'; END IF;
  IF to_regprocedure('public.login_lookup(text)') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: public.login_lookup(text) fehlt'; END IF;
  IF (SELECT pg_get_function_result('public.login_lookup(text)'::regprocedure)) <> 'jsonb' THEN
    RAISE EXCEPTION 'Vorpruefung: login_lookup liefert nicht jsonb - Client-Vertrag pruefen'; END IF;
  -- users_update muss existieren; jede WEITERE freizuegige UPDATE/ALL-Policy auf users wuerde die Einengung aushebeln
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='users' AND policyname='users_update') THEN
    RAISE EXCEPTION 'Vorpruefung: Policy users_update fehlt'; END IF;
  SELECT string_agg(policyname||' ('||cmd||')', ', ') INTO v_liste FROM pg_policies
   WHERE schemaname='public' AND tablename='users' AND permissive='PERMISSIVE'
     AND cmd IN ('UPDATE','ALL') AND policyname <> 'users_update';
  IF v_liste IS NOT NULL THEN
    RAISE EXCEPTION 'Vorpruefung: weitere freizuegige UPDATE/ALL-Policies auf users: % - erst klaeren', v_liste; END IF;
  -- Admin-RPCs: je genau eine Fassung, erwartete Parameter
  SELECT count(*) INTO v_n FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='admin_create_user';
  IF v_n <> 1 THEN RAISE EXCEPTION 'Vorpruefung: admin_create_user gibt es %-mal (erwartet 1)', v_n; END IF;
  SELECT count(*) INTO v_n FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='admin_reset_password';
  IF v_n <> 1 THEN RAISE EXCEPTION 'Vorpruefung: admin_reset_password gibt es %-mal (erwartet 1)', v_n; END IF;
  SELECT count(*) INTO v_n FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='admin_create_user'
     AND proargnames @> ARRAY['p_email','p_password','p_username'];
  IF v_n <> 1 THEN RAISE EXCEPTION 'Vorpruefung: admin_create_user hat nicht die Parameter p_email/p_password/p_username'; END IF;
  SELECT count(*) INTO v_n FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='admin_reset_password'
     AND proargnames @> ARRAY['target_user_id','new_password'];
  IF v_n <> 1 THEN RAISE EXCEPTION 'Vorpruefung: admin_reset_password hat nicht die Parameter target_user_id/new_password'; END IF;
  -- auth-Schema: Sitzungen und Refresh-Tokens wie erwartet, und wir duerfen sie anfassen
  IF to_regclass('auth.sessions') IS NULL OR to_regclass('auth.refresh_tokens') IS NULL THEN
    RAISE EXCEPTION 'Vorpruefung: auth.sessions/auth.refresh_tokens fehlen'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='auth' AND table_name='sessions' AND column_name='user_id' AND data_type='uuid') THEN
    RAISE EXCEPTION 'Vorpruefung: auth.sessions.user_id (uuid) fehlt'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='auth' AND table_name='refresh_tokens' AND column_name='revoked') THEN
    RAISE EXCEPTION 'Vorpruefung: auth.refresh_tokens.revoked fehlt'; END IF;
  -- Huellen-Eigentuemer = Ausfuehrender, sonst darf die Huelle ihre Basis (nur Eigentuemer) nicht aufrufen
  SELECT string_agg(proname||'='||pg_get_userbyid(proowner), ', ') INTO v_liste FROM pg_proc
   WHERE pronamespace='public'::regnamespace AND proname IN ('admin_create_user','admin_reset_password')
     AND pg_get_userbyid(proowner) <> current_user;
  IF v_liste IS NOT NULL THEN
    RAISE EXCEPTION 'Vorpruefung: Eigentuemer % weicht von der ausfuehrenden Rolle % ab - als Eigentuemer ausfuehren', v_liste, current_user; END IF;
  IF NOT has_table_privilege('auth.sessions','DELETE') OR NOT has_table_privilege('auth.refresh_tokens','UPDATE') THEN
    RAISE EXCEPTION 'Vorpruefung: die ausfuehrende Rolle (%) darf auth.sessions/refresh_tokens nicht aendern', current_user; END IF;
  -- Hinweis (bricht nicht ab): weitere BEFORE-UPDATE-Trigger auf users (koennen NEW veraendern)
  SELECT string_agg(tgname, ', ') INTO v_liste FROM pg_trigger
   WHERE tgrelid='public.users'::regclass AND NOT tgisinternal AND tgname <> 'zz_users_selbst_nur_harmlos';
  RAISE NOTICE 'HINWEIS Trigger auf users (bleiben): %', coalesce(v_liste,'-');
END $$;

-- 0a. Sicherungstabelle (gemeinsam fuer AUTH_HAERTUNG_1..4; nur Eigentuemer)
CREATE TABLE IF NOT EXISTS public._auth_haertung_v1056_sicherung (
  objekt       text PRIMARY KEY,
  art          text NOT NULL,
  definition   text,
  extra        jsonb,
  gesichert_am timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public._auth_haertung_v1056_sicherung ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public._auth_haertung_v1056_sicherung FROM PUBLIC, anon, authenticated;

-- 0b. Stand VORHER (nur Zahlen, nie Werte)
DO $$
DECLARE v_alle int; v_hash int; v_akt int; v_gesp int;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE password_hash IS NOT NULL AND password_hash <> ''),
         count(*) FILTER (WHERE coalesce(active::text,'') IN ('1','t','true')),
         count(*) FILTER (WHERE coalesce(locked::text,'') IN ('1','t','true'))
    INTO v_alle, v_hash, v_akt, v_gesp FROM public.users;
  RAISE NOTICE 'VORHER users: % Zeilen, % mit password_hash, % aktiv, % gesperrt', v_alle, v_hash, v_akt, v_gesp;
  RAISE NOTICE 'VORHER Leserecht password_hash: anon=% authenticated=%',
    has_column_privilege('anon','public.users','password_hash','SELECT'),
    has_column_privilege('authenticated','public.users','password_hash','SELECT');
  RAISE NOTICE 'VORHER Tabellen-SELECT users: anon=% authenticated=%',
    has_table_privilege('anon','public.users','SELECT'), has_table_privilege('authenticated','public.users','SELECT');
END $$;

-- Sicherung der Rechte (nur beim ersten Lauf)
INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, extra)
SELECT 'grant:public.users:select', 'grant',
       jsonb_build_object('anon_tabelle', has_table_privilege('anon','public.users','SELECT'),
                          'authenticated_tabelle', has_table_privilege('authenticated','public.users','SELECT'))
ON CONFLICT (objekt) DO NOTHING;

-- 1. SPALTENRECHT: password_hash nicht mehr lesbar (Tabellen-SELECT weg, alle anderen Spalten einzeln)
DO $$
DECLARE v_spalten text;
BEGIN
  SELECT string_agg(quote_ident(column_name), ', ' ORDER BY ordinal_position) INTO v_spalten
    FROM information_schema.columns
   WHERE table_schema='public' AND table_name='users' AND column_name <> 'password_hash';
  REVOKE SELECT ON public.users FROM anon, authenticated;
  EXECUTE format('GRANT SELECT (%s) ON public.users TO anon, authenticated', v_spalten);
  -- falls irgendwo ein Spaltenrecht auf den Hash steht: weg
  REVOKE SELECT (password_hash) ON public.users FROM anon, authenticated;
END $$;

-- 2. users_update: eigene Zeile oder Admin (+ Sicherung der alten Fassung)
INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, extra)
SELECT 'policy:public.users.'||policyname, 'policy',
       jsonb_build_object('permissive', permissive, 'roles', roles, 'cmd', cmd, 'qual', qual, 'with_check', with_check)
  FROM pg_policies WHERE schemaname='public' AND tablename='users' AND policyname='users_update'
ON CONFLICT (objekt) DO NOTHING;

DROP POLICY IF EXISTS users_update ON public.users;
CREATE POLICY users_update ON public.users
  FOR UPDATE TO authenticated
  USING (public.auth_role() = 'admin' OR auth_user_id = (SELECT auth.uid()))
  WITH CHECK (public.auth_role() = 'admin' OR auth_user_id = (SELECT auth.uid()));

-- 2b. Nicht-Admin: an der eigenen Zeile nur harmlose Spalten
CREATE OR REPLACE FUNCTION public._users_selbst_nur_harmlos()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
  v_frei constant text[] := ARRAY['last_login','login_count','updated_at','phone','avatar'];
  v_alt jsonb; v_neu jsonb; v_k text;
BEGIN
  -- Nur Anfragen mit Benutzer-Identitaet ueber die API. SQL-Editor/Cron (auth.uid() NULL) und service_role bleiben
  -- frei; Admin-RPCs laufen mit der Identitaet des Admins und passieren die Admin-Pruefung.
  IF auth.uid() IS NULL OR coalesce(auth.role(),'') <> 'authenticated' THEN RETURN NEW; END IF;
  IF public.auth_role() = 'admin' THEN RETURN NEW; END IF;
  v_alt := to_jsonb(OLD); v_neu := to_jsonb(NEW);
  FOREACH v_k IN ARRAY v_frei LOOP v_alt := v_alt - v_k; v_neu := v_neu - v_k; END LOOP;
  IF v_alt IS DISTINCT FROM v_neu THEN
    RAISE EXCEPTION 'users: diese Felder darf nur der Admin aendern (eigenes Konto: nur %)', array_to_string(v_frei, ', ')
      USING ERRCODE = '42501';
  END IF;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION public._users_selbst_nur_harmlos() FROM PUBLIC, anon, authenticated;
-- Name mit zz_: BEFORE-Trigger laufen alphabetisch - dieser sieht NEW nach allen anderen
DROP TRIGGER IF EXISTS zz_users_selbst_nur_harmlos ON public.users;
CREATE TRIGGER zz_users_selbst_nur_harmlos BEFORE UPDATE ON public.users
  FOR EACH ROW EXECUTE FUNCTION public._users_selbst_nur_harmlos();

-- 2c. users INSERT/DELETE, die nur "angemeldet" pruefen -> Admin (sonst kann jeder Angemeldete Benutzerzeilen anlegen)
DO $$
DECLARE r record; v_norm_q text; v_norm_c text;
  v_nur_angemeldet constant text[] := ARRAY[
    '(auth.role()=''authenticated''::text)', 'auth.role()=''authenticated''::text',
    '((selectauth.role()asrole)=''authenticated''::text)', '(auth.uid()isnotnull)', 'auth.uid()isnotnull',
    '((selectauth.uid()asuid)isnotnull)', 'true'];
BEGIN
  FOR r IN SELECT * FROM pg_policies WHERE schemaname='public' AND tablename='users'
             AND permissive='PERMISSIVE' AND cmd IN ('INSERT','DELETE') LOOP
    v_norm_q := regexp_replace(lower(coalesce(r.qual,'')), '\s+', '', 'g');
    v_norm_c := regexp_replace(lower(coalesce(r.with_check,'')), '\s+', '', 'g');
    IF (r.cmd = 'DELETE' AND v_norm_q = ANY (v_nur_angemeldet))
       OR (r.cmd = 'INSERT' AND v_norm_c = ANY (v_nur_angemeldet)) THEN
      INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, extra)
      VALUES ('policy:public.users.'||r.policyname, 'policy',
              jsonb_build_object('permissive', r.permissive, 'roles', r.roles, 'cmd', r.cmd, 'qual', r.qual, 'with_check', r.with_check))
      ON CONFLICT (objekt) DO NOTHING;
      IF r.cmd = 'DELETE' THEN
        EXECUTE format('ALTER POLICY %I ON public.users USING (public.auth_role() = %L)', r.policyname, 'admin');
      ELSE
        EXECUTE format('ALTER POLICY %I ON public.users WITH CHECK (public.auth_role() = %L)', r.policyname, 'admin');
      END IF;
      RAISE NOTICE 'users-Policy % (%) auf Admin eingeengt', r.policyname, r.cmd;
    ELSE
      RAISE NOTICE 'users-Policy % (%) unveraendert: qual=% with_check=%', r.policyname, r.cmd, r.qual, r.with_check;
    END IF;
  END LOOP;
END $$;

-- 3. login_lookup: nur E-Mail, nur aktive/nicht gesperrte/nicht ausgeschiedene Konten
INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, definition)
SELECT 'funktion:public.login_lookup(text)', 'funktion', pg_get_functiondef('public.login_lookup(text)'::regprocedure)
ON CONFLICT (objekt) DO NOTHING;

CREATE OR REPLACE FUNCTION public.login_lookup(p_username text)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  -- AUTH_HAERTUNG_v1056: anonym aufrufbar (Anmeldung) -> gibt NUR die E-Mail heraus. Gesperrt, inaktiv,
  -- ausgeschieden, unbekannt oder ohne E-Mail: NULL (die App zeigt dann dieselbe Meldung wie bei falschem Passwort).
  SELECT jsonb_build_object('email', btrim(u.email))
    FROM public.users u
   WHERE lower(u.username) = lower(btrim(p_username))
     AND coalesce(u.active::text,'') IN ('1','t','true')
     AND NOT coalesce(u.locked::text IN ('1','t','true'), false)
     AND (u.deactivate_at IS NULL OR u.deactivate_at > current_date)
     AND nullif(btrim(coalesce(u.email,'')),'') IS NOT NULL
   LIMIT 1;
$$;

-- 4. Admin-RPCs in eine Huelle legen (Original bleibt byte-gleich als *_basis_v1056)
DO $$
DECLARE
  v_name text; v_basis text; v_oid oid; v_src text; v_def text; v_args text; v_idargs text; v_res text;
  v_set boolean; v_names text[]; v_modes text[]; v_i int; v_call text; v_pruef text; v_rumpf text;
BEGIN
  FOREACH v_name IN ARRAY ARRAY['admin_create_user','admin_reset_password'] LOOP
    v_basis := '_' || v_name || '_basis_v1056';
    SELECT p.oid, p.prosrc, pg_get_function_arguments(p.oid), pg_get_function_identity_arguments(p.oid),
           pg_get_function_result(p.oid), p.proretset, p.proargnames, p.proargmodes::text[]
      INTO v_oid, v_src, v_args, v_idargs, v_res, v_set, v_names, v_modes
      FROM pg_proc p WHERE p.pronamespace='public'::regnamespace AND p.proname=v_name;
    IF position('AUTH_HAERTUNG_v1056_HUELLE' in v_src) > 0 THEN
      RAISE NOTICE '% ist schon die Huelle v1056 - uebersprungen', v_name; CONTINUE;
    END IF;
    IF v_set THEN RAISE EXCEPTION '% liefert eine Menge (SETOF/TABLE) - Huelle nicht vorgesehen, melden', v_name; END IF;
    IF v_modes IS NOT NULL AND NOT (v_modes <@ ARRAY['i']) THEN
      RAISE EXCEPTION '% hat OUT/INOUT/VARIADIC-Parameter (%) - Huelle nicht vorgesehen, melden', v_name, v_modes; END IF;
    IF v_names IS NULL OR array_position(v_names, '') IS NOT NULL THEN
      RAISE EXCEPTION '% hat unbenannte Parameter - Huelle nicht vorgesehen, melden', v_name; END IF;
    -- Original sichern (erster Lauf) und als Basis kopieren
    v_def := pg_get_functiondef(v_oid);
    INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, definition)
    VALUES ('funktion:public.'||v_name, 'funktion', v_def) ON CONFLICT (objekt) DO NOTHING;
    IF position(('FUNCTION public.'||v_name||'(') in v_def) = 0 THEN
      RAISE EXCEPTION 'Kopf von % unerwartet - melden', v_name; END IF;
    EXECUTE replace(v_def, 'FUNCTION public.'||v_name||'(', 'FUNCTION public.'||v_basis||'(');
    EXECUTE format('REVOKE ALL ON FUNCTION public.%I(%s) FROM PUBLIC, anon, authenticated', v_basis, v_idargs);
    -- Aufruf mit benannten Parametern
    v_call := '';
    FOR v_i IN 1..array_length(v_names,1) LOOP
      v_call := v_call || CASE WHEN v_call = '' THEN '' ELSE ', ' END || format('%1$I => %1$I', v_names[v_i]);
    END LOOP;
    v_call := format('public.%I(%s)', v_basis, v_call);
    IF v_name = 'admin_create_user' THEN
      v_pruef := $p$
  IF length(coalesce(p_password,'')) < 8 THEN
    RAISE EXCEPTION 'admin_create_user: Passwort mindestens 8 Zeichen' USING ERRCODE = '22023';
  END IF;
  SELECT au.id INTO v_vorhanden FROM auth.users au WHERE lower(au.email) = lower(btrim(p_email)) LIMIT 1;
  IF v_vorhanden IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM public.users pu
        WHERE pu.auth_user_id = v_vorhanden AND lower(pu.username) = lower(btrim(p_username))) THEN
    RAISE EXCEPTION 'admin_create_user: fuer diese E-Mail gibt es schon einen Login - nichts geaendert. E-Mail pruefen oder das Passwort ueber Passwort zuruecksetzen setzen.'
      USING ERRCODE = '23505';
  END IF;$p$;
    ELSE
      v_pruef := $p$
  IF length(coalesce(new_password,'')) < 8 THEN
    RAISE EXCEPTION 'admin_reset_password: Passwort mindestens 8 Zeichen' USING ERRCODE = '22023';
  END IF;$p$;
    END IF;
    IF v_res = 'void' THEN
      v_rumpf := format('PERFORM %s;', v_call);
    ELSE
      v_rumpf := format('v_erg := %s;', v_call);
    END IF;
    IF v_name = 'admin_reset_password' THEN
      v_rumpf := v_rumpf || $r$
  -- Fund 13: nach erfolgreichem Reset alle Sitzungen des Ziels beenden
  UPDATE auth.refresh_tokens SET revoked = true WHERE user_id = target_user_id::text AND revoked IS DISTINCT FROM true;
  DELETE FROM auth.sessions WHERE user_id = target_user_id;$r$;
    END IF;
    v_rumpf := v_rumpf || CASE WHEN v_res = 'void' THEN E'\n  RETURN;' ELSE E'\n  RETURN v_erg;' END;
    EXECUTE format($f$CREATE OR REPLACE FUNCTION public.%1$I(%2$s)
RETURNS %3$s
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $huelle$
#variable_conflict use_column
DECLARE v_vorhanden uuid;%4$s
BEGIN
  -- AUTH_HAERTUNG_v1056_HUELLE: Original unveraendert in public.%5$I, Sicherung in public._auth_haertung_v1056_sicherung
  IF public.auth_role() IS DISTINCT FROM 'admin' THEN
    RAISE EXCEPTION '%1$s: nur Admin' USING ERRCODE = '42501';
  END IF;%6$s
  %7$s
END
$huelle$;$f$,
      v_name, v_args, v_res,
      CASE WHEN v_res = 'void' THEN '' ELSE format(' v_erg %s;', v_res) END,
      v_basis, v_pruef, v_rumpf);
    RAISE NOTICE '% in Huelle gelegt (Basis %)', v_name, v_basis;
  END LOOP;
END $$;

-- 5. (NUR MIT FREIGABE, auskommentiert) Hash-Spalte leeren - erst wenn alle Geraete >= v3.9.1056 haben.
--    Nicht umkehrbar (die Werte sind danach weg). Pruefen, ob password_hash NOT NULL ist:
--      SELECT is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='password_hash';
-- UPDATE public.users SET password_hash = NULL WHERE password_hash IS NOT NULL;

-- 6. Stand NACHHER (bricht ab, wenn das Ziel verfehlt ist)
DO $$
DECLARE v_q text; v_c text; v_n int;
BEGIN
  IF has_column_privilege('authenticated','public.users','password_hash','SELECT')
     OR has_column_privilege('anon','public.users','password_hash','SELECT') THEN
    RAISE EXCEPTION 'Nachpruefung: password_hash ist noch lesbar'; END IF;
  IF NOT has_column_privilege('authenticated','public.users','email','SELECT') THEN
    RAISE EXCEPTION 'Nachpruefung: authenticated kann users.email nicht mehr lesen - Spaltenrechte falsch'; END IF;
  SELECT qual, with_check INTO v_q, v_c FROM pg_policies WHERE schemaname='public' AND tablename='users' AND policyname='users_update';
  IF v_c IS NULL OR position('auth.uid()' in v_q) = 0 THEN RAISE EXCEPTION 'Nachpruefung: users_update nicht wie erwartet: % / %', v_q, v_c; END IF;
  SELECT count(*) INTO v_n FROM pg_proc WHERE pronamespace='public'::regnamespace
     AND proname IN ('admin_create_user','admin_reset_password') AND position('AUTH_HAERTUNG_v1056_HUELLE' in prosrc) > 0;
  IF v_n <> 2 THEN RAISE EXCEPTION 'Nachpruefung: nur % von 2 Admin-RPCs in der Huelle', v_n; END IF;
  RAISE NOTICE 'NACHHER: password_hash nicht lesbar, users_update eng, Admin-RPCs in Huelle, login_lookup nur E-Mail';
END $$;

COMMIT;

-- =====================================================================================
-- PROBE (nach dem Apply, eigener Lauf; aendert nichts: BEGIN ... ROLLBACK). Gibt NIE Werte aus, nur Zahlen/Ja-Nein.
-- Erwartung: Monteur/Buero/Kiosk koennen password_hash nicht lesen, fremde Zeilen nicht aendern, an der eigenen nur
-- last_login/login_count; Admin aendert fremde Zeilen; anon bekommt aus login_lookup nur {email}; gesperrte Konten
-- bekommen NULL; admin_create_user mit vorhandener E-Mail bricht ab; admin_reset_password beendet die Sitzungen.
-- =====================================================================================
-- BEGIN;
-- DO $probe$
-- DECLARE v_uid uuid; v_id text; v_fremd text; v_rolle text; v_n int; v_j jsonb; v_name text; v_admin uuid; v_mail text;
-- BEGIN
--   FOREACH v_rolle IN ARRAY ARRAY['monteur','buero','projektleiter','lager_display','admin'] LOOP
--     v_uid := NULL;
--     SELECT auth_user_id, id::text INTO v_uid, v_id FROM public.users WHERE role = v_rolle AND auth_user_id IS NOT NULL LIMIT 1;
--     IF v_uid IS NULL THEN RAISE NOTICE 'Probe %: kein Nutzer mit dieser Rolle', v_rolle; CONTINUE; END IF;
--     SELECT id::text INTO v_fremd FROM public.users WHERE id::text <> v_id ORDER BY id LIMIT 1;
--     PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
--     EXECUTE 'SET LOCAL ROLE authenticated';
--     BEGIN
--       EXECUTE 'SELECT count(password_hash) FROM public.users';
--       RAISE EXCEPTION 'PROBE FEHLER % kann password_hash LESEN', v_rolle;
--     EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe %: password_hash nicht lesbar - ok', v_rolle;
--     END;
--     SELECT count(*) INTO v_n FROM public.users;   -- Spaltenliste ohne Hash geht (select= der App)
--     EXECUTE 'UPDATE public.users SET last_login = now() WHERE id::text = $1' USING v_id;   -- eigene Zeile: erlaubt
--     IF v_rolle <> 'admin' THEN
--       EXECUTE 'UPDATE public.users SET name = name || $2 WHERE id::text = $1' USING v_fremd, 'x';
--       GET DIAGNOSTICS v_n = ROW_COUNT;
--       IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER % aendert fremde Zeile', v_rolle; END IF;
--       BEGIN
--         EXECUTE 'UPDATE public.users SET active = active WHERE id::text = $1' USING v_id;   -- unveraendert: ok
--         EXECUTE 'UPDATE public.users SET email = email || $2 WHERE id::text = $1' USING v_id, 'x';
--         RAISE EXCEPTION 'PROBE FEHLER % aendert eigene E-Mail', v_rolle;
--       EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe %: eigene E-Mail gesperrt - ok', v_rolle;
--       END;
--       BEGIN
--         PERFORM public.admin_reset_password(v_uid, 'Probe-Kennwort-123');
--         RAISE EXCEPTION 'PROBE FEHLER % darf admin_reset_password', v_rolle;
--       EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe %: admin_reset_password abgewiesen - ok', v_rolle;
--       END;
--     ELSE
--       v_admin := v_uid;
--       EXECUTE 'UPDATE public.users SET name = name WHERE id::text = $1' USING v_fremd;
--       GET DIAGNOSTICS v_n = ROW_COUNT;
--       IF v_n <> 1 THEN RAISE EXCEPTION 'PROBE FEHLER admin kann fremde Zeile nicht aendern'; END IF;
--       -- vorhandene E-Mail -> Abbruch
--       SELECT email, username INTO v_mail, v_name FROM public.users WHERE auth_user_id IS NOT NULL AND id::text <> v_id LIMIT 1;
--       BEGIN
--         PERFORM public.admin_create_user(p_email => v_mail, p_password => 'Probe-Kennwort-123', p_username => 'probe_neu_v1056');
--         RAISE EXCEPTION 'PROBE FEHLER admin_create_user hat vorhandene E-Mail angenommen';
--       EXCEPTION WHEN unique_violation THEN RAISE NOTICE 'Probe admin: vorhandene E-Mail abgewiesen - ok';
--       END;
--       -- (falls admin_create_user weitere Pflichtparameter hat: oben ergaenzen)
--     END IF;
--     EXECUTE 'RESET ROLE';
--   END LOOP;
--   -- Reset beendet Sitzungen (als Admin, Ziel = ein Nicht-Admin mit Sitzung)
--   SELECT pu.auth_user_id INTO v_uid FROM public.users pu
--    WHERE pu.role <> 'admin' AND EXISTS (SELECT 1 FROM auth.sessions s WHERE s.user_id = pu.auth_user_id) LIMIT 1;
--   IF v_uid IS NOT NULL AND v_admin IS NOT NULL THEN
--     PERFORM set_config('request.jwt.claims', json_build_object('sub', v_admin, 'role', 'authenticated')::text, true);
--     EXECUTE 'SET LOCAL ROLE authenticated';
--     PERFORM public.admin_reset_password(v_uid, 'Probe-Kennwort-123');
--     EXECUTE 'RESET ROLE';
--     SELECT count(*) INTO v_n FROM auth.sessions WHERE user_id = v_uid;
--     IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER nach Reset noch % Sitzungen', v_n; END IF;
--     RAISE NOTICE 'Probe Reset: Sitzungen beendet - ok';
--   END IF;
--   -- anon: login_lookup nur {email}; gesperrtes Konto -> NULL
--   SELECT username INTO v_name FROM public.users WHERE coalesce(active::text,'') IN ('1','t','true') AND email <> '' LIMIT 1;
--   PERFORM set_config('request.jwt.claims', '{"role":"anon"}', true);
--   EXECUTE 'SET LOCAL ROLE anon';
--   v_j := public.login_lookup(v_name);
--   IF v_j IS NULL OR (SELECT array_agg(k) FROM jsonb_object_keys(v_j) k) <> ARRAY['email'] THEN
--     RAISE EXCEPTION 'PROBE FEHLER login_lookup liefert nicht genau {email}'; END IF;
--   BEGIN
--     EXECUTE 'SELECT count(password_hash) FROM public.users';
--     RAISE EXCEPTION 'PROBE FEHLER anon kann password_hash lesen';
--   EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe anon: password_hash nicht lesbar - ok';
--   END;
--   EXECUTE 'RESET ROLE';
--   -- gesperrt simulieren: Typ von users.locked pruefen und GENAU EINE der beiden Zeilen einkommentieren
--   -- UPDATE public.users SET locked = 1    WHERE username = v_name;   -- locked ist integer
--   -- UPDATE public.users SET locked = true WHERE username = v_name;   -- locked ist boolean
--   -- IF public.login_lookup(v_name) IS NOT NULL THEN RAISE EXCEPTION 'PROBE FEHLER gesperrtes Konto bekommt E-Mail'; END IF;
--   RAISE NOTICE 'PROBE fertig';
-- END $probe$;
-- ROLLBACK;
--
-- WIEDERKEHRENDE KONTROLLE (lesend):
--   SELECT has_column_privilege('authenticated','public.users','password_hash','SELECT') AS hash_lesbar;  -- soll false
--   SELECT policyname, cmd, qual, with_check FROM pg_policies WHERE schemaname='public' AND tablename='users';
-- =====================================================================================
