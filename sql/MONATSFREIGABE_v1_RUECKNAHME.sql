-- =====================================================================================
-- MONATSFREIGABE_v1_RUECKNAHME.sql  -  nimmt sql/MONATSFREIGABE_v1_ENTWURF.sql vollstaendig zurueck.
-- Stand vorher (gemessen 24.11.2026 auf Prod): finkzeit mit EINER Policy finkzeit_staff_all (admin/projektleiter/buero),
-- ohne Trigger/CHECK; storage.objects epkolar_docs_select/insert/update/delete wie unten wiederhergestellt.
-- ACHTUNG: entfernt die neuen Spalten. Bricht ab, solange Freigabe-Zeilen existieren (sonst gingen Schnappschuss,
-- Fristen und Freigabe-Nachweise verloren). Vorher sichern bzw. bewusst loeschen. Storage-Dateien unter
-- epkolar-docs/monatsfreigabe/ bleiben liegen (nur noch fuer Buero/Admin/PL lesbar wie alle docs).
-- =====================================================================================
DO $vor$
BEGIN
  IF EXISTS (SELECT 1 FROM public.finkzeit WHERE status IN ('in_arbeit','zur_admin_freigabe','zur_freigabe','freigegeben')) THEN
    RAISE EXCEPTION 'Ruecknahme: es gibt Monatsfreigabe-Zeilen - erst sichern/entfernen'; END IF;
END $vor$;

DROP TRIGGER IF EXISTS zz_finkzeit_monatsfreigabe ON public.finkzeit;
DROP FUNCTION IF EXISTS public._finkzeit_monatsfreigabe();
DROP FUNCTION IF EXISTS public.monatsfreigabe_beanstanden(text, text);

DROP POLICY IF EXISTS finkzeit_buero_admin ON public.finkzeit;
DROP POLICY IF EXISTS finkzeit_monteur_select ON public.finkzeit;
DROP POLICY IF EXISTS finkzeit_monteur_update ON public.finkzeit;
CREATE POLICY finkzeit_staff_all ON public.finkzeit FOR ALL TO authenticated
  USING (public.current_user_role() = ANY (ARRAY['admin'::text, 'projektleiter'::text, 'buero'::text]))
  WITH CHECK (public.current_user_role() = ANY (ARRAY['admin'::text, 'projektleiter'::text, 'buero'::text]));

DROP INDEX IF EXISTS public.finkzeit_freigabe_je_monat;
ALTER TABLE public.finkzeit DROP CONSTRAINT IF EXISTS finkzeit_period_check;
ALTER TABLE public.finkzeit DROP CONSTRAINT IF EXISTS finkzeit_status_check;
ALTER TABLE public.finkzeit
  DROP COLUMN IF EXISTS freigabe_bis,
  DROP COLUMN IF EXISTS admin_freigabe_am,
  DROP COLUMN IF EXISTS admin_freigabe_von,
  DROP COLUMN IF EXISTS freigegeben_am,
  DROP COLUMN IF EXISTS freigegeben_von,
  DROP COLUMN IF EXISTS ohne_monteur,
  DROP COLUMN IF EXISTS beanstandung,
  DROP COLUMN IF EXISTS rueckgabe_grund,
  DROP COLUMN IF EXISTS snapshot,
  DROP COLUMN IF EXISTS signatur_pfad,
  DROP COLUMN IF EXISTS pdf_pfad,
  DROP COLUMN IF EXISTS admin_vermerk;

DROP TABLE IF EXISTS public.finkzeit_verlauf;
DROP TRIGGER IF EXISTS zz_mf_einst_stempel ON public.monatsfreigabe_einstellungen;
DROP TABLE IF EXISTS public.monatsfreigabe_einstellungen;
DROP FUNCTION IF EXISTS public._mf_einst_stempel();

DROP POLICY IF EXISTS monatsfreigabe_monteur_insert ON storage.objects;
DROP POLICY IF EXISTS epkolar_docs_select ON storage.objects;
DROP POLICY IF EXISTS epkolar_docs_insert ON storage.objects;
DROP POLICY IF EXISTS epkolar_docs_update ON storage.objects;
DROP POLICY IF EXISTS epkolar_docs_delete ON storage.objects;
CREATE POLICY epkolar_docs_select ON storage.objects FOR SELECT TO authenticated
  USING ((bucket_id = 'epkolar-docs'::text) AND (public.is_staff() OR ((storage.foldername(name))[2] = public.current_monteur_id())));
CREATE POLICY epkolar_docs_insert ON storage.objects FOR INSERT TO authenticated
  WITH CHECK ((bucket_id = 'epkolar-docs'::text) AND public.is_staff());
CREATE POLICY epkolar_docs_update ON storage.objects FOR UPDATE TO authenticated
  USING ((bucket_id = 'epkolar-docs'::text) AND public.is_staff())
  WITH CHECK ((bucket_id = 'epkolar-docs'::text) AND public.is_staff());
CREATE POLICY epkolar_docs_delete ON storage.objects FOR DELETE TO authenticated
  USING ((bucket_id = 'epkolar-docs'::text) AND public.is_staff());

DO $nach$
BEGIN
  IF (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit') <> 1 THEN
    RAISE EXCEPTION 'Nachpruefung: erwartet wieder genau finkzeit_staff_all'; END IF;
  IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='public.finkzeit'::regclass AND NOT tgisinternal) THEN
    RAISE EXCEPTION 'Nachpruefung: Trigger auf finkzeit uebrig'; END IF;
END $nach$;
