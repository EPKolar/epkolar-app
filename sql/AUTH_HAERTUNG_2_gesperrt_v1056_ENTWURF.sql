-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_2_gesperrt_v1056_ENTWURF.sql  —  gesperrt / inaktiv / ausgeschieden auch SERVERSEITIG durchsetzen
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Pruefung durch Chat-Claude, Einspielen nur durch Sebastian ueber das Tor.
-- Bericht: C:/repos/epk-auth-pruefung-2026-11-19.md Fund 3 (locked/active/deactivate_at nur im Client geprueft).
--
-- WAS ES AENDERT
--   1. NEU public.ist_aktiver_benutzer() (boolean): true nur, wenn zum Token (auth.uid()) eine users-Zeile gehoert,
--      die aktiv ist (active 1/true), nicht gesperrt (locked nicht 1/true) und deren deactivate_at noch nicht
--      erreicht ist (deactivate_at > current_date - dieselbe Regel wie login_lookup). Ohne users-Zeile (Waise,
--      Selbstregistrierung): false. Fuer Policies gedacht (AUTH_HAERTUNG_4) - dort als (SELECT ...) einbetten,
--      dann rechnet Postgres sie einmal pro Anfrage statt pro Zeile.
--   2. Die Helfer, auf denen die Policies stehen, werden in eine HUELLE gelegt (Original byte-gleich als
--      _<name>_basis_v1056 erhalten, Kopie aus pg_get_functiondef - die Rumpfe liegen nicht vollstaendig im Repo):
--        auth_role()          -> fuer nicht aktive Benutzer 'anon' (wie heute ohne users-Zeile)
--        current_user_role()  -> fuer nicht aktive Benutzer NULL
--        is_staff(), is_hr(), is_logged_in() -> fuer nicht aktive Benutzer false
--      Fuer aktive Benutzer liefern alle Helfer EXAKT dasselbe wie vorher (die Huelle ruft das Original).
--      Fehlt ein optionaler Helfer (is_hr, is_logged_in, current_user_role), wird er uebersprungen (Hinweis).
--      is_kiosk_role() ruft auth_role() und folgt damit automatisch.
--
-- WIRKUNG AUF POLICIES (Abschnitt 3 listet sie zur Laufzeit; Repo-Stand siehe Pruefbericht v1056):
--   * Positive Verwendung (auth_role() = 'admin', is_staff(), is_hr(), auth_role() IN (...)): gesperrte/inaktive/
--     ausgeschiedene Benutzer verlieren genau diese Rechte. Aktive Benutzer: keine Aenderung.
--   * NEGIERTE Verwendung (NOT is_kiosk_role(), NOT is_staff(), auth_role() <> 'x', auth_role() = 'anon'):
--     fuer nicht aktive Benutzer wird die Bedingung WAHR. Im Repo nur als RESTRICTIVE-Policy
--     (NOT public.is_kiosk_role(), 14x) - restriktive Policies verengen nur, das oeffnet nichts. Abschnitt 3 bricht
--     AB, wenn eine FREIZUEGIGE Policy einen Helfer negiert - die muss vorher jemand ansehen.
--   * Policies, die nur auth.role() = 'authenticated' pruefen, merken davon NICHTS -> AUTH_HAERTUNG_4.
--   * GoTrue stellt gesperrten Benutzern weiter Tokens aus (es kennt users.locked nicht). Mit diesem Skript sind die
--     Tokens fuer alle helfergestuetzten Policies wertlos; ganz zu ist es erst mit AUTH_HAERTUNG_4. Offen
--     (eigener Auftrag): beim Sperren/Loeschen zusaetzlich auth.users.banned_until setzen (siehe AUTH_HAERTUNG_3).
--   * Leistung: jede Huelle fragt users einmal mehr ab (10 Zeilen, Index auf auth_user_id empfohlen, Abschnitt 1b).
--
-- VORAUSSETZUNG: mindestens EIN aktiver, verknuepfter Admin (sonst sperrt sich das Buero aus) - wird geprueft.
-- ROLLBACK: sql/AUTH_HAERTUNG_2_gesperrt_v1056_ROLLBACK.sql (erst AUTH_HAERTUNG_4 zuruecknehmen, falls angewendet).
-- =====================================================================================

BEGIN;

-- 0. VORPRUEFUNG
DO $$
DECLARE v_t text; v_n int; v_liste text;
BEGIN
  IF to_regclass('public.users') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: public.users fehlt'; END IF;
  FOREACH v_t IN ARRAY ARRAY['auth_user_id','active','locked','deactivate_at','role'] LOOP
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_schema='public' AND table_name='users' AND column_name=v_t) THEN
      RAISE EXCEPTION 'Vorpruefung: users.% fehlt', v_t; END IF;
  END LOOP;
  SELECT data_type INTO v_t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='users' AND column_name='deactivate_at';
  IF v_t NOT IN ('date','timestamp with time zone','timestamp without time zone') THEN
    RAISE EXCEPTION 'Vorpruefung: users.deactivate_at ist %, erwartet date/timestamp', v_t; END IF;
  -- Pflicht-Helfer
  IF to_regprocedure('public.auth_role()') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: auth_role() fehlt'; END IF;
  IF to_regprocedure('public.is_staff()') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: is_staff() fehlt'; END IF;
  -- Eigentuemer = Ausfuehrender (die Huelle muss ihre Basis aufrufen duerfen)
  SELECT string_agg(proname||'='||pg_get_userbyid(proowner), ', ') INTO v_liste FROM pg_proc
   WHERE pronamespace='public'::regnamespace
     AND proname IN ('auth_role','is_staff','is_hr','is_logged_in','current_user_role') AND pronargs = 0
     AND pg_get_userbyid(proowner) <> current_user;
  IF v_liste IS NOT NULL THEN
    RAISE EXCEPTION 'Vorpruefung: Eigentuemer % weicht von % ab - als Eigentuemer ausfuehren', v_liste, current_user; END IF;
  -- Aussperr-Schutz: es muss ein aktiver, verknuepfter Admin bleiben
  SELECT count(*) INTO v_n FROM public.users u
   WHERE u.role = 'admin' AND u.auth_user_id IS NOT NULL
     AND coalesce(u.active::text,'') IN ('1','t','true')
     AND NOT coalesce(u.locked::text IN ('1','t','true'), false)
     AND (u.deactivate_at IS NULL OR u.deactivate_at > current_date);
  IF v_n = 0 THEN RAISE EXCEPTION 'Vorpruefung: kein aktiver, verknuepfter Admin - das Skript wuerde das Buero aussperren'; END IF;
  RAISE NOTICE 'Vorpruefung ok: % aktive, verknuepfte Admins', v_n;
END $$;

CREATE TABLE IF NOT EXISTS public._auth_haertung_v1056_sicherung (
  objekt       text PRIMARY KEY,
  art          text NOT NULL,
  definition   text,
  extra        jsonb,
  gesichert_am timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public._auth_haertung_v1056_sicherung ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public._auth_haertung_v1056_sicherung FROM PUBLIC, anon, authenticated;

-- 0b. Stand VORHER: wer waere ab jetzt "nicht aktiv"? (nur Zahlen)
DO $$
DECLARE v_alle int; v_inaktiv int; v_gesp int; v_aus int; v_ohne int;
BEGIN
  SELECT count(*),
         count(*) FILTER (WHERE coalesce(active::text,'') NOT IN ('1','t','true')),
         count(*) FILTER (WHERE coalesce(locked::text,'') IN ('1','t','true')),
         count(*) FILTER (WHERE deactivate_at IS NOT NULL AND deactivate_at <= current_date),
         count(*) FILTER (WHERE auth_user_id IS NULL)
    INTO v_alle, v_inaktiv, v_gesp, v_aus, v_ohne FROM public.users;
  RAISE NOTICE 'VORHER users: % gesamt, % inaktiv, % gesperrt, % ausgeschieden (deactivate_at erreicht), % ohne Login-Verknuepfung',
    v_alle, v_inaktiv, v_gesp, v_aus, v_ohne;
  SELECT count(*) INTO v_ohne FROM auth.users au WHERE NOT EXISTS (SELECT 1 FROM public.users pu WHERE pu.auth_user_id = au.id);
  RAISE NOTICE 'VORHER auth.users ohne users-Zeile (Waisen): % (siehe AUTH_HAERTUNG_3)', v_ohne;
END $$;

-- 1. Der Helfer fuer Policies
CREATE OR REPLACE FUNCTION public.ist_aktiver_benutzer()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  -- AUTH_HAERTUNG_v1056: angemeldet UND aktive App-Benutzerzeile (nicht gesperrt, nicht ausgeschieden)
  SELECT EXISTS (
    SELECT 1 FROM public.users u
     WHERE u.auth_user_id = auth.uid()
       AND coalesce(u.active::text,'') IN ('1','t','true')
       AND NOT coalesce(u.locked::text IN ('1','t','true'), false)
       AND (u.deactivate_at IS NULL OR u.deactivate_at > current_date)
  );
$$;
REVOKE ALL ON FUNCTION public.ist_aktiver_benutzer() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.ist_aktiver_benutzer() TO anon, authenticated, service_role;

-- 1b. Index fuer die Abfrage (klein, idempotent)
CREATE INDEX IF NOT EXISTS users_auth_user_id_idx_v1056 ON public.users (auth_user_id);

-- 2. Helfer in die Huelle legen
DO $$
DECLARE
  v_name text; v_basis text; v_oid oid; v_src text; v_def text; v_res text; v_sonst text; v_ausdruck text;
BEGIN
  FOREACH v_name IN ARRAY ARRAY['auth_role','current_user_role','is_staff','is_hr','is_logged_in'] LOOP
    v_oid := to_regprocedure('public.'||v_name||'()');
    IF v_oid IS NULL THEN RAISE NOTICE '%() gibt es nicht - uebersprungen', v_name; CONTINUE; END IF;
    SELECT prosrc, pg_get_function_result(oid) INTO v_src, v_res FROM pg_proc WHERE oid = v_oid;
    IF position('AUTH_HAERTUNG_v1056_HUELLE' in v_src) > 0 THEN
      RAISE NOTICE '%() ist schon die Huelle v1056 - uebersprungen', v_name; CONTINUE; END IF;
    IF v_res NOT IN ('boolean','text') THEN
      RAISE EXCEPTION '%() liefert % (erwartet boolean/text) - melden', v_name, v_res; END IF;
    v_basis := '_' || v_name || '_basis_v1056';
    v_def := pg_get_functiondef(v_oid);
    INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, definition)
    VALUES ('funktion:public.'||v_name||'()', 'funktion', v_def) ON CONFLICT (objekt) DO NOTHING;
    IF position(('FUNCTION public.'||v_name||'()') in v_def) = 0 THEN
      RAISE EXCEPTION 'Kopf von %() unerwartet - melden', v_name; END IF;
    EXECUTE replace(v_def, 'FUNCTION public.'||v_name||'()', 'FUNCTION public.'||v_basis||'()');
    EXECUTE format('REVOKE ALL ON FUNCTION public.%I() FROM PUBLIC, anon, authenticated', v_basis);
    IF v_res = 'boolean' THEN
      v_ausdruck := format('public.ist_aktiver_benutzer() AND public.%I()', v_basis);  -- aktiv: genau das Original (auch NULL)
    ELSE
      v_sonst := CASE WHEN v_name = 'auth_role' THEN '''anon''' ELSE 'NULL::text' END;
      v_ausdruck := format('CASE WHEN public.ist_aktiver_benutzer() THEN public.%I() ELSE %s END', v_basis, v_sonst);
    END IF;
    EXECUTE format($f$CREATE OR REPLACE FUNCTION public.%1$I()
RETURNS %2$s
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $huelle$
  -- AUTH_HAERTUNG_v1056_HUELLE: Original unveraendert in public.%3$I; nicht aktive Benutzer bekommen nichts
  SELECT %4$s;
$huelle$;$f$, v_name, v_res, v_basis, v_ausdruck);
    RAISE NOTICE '%() in Huelle gelegt', v_name;
  END LOOP;
END $$;

-- 3. Wirkungsliste: alle Policies mit diesen Helfern; FREIZUEGIGE mit negiertem Helfer -> Abbruch
DO $$
DECLARE r record; v_neg int := 0; v_alle int := 0;
  v_muster constant text := '(auth_role|current_user_role|is_staff|is_hr|is_logged_in|is_kiosk_role)\(\)';
  v_negiert constant text := '(not\s*\(?\s*(public\.)?(is_staff|is_hr|is_logged_in|is_kiosk_role)\(\))|(auth_role\(\)\s*(<>|!=))|(auth_role\(\)\s*=\s*''anon'')|(current_user_role\(\)\s*(<>|!=))|(auth_role\(\)\)?\s*<>\s*all)';
BEGIN
  FOR r IN SELECT schemaname, tablename, policyname, permissive, cmd,
                  coalesce(qual,'') || ' ' || coalesce(with_check,'') AS ausdruck
             FROM pg_policies
            WHERE (coalesce(qual,'') || ' ' || coalesce(with_check,'')) ~* v_muster
            ORDER BY tablename, policyname LOOP
    v_alle := v_alle + 1;
    IF r.ausdruck ~* v_negiert THEN
      IF r.permissive = 'PERMISSIVE' THEN
        v_neg := v_neg + 1;
        RAISE WARNING 'NEGIERT + FREIZUEGIG: %.% % (%) - fuer gesperrte Benutzer jetzt WAHR', r.tablename, r.policyname, r.cmd, r.ausdruck;
      ELSE
        RAISE NOTICE 'negiert, restriktiv (verengt nur, unkritisch): %.% %', r.tablename, r.policyname, r.cmd;
      END IF;
    ELSE
      RAISE NOTICE 'positiv (gesperrte verlieren das Recht): %.% % %', r.tablename, r.policyname, r.permissive, r.cmd;
    END IF;
  END LOOP;
  RAISE NOTICE 'Policies mit Helfern: %', v_alle;
  IF v_neg > 0 THEN
    RAISE EXCEPTION '% freizuegige Policies negieren einen Helfer (WARNING oben) - erst ansehen, dann bewusst freigeben', v_neg;
  END IF;
END $$;

-- 4. NACHHER
DO $$
DECLARE v_n int;
BEGIN
  IF to_regprocedure('public.ist_aktiver_benutzer()') IS NULL THEN RAISE EXCEPTION 'Nachpruefung: ist_aktiver_benutzer fehlt'; END IF;
  SELECT count(*) INTO v_n FROM pg_proc WHERE pronamespace='public'::regnamespace AND pronargs = 0
     AND proname IN ('auth_role','current_user_role','is_staff','is_hr','is_logged_in')
     AND position('AUTH_HAERTUNG_v1056_HUELLE' in prosrc) > 0;
  IF v_n < 2 THEN RAISE EXCEPTION 'Nachpruefung: nur % Helfer in der Huelle (mindestens auth_role + is_staff)', v_n; END IF;
  RAISE NOTICE 'NACHHER: % Helfer in der Huelle, ist_aktiver_benutzer() da', v_n;
END $$;

COMMIT;

-- =====================================================================================
-- PROBE (eigener Lauf, BEGIN ... ROLLBACK; aendert nichts dauerhaft). Nur Ja/Nein und Rollen, keine Werte.
-- Erwartung: aktive Benutzer: Helfer wie vorher; derselbe Benutzer gesperrt / inaktiv / ausgeschieden: auth_role='anon',
-- is_staff=false, ist_aktiver_benutzer=false; Token ohne users-Zeile: ebenso; anon: false/'anon'.
-- =====================================================================================
-- BEGIN;
-- DO $probe$
-- DECLARE v_uid uuid; v_id text; v_rolle text; v_r text; v_b boolean; v_fall text;
-- BEGIN
--   SELECT auth_user_id, id::text, role INTO v_uid, v_id, v_rolle FROM public.users
--    WHERE role IN ('buero','projektleiter','admin') AND auth_user_id IS NOT NULL
--      AND coalesce(active::text,'') IN ('1','t','true') LIMIT 1;
--   IF v_uid IS NULL THEN RAISE EXCEPTION 'Probe: kein aktiver Staff-Benutzer'; END IF;
--   PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
--   EXECUTE 'SET LOCAL ROLE authenticated';
--   IF public.auth_role() IS DISTINCT FROM v_rolle OR NOT public.is_staff() OR NOT public.ist_aktiver_benutzer() THEN
--     RAISE EXCEPTION 'PROBE FEHLER aktiver % verliert Rechte', v_rolle; END IF;
--   EXECUTE 'RESET ROLE';
--   FOREACH v_fall IN ARRAY ARRAY['inaktiv','ausgeschieden'] LOOP   -- gesperrt: Zeile je nach Typ von locked ergaenzen
--     IF v_fall = 'inaktiv' THEN EXECUTE 'UPDATE public.users SET active = 0 WHERE id::text = $1' USING v_id; END IF;
--     IF v_fall = 'ausgeschieden' THEN EXECUTE 'UPDATE public.users SET active = 1, deactivate_at = current_date WHERE id::text = $1' USING v_id; END IF;
--     EXECUTE 'SET LOCAL ROLE authenticated';
--     v_r := public.auth_role(); v_b := public.is_staff();
--     IF v_r <> 'anon' OR v_b OR public.ist_aktiver_benutzer() THEN
--       RAISE EXCEPTION 'PROBE FEHLER % behaelt Rechte (auth_role=%, is_staff=%)', v_fall, v_r, v_b; END IF;
--     EXECUTE 'RESET ROLE';
--     RAISE NOTICE 'Probe %: Rechte weg - ok', v_fall;
--   END LOOP;
--   -- Token ohne users-Zeile (Waise / Selbstregistrierung)
--   PERFORM set_config('request.jwt.claims', json_build_object('sub', gen_random_uuid(), 'role', 'authenticated')::text, true);
--   EXECUTE 'SET LOCAL ROLE authenticated';
--   IF public.ist_aktiver_benutzer() OR public.is_staff() OR public.auth_role() <> 'anon' THEN
--     RAISE EXCEPTION 'PROBE FEHLER Waise hat Rechte'; END IF;
--   EXECUTE 'RESET ROLE';
--   RAISE NOTICE 'PROBE fertig - ok';
-- END $probe$;
-- ROLLBACK;
-- =====================================================================================
