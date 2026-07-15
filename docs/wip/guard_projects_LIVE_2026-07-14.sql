-- guard_projects() — Live-Body aus der DB (pg_get_functiondef), 1:1, 2026-07-14.
-- Normalform (prosrc, ASCII-\s kollabiert, getrimmt): md5 5b8c7817a69429cabb562f39a41fab37 / 397 Zeichen.
-- NICHT ausfuehren als Rekonstruktion — das ist die WAHRHEIT, Quelle fuer TERMINAL_FINAL_v3.

CREATE OR REPLACE FUNCTION public.guard_projects()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE c_role text; c_sub text;
BEGIN
  c_sub := current_setting('request.jwt.claims', true)::json->>'sub';
  IF c_sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
  SELECT u.role INTO c_role FROM public.users u WHERE u.auth_user_id::text = c_sub;
  IF c_role IN ('admin','projektleiter') THEN RETURN COALESCE(NEW, OLD); END IF;
  RAISE EXCEPTION 'Nur Projektleiter/Admin duerfen Projekte aendern';
END; $function$
