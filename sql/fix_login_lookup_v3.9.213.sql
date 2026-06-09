-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ═══════════════════════════════════════════════════════════════════════════
-- AUFGABE #2 — login_lookup: nur sichere Spalten projizieren (kein password_hash)
-- Datei: sql/fix_login_lookup_v3.9.213.sql   |   Rollback: *_ROLLBACK.sql
-- ═══════════════════════════════════════════════════════════════════════════
--
-- PROBLEM (Repo-belegt):
--   Aktueller login_lookup-Body = `to_jsonb(u.*)` → liefert die KOMPLETTE users-Row
--   an den anon-Aufrufer aus, inkl. password_hash (bcrypt-Hash = offline knackbar)
--   und email/permissions. login_lookup ist SECURITY DEFINER (umgeht RLS) und hat
--   EXECUTE-Grant für anon (Login ist anon). → password_hash leakt an anon.
--
-- FRONTEND-ZUSTAND (index.html, Commit fa9d37a = v3.9.213, CC-Cross-Check):
--   API.login (Z2207-2257) liest aus dem login_lookup-Result NUR noch:
--     user.id        (Z2215, 2248, 2249, 2252)
--     user.locked    (Z2216)
--     user.email     (Z2221, 2225 → email)
--     user.name      (Z2252, Fallback)
--     user.role      (Z2222, 2252 Fallback)
--     user.username  (Z2252 Fallback)
--   Der bcrypt-Fallback gegen login_lookup.password_hash wurde ENTFERNT (Z2226-2230).
--   Das Vollprofil (permissions/monteur_id/perms_override/login_count) wird NACH dem
--   GoTrue-Login per AUTHENTIFIZIERTEM, RLS-geschütztem _sbGetUsersSafe nachgeladen
--   (Z2240-2252). → login_lookup MUSS diese Felder NICHT mehr ausliefern.
--   => Sichere Projektion: id, auth_user_id, username, name, email, role, active, locked.
--      (auth_user_id additiv aufgenommen — unschädlich, hilft Defensiv-Pfaden; KEIN
--       password_hash, KEIN permissions, KEIN to_jsonb(u.*).)
--
-- ─────────────────────────────────────────────────────────────────────────
-- 🔴 PFLICHT-CAPTURE VOR APPLY (load-bearing — NICHT raten):
--   Die WHERE/Match-Logik (username-Match, Case-Insensitivity, ggf. Trim/active-
--   Filter) ist im Repo NICHT belegt. Diese Datei ist eine REKONSTRUKTION der
--   PROJEKTION; die LOOKUP-LOGIK MUSS aus der Live-Definition übernommen werden.
--
--   1) Live-Definition ziehen:
--        SELECT pg_get_functiondef('public.login_lookup(text)'::regprocedure);
--   2) Die EXAKTE WHERE-Klausel aus der Live-Def in den unten markierten Block
--      ("<<< CAPTURE >>>") übernehmen (ersetzt den rekonstruierten Platzhalter).
--   3) Attribute gegen Live verifizieren (müssen erhalten bleiben):
--        SELECT proname, prosecdef, provolatile, proconfig
--        FROM pg_proc
--        WHERE proname='login_lookup'
--          AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public');
--        → prosecdef='t' (SECURITY DEFINER), provolatile='s' (STABLE),
--          proconfig enthält 'search_path=public, pg_temp'.
--   4) EXECUTE-Grants gegen Live verifizieren (anon MUSS erhalten bleiben):
--        SELECT grantee, privilege_type FROM information_schema.routine_privileges
--        WHERE routine_name='login_lookup' AND routine_schema='public';
--
--   Falls die Live-Def zusätzliche Bind-Felder/CTEs/Joins hat, die das Frontend
--   NICHT konsumiert: NICHT projizieren (nur die 8 sicheren Felder ausgeben).
-- ─────────────────────────────────────────────────────────────────────────

-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK 1: Funktion neu definieren — sichere Projektion via jsonb_build_object
-- ═══════════════════════════════════════════════════════════════════════════
-- Signatur unverändert: public.login_lookup(p_username text) RETURNS jsonb.
-- CREATE OR REPLACE behält bestehende Grants bei (kein DROP → anon-EXECUTE bleibt).

CREATE OR REPLACE FUNCTION public.login_lookup(p_username text)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT jsonb_build_object(
    'id',           u.id,
    'auth_user_id', u.auth_user_id,
    'username',     u.username,
    'name',         u.name,
    'email',        u.email,
    'role',         u.role,
    'active',       u.active,
    'locked',       u.locked
  )
  FROM public.users u
  -- ╔═══════════════════════════════════════════════════════════════════════╗
  -- ║ <<< CAPTURE >>> WHERE-Klausel aus Live-Def übernehmen (REKONSTRUKTION) ║
  -- ║ Platzhalter unten ist die WAHRSCHEINLICHE Form (case-insensitiver      ║
  -- ║ username-Match). VOR APPLY gegen pg_get_functiondef() verifizieren     ║
  -- ║ und exakt ersetzen.                                                    ║
  -- ╚═══════════════════════════════════════════════════════════════════════╝
  WHERE lower(u.username) = lower(p_username)
  LIMIT 1;
$$;

-- Idempotenter Grant: anon-EXECUTE explizit sicherstellen (Login ist anon).
-- (CREATE OR REPLACE erhält Grants ohnehin; dieser GRANT ist defensiv-idempotent.)
GRANT EXECUTE ON FUNCTION public.login_lookup(text) TO anon;

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFY (nach Apply, vor 10-User-Smoke):
-- ═══════════════════════════════════════════════════════════════════════════
-- 1. Projektion enthält KEIN password_hash (als anon ausführen):
--      curl -X POST 'https://jiggujpruejkaomgxarp.supabase.co/rest/v1/rpc/login_lookup' \
--        -H 'apikey: <ANON_KEY>' -H 'Content-Type: application/json' \
--        -d '{"p_username":"barger"}'
--      → erwartet: 200 + JSON-Objekt mit GENAU den Keys
--        {id, auth_user_id, username, name, email, role, active, locked}
--      → MUSS sein: KEIN "password_hash", KEIN "permissions".
--
-- 2. Attribute erhalten:
--      SELECT prosecdef, provolatile, proconfig FROM pg_proc
--      WHERE proname='login_lookup'
--        AND pronamespace=(SELECT oid FROM pg_namespace WHERE nspname='public');
--      → prosecdef=t, provolatile=s, proconfig={search_path=public,pg_temp}
--
-- 3. anon-EXECUTE-Grant vorhanden:
--      SELECT grantee, privilege_type FROM information_schema.routine_privileges
--      WHERE routine_name='login_lookup' AND routine_schema='public';
--      → 'anon' / 'EXECUTE' MUSS gelistet sein.
--
-- 4. 10-User Token-Grant Smoke (ALLE müssen 200 + Dashboard):
--      barger / cracana / riedmann / kiener (monteure)
--      paschinger (techniker)
--      pinger / schmid (projektleiter)
--      lindhuber / schober (buero)
--      sebastian (admin)
--      → Login = GoTrue-Token-Grant; Profil-Nachladung via _sbGetUsersSafe.
--      Bricht ≥1 User → INSTANT ROLLBACK via fix_login_lookup_v3.9.213_ROLLBACK.sql.
--
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK: siehe sql/fix_login_lookup_v3.9.213_ROLLBACK.sql
-- ═══════════════════════════════════════════════════════════════════════════
