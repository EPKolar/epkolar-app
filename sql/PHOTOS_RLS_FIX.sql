-- ============================================================
-- M-2 photos RLS Fix · v3.7.2 Block 1
-- WICHTIG: Sebastian führt ZUERST PHOTOS_RLS_AUDIT.sql aus,
--          entscheidet dann welche Variante passt und kommentiert die anderen aus.
-- ============================================================

-- ─── Variante A: Policy fehlt komplett (rowsecurity=false ODER 0 Policies) ───

-- ALTER TABLE public.photos ENABLE ROW LEVEL SECURITY;

-- Admin + Büro + Projektleiter: SELECT alle
-- CREATE POLICY photos_select_staff ON public.photos
--   FOR SELECT TO authenticated
--   USING (
--     EXISTS (
--       SELECT 1 FROM public.users u
--       WHERE u.auth_user_id = auth.uid()
--         AND u.role IN ('admin','buero','projektleiter')
--     )
--   );

-- Monteur/Techniker/Obermonteur/Helfer: SELECT nur eigene (worker_id via users.monteur_id)
-- CREATE POLICY photos_select_field_self ON public.photos
--   FOR SELECT TO authenticated
--   USING (
--     worker_id IN (
--       SELECT u.monteur_id FROM public.users u
--       WHERE u.auth_user_id = auth.uid()
--         AND u.role IN ('monteur','techniker','obermonteur','helfer')
--     )
--   );

-- INSERT (alle authenticated, aber worker_id muss zum self passen für non-staff)
-- CREATE POLICY photos_insert_own ON public.photos
--   FOR INSERT TO authenticated
--   WITH CHECK (
--     EXISTS (
--       SELECT 1 FROM public.users u
--       WHERE u.auth_user_id = auth.uid()
--         AND (
--           u.role IN ('admin','buero','projektleiter')
--           OR u.monteur_id = worker_id
--         )
--     )
--   );

-- UPDATE (Staff alles, Monteur nur eigene)
-- CREATE POLICY photos_update ON public.photos
--   FOR UPDATE TO authenticated
--   USING (
--     EXISTS (
--       SELECT 1 FROM public.users u
--       WHERE u.auth_user_id = auth.uid()
--         AND (
--           u.role IN ('admin','buero','projektleiter')
--           OR u.monteur_id = worker_id
--         )
--     )
--   );

-- DELETE (nur Admin+Büro+PL)
-- CREATE POLICY photos_delete_staff ON public.photos
--   FOR DELETE TO authenticated
--   USING (
--     EXISTS (
--       SELECT 1 FROM public.users u
--       WHERE u.auth_user_id = auth.uid()
--         AND u.role IN ('admin','buero','projektleiter')
--     )
--   );

-- ─── Variante B: Policies zu offen (TO public / anon / role-frei) ───
-- Erst alle DROPPEN:
-- DROP POLICY IF EXISTS photos_select ON public.photos;
-- DROP POLICY IF EXISTS photos_insert ON public.photos;
-- DROP POLICY IF EXISTS photos_update ON public.photos;
-- DROP POLICY IF EXISTS photos_delete ON public.photos;
-- (Sebastian ersetzt Namen nach Audit-Output)
-- Dann Variante-A-Block oben ausführen.

-- ─── Variante C: Policies OK, nur Matrix-Doku falsch ───
-- Kein SQL nötig. Stattdessen: sql/PERMISSION_MATRIX_v3.7.md korrigieren (außerhalb dieses Files).

-- ─── Verify nach Fix ───
-- SELECT policyname, cmd, roles FROM pg_policies WHERE tablename='photos' ORDER BY policyname;
-- Erwartet bei Variante A/B: 4-5 Policies (select_staff, select_field_self, insert_own, update, delete_staff)

-- Danach im Browser als Monteur: window._rlsAudit()
-- photos-Zeile soll count entsprechen eigener Fotos, nicht 0 und nicht total.
