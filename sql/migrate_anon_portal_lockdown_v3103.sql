-- ═══════════════════════════════════════════════════════════
-- v3.10.3 anon-Portal-Lockdown (Sebastian-Spec 2026-06-03)
-- ═══════════════════════════════════════════════════════════
--
-- PORTAL-BEFUND (CC Code-Analyse Z3998-4068 index.html):
--   AKTIV — PortalEntry-Button auf Login-Screen, KundenPortal-Component existiert.
--   Anon-Code-Pfad:
--     1. PortalEntry.tryPortal Z4007:
--        _sbGet("projects", "portal_code=not.is.null&portal_code=neq.")
--        → anon fetcht ALLE Projekte mit Portal-Code (nicht nur 1)
--     2. Z4008 Client-Match:
--        projects.find(p => p.portalCode.toUpperCase() === code.trim().toUpperCase())
--     3. KundenPortal Z4045-4066 nach Match-Anon-Reads:
--        - defects (project_id=eq.X)
--        - project_documents (project_id=eq.X & kunde_freigabe=eq.1)
--        - plans (project_id=eq.X) + clientseitig filter kunde_freigabe
--        - checklists (project_id=eq.X)
--
-- AKTUELL ZU OFFEN:
--   projects_anon_select          qual=(auth.role()='anon') → anon liest ALLE Projekte
--   plans_anon_select             qual=(auth.role()='anon') → anon liest ALLE Pläne
--   project_documents_anon_select qual=(auth.role()='anon') → anon liest ALLE Dokumente
--
-- GEWÄHLTE VARIANTE: PORTAL AKTIV mit pragmatischer Eingrenzung
--   - projects:          nur Rows mit portal_code SET sichtbar
--   - plans:             nur Pläne von Portal-Projekten + kunde_freigabe=true
--   - project_documents: nur Docs von Portal-Projekten + kunde_freigabe=true
--
-- STRENGER WÄRE: custom header x-portal-code per Frontend-Change.
-- Aktueller Frontend-Code schickt keinen header → Pragmatic-Variante OK.
-- Future-Sprint: Frontend umbauen für header-based Policy.
--
-- ZWINGEND VOR APPLY:
--   - Bestätigen dass aktuell aktive Portal-Projekte funktionieren (PEZZ1234, GED2024)
--   - Smoke-Plan bereit:
--     a) anon /projects → sieht NUR Projekte mit portal_code (~2-3 Rows, nicht alle)
--     b) Portal-Login mit gültigem Code (z.B. PEZZ1234) → KundenPortal lädt
--     c) Eingeloggte App → unverändert (sieht alle Projekte über authenticated-Policies)

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Snapshot bestehender Policies (Audit-Reference + Rollback-Quelle)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3103 (
  ts timestamptz DEFAULT now(),
  tablename text, polname text, roles text[], cmd text,
  qual text, with_check text
);

INSERT INTO public._rls_snapshot_v3103 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname='public'
  AND tablename IN ('projects','plans','project_documents');

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: PROJECTS — Drop offen, ersetze mit portal_code-Filter
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS projects_anon_select ON public.projects;

CREATE POLICY projects_anon_select_portal
  ON public.projects FOR SELECT TO public
  USING (
    auth.role() = 'anon'
    AND portal_code IS NOT NULL
    AND portal_code <> ''
  );

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: PLANS — Drop offen, ersetze mit project-Portal + kunde_freigabe
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS plans_anon_select ON public.plans;

CREATE POLICY plans_anon_select_portal
  ON public.plans FOR SELECT TO public
  USING (
    auth.role() = 'anon'
    AND kunde_freigabe = true
    AND project_id IN (
      SELECT id FROM public.projects
      WHERE portal_code IS NOT NULL AND portal_code <> ''
    )
  );

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: PROJECT_DOCUMENTS — Drop offen, ersetze mit project-Portal + kunde_freigabe
-- ═══════════════════════════════════════════════════════════

DROP POLICY IF EXISTS project_documents_anon_select ON public.project_documents;

CREATE POLICY project_documents_anon_select_portal
  ON public.project_documents FOR SELECT TO public
  USING (
    auth.role() = 'anon'
    AND kunde_freigabe = true
    AND project_id IN (
      SELECT id FROM public.projects
      WHERE portal_code IS NOT NULL AND portal_code <> ''
    )
  );

-- ═══════════════════════════════════════════════════════════
-- BLOCK 5: HINWEIS zu defects + checklists
-- ═══════════════════════════════════════════════════════════
-- KundenPortal lädt auch defects (Z4045) und checklists (Z4064) via anon.
-- Wenn diese Tables anon-Policies haben (qual='true' oder auth.role()='anon'),
-- sind sie ähnlich zu eng-restricten oder bestätigen dass sie schon ok sind.
--
-- DIAGNOSE (read-only):
--   SELECT tablename, polname, cmd, qual FROM pg_policies
--   WHERE schemaname='public' AND tablename IN ('defects','checklists')
--     AND ('anon'::text = ANY(roles) OR 'public'::text = ANY(roles));
--
-- Falls offen: separater Sprint v3.10.4 für defects+checklists Portal-Lockdown.

-- ═══════════════════════════════════════════════════════════
-- VERIFY (nach Apply, vor Smoke)
-- ═══════════════════════════════════════════════════════════
-- 1. Neue Policies aktiv:
--    SELECT tablename, polname, cmd FROM pg_policies
--    WHERE schemaname='public' AND tablename IN ('projects','plans','project_documents')
--      AND polname LIKE '%_anon_select%';
--    → erwartet: projects_anon_select_portal, plans_anon_select_portal, project_documents_anon_select_portal
--
-- 2. anon-Direct-Test (sollte JETZT nur Portal-Projekte zeigen):
--    curl -X GET 'https://jiggujpruejkaomgxarp.supabase.co/rest/v1/projects?select=id,nr,name,portal_code' \
--      -H 'apikey: <ANON_KEY>'
--    → erwartet: nur Projekte mit portal_code != NULL (~2-3 Rows, NICHT alle)
--
-- 3. Portal-Funktional-Test:
--    a) Login-Screen → 🔗 Kundenportal → Code "PEZZ1234" oder "GED2024" eingeben
--    b) → KundenPortal MUSS laden, Mängel/Dokumente/Pläne sichtbar
--    c) Falls bricht → ROLLBACK
--
-- 4. App-Login mit beliebigem User:
--    → eingeloggte App sieht weiterhin alle Projekte (via authenticated-Policies)

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK SQL siehe migrate_anon_portal_lockdown_v3103_ROLLBACK.sql
-- ═══════════════════════════════════════════════════════════
