-- ═══════════════════════════════════════════════════════════
-- v3.10.2 anon-Lockdown auf public.users (Variante B)
-- Sebastian-Spec 2026-06-03
-- ═══════════════════════════════════════════════════════════
--
-- LOGIN-PFAD-BEFUND (CC Code-Analyse Z2163-2199 index.html):
--   App-Login nutzt RPC `login_lookup(p_username)` mit anon-apikey.
--   RPC ist (vermutlich) SECURITY DEFINER → läuft in postgres-Rolle,
--   unabhängig von RLS-Policy auf `users`.
--   Code macht KEINEN direkten `GET /users` mit anon-Key.
--   → Anon-SELECT-Policy auf `users` kann komplett gedroppt werden.
--
-- LIVE-BEWEIS: 9/9 User loggen aktuell ein (Chat-Claude Baseline) ✓
-- → RPC funktioniert. Anon-Direkt-SELECT ist Sicherheits-Leak (B-C),
--   nicht Teil des Login-Pfads.
--
-- VARIANTE B (gewählt): SELECT-Policy für anon entfernen.
--   Authenticated User bekommen eigene SELECT-Policy (read own + admin).
--   Service-Role bleibt ungebremst (Edge-Functions, Migrations).
--
-- ZWINGEND VOR APPLY:
--   1. `login_lookup` RPC-Definition prüfen — MUSS SECURITY DEFINER sein:
--      \df+ public.login_lookup
--   2. RPC-Return-Schema prüfen — MUSS enthalten:
--      id, email, password_hash, name, role, username, locked,
--      permissions, monteur_id, perms_override
--      (für bcrypt-Fallback Z2184 + GoTrue-Auth Z2180)
--   3. RPC-EXECUTE-Grant prüfen:
--      \dp+ public.login_lookup
--      → anon und authenticated MÜSSEN EXECUTE haben
--
-- SOFORT-VERIFY NACH APPLY (Sebastian/Chat-Claude):
--   9 token-grants pro User testen — alle MÜSSEN 200 + access_token liefern.
--   Bricht auch nur 1 → INSTANT REVERT via Rollback-Block unten.

-- ═══════════════════════════════════════════════════════════
-- BLOCK 0: Diagnose-Snapshot (read-only, VOR Apply)
-- ═══════════════════════════════════════════════════════════

-- 0.1 Aktuelle Policies auf users
-- SELECT polname, roles, cmd, qual, with_check
-- FROM pg_policies WHERE schemaname='public' AND tablename='users'
-- ORDER BY cmd;

-- 0.2 login_lookup-Function-Definition
-- SELECT proname, provolatile, prosecdef, proacl
-- FROM pg_proc WHERE proname='login_lookup' AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public');
-- → prosecdef='t' MUSS sein (SECURITY DEFINER)

-- 0.3 Grants auf login_lookup
-- SELECT * FROM information_schema.routine_privileges
-- WHERE routine_name='login_lookup' AND routine_schema='public';
-- → anon und authenticated MÜSSEN EXECUTE haben

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Snapshot bestehender Policies in Audit-Tabelle
-- ═══════════════════════════════════════════════════════════
-- (Sicherheit + späterer Rollback-Bezug)

CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3102 (
  ts timestamptz DEFAULT now(),
  schemaname text, tablename text,
  polname text, roles text[], cmd text,
  qual text, with_check text
);

INSERT INTO public._rls_snapshot_v3102 (schemaname, tablename, polname, roles, cmd, qual, with_check)
SELECT schemaname, tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename='users';

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: anon-SELECT-Policy auf users entfernen
-- ═══════════════════════════════════════════════════════════
-- Loop über alle Policies wo anon (oder public) SELECT mit qual=true hat

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='users'
      AND cmd IN ('SELECT','ALL')
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND (
        'anon'::text = ANY(roles)
        OR 'public'::text = ANY(roles)
        OR roles IS NULL
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.users', pol.polname);
    RAISE NOTICE 'Dropped anon/public SELECT/ALL-Policy on users: %', pol.polname;
  END LOOP;
END $$;

-- Zusätzlich: REVOKE direkte Grants
REVOKE SELECT ON public.users FROM anon;
REVOKE SELECT ON public.users FROM PUBLIC;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: Authenticated SELECT-Policy (eigene + admin/PL/buero)
-- ═══════════════════════════════════════════════════════════
-- WICHTIG: helper-function is_admin() aus Sprint 53 v3.9.53 wird wiederverwendet.
-- Falls is_admin() noch nicht existiert: zuerst migrate_notifications_rls_v3953.sql laufen lassen.

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname='is_admin' AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public')) THEN
    RAISE EXCEPTION 'is_admin() Helper fehlt — zuerst migrate_notifications_rls_v3953.sql ausführen';
  END IF;
END $$;

-- Drop bestehende authenticated-SELECT-Policies (frischer Stand)
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='users'
      AND cmd='SELECT'
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.users', pol.polname);
  END LOOP;
END $$;

-- Neue SELECT-Policy für authenticated
CREATE POLICY users_select_authenticated
  ON public.users FOR SELECT TO authenticated
  USING (
    is_admin()
    OR auth_user_id = auth.uid()
    OR EXISTS(
      SELECT 1 FROM public.users me
      WHERE me.auth_user_id = auth.uid()
        AND me.role IN ('projektleiter','buero','obermonteur')
    )
  );

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: Grant
-- ═══════════════════════════════════════════════════════════

GRANT SELECT ON public.users TO authenticated;
-- service_role: unverändert, bypassed RLS

-- ═══════════════════════════════════════════════════════════
-- BLOCK 5: Sanity-Check login_lookup (Diagnose, vor App-Smoke)
-- ═══════════════════════════════════════════════════════════
-- Falls login_lookup NICHT SECURITY DEFINER ist → wird durch RLS-Drop brechen!

-- SELECT proname, prosecdef AS is_security_definer
-- FROM pg_proc
-- WHERE proname='login_lookup'
--   AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public');
--
-- Wenn is_security_definer='f' (false) → STOP, ROLLBACK!
-- Erst RPC auf SECURITY DEFINER setzen:
--   ALTER FUNCTION public.login_lookup(text) SECURITY DEFINER;

-- ═══════════════════════════════════════════════════════════
-- VERIFY (nach Apply, vor Smoke)
-- ═══════════════════════════════════════════════════════════
-- 1. Policies auf users:
--    SELECT polname, roles, cmd FROM pg_policies
--    WHERE schemaname='public' AND tablename='users';
--    → Erwartet: KEINE anon-Policy mehr, nur authenticated_select
--
-- 2. anon-Direct-Test (sollte JETZT failen):
--    Headers: apikey=<anon-key>, Authorization: NICHT setzen
--    GET /rest/v1/users?select=id&limit=1
--    → erwartet: 200 + leeres Array ODER 401
--
-- 3. login_lookup-Test (sollte WEITERHIN funktionieren):
--    Headers: apikey=<anon-key>
--    POST /rest/v1/rpc/login_lookup body:{"p_username":"barger"}
--    → erwartet: 200 + user-row
--
-- 4. 9-User Token-Grant Smoke (alle MÜSSEN 200):
--    barger / cracana / riedmann / kiener (monteure)
--    paschinger (techniker)
--    pinger / schmid (projektleiter)
--    lindhuber / schober (buero)
--    + sebastian (admin)
--    POST /auth/v1/token?grant_type=password body:{email,password}

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK SQL (bei Smoke-Test-Fehler SOFORT laufen lassen!)
-- ═══════════════════════════════════════════════════════════
-- siehe migrate_users_anon_lockdown_v3102_ROLLBACK.sql
