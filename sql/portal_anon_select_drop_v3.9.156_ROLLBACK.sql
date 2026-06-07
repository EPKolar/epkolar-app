-- ROLLBACK für portal_anon_select_drop_v3.9.156.sql
-- Stellt die 2 gedroppten anon-SELECT-Policies im gehärteten v3.9.155-Scope wieder her.
-- NUR nötig, falls das Portal über die RPC NICHT funktioniert und auf den Frontend-Direktread-Fallback
-- zurückgefallen werden muss (dann zusätzlich portal_fetch droppen oder im Frontend deaktivieren).
-- Exakte quals wie vor dem Drop (aus pg_policies erfasst 2026-06-07):
CREATE POLICY projects_anon_select ON public.projects
  FOR SELECT TO public
  USING ((auth.role() = 'anon'::text) AND (portal_code IS NOT NULL) AND (portal_code <> ''::text));

CREATE POLICY project_documents_anon_select ON public.project_documents
  FOR SELECT TO public
  USING ((auth.role() = 'anon'::text) AND (kunde_freigabe = 1));
