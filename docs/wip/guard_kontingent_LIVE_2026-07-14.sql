-- guard_kontingent() — Live-Body aus der DB (pg_get_functiondef), 1:1, 2026-07-14.
-- Normalform (prosrc, ASCII-\s kollabiert, getrimmt): md5 33772730121944abfc09aaa35d465ac0 / 486 Zeichen.
-- NICHT ausfuehren als Rekonstruktion — das ist die WAHRHEIT, Quelle fuer TERMINAL_FINAL_v3.

CREATE OR REPLACE FUNCTION public.guard_kontingent()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE c_role text; c_perms text; c_sub text;
BEGIN
  c_sub := current_setting('request.jwt.claims', true)::json->>'sub';
  IF c_sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
  SELECT u.role, u.permissions INTO c_role, c_perms FROM public.users u WHERE u.auth_user_id::text = c_sub;
  IF c_role = 'admin' OR (c_perms IS NOT NULL AND c_perms LIKE '%"urlaub_edit"%') THEN RETURN COALESCE(NEW, OLD); END IF;
  RAISE EXCEPTION 'Urlaubskontingent aendern erfordert urlaub_edit oder Admin';
END; $function$
