-- ═══════════════════════════════════════════════════════════
-- v3.10.2 ROLLBACK — anon-Lockdown rückgängig (bei Smoke-Fehler)
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
-- BLOCK 1: Authenticated-Policy droppen
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS users_select_authenticated ON public.users;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: Original-Policies aus Snapshot wiederherstellen
-- ═══════════════════════════════════════════════════════════

DO $$
DECLARE snap RECORD;
BEGIN
  FOR snap IN
    SELECT polname, roles, cmd, qual, with_check
    FROM public._rls_snapshot_v3102
    WHERE schemaname='public' AND tablename='users'
  LOOP
    BEGIN
      -- Versuch: Original-Policy mit USING(true) für SELECT/ALL wiederherstellen
      IF snap.cmd='SELECT' OR snap.cmd='ALL' THEN
        EXECUTE format(
          'CREATE POLICY %I ON public.users FOR %s TO %s USING (%s)',
          snap.polname,
          snap.cmd,
          array_to_string(snap.roles, ','),
          COALESCE(snap.qual, 'true')
        );
        RAISE NOTICE 'Restored Policy: %', snap.polname;
      END IF;
    EXCEPTION WHEN OTHERS THEN
      RAISE NOTICE 'Restore failed for %: % (falling back to permissive)', snap.polname, SQLERRM;
    END;
  END LOOP;
END $$;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: Fallback wenn Snapshot leer/unklar — Permissive Policy
-- ═══════════════════════════════════════════════════════════

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='users' AND cmd='SELECT'
  ) THEN
    CREATE POLICY users_select_all_fallback ON public.users
      FOR SELECT USING (true);
    RAISE NOTICE 'Fallback permissive SELECT policy created on users';
  END IF;
END $$;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: Grants
-- ═══════════════════════════════════════════════════════════

GRANT SELECT ON public.users TO anon;
GRANT SELECT ON public.users TO PUBLIC;
GRANT SELECT ON public.users TO authenticated;

-- ═══════════════════════════════════════════════════════════
-- VERIFY ROLLBACK
-- ═══════════════════════════════════════════════════════════
-- 1. Policies sollten wieder permissive sein:
--    SELECT polname, roles, cmd, qual FROM pg_policies
--    WHERE schemaname='public' AND tablename='users';
--
-- 2. anon-Test (sollte JETZT WIEDER 200 + Daten):
--    apikey=<anon-key>
--    GET /rest/v1/users?select=id&limit=1
--
-- 3. App-Login retesten — alle 9 User müssen einloggen können

-- ═══════════════════════════════════════════════════════════
-- CLEANUP Audit-Tabelle (OPTIONAL, nach erfolgreichem Rollback)
-- ═══════════════════════════════════════════════════════════
-- DROP TABLE IF EXISTS public._rls_snapshot_v3102;
