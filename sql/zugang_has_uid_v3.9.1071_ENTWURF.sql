-- ENTWURF v3.9.1071 - NICHT angewendet. Nur auf ausdrueckliche Freigabe (Sebastian).
-- Zweck: Admin > Juprowa soll auch fuer die UID "hinterlegt" zeigen koennen.
-- juprowa_get_config() liefert heute nur has_passport (Boolean); fuer die UID gibt es kein Feld,
-- die App zeigt deshalb ehrlich "nicht lesbar". Diese Aenderung ergaenzt NUR has_uid (Boolean),
-- weiterhin KEINE Werte. Sync/Push nutzen die Funktion nicht (sie lesen die Tabelle serverseitig).
-- Vorher pruefen: select pg_get_functiondef('public.juprowa_get_config()'::regprocedure);
--                 ACL: select proacl from pg_proc where oid='public.juprowa_get_config()'::regprocedure;
-- CREATE OR REPLACE behaelt Eigentuemer und ACL bei.

CREATE OR REPLACE FUNCTION public.juprowa_get_config()
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
AS $function$
DECLARE
  config_row juprowa_config%ROWTYPE;
BEGIN
  SELECT * INTO config_row FROM juprowa_config WHERE id = 'default';
  IF NOT FOUND THEN
    RETURN jsonb_build_object('configured', false);
  END IF;

  RETURN jsonb_build_object(
    'configured', true,
    'sync_enabled', config_row.sync_enabled,
    'auto_sync_interval_seconds', config_row.auto_sync_interval_seconds,
    'last_sync_at', config_row.last_sync_at,
    'last_sync_result', config_row.last_sync_result,
    'has_passport', config_row.passport IS NOT NULL AND config_row.passport != '',
    'has_uid', config_row.uid IS NOT NULL AND config_row.uid != ''
  );
END;
$function$;

-- ROLLBACK (Stand live 19.11.2026, gemessen per pg_get_functiondef):
-- CREATE OR REPLACE FUNCTION public.juprowa_get_config()
--  RETURNS jsonb
--  LANGUAGE plpgsql
--  SECURITY DEFINER
-- AS $function$
-- DECLARE
--   config_row juprowa_config%ROWTYPE;
-- BEGIN
--   SELECT * INTO config_row FROM juprowa_config WHERE id = 'default';
--   IF NOT FOUND THEN
--     RETURN jsonb_build_object('configured', false);
--   END IF;
--
--   RETURN jsonb_build_object(
--     'configured', true,
--     'sync_enabled', config_row.sync_enabled,
--     'auto_sync_interval_seconds', config_row.auto_sync_interval_seconds,
--     'last_sync_at', config_row.last_sync_at,
--     'last_sync_result', config_row.last_sync_result,
--     'has_passport', config_row.passport IS NOT NULL AND config_row.passport != ''
--   );
-- END;
-- $function$;
