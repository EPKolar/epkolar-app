-- ═══════════════════════════════════════════════════════════
-- v3.10.2 ROLLBACK — anon-Lockdown rückgängig
-- Sebastian-Spec EXAKT (Original-Policy wiederherstellen)
-- ═══════════════════════════════════════════════════════════
--
-- WANN AUSFÜHREN:
--   Wenn nach migrate_users_anon_lockdown_v3102.sql auch nur 1 von 10 User-Logins
--   fehlschlägt (token-grant != 200) → SOFORT diesen ROLLBACK.
--
-- WIE:
--   Im Supabase SQL Editor einfügen → Run.
--   Smoke-Test sofort wiederholen (sollte wieder grün sein).

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK: Original-Policy exakt wiederherstellen
-- ═══════════════════════════════════════════════════════════

CREATE POLICY users_anon_select ON public.users
  FOR SELECT TO public USING (auth.role() = 'anon');

-- ═══════════════════════════════════════════════════════════
-- VERIFY ROLLBACK
-- ═══════════════════════════════════════════════════════════
-- 1. Policy wiederhergestellt:
--    SELECT polname, roles, cmd, qual FROM pg_policies
--    WHERE schemaname='public' AND tablename='users' AND polname='users_anon_select';
--    → erwartet: 1 Zeile mit qual = "(auth.role() = 'anon'::text)"
--
-- 2. anon-Test (sollte JETZT WIEDER 200 + Daten):
--    curl -X GET 'https://jiggujpruejkaomgxarp.supabase.co/rest/v1/users?select=id&limit=1' \
--      -H 'apikey: <ANON_KEY>'
--
-- 3. App-Login retesten — alle 10 User müssen einloggen können

-- ═══════════════════════════════════════════════════════════
-- CLEANUP Snapshot-Tabelle (OPTIONAL, nach erfolgreichem Rollback)
-- ═══════════════════════════════════════════════════════════
-- DROP TABLE IF EXISTS public._rls_snapshot_v3102;
