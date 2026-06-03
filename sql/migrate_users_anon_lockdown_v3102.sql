-- ═══════════════════════════════════════════════════════════
-- v3.10.2 anon-Lockdown auf public.users (Sebastian-Spec EXAKT)
-- ═══════════════════════════════════════════════════════════
--
-- B-C Fix: anon darf users (inkl. password_hash + email) nicht mehr lesen.
--
-- LOGIN-PFAD-BEFUND (CC Code-Analyse Z2163-2199 index.html):
--   App-Login nutzt RPC `login_lookup(p_username)` — SECURITY DEFINER (umgeht RLS).
--   Code macht KEINEN direkten `GET /users` mit anon-Key.
--   Authenticated User lesen via authenticated_read_users-Policy (separat).
--
-- LIVE-BEWEIS: 9/9 User loggen aktuell ein ✓
--   → Login funktioniert weiter auch ohne anon-SELECT-Policy.
--
-- ZIEL-Variante: DROP `users_anon_select` (Sebastian-Spec exakt).
--
-- ZWINGEND VOR APPLY:
--   1. login_lookup ist SECURITY DEFINER (sonst bricht Login):
--      SELECT proname, prosecdef FROM pg_proc
--      WHERE proname='login_lookup' AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public');
--      → prosecdef='t' MUSS true sein.
--   2. login_lookup EXECUTE-Grant für anon:
--      SELECT routine_name, grantee, privilege_type FROM information_schema.routine_privileges
--      WHERE routine_name='login_lookup';
--
-- SOFORT NACH APPLY (Sebastian/Chat-Claude):
--   10-User token-grant Smoke (alle Rollen).
--   Bricht ≥1 User → INSTANT ROLLBACK via migrate_users_anon_lockdown_v3102_ROLLBACK.sql.

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Snapshot der Original-Policy in Audit-Tabelle
-- (für späteren Reference falls nötig)
-- ═══════════════════════════════════════════════════════════

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
-- BLOCK 2: B-C Fix — anon-Vollzugriff auf users entfernen
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS users_anon_select ON public.users;

-- ═══════════════════════════════════════════════════════════
-- VERIFY (nach Apply, vor Smoke)
-- ═══════════════════════════════════════════════════════════
-- 1. Policy entfernt:
--    SELECT polname FROM pg_policies
--    WHERE schemaname='public' AND tablename='users' AND polname='users_anon_select';
--    → erwartet: 0 Zeilen
--
-- 2. anon-Direct-Test (sollte JETZT 401/leer):
--    curl -X GET 'https://jiggujpruejkaomgxarp.supabase.co/rest/v1/users?select=id&limit=1' \
--      -H 'apikey: <ANON_KEY>'
--    → erwartet: 200 + [] ODER 401
--
-- 3. login_lookup-Test (sollte WEITERHIN funktionieren):
--    curl -X POST 'https://jiggujpruejkaomgxarp.supabase.co/rest/v1/rpc/login_lookup' \
--      -H 'apikey: <ANON_KEY>' \
--      -H 'Content-Type: application/json' \
--      -d '{"p_username":"barger"}'
--    → erwartet: 200 + user-row
--
-- 4. 10-User Token-Grant Smoke (alle MÜSSEN 200):
--    barger / cracana / riedmann / kiener (monteure)
--    paschinger (techniker)
--    pinger / schmid (projektleiter)
--    lindhuber / schober (buero)
--    sebastian (admin)
--    POST /auth/v1/token?grant_type=password body:{email,password}

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK: siehe migrate_users_anon_lockdown_v3102_ROLLBACK.sql
-- ═══════════════════════════════════════════════════════════
