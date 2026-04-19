-- ============================================================
-- RLS-Snapshot v3.8 · Block 5
-- Sebastian führt im Supabase SQL-Editor aus, Output kopieren nach sql/RLS_SNAPSHOT_v3.8.md
-- ============================================================

-- 1. Alle Policies in public.*
SELECT
  tablename,
  policyname,
  cmd,
  array_to_string(roles, ',') AS roles,
  qual,
  with_check
FROM pg_policies
WHERE schemaname='public'
ORDER BY tablename, cmd, policyname;

-- 2. RLS-Flag pro Tabelle (rowsecurity = RLS aktiv, forcerowsecurity = auch für owner)
SELECT
  tablename,
  rowsecurity AS rls_enabled,
  forcerowsecurity AS rls_forced
FROM pg_tables
WHERE schemaname='public'
ORDER BY tablename;

-- 3. Tabellen OHNE Policy aber MIT rls_enabled (= nichts lesbar) → finden
SELECT t.tablename
FROM pg_tables t
LEFT JOIN (
  SELECT DISTINCT tablename FROM pg_policies WHERE schemaname='public'
) p ON p.tablename = t.tablename
WHERE t.schemaname='public'
  AND t.rowsecurity = true
  AND p.tablename IS NULL
ORDER BY t.tablename;

-- 4. Tabellen OHNE rls_enabled (= alles lesbar für anon/authenticated) → potentiell kritisch
SELECT t.tablename,
  CASE WHEN t.tablename IN ('projects','workers') THEN 'ggf. öffentlich ok'
       ELSE 'PRÜFEN' END AS bewertung
FROM pg_tables t
WHERE t.schemaname='public'
  AND t.rowsecurity = false
ORDER BY t.tablename;

-- 5. Helper-Funktionen existieren (B-007)
SELECT proname, pronargs
FROM pg_proc p
JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public'
  AND p.proname IN ('current_monteur_id','current_user_role','current_user_pk','is_staff')
ORDER BY proname;
-- Erwartet: 4 rows
