-- ═══════════════════════════════════════════════════════════
-- v3.10.4 ROLLBACK — Self-Elevation-Fix rückgängig
-- ═══════════════════════════════════════════════════════════
--
-- WANN AUSFÜHREN:
--   - Wenn Login (last_login/login_count Z2198) bricht
--   - Wenn Admin keine User mehr anlegen kann (über Edge-Function ODER User-Mgmt-UI)
--   - Wenn Profil-Updates brechen
--   → SOFORT diesen ROLLBACK.

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Neue differenzierte Policies entfernen
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS users_select_self_or_admin ON public.users;
DROP POLICY IF EXISTS users_update_self_safe_columns ON public.users;
DROP POLICY IF EXISTS users_update_admin ON public.users;
DROP POLICY IF EXISTS users_insert_admin ON public.users;
DROP POLICY IF EXISTS users_delete_admin ON public.users;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: Original-Policy authenticated_write_users wiederherstellen
-- ═══════════════════════════════════════════════════════════

CREATE POLICY authenticated_write_users
  ON public.users FOR ALL TO authenticated
  USING (true) WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: Helper-Function bleibt (idempotent — nicht entfernen, Sprint-übergreifend nützlich)
-- ═══════════════════════════════════════════════════════════
-- is_admin_or_pl() bleibt erhalten — wird in anderen RLS-Policies wiederverwendet.

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: Column-Grants wiederherstellen (falls Login bcrypt-Fallback bricht)
-- ═══════════════════════════════════════════════════════════

GRANT SELECT (password_hash) ON public.users TO authenticated;
-- anon bleibt ohne password_hash-Grant (anon-Lockdown v3.10.2)

-- ═══════════════════════════════════════════════════════════
-- VERIFY ROLLBACK
-- ═══════════════════════════════════════════════════════════
-- 1. Policy wiederhergestellt:
--    SELECT polname, cmd, qual FROM pg_policies
--    WHERE schemaname='public' AND tablename='users' AND polname='authenticated_write_users';
--    → erwartet: 1 Zeile cmd=ALL qual=true
--
-- 2. App-Login retesten — alle Funktionen wieder OK
-- 3. ⚠ Self-Elevation-Lücke wieder OFFEN — sofort melden, alternativer Fix planen

-- ═══════════════════════════════════════════════════════════
-- CLEANUP (OPTIONAL nach erfolgreichem Rollback):
-- DROP TABLE IF EXISTS public._rls_snapshot_v3104;
-- ═══════════════════════════════════════════════════════════
