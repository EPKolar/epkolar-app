-- ============================================================================
-- C2 — urlaub_edit serverseitig (RLS) — Sebastian-Service-Role-Run
-- ============================================================================
-- Koppelt das per-User-Recht 'urlaub_edit' (Client: users.perms_override->>'urlaub_edit')
-- serverseitig, damit die Urlaub/ZA-Bearbeitung NICHT per direktem API-Call umgehbar ist.
--
-- Modell (Sebastian-Entscheidung 2026-06-03):
--   - urlaubskontingent: SCHREIBEN nur can_edit_urlaub() (admin/PL ODER perms_override.urlaub_edit).
--                        LESEN: eigene + can_edit_urlaub() alle.
--   - absences (Anträge): Monteur darf EIGENE im Status 'beantragt' ändern/löschen;
--                         genehmigte/fremde nur can_edit_urlaub().
--
-- VORAUSSETZUNG: public.users hat Spalten role, perms_override (jsonb), auth_user_id.
-- IDEMPOTENT: DROP POLICY IF EXISTS vor CREATE. Snapshot der alten Policies optional.
-- ============================================================================
BEGIN;

-- ---- Helper: can_edit_urlaub() (SECURITY DEFINER) --------------------------
CREATE OR REPLACE FUNCTION public.can_edit_urlaub()
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.users u
    WHERE u.auth_user_id = auth.uid()
      AND u.active AND NOT u.locked
      AND (
        u.role IN ('admin','projektleiter')
        OR COALESCE((u.perms_override->>'urlaub_edit')::boolean, false)
      )
  );
$$;

-- Helper: eigene monteur_id des Callers
CREATE OR REPLACE FUNCTION public.current_monteur_id()
RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT u.monteur_id FROM public.users u WHERE u.auth_user_id = auth.uid() LIMIT 1;
$$;

-- ---- urlaubskontingent -----------------------------------------------------
ALTER TABLE public.urlaubskontingent ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS urlaubskontingent_select ON public.urlaubskontingent;
CREATE POLICY urlaubskontingent_select ON public.urlaubskontingent
  FOR SELECT TO authenticated
  USING ( public.can_edit_urlaub() OR worker_id = public.current_monteur_id() );

DROP POLICY IF EXISTS urlaubskontingent_write ON public.urlaubskontingent;
CREATE POLICY urlaubskontingent_write ON public.urlaubskontingent
  FOR ALL TO authenticated
  USING ( public.can_edit_urlaub() )
  WITH CHECK ( public.can_edit_urlaub() );

-- ---- absences (Anträge: eigene im 'beantragt' ODER Verwalter) --------------
ALTER TABLE public.absences ENABLE ROW LEVEL SECURITY;

-- SELECT: eigene immer, Verwalter alle (bestehende Select-Policy ggf. ersetzen — prüfen!)
DROP POLICY IF EXISTS absences_select_self_or_mgr ON public.absences;
CREATE POLICY absences_select_self_or_mgr ON public.absences
  FOR SELECT TO authenticated
  USING ( public.can_edit_urlaub() OR worker_id = public.current_monteur_id() );

-- INSERT: eigene anlegen (Monteur), oder Verwalter beliebig
DROP POLICY IF EXISTS absences_insert_self_or_mgr ON public.absences;
CREATE POLICY absences_insert_self_or_mgr ON public.absences
  FOR INSERT TO authenticated
  WITH CHECK ( public.can_edit_urlaub() OR worker_id = public.current_monteur_id() );

-- UPDATE: Verwalter alle; Monteur nur EIGENE solange status='beantragt' (vorher UND nachher)
DROP POLICY IF EXISTS absences_update_self_beantragt_or_mgr ON public.absences;
CREATE POLICY absences_update_self_beantragt_or_mgr ON public.absences
  FOR UPDATE TO authenticated
  USING ( public.can_edit_urlaub()
          OR (worker_id = public.current_monteur_id() AND status = 'beantragt') )
  WITH CHECK ( public.can_edit_urlaub()
          OR (worker_id = public.current_monteur_id() AND status = 'beantragt') );

-- DELETE: Verwalter alle; Monteur nur EIGENE im 'beantragt'
DROP POLICY IF EXISTS absences_delete_self_beantragt_or_mgr ON public.absences;
CREATE POLICY absences_delete_self_beantragt_or_mgr ON public.absences
  FOR DELETE TO authenticated
  USING ( public.can_edit_urlaub()
          OR (worker_id = public.current_monteur_id() AND status = 'beantragt') );

COMMIT;

-- ============================================================================
-- VERIFY (mit verschiedenen Tokens, Chat-Claude):
--  - Monteur OHNE urlaub_edit: SELECT eigene OK, UPDATE fremde/genehmigte → 0 rows/403,
--    UPDATE eigene beantragt → OK.
--  - User MIT urlaub_edit: urlaubskontingent UPDATE → OK; absences fremde UPDATE → OK.
--  - SELECT public.can_edit_urlaub();  -- als jeweiliger Token true/false plausibel.
-- ⚠️ Bestehende absences-Policies (status-PUT etc.) prüfen, dass sie nicht kollidieren —
--    ggf. alte FOR UPDATE-Policy droppen, sonst additives OR weicht das Modell auf.
-- ============================================================================
