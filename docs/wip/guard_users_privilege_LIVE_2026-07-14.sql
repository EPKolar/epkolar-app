-- guard_users_privilege() — Live-Body aus der DB (pg_get_functiondef), 1:1, 2026-07-14.
-- Normalform (prosrc, ASCII-\s kollabiert, getrimmt): md5 dcbf3756cf1af4f77623a292a7539f7d / 699 Zeichen.
-- NICHT ausfuehren als Rekonstruktion — das ist die WAHRHEIT, Quelle fuer TERMINAL_FINAL_v3.

CREATE OR REPLACE FUNCTION public.guard_users_privilege()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE caller_role text; caller_sub text;
BEGIN
  caller_sub := current_setting('request.jwt.claims', true)::json->>'sub';
  IF caller_sub IS NULL THEN RETURN NEW; END IF;
  SELECT u.role INTO caller_role FROM public.users u
    WHERE u.auth_user_id::text = caller_sub;
  IF caller_role = 'admin' THEN RETURN NEW; END IF;
  IF NEW.role IS DISTINCT FROM OLD.role
     OR NEW.locked IS DISTINCT FROM OLD.locked
     OR NEW.permissions IS DISTINCT FROM OLD.permissions
     OR NEW.perms_override IS DISTINCT FROM OLD.perms_override
     OR NEW.auth_user_id IS DISTINCT FROM OLD.auth_user_id
     OR NEW.monteur_id IS DISTINCT FROM OLD.monteur_id THEN
    RAISE EXCEPTION 'Privilege fields can only be changed by admin';
  END IF;
  RETURN NEW;
END; $function$
