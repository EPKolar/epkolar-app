-- ═══════════════════════════════════════════════════════════
-- v3.9.97 Phase-3 Hardening — /ALL → role-gated für kritische Tables
-- Sebastian-Spec 2026-06-03: NICHT ohne Freigabe ausführen
-- ═══════════════════════════════════════════════════════════
--
-- VORAUSSETZUNG: migrate_remove_anon_users_select_v3997.sql LÄUFT ZUERST
--
-- BETROFFENE Tables (gefährlich offen mit qual=true):
-- 1. users           - Self-Elevation-Risiko
-- 2. system_config   - App-State-Manipulation
-- 3. urlaubskontingent - Lohn-Relevanz
-- 4. activity_log    - Audit-Trail-Manipulation
--
-- WICHTIG Client-Insert-Pfade unverändert lassen:
-- - notifications INSERT (Client postet eigene)
-- - photos INSERT (PhotoQ.flush)
-- - forms INSERT (Mängel/Regie/SF/DH/AH/Abnahme)
-- - as_kommentare INSERT
-- - juprowa_log INSERT

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: users — Self-Elevation-Risiko schließen
-- ═══════════════════════════════════════════════════════════

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='users'
      AND cmd IN ('ALL','UPDATE')
      AND (qual='true' OR qual IS NULL OR qual='(true)')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.users', pol.polname);
    RAISE NOTICE 'Dropped open UPDATE/ALL-Policy on users: %', pol.polname;
  END LOOP;
END $$;

CREATE POLICY IF NOT EXISTS users_update_admin
  ON public.users FOR UPDATE TO authenticated
  USING (is_admin())
  WITH CHECK (is_admin());

-- Self-update mit role-Lock (eigene Spalten ändern, NICHT role)
CREATE POLICY IF NOT EXISTS users_update_self_no_role_change
  ON public.users FOR UPDATE TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (
    auth_user_id = auth.uid()
    -- role-Lock: kann nicht zu admin/PL elevation
    AND role = (SELECT role FROM public.users u WHERE u.auth_user_id = auth.uid())
  );

-- INSERT: nur Admin
CREATE POLICY IF NOT EXISTS users_insert_admin
  ON public.users FOR INSERT TO authenticated
  WITH CHECK (is_admin());

-- DELETE: nur Admin
CREATE POLICY IF NOT EXISTS users_delete_admin
  ON public.users FOR DELETE TO authenticated
  USING (is_admin());

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: system_config — Admin-only
-- ═══════════════════════════════════════════════════════════

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='system_config'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.system_config', pol.polname);
    RAISE NOTICE 'Dropped open Policy on system_config: %', pol.polname;
  END LOOP;
END $$;

CREATE POLICY IF NOT EXISTS system_config_select
  ON public.system_config FOR SELECT TO authenticated
  USING (true);

CREATE POLICY IF NOT EXISTS system_config_modify_admin
  ON public.system_config FOR INSERT TO authenticated
  WITH CHECK (is_admin());
CREATE POLICY IF NOT EXISTS system_config_update_admin
  ON public.system_config FOR UPDATE TO authenticated
  USING (is_admin()) WITH CHECK (is_admin());
CREATE POLICY IF NOT EXISTS system_config_delete_admin
  ON public.system_config FOR DELETE TO authenticated
  USING (is_admin());

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: urlaubskontingent — Lohn-Relevant
-- ═══════════════════════════════════════════════════════════

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='urlaubskontingent'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.urlaubskontingent', pol.polname);
    RAISE NOTICE 'Dropped open Policy on urlaubskontingent: %', pol.polname;
  END LOOP;
END $$;

-- SELECT: eigene oder Admin/PL/buero
CREATE POLICY IF NOT EXISTS urlaubskontingent_select_own_or_admin
  ON public.urlaubskontingent FOR SELECT TO authenticated
  USING (
    is_admin()
    OR worker_id IN (
      SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid()
    )
    OR EXISTS(SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role IN ('projektleiter','buero'))
  );

-- UPDATE/INSERT/DELETE: nur Admin/PL/buero (HR)
CREATE POLICY IF NOT EXISTS urlaubskontingent_modify_hr
  ON public.urlaubskontingent FOR ALL TO authenticated
  USING (
    is_admin()
    OR EXISTS(SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role IN ('projektleiter','buero'))
  )
  WITH CHECK (
    is_admin()
    OR EXISTS(SELECT 1 FROM public.users WHERE auth_user_id=auth.uid() AND role IN ('projektleiter','buero'))
  );

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: activity_log — append-only (INSERT ok, UPDATE/DELETE deny)
-- ═══════════════════════════════════════════════════════════

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN
    SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='activity_log'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.activity_log', pol.polname);
    RAISE NOTICE 'Dropped open Policy on activity_log: %', pol.polname;
  END LOOP;
END $$;

-- INSERT: für alle authenticated (Client-Pfad — Logging)
CREATE POLICY IF NOT EXISTS activity_log_insert
  ON public.activity_log FOR INSERT TO authenticated
  WITH CHECK (true);

-- SELECT: eigene + Admin
CREATE POLICY IF NOT EXISTS activity_log_select_own_or_admin
  ON public.activity_log FOR SELECT TO authenticated
  USING (
    is_admin()
    OR user_id IN (SELECT username FROM public.users WHERE auth_user_id = auth.uid())
    OR user_id IN (SELECT id::text FROM public.users WHERE auth_user_id = auth.uid())
  );

-- UPDATE: nur Admin (Audit-Trail-Schutz)
CREATE POLICY IF NOT EXISTS activity_log_update_admin
  ON public.activity_log FOR UPDATE TO authenticated
  USING (is_admin()) WITH CHECK (is_admin());

-- DELETE: nur Admin
CREATE POLICY IF NOT EXISTS activity_log_delete_admin
  ON public.activity_log FOR DELETE TO authenticated
  USING (is_admin());

-- ═══════════════════════════════════════════════════════════
-- BLOCK 5: Client-Insert-Pfade VERIFIZIEREN (sollen offen bleiben)
-- ═══════════════════════════════════════════════════════════
-- Diese Tables sollen für authenticated INSERTen erlaubt sein.
-- Falls eine /ALL-Policy vorhanden ist, NICHT removen — sondern PRÜFEN
-- dass INSERT-Path nicht bricht.

-- notifications: bereits via Sprint 53 v3.9.53 RLS-Skript abgedeckt
-- photos: Client kann eigene Fotos POSTen
-- forms: Client kann eigene Forms POSTen
-- as_kommentare: Client kann eigene Kommentare POSTen
-- juprowa_log: Client kann eigene Log-Einträge POSTen

-- DIESE Tables NICHT anfassen — nur Spot-Check ob Policies existieren:
-- SELECT tablename, polname, cmd FROM pg_policies
--  WHERE schemaname='public'
--    AND tablename IN ('notifications','photos','forms','as_kommentare','juprowa_log')
--    AND cmd IN ('INSERT','ALL')
--  ORDER BY tablename;

-- ═══════════════════════════════════════════════════════════
-- VERIFIKATION nach Run
-- ═══════════════════════════════════════════════════════════
-- 1. Pro Tabelle alle Policies anschauen:
--    SELECT tablename, polname, cmd, roles, qual, with_check
--    FROM pg_policies WHERE schemaname='public'
--    AND tablename IN ('users','system_config','urlaubskontingent','activity_log')
--    ORDER BY tablename, cmd;
--
-- 2. SOLL nach Run:
--    users:               4 Policies (select-auth, update-admin, update-self-no-role, insert-admin, delete-admin)
--    system_config:       4 Policies (select-auth, insert/update/delete-admin)
--    urlaubskontingent:   2 Policies (select-own-or-admin, modify-hr)
--    activity_log:        4 Policies (insert-auth, select-own-or-admin, update-admin, delete-admin)
--
-- 3. App-Live-Smoke pro Rolle nach Run:
--    - Login als monteur (barger): kann eigene users-Row updaten OHNE role-Change ✓
--    - Login als monteur: PATCH /users {role:'admin'} → 403 ✓
--    - Login als monteur: PATCH /system_config → 403 ✓
--    - Login als monteur: PATCH /activity_log → 403 ✓ (UPDATE blocked)
--    - Login als monteur: POST /activity_log → 201 ✓ (INSERT ok)
--    - Login als buero: PATCH /urlaubskontingent → 200 ✓
--    - Login als admin: alles ✓

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK (manuell, NICHT automatisch — Reihenfolge wichtig!)
-- ═══════════════════════════════════════════════════════════
/*
-- Reset auf "alles offen" (vor-Hardening-Stand):
DROP POLICY IF EXISTS users_update_admin ON public.users;
DROP POLICY IF EXISTS users_update_self_no_role_change ON public.users;
DROP POLICY IF EXISTS users_insert_admin ON public.users;
DROP POLICY IF EXISTS users_delete_admin ON public.users;
CREATE POLICY users_all_open ON public.users FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS system_config_select ON public.system_config;
DROP POLICY IF EXISTS system_config_modify_admin ON public.system_config;
DROP POLICY IF EXISTS system_config_update_admin ON public.system_config;
DROP POLICY IF EXISTS system_config_delete_admin ON public.system_config;
CREATE POLICY system_config_all_open ON public.system_config FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS urlaubskontingent_select_own_or_admin ON public.urlaubskontingent;
DROP POLICY IF EXISTS urlaubskontingent_modify_hr ON public.urlaubskontingent;
CREATE POLICY urlaubskontingent_all_open ON public.urlaubskontingent FOR ALL TO authenticated USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS activity_log_insert ON public.activity_log;
DROP POLICY IF EXISTS activity_log_select_own_or_admin ON public.activity_log;
DROP POLICY IF EXISTS activity_log_update_admin ON public.activity_log;
DROP POLICY IF EXISTS activity_log_delete_admin ON public.activity_log;
CREATE POLICY activity_log_all_open ON public.activity_log FOR ALL TO authenticated USING (true) WITH CHECK (true);
*/
