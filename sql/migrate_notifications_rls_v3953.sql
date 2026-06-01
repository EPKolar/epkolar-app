-- v3.9.53 Notifications UPDATE-RLS Fix für Monteure (Riedmann-Bug)
-- Monteur darf NUR seine eigenen Notifications als gelesen markieren.
-- Bisher fehlte UPDATE-Policy → PATCH-Request schlug silent fehl.
--
-- Sebastian-Action: In Supabase SQL-Editor ausführen.
-- Backend: jiggujpruejkaomgxarp.supabase.co
-- Vor Ausführung: Backup empfohlen. RLS-policies sind additiv (CREATE POLICY IF NOT EXISTS).

-- Helper-Funktion is_admin() falls nicht existent
CREATE OR REPLACE FUNCTION is_admin() RETURNS boolean AS $$
  SELECT EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role = 'admin');
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- RLS auf notifications aktiv (falls nicht schon)
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- SELECT: Eigene + Admin sieht alles
CREATE POLICY IF NOT EXISTS notifications_select_own_or_admin
  ON public.notifications FOR SELECT TO authenticated
  USING (
    is_admin() OR
    user_id IN (SELECT id FROM public.users WHERE auth_user_id = auth.uid())
  );

-- UPDATE: Eigene Notifications nur Lese-Flag (read) ändern
-- (Column-level CHECK in Postgres-RLS nicht direkt möglich, daher Schutz auf user_id-Ebene
--  + Frontend-Layer beschränkt PATCH-Body auf {read:1}.)
CREATE POLICY IF NOT EXISTS notifications_update_own_read
  ON public.notifications FOR UPDATE TO authenticated
  USING (
    user_id IN (SELECT id FROM public.users WHERE auth_user_id = auth.uid())
  )
  WITH CHECK (
    user_id IN (SELECT id FROM public.users WHERE auth_user_id = auth.uid())
  );

-- Admin UPDATE (für Bulk-Operationen via Admin-Tools)
CREATE POLICY IF NOT EXISTS notifications_update_admin
  ON public.notifications FOR UPDATE TO authenticated
  USING (is_admin())
  WITH CHECK (is_admin());

-- DELETE: nur eigene oder Admin (für deleteNotif/clear-all)
CREATE POLICY IF NOT EXISTS notifications_delete_own_or_admin
  ON public.notifications FOR DELETE TO authenticated
  USING (
    is_admin() OR
    user_id IN (SELECT id FROM public.users WHERE auth_user_id = auth.uid())
  );

-- INSERT: nur Admin/PL/Büro (für system-erzeugte Notifications wie Mention, Abwesenheit)
CREATE POLICY IF NOT EXISTS notifications_insert_admin_pl
  ON public.notifications FOR INSERT TO authenticated
  WITH CHECK (
    is_admin() OR
    EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role IN ('projektleiter','buero'))
  );
