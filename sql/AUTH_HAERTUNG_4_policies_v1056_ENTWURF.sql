-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_4_policies_v1056_ENTWURF.sql  —  "nur angemeldet" reicht nicht: aktive App-Benutzer verlangen
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Pruefung durch Chat-Claude, Einspielen nur durch Sebastian ueber das Tor.
-- Bericht: C:/repos/epk-auth-pruefung-2026-11-19.md Fund 1/3/14. VORAUSSETZUNG: AUTH_HAERTUNG_2 (ist_aktiver_benutzer)
--   ist angewendet; AUTH_HAERTUNG_3 (Waisen gesperrt) empfohlen vorher.
--
-- PROBLEM: Policies mit USING (auth.role() = 'authenticated') (oder auth.uid() IS NOT NULL, oder TO authenticated
--   USING (true)) lassen JEDES gueltige Token durch: Selbstregistrierte (solange Signup offen war), verwaiste
--   Logins, gesperrte/ausgeschiedene Mitarbeiter mit noch laufender Sitzung.
--
-- WAS ES AENDERT: fuer die unten aufgezaehlten Tabellen wird in JEDER freizuegigen Policy, deren Bedingung GENAU
--   eine dieser "nur angemeldet"-Formen ist, die Bedingung ersetzt durch (SELECT public.ist_aktiver_benutzer()).
--   ALTER POLICY - Name, Befehl, Rollen bleiben; nur USING/WITH CHECK wechseln. Zusammengesetzte Bedingungen
--   (z. B. authenticated AND owner = ...) werden NICHT angefasst, nur gelistet (Abschnitt 3) - die sind Handarbeit.
--   Alte Bedingung je Policy in public._auth_haertung_v1056_sicherung (objekt 'policy4:...').
--   Fuer aktive Benutzer aendert sich nichts. Wer nicht (mehr) aktiv ist, sieht und schreibt in diesen Tabellen nichts.
--
-- TABELLEN UND WIRKUNG (nicht vorhandene werden uebersprungen):
--   users               Benutzerliste (E-Mail, Telefon, Rechte). Gesperrte sehen auch ihr eigenes Profil nicht mehr ->
--                       die App >= v1056 meldet dann "Zugang nicht mehr aktiv" und meldet ab (gewollt).
--   workers             Mitarbeiter-PII (SVNR, Reisepass, Adresse). Zusaetzlich Abschnitt K (Kiosk).
--   projects, worker_projects, weekplans, weekplan_rows, dispo_blocks   Planung/Projekte (lesen UND schreiben).
--   fahrzeuge, fahrzeug_buchungen, fz_termine, fz_finanzen, fz_fs_kontrollen, fz_positions, fahrbewilligungen
--                       Flotte inkl. Finanzen/Fuehrerschein - fz_finanzen ist heute is_hr-gestuetzt (folgt via _2).
--   werkzeuge, wz_service, as_vorlagen   Werkzeuge/Vorlagen.
--   time_entries, absences, absence_files, urlaubskontingent, bescheinigungen, anmeldungen, stempel_log
--                       Zeit/Abwesenheit (lohnrelevant). stempel_log: Stempel-Terminal ist ein aktiver users-Eintrag ->
--                       unveraendert; bitte in der Probe mit dem Terminal-Konto pruefen.
--   photos, project_documents, project_folders, plans, defects, tickets, forms, checklists, bautagebuch,
--   bauprovisorien, bauprovisorien_mieten, gefahrstoff_files, gefahrstoff_folders
--                       Baustellendaten. Das Kundenportal laeuft ueber portal_fetch (SECURITY DEFINER) bzw. anon-Policies
--                       -> nicht betroffen (nur authenticated-Formen werden ersetzt; TO public USING (true) bleibt).
--   material_items, material_orders, material_catalogs, supplier_orders, supplier_articles
--   notifications, activity_log, system_config, plz_geo, plz_distanz
--                       notifications/activity_log: INSERT nur noch fuer aktive Benutzer (die App schreibt beim Login
--                       NACH dem Profil-Lesen - passt).
--   NICHT HIER: supplier_configs/supplier_credentials (eigener Entwurf LIEFERANTEN_ZUGANG_v1052).
--   NUR MIT FREIGABE (Abschnitt F, auskommentiert): arbeitsscheine, kunden, finkzeit und alles mit offa/juprowa/feed
--                       im Namen - dort koennen externe Anbindungen mit eigenem Login haengen (OFFA ist tabu).
--
-- SCHUTZ VOR AUSSPERREN von Diensten: Abbruch, wenn sich in den letzten 30 Tagen ein Login OHNE aktive users-Zeile
--   angemeldet oder seine Sitzung erneuert hat (das waere ein Dienst/Kiosk, der hier sonst verstummt).
--
-- ROLLBACK: sql/AUTH_HAERTUNG_4_policies_v1056_ROLLBACK.sql
-- =====================================================================================

BEGIN;

-- 0. VORPRUEFUNG
DO $$
DECLARE v_n int; v_liste text;
BEGIN
  IF to_regprocedure('public.ist_aktiver_benutzer()') IS NULL THEN
    RAISE EXCEPTION 'Vorpruefung: public.ist_aktiver_benutzer() fehlt - erst AUTH_HAERTUNG_2 anwenden'; END IF;
  IF to_regclass('public._auth_haertung_v1056_sicherung') IS NULL THEN
    RAISE EXCEPTION 'Vorpruefung: Sicherungstabelle fehlt - erst AUTH_HAERTUNG_2 anwenden'; END IF;
  -- aktive Logins ohne aktive App-Benutzerzeile (letzte 30 Tage) -> waeren Dienste, die gleich verstummen
  SELECT count(*), string_agg(au.id::text || ' (' || split_part(au.email,'@',2) || ')', ', ')
    INTO v_n, v_liste
    FROM auth.users au
   WHERE (au.banned_until IS NULL OR au.banned_until < now())
     AND (au.last_sign_in_at > now() - interval '30 days'
          OR EXISTS (SELECT 1 FROM auth.sessions s WHERE s.user_id = au.id AND s.updated_at > now() - interval '30 days'))
     AND NOT EXISTS (
       SELECT 1 FROM public.users u
        WHERE u.auth_user_id = au.id
          AND coalesce(u.active::text,'') IN ('1','t','true')
          AND NOT coalesce(u.locked::text IN ('1','t','true'), false)
          AND (u.deactivate_at IS NULL OR u.deactivate_at > current_date));
  IF v_n > 0 THEN
    RAISE EXCEPTION 'Vorpruefung: % Logins ohne aktive users-Zeile waren in den letzten 30 Tagen aktiv: % - Dienstkonto? Erst klaeren (AUTH_HAERTUNG_3 / users-Zeile)', v_n, v_liste; END IF;
END $$;

-- 0b. VORHER (nur Zahlen)
DO $$
DECLARE v_n int; v_k int;
BEGIN
  SELECT count(*) INTO v_n FROM pg_policies
   WHERE schemaname='public' AND permissive='PERMISSIVE'
     AND (coalesce(qual,'') || ' ' || coalesce(with_check,'')) ~* '(auth\.role\(\)|auth\.uid\(\)\s+is\s+not\s+null)';
  SELECT count(*) INTO v_k FROM pg_policies
   WHERE schemaname='public' AND (coalesce(qual,'') || ' ' || coalesce(with_check,'')) ILIKE '%ist_aktiver_benutzer%';
  RAISE NOTICE 'VORHER: % freizuegige Policies pruefen auth.role()/auth.uid(), % verlangen schon ist_aktiver_benutzer()', v_n, v_k;
END $$;

-- 1+2. Ersetzen (je Tabelle alle freizuegigen Policies mit GENAU einer "nur angemeldet"-Form)
DO $$
DECLARE
  v_tabellen constant text[] := ARRAY[
    'users','workers','projects','worker_projects','weekplans','weekplan_rows','dispo_blocks',
    'fahrzeuge','fahrzeug_buchungen','fz_termine','fz_finanzen','fz_fs_kontrollen','fz_positions','fahrbewilligungen',
    'werkzeuge','wz_service','as_vorlagen',
    'time_entries','absences','absence_files','urlaubskontingent','bescheinigungen','anmeldungen','stempel_log',
    'photos','project_documents','project_folders','plans','defects','tickets','forms','checklists','bautagebuch',
    'bauprovisorien','bauprovisorien_mieten','gefahrstoff_files','gefahrstoff_folders',
    'material_items','material_orders','material_catalogs','supplier_orders','supplier_articles',
    'notifications','activity_log','system_config','plz_geo','plz_distanz'];
  v_nur_angemeldet constant text[] := ARRAY[
    '(auth.role()=''authenticated''::text)', 'auth.role()=''authenticated''::text',
    '((selectauth.role()asrole)=''authenticated''::text)', '(auth.uid()isnotnull)', 'auth.uid()isnotnull',
    '((selectauth.uid()asuid)isnotnull)'];
  v_neu constant text := '(SELECT public.ist_aktiver_benutzer())';
  v_t text; r record; v_q text; v_c text; v_nur_auth boolean; v_q_treffer boolean; v_c_treffer boolean;
  v_geaendert int := 0; v_tab_fehlt int := 0; v_sql text;
BEGIN
  FOREACH v_t IN ARRAY v_tabellen LOOP
    IF to_regclass('public.'||v_t) IS NULL THEN v_tab_fehlt := v_tab_fehlt + 1; RAISE NOTICE 'Tabelle % fehlt - uebersprungen', v_t; CONTINUE; END IF;
    FOR r IN SELECT * FROM pg_policies WHERE schemaname='public' AND tablename=v_t AND permissive='PERMISSIVE' LOOP
      v_q := regexp_replace(lower(coalesce(r.qual,'')), '\s+', '', 'g');
      v_c := regexp_replace(lower(coalesce(r.with_check,'')), '\s+', '', 'g');
      v_nur_auth := r.roles = ARRAY['authenticated']::name[];
      -- "true" zaehlt nur, wenn die Policy ausschliesslich fuer authenticated gilt (TO public USING (true) = gewollt oeffentlich)
      v_q_treffer := r.qual IS NOT NULL AND (v_q = ANY (v_nur_angemeldet) OR (v_nur_auth AND v_q = 'true'));
      v_c_treffer := r.with_check IS NOT NULL AND (v_c = ANY (v_nur_angemeldet) OR (v_nur_auth AND v_c = 'true'));
      IF NOT (v_q_treffer OR v_c_treffer) THEN CONTINUE; END IF;
      INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, extra)
      VALUES ('policy4:public.'||v_t||'.'||r.policyname, 'policy',
              jsonb_build_object('tabelle', v_t, 'policy', r.policyname, 'cmd', r.cmd, 'qual', r.qual, 'with_check', r.with_check))
      ON CONFLICT (objekt) DO NOTHING;
      v_sql := format('ALTER POLICY %I ON public.%I', r.policyname, v_t);
      IF v_q_treffer AND r.cmd <> 'INSERT' THEN v_sql := v_sql || ' USING ' || v_neu; END IF;
      IF v_c_treffer AND r.cmd <> 'SELECT' AND r.cmd <> 'DELETE' THEN v_sql := v_sql || ' WITH CHECK ' || v_neu; END IF;
      IF v_sql = format('ALTER POLICY %I ON public.%I', r.policyname, v_t) THEN
        RAISE NOTICE 'nichts zu ersetzen: %.% (%)', v_t, r.policyname, r.cmd; CONTINUE; END IF;
      EXECUTE v_sql;
      v_geaendert := v_geaendert + 1;
      RAISE NOTICE 'ersetzt: %.% (%)', v_t, r.policyname, r.cmd;
    END LOOP;
  END LOOP;
  RAISE NOTICE 'Policies ersetzt: %, Tabellen nicht vorhanden: %', v_geaendert, v_tab_fehlt;
END $$;

-- 3. Liste fuer die Handarbeit: freizuegige Policies, die "authenticated" erwaehnen, aber NICHT ersetzt wurden
--    (zusammengesetzt, oder Tabelle nicht in der Liste). Bricht nicht ab.
DO $$
DECLARE r record; v_n int := 0;
BEGIN
  FOR r IN SELECT tablename, policyname, cmd, qual, with_check FROM pg_policies
            WHERE schemaname='public' AND permissive='PERMISSIVE'
              AND (coalesce(qual,'') || ' ' || coalesce(with_check,'')) ~* '(auth\.role\(\)|auth\.uid\(\)\s+is\s+not\s+null)'
              AND (coalesce(qual,'') || ' ' || coalesce(with_check,'')) !~* 'ist_aktiver_benutzer'
            ORDER BY tablename, policyname LOOP
    v_n := v_n + 1;
    RAISE NOTICE 'HANDARBEIT %.% (%): qual=% check=%', r.tablename, r.policyname, r.cmd, r.qual, r.with_check;
  END LOOP;
  RAISE NOTICE 'Handarbeit-Liste: % Policies', v_n;
END $$;

-- K. KIOSK (Fund 14): Wandtafel/Stempel-Terminal lesen workers nicht direkt (App >= v3.9.569 nimmt dafuer die RPCs
--    kiosk_field_workers / stempel_terminal_workers, beide SECURITY DEFINER). Restriktive Policy wie forms_no_kiosk.
--    Rolle aus public.users (is_kiosk_role), NICHT aus app_metadata wie im alten KIOSK_PII_LOCKDOWN_stage.sql.
--    Vor dem Apply: Lager-Tafel (?screen=monteure, ?screen=planung) und Stempel-Terminal einmal oeffnen und pruefen.
DO $$
BEGIN
  IF to_regclass('public.workers') IS NULL OR to_regprocedure('public.is_kiosk_role()') IS NULL THEN
    RAISE NOTICE 'Kiosk: workers oder is_kiosk_role() fehlt - uebersprungen'; RETURN; END IF;
  -- die Ersatz-RPCs muessen SECURITY DEFINER sein, sonst sperrt die restriktive Policy auch sie
  IF EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace='public'::regnamespace
              AND proname IN ('kiosk_field_workers','stempel_terminal_workers') AND NOT prosecdef)
     OR (SELECT count(DISTINCT proname) FROM pg_proc WHERE pronamespace='public'::regnamespace
              AND proname IN ('kiosk_field_workers','stempel_terminal_workers')) < 2 THEN
    RAISE NOTICE 'Kiosk: kiosk_field_workers/stempel_terminal_workers fehlen oder sind nicht SECURITY DEFINER - uebersprungen, melden';
    RETURN;
  END IF;
  DROP POLICY IF EXISTS workers_kein_kiosk_v1056 ON public.workers;
  CREATE POLICY workers_kein_kiosk_v1056 ON public.workers AS RESTRICTIVE FOR SELECT TO authenticated
    USING (NOT public.is_kiosk_role());
  RAISE NOTICE 'Kiosk: workers fuer lager_display/stempel_terminal gesperrt (restriktiv)';
END $$;

-- 4. NACHHER
DO $$
DECLARE v_n int;
BEGIN
  SELECT count(*) INTO v_n FROM pg_policies
   WHERE schemaname='public' AND (coalesce(qual,'') || ' ' || coalesce(with_check,'')) ILIKE '%ist_aktiver_benutzer%';
  RAISE NOTICE 'NACHHER: % Policies verlangen einen aktiven App-Benutzer', v_n;
  IF to_regclass('public.users') IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='users' AND cmd IN ('SELECT','ALL')
          AND (coalesce(qual,'')) ILIKE '%ist_aktiver_benutzer%') THEN
    RAISE NOTICE 'HINWEIS: users_select wurde nicht ersetzt (Form weicht ab) - siehe Handarbeit-Liste';
  END IF;
END $$;

COMMIT;

-- -------------------------------------------------------------------------------------
-- F. NUR MIT FREIGABE (auskommentiert): Tabellen mit moeglicher externer Anbindung (OFFA/Juprowa/Feed).
--    Erst klaeren, mit welchem Login die Anbindung schreibt/liest (service_role = unberuehrt; eigener Login ohne
--    users-Zeile = wuerde verstummen). Dann denselben Block wie oben mit dieser Liste laufen lassen:
--      v_tabellen := ARRAY['arbeitsscheine','kunden','finkzeit'] || (SELECT array_agg(tablename::text) FROM pg_tables
--                      WHERE schemaname='public' AND tablename ~* '(offa|juprowa|feed)');
-- -------------------------------------------------------------------------------------

-- =====================================================================================
-- PROBE (eigener Lauf, BEGIN ... ROLLBACK). Nur Zahlen.
-- Erwartung: aktiver Monteur liest projects/workers wie vorher (Zahl > 0); Token ohne users-Zeile liest 0 Zeilen und
-- kann nicht schreiben; derselbe Monteur inaktiv liest 0; Kiosk-Konto liest workers 0 Zeilen, die RPC liefert weiter.
-- =====================================================================================
-- BEGIN;
-- DO $probe$
-- DECLARE v_uid uuid; v_id text; v_n int; v_m int; v_t text;
-- BEGIN
--   SELECT auth_user_id, id::text INTO v_uid, v_id FROM public.users
--    WHERE role = 'monteur' AND auth_user_id IS NOT NULL AND coalesce(active::text,'') IN ('1','t','true') LIMIT 1;
--   PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
--   EXECUTE 'SET LOCAL ROLE authenticated';
--   SELECT count(*) INTO v_n FROM public.projects;
--   IF v_n = 0 THEN RAISE EXCEPTION 'PROBE FEHLER aktiver Monteur sieht keine Projekte'; END IF;
--   EXECUTE 'RESET ROLE';
--   -- Waise / Selbstregistrierung
--   PERFORM set_config('request.jwt.claims', json_build_object('sub', gen_random_uuid(), 'role', 'authenticated')::text, true);
--   EXECUTE 'SET LOCAL ROLE authenticated';
--   FOREACH v_t IN ARRAY ARRAY['users','workers','projects','worker_projects','weekplan_rows'] LOOP
--     IF to_regclass('public.'||v_t) IS NULL THEN CONTINUE; END IF;
--     EXECUTE format('SELECT count(*) FROM public.%I', v_t) INTO v_m;
--     IF v_m <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER Waise liest % Zeilen aus %', v_m, v_t; END IF;
--   END LOOP;
--   BEGIN
--     EXECUTE 'INSERT INTO public.worker_projects (id, worker_id, project_id) VALUES ($1, $1, $1)' USING 'probe_v1056';
--     RAISE EXCEPTION 'PROBE FEHLER Waise darf worker_projects schreiben';
--   EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe Waise: Schreiben abgewiesen - ok';
--   END;
--   EXECUTE 'RESET ROLE';
--   -- derselbe Monteur inaktiv
--   EXECUTE 'UPDATE public.users SET active = 0 WHERE id::text = $1' USING v_id;
--   PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
--   EXECUTE 'SET LOCAL ROLE authenticated';
--   SELECT count(*) INTO v_n FROM public.projects;
--   IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER inaktiver Monteur sieht % Projekte', v_n; END IF;
--   EXECUTE 'RESET ROLE';
--   -- Kiosk
--   SELECT auth_user_id INTO v_uid FROM public.users WHERE role = 'lager_display' AND auth_user_id IS NOT NULL LIMIT 1;
--   IF v_uid IS NOT NULL THEN
--     PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
--     EXECUTE 'SET LOCAL ROLE authenticated';
--     SELECT count(*) INTO v_n FROM public.workers;
--     IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER Kiosk liest % workers-Zeilen', v_n; END IF;
--     EXECUTE 'RESET ROLE';
--     RAISE NOTICE 'Probe Kiosk: workers direkt gesperrt - ok (RPC kiosk_field_workers separat in der App pruefen)';
--   END IF;
--   RAISE NOTICE 'PROBE fertig - ok';
-- END $probe$;
-- ROLLBACK;
-- =====================================================================================
