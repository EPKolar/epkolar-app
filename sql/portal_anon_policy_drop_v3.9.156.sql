-- ✅ APPLIZIERT 2026-06-07 (CC). DROP der anon-SELECT-Policies — Endzustand, da das Portal jetzt
-- ausschließlich über portal_fetch (SECURITY DEFINER) liest. anon braucht keinen Direkt-Tabellenzugriff.
-- VORAUSSETZUNG (erfüllt vor Apply): portal_fetch live + anon-EXECUTE=true + Frontend v3.9.156 (RPC-first) live.
-- defects hatte KEINE anon-SELECT-Policy (defects_select = authenticated) → nichts zu droppen.
DROP POLICY IF EXISTS projects_anon_select ON public.projects;
DROP POLICY IF EXISTS project_documents_anon_select ON public.project_documents;

-- Smoke (anon-curl, anon-Key): GET /projects?select=id → 0 rows; GET /project_documents?select=id → 0 rows;
--   POST /rpc/portal_fetch {GED2024} → 200 + Projekt. (Alles am 2026-06-07 grün verifiziert.)
-- ROLLBACK: sql/portal_anon_policy_drop_v3.9.156_ROLLBACK.sql (Recreate mit dem gehärteten v3.9.155-Scope
--   aus RLS_anon_scope_v3.9.155.sql). Reihenfolge: NUR rückgängig machen, wenn parallel portal_fetch entfernt
--   ODER das Frontend zurückgerollt wird — sonst doppelter (redundanter) anon-Lesepfad.
