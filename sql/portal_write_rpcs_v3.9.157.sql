-- ✅ APPLIZIERT 2026-06-07 (CC, Sebastian-freigegeben). Portal-Write-Fix.
--
-- BUG: Kunden-Portal „Mangel melden" (POST defects) + „Abnahme bestätigen" (PUT defects) schrieben via
--   Sync-Queue als anon — aber defects hat NUR authenticated-Policies (kein anon-INSERT/UPDATE) → 403,
--   Kundenmeldungen/Abnahmen landeten nie in der DB (langjährig, kein Regress).
--
-- FIX: 2 SECURITY-DEFINER-RPCs als einziger sicherer anon-Schreibpfad. Validieren den portal_code, erzwingen
--   melder='Kunde'/Status (kein Status-Injection), scopen aufs Projekt des Codes (kein Fremdprojekt). Frontend
--   v3.9.157 ruft sie statt SQ (submitMangel → portal_submit_defect, kundeAbnahme → portal_confirm_abnahme).
--   Live anon-verifiziert: submit 200 + erscheint in portal_fetch (melder/status erzwungen); Abnahme-Guard
--   (gemeldet→false, behoben→true→abgenommen); falscher Code abgewiesen. Test-Mangel danach gelöscht.

CREATE OR REPLACE FUNCTION public.portal_submit_defect(
  p_code text, p_id text, p_title text, p_description text, p_ort text, p_images text
) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = public, pg_temp
AS $$
DECLARE v_pid text; v_id text;
BEGIN
  SELECT id INTO v_pid FROM public.projects
   WHERE portal_code = btrim(coalesce(p_code,'')) AND portal_code <> ''
     AND length(btrim(coalesce(p_code,''))) >= 3
   LIMIT 1;
  IF v_pid IS NULL THEN RAISE EXCEPTION 'invalid_portal_code'; END IF;
  IF length(btrim(coalesce(p_title,''))) < 3 THEN RAISE EXCEPTION 'title_too_short'; END IF;
  IF length(coalesce(p_title,'')) > 200 OR length(coalesce(p_description,'')) > 5000 THEN RAISE EXCEPTION 'text_too_long'; END IF;
  v_id := coalesce(nullif(btrim(coalesce(p_id,'')),''), gen_random_uuid()::text);
  INSERT INTO public.defects
    (id, project_id, title, description, ort, images, melder, kunde_status, status, prio, created_by, created_at)
  VALUES
    (v_id, v_pid, btrim(p_title), coalesce(p_description,''), coalesce(p_ort,''),
     coalesce(nullif(p_images,''),'[]'), 'Kunde', 'gemeldet', 'offen', 'normal', 'Kunde', now());
  RETURN v_id;
END; $$;

CREATE OR REPLACE FUNCTION public.portal_confirm_abnahme(p_code text, p_defect_id text)
RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path = public, pg_temp
AS $$
DECLARE v_pid text; v_n int;
BEGIN
  SELECT id INTO v_pid FROM public.projects
   WHERE portal_code = btrim(coalesce(p_code,'')) AND portal_code <> ''
     AND length(btrim(coalesce(p_code,''))) >= 3
   LIMIT 1;
  IF v_pid IS NULL THEN RAISE EXCEPTION 'invalid_portal_code'; END IF;
  UPDATE public.defects
     SET status='behoben', kunde_status='abgenommen'
   WHERE id = p_defect_id AND project_id = v_pid AND kunde_status = 'behoben';
  GET DIAGNOSTICS v_n = ROW_COUNT;
  RETURN v_n > 0;
END; $$;

REVOKE ALL ON FUNCTION public.portal_submit_defect(text,text,text,text,text,text) FROM public;
REVOKE ALL ON FUNCTION public.portal_confirm_abnahme(text,text) FROM public;
GRANT EXECUTE ON FUNCTION public.portal_submit_defect(text,text,text,text,text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.portal_confirm_abnahme(text,text) TO anon, authenticated;

-- ROLLBACK:
--   DROP FUNCTION IF EXISTS public.portal_submit_defect(text,text,text,text,text,text);
--   DROP FUNCTION IF EXISTS public.portal_confirm_abnahme(text,text);
--   (+ Frontend v3.9.157 zurück, sonst senden submitMangel/kundeAbnahme ins Leere.)
