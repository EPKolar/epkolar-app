-- guard_admin_only() — Live-Body aus der DB (pg_get_functiondef), 1:1, 2026-07-14.
-- Normalform (prosrc, ASCII-\s kollabiert, getrimmt): md5 7f6f0375c5cb69c316f38ce7011f4a9b / 366 Zeichen.
-- NICHT ausfuehren als Rekonstruktion — das ist die WAHRHEIT, Quelle fuer TERMINAL_FINAL_v3.

CREATE OR REPLACE FUNCTION public.guard_admin_only()
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
  IF c_role = 'admin' THEN RETURN COALESCE(NEW, OLD); END IF;
  RAISE EXCEPTION 'Nur Admin darf system_config aendern';
END; $function$
