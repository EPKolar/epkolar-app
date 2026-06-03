-- ═══════════════════════════════════════════════════════════
-- v3.9.97 VORZIEHEN — anon SELECT auf users entfernen
-- Sebastian-Spec 2026-06-03: vor Phase-3-Hardening, sicher, kein Client-Pfad-Bruch
-- ═══════════════════════════════════════════════════════════
--
-- KONTEXT: Anon-Key GET /users → 200 + Daten (Hashes/Emails sichtbar) — bestätigt 2026-06-02
-- Risiko: KRITISCH — Email-Liste + Hash-Listen exposed an Angreifer mit anon-Key
-- Fix: anon (PUBLIC) verliert SELECT-Zugriff auf users. Login-Lookup läuft separat.
--
-- WIRD NICHT BRECHEN:
-- - Authenticated User lesen weiter via eigenem JWT-Token (separate Policy für `authenticated`)
-- - Client-Insert-Pfade (notifications/photos/forms) unverändert
-- - Login-Username-Lookup läuft über RPC (z.B. login_lookup-Function mit SECURITY DEFINER)
--
-- WICHTIG: Falls Login aktuell DIREKT GET /users?username=eq.X via anon macht,
-- MUSS vorher ein SECURITY-DEFINER-Function-Wrapper existieren.

-- ── 1. Diagnose: bestehende Policies anschauen ─────────
-- Run zuerst zur Verifikation:
--   SELECT polname, roles, cmd, qual
--   FROM pg_policies WHERE tablename='users' AND schemaname='public';
-- Erwartet: zumindest 1 Policy mit roles enthält 'anon' oder 'public'

-- ── 2. anon-SELECT-Policy entfernen ─────────────────────
-- Suche alle Policies auf public.users mit cmd='r' (SELECT) UND offenem qual=true:
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN
    SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='users'
      AND cmd='SELECT'
      AND (qual='true' OR qual IS NULL OR qual = '(true)')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.users', pol.polname);
    RAISE NOTICE 'Dropped open SELECT-Policy: %', pol.polname;
  END LOOP;
END $$;

-- ── 3. Neue restriktive SELECT-Policy ───────────────────
-- Authenticated User dürfen lesen: eigene Row + (wenn admin/PL/buero) alle anderen
-- WICHTIG: helper-function is_admin() muss existieren (aus Sprint 53 v3.9.53)

CREATE POLICY IF NOT EXISTS users_select_authenticated
  ON public.users FOR SELECT TO authenticated
  USING (
    is_admin()
    OR auth_user_id = auth.uid()
    OR EXISTS(
      SELECT 1 FROM public.users
      WHERE auth_user_id = auth.uid()
        AND role IN ('projektleiter','buero','obermonteur')
    )
  );

-- ── 4. ANON bekommt EXPLICIT NICHT-erlaubt ──────────────
-- Default deny via RLS (kein Policy für 'anon' Rolle = deny)
-- Aber zur Sicherheit: REVOKE jeglicher Grants

REVOKE ALL ON public.users FROM anon;
REVOKE ALL ON public.users FROM PUBLIC;
GRANT SELECT ON public.users TO authenticated;

-- ── 5. Login-Lookup SECURITY-DEFINER-Function ──────────
-- Falls Login (B020-A login_lookup RPC) DIREKT GET /users macht,
-- MUSS Sebastian VOR diesem Skript-Run die Lookup-RPC anlegen:

-- BEISPIEL (kommentiert, Sebastian-Action falls noch nicht existent):
/*
CREATE OR REPLACE FUNCTION public.login_username_lookup(p_username text)
RETURNS TABLE(user_id text, email text, auth_user_id uuid) AS $$
BEGIN
  RETURN QUERY
  SELECT u.id::text, u.email::text, u.auth_user_id
  FROM public.users u
  WHERE u.username = p_username AND u.active = 1
  LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

GRANT EXECUTE ON FUNCTION public.login_username_lookup(text) TO anon, authenticated;
*/

-- ── 6. Verify ──────────────────────────────────────────
-- Nach Run prüfen:
-- SELECT polname, roles, cmd FROM pg_policies WHERE tablename='users' AND schemaname='public';
-- Sollte zeigen: nur 'authenticated' role in Policies, KEIN 'anon'.

-- Anschließend: Live-Test via app — Login muss noch funktionieren!
-- Falls Login bricht: SELECT-Policy für anon mit minimaler Spalten-Maske wiederherstellen:
/*
CREATE POLICY users_select_anon_login ON public.users FOR SELECT TO anon
  USING (true);
-- + View `users_login_safe` mit nur username+id+auth_user_id (KEIN email/hash)
-- + App-Code GET /users_login_safe statt /users
*/

-- ROLLBACK:
-- DROP POLICY IF EXISTS users_select_authenticated ON public.users;
-- CREATE POLICY users_select_all ON public.users FOR SELECT USING (true);
-- GRANT SELECT ON public.users TO anon;
