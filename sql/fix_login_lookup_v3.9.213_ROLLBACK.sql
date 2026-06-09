-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK für sql/fix_login_lookup_v3.9.213.sql
-- Stellt den VORHERIGEN login_lookup-Body wieder her.
-- ═══════════════════════════════════════════════════════════════════════════
--
-- 🔴 PFLICHT-CAPTURE (load-bearing): Der untenstehende Body ist eine
--    REKONSTRUKTION (to_jsonb(u.*)-Form laut Repo-Befund). Die EXAKTE WHERE-
--    Klausel UND der exakte Original-Body sind im Repo NICHT belegt.
--    VOR jedem Apply der FIX-Datei ZUERST die Live-Definition als Snapshot ziehen
--    und HIER eintragen, damit ein echtes 1:1-Rollback möglich ist:
--
--      SELECT pg_get_functiondef('public.login_lookup(text)'::regprocedure);
--
--    Den so erhaltenen CREATE-OR-REPLACE-Block UNVERÄNDERT in diese Datei kopieren
--    (ersetzt den rekonstruierten Block unten). Attribute STABLE / SECURITY DEFINER
--    / SET search_path=public,pg_temp und den anon-EXECUTE-Grant MITNEHMEN.
--
-- ═══════════════════════════════════════════════════════════════════════════
-- REKONSTRUKTION — vor Apply gegen Live (Snapshot aus pg_get_functiondef) verifizieren
-- ═══════════════════════════════════════════════════════════════════════════
-- ⚠️ ACHTUNG: Dieser Body stellt den HASH-LEAK (to_jsonb(u.*)) WIEDER HER.
--    Nur als Notfall-Rollback nutzen, wenn der Fix den Login bricht; danach
--    Ursache klären und Fix erneut (mit korrekt gecaptureter WHERE-Klausel) anwenden.

CREATE OR REPLACE FUNCTION public.login_lookup(p_username text)
RETURNS jsonb
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT to_jsonb(u.*)
  FROM public.users u
  -- <<< CAPTURE >>> EXAKTE Original-WHERE-Klausel aus Live-Snapshot einsetzen.
  --     Platzhalter (rekonstruiert) — vor Apply ersetzen:
  WHERE lower(u.username) = lower(p_username)
  LIMIT 1;
$$;

GRANT EXECUTE ON FUNCTION public.login_lookup(text) TO anon;

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFY (nach Rollback):
--   1. login_lookup gibt wieder die volle Row aus (alter Zustand):
--        curl -X POST '.../rpc/login_lookup' -H 'apikey: <ANON_KEY>' \
--          -H 'Content-Type: application/json' -d '{"p_username":"barger"}'
--        → 200 + Objekt (alter Umfang).
--   2. 10-User Token-Grant Smoke wie in der FIX-Datei (alle 200).
--   3. prosecdef=t, provolatile=s, proconfig={search_path=public,pg_temp}.
-- ═══════════════════════════════════════════════════════════════════════════
