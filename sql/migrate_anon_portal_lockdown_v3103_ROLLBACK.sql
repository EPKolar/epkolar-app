-- ═══════════════════════════════════════════════════════════
-- v3.10.3 ROLLBACK — anon-Portal-Lockdown rückgängig
-- ═══════════════════════════════════════════════════════════
--
-- WANN AUSFÜHREN:
--   Wenn nach migrate_anon_portal_lockdown_v3103.sql der Portal-Zugriff bricht
--   (KundenPortal lädt nicht, "Code ungültig", oder Mängel/Dokumente fehlen) → SOFORT.
--
-- WIE:
--   Im Supabase SQL Editor einfügen → Run.
--   Portal-Smoke wiederholen (z.B. Code PEZZ1234 → KundenPortal lädt).

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Neue Portal-Policies entfernen
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS projects_anon_select_portal ON public.projects;
DROP POLICY IF EXISTS plans_anon_select_portal ON public.plans;
DROP POLICY IF EXISTS project_documents_anon_select_portal ON public.project_documents;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: Original-Policies exakt wiederherstellen
-- ═══════════════════════════════════════════════════════════

CREATE POLICY projects_anon_select ON public.projects
  FOR SELECT TO public USING (auth.role() = 'anon');

CREATE POLICY plans_anon_select ON public.plans
  FOR SELECT TO public USING (auth.role() = 'anon');

CREATE POLICY project_documents_anon_select ON public.project_documents
  FOR SELECT TO public USING (auth.role() = 'anon');

-- ═══════════════════════════════════════════════════════════
-- VERIFY ROLLBACK
-- ═══════════════════════════════════════════════════════════
-- 1. Policies wiederhergestellt:
--    SELECT tablename, polname, cmd, qual FROM pg_policies
--    WHERE schemaname='public' AND tablename IN ('projects','plans','project_documents')
--      AND polname LIKE '%_anon_select%';
--    → erwartet: projects_anon_select, plans_anon_select, project_documents_anon_select
--      mit qual = "(auth.role() = 'anon'::text)"
--
-- 2. Portal-Test: KundenPortal mit Code → lädt wieder
--
-- 3. Anon liest wieder alle Projekte (vorheriger Stand)

-- ═══════════════════════════════════════════════════════════
-- CLEANUP (OPTIONAL, nach erfolgreichem Rollback):
-- DROP TABLE IF EXISTS public._rls_snapshot_v3103;
-- ═══════════════════════════════════════════════════════════
