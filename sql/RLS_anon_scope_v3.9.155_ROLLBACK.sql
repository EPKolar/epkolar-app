-- ═══════════════════════════════════════════════════════════
-- ROLLBACK für RLS_anon_scope_v3.9.155.sql
-- Setzt die anon-SELECT-Policies auf den ungehärteten Zustand zurück (auth.role()='anon').
-- Anwenden, wenn der Smoke-Test zeigt, dass das Portal gebrochen ist (Portal-Login liefert
-- keine Zeile). Grundsatz: lieber Leak offen als Portal kaputt.
-- ═══════════════════════════════════════════════════════════
ALTER POLICY projects_anon_select ON public.projects
  USING (auth.role()='anon');

ALTER POLICY project_documents_anon_select ON public.project_documents
  USING (auth.role()='anon');

-- Kontrolle:
SELECT policyname, qual FROM pg_policies
WHERE schemaname='public'
  AND policyname IN ('projects_anon_select','project_documents_anon_select');
-- Erwartet: qual = (auth.role() = 'anon'::text) bei beiden.
