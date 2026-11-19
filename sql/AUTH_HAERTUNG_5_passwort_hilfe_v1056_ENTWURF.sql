-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_5_passwort_hilfe_v1056_ENTWURF.sql  —  "Passwort vergessen" kommt wirklich beim Admin an
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Pruefung durch Chat-Claude, Einspielen nur durch Sebastian ueber das Tor.
-- Bericht: C:/repos/epk-auth-pruefung-2026-11-19.md Fund 4 (falsches Gruen: anonym kein Lesen von users, kein
--   INSERT auf notifications -> nichts kam an, die Maske zeigte trotzdem "gesendet").
--
-- WAS ES ANLEGT
--   * public.passwort_hilfe_anfragen(p_username text) RETURNS jsonb - SECURITY DEFINER, EXECUTE fuer anon/authenticated.
--     Antwortet IMMER {"ok": true} (auch fuer unbekannte Namen und bei Drosselung) - die Antwort verraet nicht, ob es
--     den Benutzernamen gibt. Fuer einen vorhandenen Benutzernamen legt sie fuer jeden aktiven Admin eine
--     Benachrichtigung an (notifications, Typ system) - mit Status des Kontos (aktiv/gesperrt/inaktiv) fuer den Admin.
--     Drosselung (Sicherheitspruefung 20.11., ersetzt die Fassung zu Review-Fund 8): EINE globale Grenze fuer JEDEN
--     Aufruf vor dem Nachschlagen (30 Aufrufe in 10 Minuten, Treffer oder nicht); danach laufen Treffer und
--     Nicht-Treffer denselben Weg (Sperre auf die normalisierte Eingabe, Zaehlung je Name und global, genau eine
--     Protokollzeile) - nur das Anlegen der Benachrichtigungen unterscheidet sich. Gemeldet wird hoechstens
--     1x je Benutzername pro Stunde und hoechstens 10x pro Stunde insgesamt (harte Grenze, Admins werden nicht
--     zugeschuettet). Abwaegung: eine Flut mit erfundenen Namen kann echte Anfragen fuer bis zu 10 Minuten
--     verschlucken (Antwort trotzdem ok:true) - dann direkt an das Buero wenden. Antwort bleibt in jedem Fall gleich.
--     created_at (Fund 9): ist die Spalte Text, wird ISO-8601 in UTC geschrieben ('YYYY-MM-DD"T"HH24:MI:SS.MS"Z"').
--   * public.passwort_hilfe_log - Protokoll (Benutzername klein, Zeitpunkt, Treffer ja/nein), RLS an, KEINE Rechte fuer
--     anon/authenticated; Eintraege > 30 Tage werden bei jedem Aufruf entfernt.
--   Die App (>= v3.9.1056) ruft die RPC mit dem anon-Schluessel; 404 (noch nicht eingespielt) -> ehrlicher Text
--   "Bitte wende dich direkt an das Buero oder den Admin". Erfolg zeigt sie nur bei ok:true.
--   Restrisiko Zeitmessung: in plpgsql laesst sich die Laufzeit NICHT vollkommen gleich machen - ein Treffer legt
--   zusaetzlich die Benachrichtigungen an (nur wenn gemeldet wird), Index-/Cache-Zustaende schwanken. Der Unterschied
--   ist klein gegenueber dem Netzrauschen, und anon erfaehrt hoechstens "Name existiert" mit Rauschen, gedrosselt auf
--   30 Versuche in 10 Minuten. Bei 10 Konten mit erratbaren Nachnamen ist das gering; login_lookup war der viel
--   groessere Hebel (in AUTH_HAERTUNG_1 geschlossen).
--
-- ROLLBACK: sql/AUTH_HAERTUNG_5_passwort_hilfe_v1056_ROLLBACK.sql
-- =====================================================================================

BEGIN;

-- 0. VORPRUEFUNG: notifications so, wie die App sie schreibt (id text, user_id = users.id, type/title/body/created_at)
DO $$
DECLARE v_t text; v_u text; v_liste text;
BEGIN
  IF to_regclass('public.notifications') IS NULL OR to_regclass('public.users') IS NULL THEN
    RAISE EXCEPTION 'Vorpruefung: notifications/users fehlt'; END IF;
  SELECT data_type INTO v_t FROM information_schema.columns WHERE table_schema='public' AND table_name='notifications' AND column_name='id';
  IF v_t IS NULL OR v_t NOT IN ('text','character varying') THEN
    RAISE EXCEPTION 'Vorpruefung: notifications.id ist %, erwartet text', v_t; END IF;
  SELECT data_type INTO v_t FROM information_schema.columns WHERE table_schema='public' AND table_name='notifications' AND column_name='user_id';
  SELECT data_type INTO v_u FROM information_schema.columns WHERE table_schema='public' AND table_name='users' AND column_name='id';
  IF v_t IS NULL OR v_t <> v_u THEN
    RAISE EXCEPTION 'Vorpruefung: notifications.user_id (%) passt nicht zu users.id (%)', v_t, v_u; END IF;
  -- jede Pflichtspalte ohne Vorgabe muss von uns befuellt werden
  SELECT string_agg(column_name, ', ') INTO v_liste FROM information_schema.columns
   WHERE table_schema='public' AND table_name='notifications' AND is_nullable='NO' AND column_default IS NULL
     AND column_name NOT IN ('id','user_id','type','title','body','created_at');
  IF v_liste IS NOT NULL THEN
    RAISE EXCEPTION 'Vorpruefung: notifications hat Pflichtspalten ohne Vorgabe: % - Entwurf anpassen', v_liste; END IF;
  FOREACH v_t IN ARRAY ARRAY['type','title','body','created_at'] LOOP
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='notifications' AND column_name=v_t) THEN
      RAISE EXCEPTION 'Vorpruefung: notifications.% fehlt', v_t; END IF;
  END LOOP;
  SELECT data_type INTO v_t FROM information_schema.columns WHERE table_schema='public' AND table_name='notifications' AND column_name='created_at';
  IF v_t NOT IN ('text','character varying','timestamp with time zone','timestamp without time zone') THEN
    RAISE EXCEPTION 'Vorpruefung: notifications.created_at ist % - Entwurf anpassen', v_t; END IF;
END $$;

-- 0b. VORHER
DO $$
BEGIN
  RAISE NOTICE 'VORHER: passwort_hilfe_anfragen vorhanden=%, Log vorhanden=%',
    to_regprocedure('public.passwort_hilfe_anfragen(text)') IS NOT NULL, to_regclass('public.passwort_hilfe_log') IS NOT NULL;
END $$;

-- 1. Protokoll
CREATE TABLE IF NOT EXISTS public.passwort_hilfe_log (
  id            bigserial PRIMARY KEY,
  username_norm text        NOT NULL,
  angefragt_am  timestamptz NOT NULL DEFAULT now(),
  treffer       boolean     NOT NULL DEFAULT false,
  gemeldet      boolean     NOT NULL DEFAULT false
);
-- Sicherheitspruefung 20.11.: falls die Tabelle aus einem frueheren Entwurfslauf schon da ist
ALTER TABLE public.passwort_hilfe_log ADD COLUMN IF NOT EXISTS gemeldet boolean NOT NULL DEFAULT false;
CREATE INDEX IF NOT EXISTS passwort_hilfe_log_zeit_idx ON public.passwort_hilfe_log (angefragt_am);
CREATE INDEX IF NOT EXISTS passwort_hilfe_log_name_idx ON public.passwort_hilfe_log (username_norm, angefragt_am);
ALTER TABLE public.passwort_hilfe_log ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.passwort_hilfe_log FROM PUBLIC, anon, authenticated;
REVOKE ALL ON SEQUENCE public.passwort_hilfe_log_id_seq FROM PUBLIC, anon, authenticated;

-- 2. Die RPC
CREATE OR REPLACE FUNCTION public.passwort_hilfe_anfragen(p_username text)
RETURNS jsonb
LANGUAGE plpgsql
VOLATILE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  v_norm text := lower(btrim(coalesce(p_username, '')));
  v_ok constant jsonb := jsonb_build_object('ok', true);
  v_n int; v_n_name int; v_n_global int; v_user record; v_treffer boolean; v_melden boolean; v_status text;
  v_jetzt timestamptz := now(); v_zeit_text boolean;
BEGIN
  -- AUTH_HAERTUNG_v1056: Antwort immer gleich - verraet nie, ob es den Namen gibt.
  -- Sicherheitspruefung 20.11.: Treffer und Nicht-Treffer laufen DENSELBEN Weg (Drosselung, Sperre, Zaehlungen,
  -- genau eine Protokollzeile); nur das Anlegen der Benachrichtigungen unterscheidet sich.
  IF v_norm = '' OR length(v_norm) > 80 THEN RETURN v_ok; END IF;
  DELETE FROM public.passwort_hilfe_log WHERE angefragt_am < v_jetzt - interval '30 days';
  -- (a) eine globale Drosselung fuer JEDEN Aufruf, VOR dem Nachschlagen: hoechstens 30 Aufrufe in 10 Minuten
  SELECT count(*) INTO v_n FROM public.passwort_hilfe_log WHERE angefragt_am > v_jetzt - interval '10 minutes';
  IF v_n >= 30 THEN RETURN v_ok; END IF;
  -- (b) Sperren IMMER (global fuer die harte Meldegrenze, dann je normalisierter Eingabe - Treffer oder nicht;
  --     feste Reihenfolge, daher keine Verklemmung)
  PERFORM pg_advisory_xact_lock(hashtext('passwort_hilfe:global'));
  PERFORM pg_advisory_xact_lock(hashtext('passwort_hilfe:' || v_norm));
  SELECT u.id, u.name, u.username, u.active, u.locked, u.deactivate_at INTO v_user
    FROM public.users u WHERE lower(u.username) = v_norm LIMIT 1;
  v_treffer := FOUND;
  -- (c) Zaehlungen IMMER: je Name hoechstens 1 Meldung pro Stunde, insgesamt hoechstens 10 Meldungen pro Stunde
  SELECT count(*) INTO v_n_name FROM public.passwort_hilfe_log
   WHERE username_norm = v_norm AND gemeldet AND angefragt_am > v_jetzt - interval '1 hour';
  SELECT count(*) INTO v_n_global FROM public.passwort_hilfe_log
   WHERE gemeldet AND angefragt_am > v_jetzt - interval '1 hour';
  v_melden := v_treffer AND v_n_name = 0 AND v_n_global < 10;
  -- (d) IMMER genau eine Protokollzeile
  INSERT INTO public.passwort_hilfe_log (username_norm, treffer, gemeldet) VALUES (v_norm, v_treffer, v_melden);
  v_status := CASE
    WHEN coalesce(v_user.locked::text,'') IN ('1','t','true') THEN 'gesperrt'
    WHEN coalesce(v_user.active::text,'') NOT IN ('1','t','true') THEN 'inaktiv'
    WHEN v_user.deactivate_at IS NOT NULL AND v_user.deactivate_at <= current_date THEN 'ausgeschieden'
    ELSE 'aktiv' END;
  -- Review 19.11. Fund 9: ist notifications.created_at Text, schreiben wir ISO-8601 in UTC wie die App
  -- (toISOString: 2026-11-19T08:15:00.000Z) - sonst stuende dort das Sitzungsformat '2026-11-19 08:15:00.123+00'.
  SELECT a.atttypid IN ('text'::regtype, 'character varying'::regtype) INTO v_zeit_text
    FROM pg_attribute a WHERE a.attrelid = 'public.notifications'::regclass AND a.attname = 'created_at' AND NOT a.attisdropped;
  -- (e) NUR hier unterscheiden sich Treffer und Nicht-Treffer
  IF NOT v_melden THEN
    NULL;
  ELSIF v_zeit_text THEN
    INSERT INTO public.notifications (id, user_id, type, title, body, created_at)
    SELECT 'pwh_' || to_char(v_jetzt AT TIME ZONE 'UTC', 'YYYYMMDDHH24MISSMS') || '_' || a.id::text,
           a.id, 'system', 'Passwort-Hilfe angefragt',
           'Benutzer ' || coalesce(nullif(v_user.name,''), v_user.username) || ' (' || v_user.username || ', Konto ' || v_status
             || ') bittet um ein neues Passwort. Bitte persoenlich bestaetigen, dann in der Benutzerverwaltung zuruecksetzen.',
           to_char(v_jetzt AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
      FROM public.users a
     WHERE a.role = 'admin'
       AND coalesce(a.active::text,'') IN ('1','t','true')
       AND NOT coalesce(a.locked::text IN ('1','t','true'), false)
    ON CONFLICT DO NOTHING;
  ELSE
    INSERT INTO public.notifications (id, user_id, type, title, body, created_at)
    SELECT 'pwh_' || to_char(v_jetzt AT TIME ZONE 'UTC', 'YYYYMMDDHH24MISSMS') || '_' || a.id::text,
           a.id, 'system', 'Passwort-Hilfe angefragt',
           'Benutzer ' || coalesce(nullif(v_user.name,''), v_user.username) || ' (' || v_user.username || ', Konto ' || v_status
             || ') bittet um ein neues Passwort. Bitte persoenlich bestaetigen, dann in der Benutzerverwaltung zuruecksetzen.',
           v_jetzt
      FROM public.users a
     WHERE a.role = 'admin'
       AND coalesce(a.active::text,'') IN ('1','t','true')
       AND NOT coalesce(a.locked::text IN ('1','t','true'), false)
    ON CONFLICT DO NOTHING;
  END IF;
  RETURN v_ok;
END $$;
REVOKE ALL ON FUNCTION public.passwort_hilfe_anfragen(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.passwort_hilfe_anfragen(text) TO anon, authenticated;

-- 3. NACHHER
DO $$
BEGIN
  IF to_regprocedure('public.passwort_hilfe_anfragen(text)') IS NULL THEN RAISE EXCEPTION 'Nachpruefung: RPC fehlt'; END IF;
  IF NOT has_function_privilege('anon', 'public.passwort_hilfe_anfragen(text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'Nachpruefung: anon darf die RPC nicht ausfuehren'; END IF;
  IF has_table_privilege('anon', 'public.passwort_hilfe_log', 'SELECT') OR has_table_privilege('authenticated', 'public.passwort_hilfe_log', 'SELECT') THEN
    RAISE EXCEPTION 'Nachpruefung: Log ist lesbar'; END IF;
  RAISE NOTICE 'NACHHER: RPC da, anon darf sie rufen, Log nicht lesbar';
END $$;

COMMIT;

-- =====================================================================================
-- PROBE (eigener Lauf, BEGIN ... ROLLBACK). Nur Zahlen.
-- Erwartung: unbekannter Name -> ok:true, 0 neue Benachrichtigungen; bekannter Name -> ok:true, je aktivem Admin 1;
-- zweiter Aufruf in derselben Stunde -> 0 weitere; anon kann das Log nicht lesen.
-- =====================================================================================
-- BEGIN;
-- DO $probe$
-- DECLARE v_vorher int; v_nach int; v_admins int; v_name text; v_j jsonb;
-- BEGIN
--   SELECT username INTO v_name FROM public.users WHERE role = 'monteur' LIMIT 1;
--   SELECT count(*) INTO v_admins FROM public.users WHERE role = 'admin' AND coalesce(active::text,'') IN ('1','t','true')
--      AND NOT coalesce(locked::text IN ('1','t','true'), false);
--   PERFORM set_config('request.jwt.claims', '{"role":"anon"}', true);
--   EXECUTE 'SET LOCAL ROLE anon';
--   v_j := public.passwort_hilfe_anfragen('gibt-es-nicht-' || md5(random()::text));
--   IF v_j <> '{"ok": true}'::jsonb THEN RAISE EXCEPTION 'PROBE FEHLER Antwort unbekannter Name: %', v_j; END IF;
--   BEGIN
--     EXECUTE 'SELECT count(*) FROM public.passwort_hilfe_log';
--     RAISE EXCEPTION 'PROBE FEHLER anon liest das Log';
--   EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe anon: Log nicht lesbar - ok';
--   END;
--   EXECUTE 'RESET ROLE';
--   SELECT count(*) INTO v_vorher FROM public.notifications WHERE id LIKE 'pwh_%';
--   EXECUTE 'SET LOCAL ROLE anon';
--   v_j := public.passwort_hilfe_anfragen(v_name);
--   v_j := public.passwort_hilfe_anfragen(upper(v_name));   -- zweimal in derselben Stunde
--   EXECUTE 'RESET ROLE';
--   SELECT count(*) INTO v_nach FROM public.notifications WHERE id LIKE 'pwh_%';
--   IF v_nach - v_vorher <> v_admins THEN
--     RAISE EXCEPTION 'PROBE FEHLER % neue Benachrichtigungen, erwartet % (eine je aktivem Admin)', v_nach - v_vorher, v_admins; END IF;
--   RAISE NOTICE 'PROBE fertig - ok (% Admin-Benachrichtigungen)', v_admins;
-- END $probe$;
-- ROLLBACK;
-- =====================================================================================
