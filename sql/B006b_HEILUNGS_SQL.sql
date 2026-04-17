-- =====================================================================
-- B-006b HEILUNGS-SQL — Nachzieh-Fix für RLS-Tabellen ohne Policies
-- Ausführung: Supabase Dashboard → SQL Editor → paste → Run
-- Idempotent (kann mehrfach laufen)
--
-- Problem: Nach B-006-Teilfix wurde RLS aktiviert, aber 3/8 Tabellen
-- haben keine authenticated_read Policy → Admin sieht 0 Rows.
-- Fix: Für alle Base-Tabellen authenticated_read + authenticated_write
-- Policy hinzufügen (USING true, da Business-Logik-Filterung client-side
-- bzw. für Monteur-sensitive Daten via B-007 separat enger gefasst wird).
-- =====================================================================

-- View entfernen (falls vorhanden — früher für supplier_articles_public benutzt)
DROP VIEW IF EXISTS public.supplier_articles_public;

-- RLS überall sicher aktivieren (idempotent) + authenticated-Policies setzen
DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY[
    'users','projects','supplier_articles','supplier_configs',
    'material_items','material_orders','bautagebuch','project_documents',
    'fahrzeug_buchungen','activity_log','as_vorlagen','juprowa_log',
    'system_config','fahrzeuge','werkzeuge','monteure','abs',
    'project_plans','checklisten','photos'
  ] LOOP
    BEGIN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
      EXECUTE format('DROP POLICY IF EXISTS "anon_read" ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS "Enable read access for all users" ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS "authenticated_read_%s" ON public.%I', t, t);
      EXECUTE format('DROP POLICY IF EXISTS "authenticated_write_%s" ON public.%I', t, t);
      EXECUTE format('CREATE POLICY "authenticated_read_%s" ON public.%I FOR SELECT TO authenticated USING (true)', t, t);
      EXECUTE format('CREATE POLICY "authenticated_write_%s" ON public.%I FOR ALL TO authenticated USING (true) WITH CHECK (true)', t, t);
    EXCEPTION WHEN undefined_table THEN NULL; END;
  END LOOP;
END $$;

-- =====================================================================
-- Verifikation
-- =====================================================================

-- Anon sollte weiterhin 0 Rows sehen auf sensiblen Tabellen
-- (muss separat im Incognito-Tab getestet werden)

-- Authenticated-Policies-Count pro Tabelle
SELECT tablename, COUNT(*) AS policy_count, bool_or(rowsecurity) AS rls_on
FROM pg_policies p
RIGHT JOIN pg_tables t USING (tablename)
WHERE t.schemaname='public'
  AND t.tablename IN (
    'users','projects','supplier_articles','supplier_configs',
    'material_items','material_orders','bautagebuch','project_documents',
    'fahrzeug_buchungen','activity_log','as_vorlagen','juprowa_log',
    'system_config','fahrzeuge','werkzeuge','monteure','abs',
    'project_plans','checklisten','photos'
  )
GROUP BY tablename
ORDER BY tablename;
-- Erwartet: jede Tabelle ≥ 2 Policies (authenticated_read + authenticated_write)
