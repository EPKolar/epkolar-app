-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_3_waisen_v1056_ENTWURF.sql  —  verwaiste Logins (auth.users ohne public.users-Zeile) sperren
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Pruefung durch Chat-Claude, Einspielen nur durch Sebastian ueber das Tor.
-- Bericht: C:/repos/epk-auth-pruefung-2026-11-19.md Fund 3: 13 auth.users, davon 3 ohne users-Zeile
--   (Domains ep-kolar.at x2 = ausgeschiedene Monteure, epkolar.local x1 = intern; eines zuletzt am 13.06. angemeldet).
--   Ein verwaister Login bekommt von GoTrue weiter ein authenticated-Token -> alle Policies, die nur
--   "angemeldet" pruefen, stehen ihm offen.
--
-- VORGEHEN (zwei Laeufe, NIE geraten):
--   SCHRITT A (nur lesen): Waisen-Liste ziehen, jede Zeile von Hand pruefen. Besonders das epkolar.local-Konto:
--     ist es ein Dienstkonto (Anbindung, Kiosk, Skript)? Wenn ja: NICHT sperren, sondern eine users-Zeile anlegen
--     oder die Anbindung auf service_role umstellen - sonst bricht sie mit diesem Skript UND mit AUTH_HAERTUNG_4.
--   SCHRITT B: die geprueften IDs unten in v_ziel eintragen und den Block laufen lassen.
--
-- WIE GESPERRT WIRD
--   auth.users.banned_until = now() + 100 Jahre, dazu Refresh-Tokens widerrufen und Sitzungen loeschen.
--   Bewusst NICHT 'infinity': GoTrue liest banned_until als Go-Zeitwert; 'infinity' kann beim Einlesen scheitern und
--   dann den Login (oder die Benutzerliste im Dashboard) mit 500 abbrechen. 100 Jahre ist dasselbe, was die Admin-API
--   mit ban_duration '876000h' setzt.
--   Gleichwertige Alternative ohne direktes Schreiben ins auth-Schema: Dashboard -> Authentication -> Users -> Benutzer
--   -> "Ban user", oder Admin-API PUT /auth/v1/admin/users/<id> {"ban_duration":"876000h"} (service_role-Schluessel,
--   nur von Sebastians Rechner, nie in die App). Loeschen statt sperren (auth.admin.deleteUser) ist endgueltig.
--   Hinweis: admin_create_user schreibt bereits direkt in auth.users - direktes Schreiben ist hier also gelebte Praxis.
--
-- ROLLBACK: sql/AUTH_HAERTUNG_3_waisen_v1056_ROLLBACK.sql (setzt banned_until auf den gesicherten Vorwert;
--   beendete Sitzungen kommen nicht zurueck - die Betroffenen melden sich neu an).
-- =====================================================================================

-- -------------------------------------------------------------------------------------
-- SCHRITT A — nur lesen (eigener Lauf). Keine E-Mail im Klartext, nur Domain.
-- -------------------------------------------------------------------------------------
-- SELECT au.id,
--        split_part(au.email, '@', 2)                                        AS domain,
--        au.created_at, au.last_sign_in_at, au.banned_until,
--        (SELECT max(coalesce(s.refreshed_at, s.updated_at)) FROM auth.sessions s WHERE s.user_id = au.id) AS letzte_sitzung,
--        (SELECT count(*) FROM auth.refresh_tokens rt WHERE rt.user_id = au.id::text AND NOT rt.revoked)   AS offene_refresh_tokens
--   FROM auth.users au
--  WHERE NOT EXISTS (SELECT 1 FROM public.users pu WHERE pu.auth_user_id = au.id)
--  ORDER BY au.created_at;
-- (Hat auth.sessions keine Spalte refreshed_at, coalesce(...) durch s.updated_at ersetzen.)

-- -------------------------------------------------------------------------------------
-- SCHRITT B — sperren
-- -------------------------------------------------------------------------------------
BEGIN;

CREATE TABLE IF NOT EXISTS public._auth_haertung_v1056_sicherung (
  objekt       text PRIMARY KEY,
  art          text NOT NULL,
  definition   text,
  extra        jsonb,
  gesichert_am timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public._auth_haertung_v1056_sicherung ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public._auth_haertung_v1056_sicherung FROM PUBLIC, anon, authenticated;

DO $$
DECLARE
  -- >>> HIER die in Schritt A geprueften IDs eintragen (erwartet: 3). Leer = Abbruch. <<<
  v_ziel uuid[] := ARRAY[
    -- '00000000-0000-0000-0000-000000000000'
  ]::uuid[];
  -- Schutz gegen Dienstkonten: Anmeldung oder Sitzung juenger als so viele Tage -> Abbruch
  v_frisch_tage constant int := 14;
  v_id uuid; v_n int; v_waisen int; v_letzt timestamptz;
BEGIN
  -- VORPRUEFUNG (bricht ab, wenn etwas nicht stimmt)
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='auth' AND table_name='users' AND column_name='banned_until') THEN
    RAISE EXCEPTION 'Vorpruefung: auth.users.banned_until fehlt'; END IF;
  IF NOT has_column_privilege('auth.users','banned_until','UPDATE') OR NOT has_table_privilege('auth.sessions','DELETE')
     OR NOT has_table_privilege('auth.refresh_tokens','UPDATE') THEN
    RAISE EXCEPTION 'Vorpruefung: % darf auth.users.banned_until / auth.sessions / auth.refresh_tokens nicht aendern - Dashboard/Admin-API nehmen', current_user; END IF;
  IF coalesce(array_length(v_ziel, 1), 0) = 0 THEN
    RAISE EXCEPTION 'Keine IDs eingetragen - erst Schritt A, dann v_ziel fuellen'; END IF;
  IF array_length(v_ziel, 1) > 3 THEN
    RAISE EXCEPTION '% IDs eingetragen, bekannt sind 3 - Liste pruefen (bei Absicht diese Grenze bewusst anheben)', array_length(v_ziel, 1); END IF;
  SELECT count(*) INTO v_waisen FROM auth.users au WHERE NOT EXISTS (SELECT 1 FROM public.users pu WHERE pu.auth_user_id = au.id);
  RAISE NOTICE 'VORHER: % Waisen in auth.users, % zum Sperren eingetragen', v_waisen, array_length(v_ziel, 1);
  FOREACH v_id IN ARRAY v_ziel LOOP
    IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = v_id) THEN RAISE EXCEPTION 'ID % gibt es in auth.users nicht', v_id; END IF;
    IF EXISTS (SELECT 1 FROM public.users WHERE auth_user_id = v_id) THEN
      RAISE EXCEPTION 'ID % hat eine users-Zeile - ist KEINE Waise, nicht sperren', v_id; END IF;
    SELECT greatest(au.last_sign_in_at, (SELECT max(s.updated_at) FROM auth.sessions s WHERE s.user_id = au.id))
      INTO v_letzt FROM auth.users au WHERE au.id = v_id;
    IF v_letzt IS NOT NULL AND v_letzt > now() - make_interval(days => v_frisch_tage) THEN
      RAISE EXCEPTION 'ID % war vor weniger als % Tagen aktiv (%) - Dienstkonto? Erst klaeren', v_id, v_frisch_tage, v_letzt; END IF;
  END LOOP;

  -- Vorwert sichern (erster Lauf), dann sperren
  INSERT INTO public._auth_haertung_v1056_sicherung (objekt, art, extra)
  SELECT 'ban:auth.users.'||au.id, 'ban', jsonb_build_object('banned_until', au.banned_until)
    FROM auth.users au WHERE au.id = ANY (v_ziel)
  ON CONFLICT (objekt) DO NOTHING;
  UPDATE auth.users SET banned_until = now() + interval '100 years'
   WHERE id = ANY (v_ziel) AND (banned_until IS NULL OR banned_until < now() + interval '50 years');
  GET DIAGNOSTICS v_n = ROW_COUNT;
  RAISE NOTICE 'gesperrt: %', v_n;
  UPDATE auth.refresh_tokens SET revoked = true WHERE user_id = ANY (SELECT unnest(v_ziel)::text) AND revoked IS DISTINCT FROM true;
  GET DIAGNOSTICS v_n = ROW_COUNT;
  RAISE NOTICE 'Refresh-Tokens widerrufen: %', v_n;
  DELETE FROM auth.sessions WHERE user_id = ANY (v_ziel);
  GET DIAGNOSTICS v_n = ROW_COUNT;
  RAISE NOTICE 'Sitzungen geloescht: %', v_n;

  -- NACHHER
  SELECT count(*) INTO v_n FROM auth.users WHERE id = ANY (v_ziel) AND (banned_until IS NULL OR banned_until < now() + interval '50 years');
  IF v_n > 0 THEN RAISE EXCEPTION 'Nachpruefung: % Ziel-Konten nicht gesperrt', v_n; END IF;
  SELECT count(*) INTO v_n FROM auth.sessions WHERE user_id = ANY (v_ziel);
  IF v_n > 0 THEN RAISE EXCEPTION 'Nachpruefung: % Sitzungen uebrig', v_n; END IF;
  RAISE NOTICE 'NACHHER: alle % Ziel-Konten gesperrt, keine Sitzung mehr', array_length(v_ziel, 1);
END $$;

COMMIT;

-- -------------------------------------------------------------------------------------
-- WIEDERKEHRENDE KONTROLLE (lesend, z. B. monatlich oder nach jedem Austritt):
--   1) Waisen, die NICHT gesperrt sind (soll: 0 Zeilen)
--   2) users-Zeilen gesperrt/inaktiv/ausgeschieden, deren Login noch Sitzungen hat (Hinweis: mit AUTH_HAERTUNG_2/4 ohne
--      Datenzugriff; trotzdem aufraeumen oder sperren)
-- -------------------------------------------------------------------------------------
-- SELECT 'waise_offen' AS art, au.id, split_part(au.email,'@',2) AS domain, au.last_sign_in_at
--   FROM auth.users au
--  WHERE NOT EXISTS (SELECT 1 FROM public.users pu WHERE pu.auth_user_id = au.id)
--    AND (au.banned_until IS NULL OR au.banned_until < now())
-- UNION ALL
-- SELECT 'gesperrt_mit_sitzung', pu.auth_user_id, split_part(pu.email,'@',2), NULL
--   FROM public.users pu
--  WHERE pu.auth_user_id IS NOT NULL
--    AND (coalesce(pu.active::text,'') NOT IN ('1','t','true')
--         OR coalesce(pu.locked::text,'') IN ('1','t','true')
--         OR (pu.deactivate_at IS NOT NULL AND pu.deactivate_at <= current_date))
--    AND EXISTS (SELECT 1 FROM auth.sessions s WHERE s.user_id = pu.auth_user_id);
-- =====================================================================================
--
-- PROBE (eigener Lauf, BEGIN ... ROLLBACK): ein gesperrtes Ziel hat nach dem Lauf keine Rechte mehr (mit AUTH_HAERTUNG_2)
-- BEGIN;
-- DO $probe$
-- DECLARE v_id uuid;
-- BEGIN
--   SELECT au.id INTO v_id FROM auth.users au WHERE NOT EXISTS (SELECT 1 FROM public.users pu WHERE pu.auth_user_id = au.id) LIMIT 1;
--   IF v_id IS NULL THEN RAISE NOTICE 'keine Waise - nichts zu pruefen'; RETURN; END IF;
--   IF (SELECT banned_until FROM auth.users WHERE id = v_id) IS NULL OR (SELECT banned_until FROM auth.users WHERE id = v_id) < now() THEN
--     RAISE EXCEPTION 'PROBE FEHLER Waise % nicht gesperrt', v_id; END IF;
--   PERFORM set_config('request.jwt.claims', json_build_object('sub', v_id, 'role', 'authenticated')::text, true);
--   EXECUTE 'SET LOCAL ROLE authenticated';
--   IF to_regprocedure('public.ist_aktiver_benutzer()') IS NOT NULL AND public.ist_aktiver_benutzer() THEN
--     RAISE EXCEPTION 'PROBE FEHLER Waise gilt als aktiv'; END IF;
--   EXECUTE 'RESET ROLE';
--   RAISE NOTICE 'Probe Waise: gesperrt, ohne Rechte - ok';
-- END $probe$;
-- ROLLBACK;
