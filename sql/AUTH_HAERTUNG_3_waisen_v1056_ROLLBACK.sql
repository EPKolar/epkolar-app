-- IDEMPOTENT
-- =====================================================================================
-- AUTH_HAERTUNG_3_waisen_v1056_ROLLBACK.sql  —  Sperre der verwaisten Logins aufheben (Vorwert aus der Sicherung)
-- STATUS: ENTWURF — nur durch Sebastian ueber das Tor. Beendete Sitzungen kommen nicht zurueck.
-- =====================================================================================

BEGIN;

DO $$
DECLARE r record; v_n int := 0;
BEGIN
  IF to_regclass('public._auth_haertung_v1056_sicherung') IS NULL THEN
    RAISE EXCEPTION 'Keine Sicherung vorhanden - AUTH_HAERTUNG_3 wurde nie angewendet (nichts zu tun)'; END IF;
  FOR r IN SELECT objekt, extra FROM public._auth_haertung_v1056_sicherung WHERE art = 'ban' AND objekt LIKE 'ban:auth.users.%' LOOP
    UPDATE auth.users SET banned_until = (r.extra->>'banned_until')::timestamptz
     WHERE id = substr(r.objekt, length('ban:auth.users.') + 1)::uuid;
    DELETE FROM public._auth_haertung_v1056_sicherung WHERE objekt = r.objekt;
    v_n := v_n + 1;
  END LOOP;
  RAISE NOTICE 'Sperre aufgehoben fuer % Konten', v_n;
END $$;

COMMIT;
