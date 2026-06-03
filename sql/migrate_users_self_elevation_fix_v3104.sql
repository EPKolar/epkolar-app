-- ═══════════════════════════════════════════════════════════
-- v3.10.4 P0 KRITISCH — users Self-Elevation Fix (Sebastian-Spec 2026-06-03)
-- ═══════════════════════════════════════════════════════════
--
-- BEFUND (Chat-Claude live mit barger-Token, NO-OP-Probe, kein Schaden):
--   - Monteur barger kann role auf SEINER Zeile setzen (Status 200, 1 row) → Self-Elevation
--   - Monteur kann ADMIN-Zeile patchen (Status 200, 1 row) → Konten-Übernahme/Sperrung
--   - Ursache: Policy `authenticated_write_users` (cmd=ALL, qual=true, roles=authenticated)
--
-- FIX (Sebastian-Spec):
--   1. authenticated_write_users (ALL qual=true) ERSETZEN durch differenzierte Policies:
--      - SELECT: eingeloggt = eigene Zeile + (admin/PL) alle
--      - UPDATE eigene: nur unkritische Felder (NICHT role/locked/perms/monteur_id/auth_user_id)
--      - UPDATE fremde + role/locked: NUR admin (ggf. PL)
--      - INSERT/DELETE: nur admin
--   2. Self-Elevation MUSS nach Apply 403/0-rows geben
--   3. App-Funktionen NICHT brechen: login_count/last_login Self-Update, +Neuer Benutzer (Edge-Function)
--
-- LIVE-APP-Pfade die users.UPDATE machen (Code-Analyse):
--   Z2198 _sbPatch("users", user.id, {last_login, login_count})  ← User-JWT eigener User
--   Z7321 SQ.push /api/users POST {id, username, password, name, email, role, monteurId} ← Admin-Create-User
--   Z7341 toggleActive {active}  ← Admin-only (Code-Side-Guard)
--   Z7342 toggleLock {locked}    ← Admin-only (Code-Side-Guard)
--   Z7343 setRole {role}         ← Admin-only (Code-Side-Guard)
--   Z7344 togglePermOverride {permsOverride}  ← Admin-only
--   Z7356 delUser DELETE         ← Admin-only

-- ═══════════════════════════════════════════════════════════
-- VORAUSSETZUNG: helper-Function is_admin() existiert (Sprint 53 v3.9.53)
-- ═══════════════════════════════════════════════════════════

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname='is_admin' AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public')) THEN
    RAISE EXCEPTION 'is_admin() Helper fehlt — zuerst migrate_notifications_rls_v3953.sql ausführen';
  END IF;
END $$;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Snapshot vorhandener Policies (Audit + Rollback-Quelle)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3104 (
  ts timestamptz DEFAULT now(),
  tablename text, polname text, roles text[], cmd text,
  qual text, with_check text
);

INSERT INTO public._rls_snapshot_v3104 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename='users';

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: P0 — authenticated_write_users entfernen
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS authenticated_write_users ON public.users;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: Helper-Function is_admin_or_pl() (Admin oder Projektleiter)
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.is_admin_or_pl() RETURNS boolean AS $$
  SELECT EXISTS(
    SELECT 1 FROM public.users
    WHERE auth_user_id = auth.uid()
      AND role IN ('admin','projektleiter')
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: SELECT — eigene Zeile + Admin/PL alle
-- (authenticated_read_users-Policy schon vorhanden lt. Chat-Claude;
--  hier nur Defense-in-Depth falls noch nicht gesetzt)
-- ═══════════════════════════════════════════════════════════

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='users' AND cmd='SELECT' AND 'authenticated'::text = ANY(roles)) THEN
    EXECUTE 'CREATE POLICY users_select_self_or_admin ON public.users FOR SELECT TO authenticated USING (is_admin_or_pl() OR auth_user_id = auth.uid())';
    RAISE NOTICE 'Created users_select_self_or_admin';
  END IF;
END $$;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 5: UPDATE eigene Zeile — nur unkritische Felder
-- ═══════════════════════════════════════════════════════════
-- Erlaubte Self-Updates: last_login, login_count, phone, avatar_url, theme_pref, lang_pref
-- VERBOTEN (Trigger blockt): role, locked, perms_override, monteur_id, auth_user_id, username, email,
--                            password_hash, active
--
-- Da PostgreSQL keine column-level UPDATE in RLS-Policies hat, verwenden wir Trigger zur Spalten-Validierung.

CREATE POLICY users_update_self_safe_columns
  ON public.users FOR UPDATE TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (
    auth_user_id = auth.uid()
    -- WICHTIG: kritische Felder dürfen sich nicht ändern (Vergleich neuer Wert = aktueller Wert):
    AND role = (SELECT role FROM public.users WHERE auth_user_id = auth.uid())
    AND COALESCE(locked, false) = COALESCE((SELECT locked FROM public.users WHERE auth_user_id = auth.uid()), false)
    AND COALESCE(active, 1) = COALESCE((SELECT active FROM public.users WHERE auth_user_id = auth.uid()), 1)
    AND COALESCE(monteur_id, '') = COALESCE((SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid()), '')
    AND COALESCE(auth_user_id, gen_random_uuid()) = (SELECT auth_user_id FROM public.users WHERE auth_user_id = auth.uid())
    AND COALESCE(username, '') = COALESCE((SELECT username FROM public.users WHERE auth_user_id = auth.uid()), '')
    AND COALESCE(email, '') = COALESCE((SELECT email FROM public.users WHERE auth_user_id = auth.uid()), '')
    -- perms_override: kann text oder json sein, nur via Admin änderbar
    AND COALESCE(perms_override::text, '') = COALESCE((SELECT perms_override::text FROM public.users WHERE auth_user_id = auth.uid()), '')
    -- password_hash bewusst NICHT in WITH CHECK (Server-Side bcrypt-Update via login darf hash NICHT ändern,
    --   App ruft kein direktes password_hash-Update auf — alle pw-changes über admin_reset_password RPC)
  );

-- ═══════════════════════════════════════════════════════════
-- BLOCK 6: UPDATE fremde Zeilen + kritische Felder — nur Admin
-- ═══════════════════════════════════════════════════════════

CREATE POLICY users_update_admin
  ON public.users FOR UPDATE TO authenticated
  USING (is_admin())
  WITH CHECK (is_admin());

-- ═══════════════════════════════════════════════════════════
-- BLOCK 7: INSERT — nur Admin (via Edge-Function service_role bleibt unverändert offen)
-- ═══════════════════════════════════════════════════════════

CREATE POLICY users_insert_admin
  ON public.users FOR INSERT TO authenticated
  WITH CHECK (is_admin());

-- ═══════════════════════════════════════════════════════════
-- BLOCK 8: DELETE — nur Admin
-- ═══════════════════════════════════════════════════════════

CREATE POLICY users_delete_admin
  ON public.users FOR DELETE TO authenticated
  USING (is_admin());

-- ═══════════════════════════════════════════════════════════
-- BLOCK 9: REVOKE password_hash + perms_override für Authenticated (Defense)
-- ═══════════════════════════════════════════════════════════
-- column-Grant für SELECT auf authenticated (kein password_hash, kein perms_override):
-- HINWEIS: REVOKE ist additiv zu RLS — wenn SELECT-Policy passt, sind Spalten via Column-Grants begrenzt.

REVOKE SELECT (password_hash) ON public.users FROM authenticated;
REVOKE SELECT (password_hash) ON public.users FROM anon;
-- perms_override-Lesen: bleibt für authenticated erlaubt (App liest es für UI-Permission-Checks)

-- ═══════════════════════════════════════════════════════════
-- VERIFY (nach Apply, vor Smoke)
-- ═══════════════════════════════════════════════════════════
-- 1. Policies auf users:
--    SELECT polname, cmd, qual, with_check FROM pg_policies
--    WHERE schemaname='public' AND tablename='users'
--    ORDER BY cmd, polname;
--    → erwartet: users_select_*, users_update_self_safe_columns, users_update_admin,
--      users_insert_admin, users_delete_admin (KEIN authenticated_write_users mehr)
--
-- 2. Self-Elevation-Test mit barger-Token:
--    PATCH /rest/v1/users?id=eq.<barger-uuid> body:{role:'admin'}
--    → erwartet: 403 ODER 0 rows updated
--
-- 3. Cross-User-PATCH mit barger-Token:
--    PATCH /rest/v1/users?id=eq.<admin-uuid> body:{role:'monteur'}
--    → erwartet: 403 ODER 0 rows updated
--
-- 4. Self-NO-OP-Update mit barger-Token (legitime Felder):
--    PATCH /rest/v1/users?id=eq.<barger-uuid> body:{login_count:99}
--    → erwartet: 200, 1 row (legitime Self-Update)
--
-- 5. Admin-PATCH mit admin-Token:
--    PATCH /rest/v1/users?id=eq.<barger-uuid> body:{role:'monteur'}
--    → erwartet: 200, 1 row (Admin kann verwalten)
--
-- 6. App-Login wiederholen — Z2198 last_login + login_count müssen geschrieben werden
--    (sollte über users_update_self_safe_columns OK sein)

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK siehe migrate_users_self_elevation_fix_v3104_ROLLBACK.sql
-- ═══════════════════════════════════════════════════════════
