-- ============================================================================
-- ROLLBACK zu migrate_urlaub_edit_rls_v3111.sql — Sebastian-Service-Role
-- ============================================================================
-- Entfernt die urlaub_edit-RLS-Policies + Helper-Functions wieder.
-- ⚠️ Stellt KEINEN vorherigen Policy-Zustand wieder her (v3111 hatte keinen Snapshot —
--    urlaubskontingent/absences hatten vor v3111 i.d.R. offene/abweichende Policies).
--    Nach diesem Rollback ggf. die ursprünglichen Policies manuell neu setzen, sonst
--    bleibt RLS aktiv OHNE passende Policy → Tabelle für non-owner gesperrt.
-- ============================================================================
BEGIN;

DROP POLICY IF EXISTS urlaubskontingent_select ON public.urlaubskontingent;
DROP POLICY IF EXISTS urlaubskontingent_write  ON public.urlaubskontingent;

DROP POLICY IF EXISTS absences_select_self_or_mgr            ON public.absences;
DROP POLICY IF EXISTS absences_insert_self_or_mgr            ON public.absences;
DROP POLICY IF EXISTS absences_update_self_beantragt_or_mgr  ON public.absences;
DROP POLICY IF EXISTS absences_delete_self_beantragt_or_mgr  ON public.absences;

DROP FUNCTION IF EXISTS public.can_edit_urlaub();
DROP FUNCTION IF EXISTS public.current_monteur_id();

COMMIT;

-- Hinweis: Falls vor v3111 offene Policies existierten (z.B. authenticated_all),
-- diese hier wieder anlegen, ODER RLS temporär deaktivieren:
--   ALTER TABLE public.urlaubskontingent DISABLE ROW LEVEL SECURITY;
--   ALTER TABLE public.absences DISABLE ROW LEVEL SECURITY;
-- (nur als Notfall — RLS sollte aktiv bleiben).
