-- ============================================================
-- M-2 photos RLS Diagnose · v3.7.2 Block 1
-- Sebastian führt im Supabase SQL-Editor aus. Output → HANDOFF_NACHT_v3.8.md
-- ============================================================

-- 1. Aktuelle Policies auf photos
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE tablename='photos'
ORDER BY policyname;

-- 2. RLS aktiv? Wenn rowsecurity=false → Tabelle ist offen (Katastrophe).
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled,
  forcerowsecurity AS rls_forced
FROM pg_tables
WHERE tablename='photos';

-- 3. Schema
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name='photos'
ORDER BY ordinal_position;

-- 4. Count-Probe pro worker_id (wenn >0 Fotos pro MA)
SELECT count(*) AS total_photos FROM public.photos;
SELECT worker_id, count(*) AS n FROM public.photos GROUP BY worker_id ORDER BY n DESC LIMIT 20;

-- 5. Anon-Access-Test (nur wenn anon in roles der Policies drin ist, sollte FAIL sein)
-- SET LOCAL ROLE anon;
-- SELECT count(*) FROM public.photos;  -- erwartet: 0 ODER error
-- RESET ROLE;

-- Ergebnis-Entscheidungsmatrix:
-- A) rls_enabled=false        → **KRITISCH**: Variante A Fix (enable+create)
-- B) rls_enabled=true, 0 policies → **KRITISCH**: Nichts lesbar aber auch nichts schreibbar (bricht App). Variante A Fix.
-- C) rls_enabled=true, policies TO public/anon → **KRITISCH**: Leak. Variante B Fix (DROP+CREATE).
-- D) rls_enabled=true, policies TO authenticated mit Rolle-Filter  → ok (MATCH)
-- E) Policies existieren aber Matrix-Doku falsch → Variante C (nur MD update)
