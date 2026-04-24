-- PW-Reset Recovery · 24.04.2026 · deployed via Chat-Claude Chrome-MCP
-- Stellt public.admin_reset_password(uuid, text) wieder her.
-- Schema-Fix vs. original: public.users.id ist text (u1/u2), Join via auth_user_id (uuid).

DROP FUNCTION IF EXISTS public.admin_reset_password(uuid, text);
DROP FUNCTION IF EXISTS public.admin_reset_password(text, text);
DROP FUNCTION IF EXISTS public.admin_reset_password(text);
DROP FUNCTION IF EXISTS public.admin_reset_password(json);

CREATE OR REPLACE FUNCTION public.admin_reset_password(
  target_user_id uuid,
  new_password text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth
AS $func$
DECLARE
  caller_role text;
  updated_count int;
BEGIN
  SELECT role INTO caller_role
  FROM public.users
  WHERE auth_user_id = auth.uid();

  IF caller_role IS NULL OR caller_role <> 'admin' THEN
    RAISE EXCEPTION 'admin_reset_password: nur Admin-Rolle berechtigt (aktuell: %)', COALESCE(caller_role, 'NULL')
      USING ERRCODE = 'insufficient_privilege';
  END IF;

  IF new_password IS NULL OR char_length(new_password) < 6 THEN
    RAISE EXCEPTION 'admin_reset_password: Passwort muss mindestens 6 Zeichen haben'
      USING ERRCODE = 'check_violation';
  END IF;

  IF NOT EXISTS (SELECT 1 FROM auth.users WHERE id = target_user_id) THEN
    RAISE EXCEPTION 'admin_reset_password: User-ID % nicht in auth.users', target_user_id
      USING ERRCODE = 'no_data_found';
  END IF;

  UPDATE auth.users
  SET encrypted_password = crypt(new_password, gen_salt('bf', 10)),
      updated_at = now()
  WHERE id = target_user_id;

  GET DIAGNOSTICS updated_count = ROW_COUNT;

  IF updated_count <> 1 THEN
    RAISE EXCEPTION 'admin_reset_password: unerwartete Zeilen-Anzahl: %', updated_count;
  END IF;

  RETURN jsonb_build_object('ok', true, 'user_id', target_user_id, 'updated_at', now());
END;
$func$;

REVOKE ALL ON FUNCTION public.admin_reset_password(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.admin_reset_password(uuid, text) TO authenticated;
GRANT EXECUTE ON FUNCTION public.admin_reset_password(uuid, text) TO service_role;

COMMENT ON FUNCTION public.admin_reset_password(uuid, text) IS
  'v3.8.43 recovery FIX-2 24.04.2026: Role-Check via public.users.auth_user_id (uuid join, nicht id text).';

NOTIFY pgrst, 'reload schema';
