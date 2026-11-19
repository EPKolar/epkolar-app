-- ENTWURF — NICHT APPLIZIERT (v3.9.1047, Zweig fix/portal-fotos-speicher)
-- portal_submit_defect: keine Dateien mehr in defects.images (Dauerregel 18.11.2026: die DB speichert nie Dateien).
--
-- Grundlage: Live-Definition aus sql/portal_write_rpcs_v3.9.157.sql (appliziert 2026-06-07). Signatur, Rueckgabe (text),
-- Validierung, erzwungene Werte (melder/kunde_status/status/prio/created_by) unveraendert. NEU:
--   (1) p_images mit 'data:' oder ';base64,'                        -> RAISE 'files_not_allowed'
--   (2) p_images muss ein JSON-Array aus hoechstens 10 Strings sein, jeder <= 300 Zeichen und beginnend mit
--       'sbpriv:epkolar-docs/portal/<projekt-id>/<mangel-id>/'       -> sonst RAISE 'invalid_images'
--       (Pfad-Konvention der App: "sbpriv:<bucket>/<pfad>", siehe _dateiZiel/_dateiSigniert in index.html;
--        die Edge Function portal-foto liefert genau diese Pfade.)
--   (3) Wiederholung mit derselben p_id im selben Projekt (Kunde) liefert die Id zurueck statt PK-Fehler
--       (Client wiederholt nach verlorener Antwort mit stabiler Mangel-Id).
--
-- REIHENFOLGE: erst Edge Function portal-foto deployen, dann die App mit dem neuen Portal-Client ausliefern,
-- ERST DANN dieses SQL. Alte Clients (<= v1045) senden Base64-Vorschauen: mit Foto -> 'files_not_allowed' (HTTP 400),
-- die alte Oberflaeche hat das Formular da schon geschlossen und zeigt nur einen Toast -> Meldung verloren.
-- Ohne Foto senden alte Clients '[]' -> geht weiter durch.
--
-- GRANTS: laut sql/portal_write_rpcs_v3.9.157.sql: REVOKE ALL FROM public; GRANT EXECUTE TO anon, authenticated.
-- (Live nicht abgefragt.) CREATE OR REPLACE behaelt bestehende Rechte; sie werden unten trotzdem explizit gesetzt.

CREATE OR REPLACE FUNCTION public.portal_submit_defect(
  p_code text, p_id text, p_title text, p_description text, p_ort text, p_images text
) RETURNS text
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path TO 'public', 'pg_temp'
AS $$
DECLARE
  v_pid    text;
  v_id     text;
  v_imgs   jsonb;
  v_el     jsonb;
  v_s      text;
  v_prefix text;
BEGIN
  SELECT id INTO v_pid FROM public.projects
   WHERE portal_code = btrim(coalesce(p_code,'')) AND portal_code <> ''
     AND length(btrim(coalesce(p_code,''))) >= 3
   LIMIT 1;
  IF v_pid IS NULL THEN RAISE EXCEPTION 'invalid_portal_code'; END IF;
  IF length(btrim(coalesce(p_title,''))) < 3 THEN RAISE EXCEPTION 'title_too_short'; END IF;
  IF length(coalesce(p_title,'')) > 200 OR length(coalesce(p_description,'')) > 5000 THEN RAISE EXCEPTION 'text_too_long'; END IF;
  v_id := coalesce(nullif(btrim(coalesce(p_id,'')),''), gen_random_uuid()::text);

  -- (1) keine Dateien
  IF position('data:' in coalesce(p_images,'')) > 0 OR position(';base64,' in coalesce(p_images,'')) > 0 THEN
    RAISE EXCEPTION 'files_not_allowed';
  END IF;

  -- (2) nur Speicher-Verweise dieses Projekts und dieses Mangels
  IF nullif(btrim(coalesce(p_images,'')),'') IS NOT NULL THEN
    BEGIN
      v_imgs := p_images::jsonb;
    EXCEPTION WHEN others THEN
      RAISE EXCEPTION 'invalid_images';
    END;
    IF jsonb_typeof(v_imgs) <> 'array' OR jsonb_array_length(v_imgs) > 10 THEN
      RAISE EXCEPTION 'invalid_images';
    END IF;
    v_prefix := 'sbpriv:epkolar-docs/portal/' || v_pid || '/' || v_id || '/';
    FOR v_el IN SELECT value FROM jsonb_array_elements(v_imgs) LOOP
      IF jsonb_typeof(v_el) <> 'string' THEN RAISE EXCEPTION 'invalid_images'; END IF;
      v_s := v_el #>> '{}';
      IF length(v_s) > 300
         OR NOT starts_with(v_s, v_prefix)
         OR substr(v_s, length(v_prefix) + 1) !~ '^[A-Za-z0-9_-]{1,64}\.(jpg|png|webp)$' THEN
        RAISE EXCEPTION 'invalid_images';
      END IF;
    END LOOP;
  END IF;

  -- (3) Wiederholung derselben Meldung (Antwort ging verloren): kein PK-Fehler, gleiche Id zurueck
  IF EXISTS (SELECT 1 FROM public.defects d WHERE d.id = v_id AND d.project_id = v_pid AND d.melder = 'Kunde') THEN
    RETURN v_id;
  END IF;

  INSERT INTO public.defects
    (id, project_id, title, description, ort, images, melder, kunde_status, status, prio, created_by, created_at)
  VALUES
    (v_id, v_pid, btrim(p_title), coalesce(p_description,''), coalesce(p_ort,''),
     coalesce(nullif(p_images,''),'[]'), 'Kunde', 'gemeldet', 'offen', 'normal', 'Kunde', now());
  RETURN v_id;
END; $$;

REVOKE ALL ON FUNCTION public.portal_submit_defect(text,text,text,text,text,text) FROM public;
GRANT EXECUTE ON FUNCTION public.portal_submit_defect(text,text,text,text,text,text) TO anon, authenticated;

-- ROLLBACK: Definition aus sql/portal_write_rpcs_v3.9.157.sql erneut ausfuehren (CREATE OR REPLACE, gleiche Signatur).

-- ─────────────────────────────────────────────────────────────────────────────
-- PROBE (vor dem Apply, als eine Transaktion; legt nichts dauerhaft an). <CODE> durch einen echten Portal-Code,
-- <PID> durch dessen projects.id ersetzen (vorher als Service-Rolle nachsehen; anon darf projects evtl. nicht lesen).
-- Ausfuehren: die CREATE OR REPLACE oben + diesen Block zwischen BEGIN und ROLLBACK.
-- ─────────────────────────────────────────────────────────────────────────────
-- BEGIN;
--   -- (Funktionsdefinition von oben hier einfuegen)
--   SET LOCAL ROLE anon;
--   -- a) ohne Fotos: muss 'probe_a_1047' liefern
--   SELECT public.portal_submit_defect('<CODE>','probe_a_1047','Probe ohne Foto','', '', '[]');
--   -- b) gueltiger Speicher-Verweis: muss 'probe_b_1047' liefern
--   SELECT public.portal_submit_defect('<CODE>','probe_b_1047','Probe mit Foto','', '',
--     '["sbpriv:epkolar-docs/portal/<PID>/probe_b_1047/abcdefgh_0.jpg"]');   -- <PID> = projects.id zu <CODE>
--   -- c) Wiederholung von b: muss wieder 'probe_b_1047' liefern (kein PK-Fehler)
--   SELECT public.portal_submit_defect('<CODE>','probe_b_1047','Probe mit Foto','', '', '[]');
--   -- d) Base64: muss mit files_not_allowed scheitern
--   SAVEPOINT s1;
--   SELECT public.portal_submit_defect('<CODE>','probe_d_1047','Probe Base64','', '', '["data:image/jpeg;base64,/9j/AAAA"]');
--   ROLLBACK TO SAVEPOINT s1;
--   -- e) fremder Pfad: muss mit invalid_images scheitern
--   SAVEPOINT s2;
--   SELECT public.portal_submit_defect('<CODE>','probe_e_1047','Probe fremd','', '', '["sbpriv:epkolar-docs/docs/x/y.pdf"]');
--   ROLLBACK TO SAVEPOINT s2;
--   -- f) kein JSON-Array: muss mit invalid_images scheitern
--   SAVEPOINT s3;
--   SELECT public.portal_submit_defect('<CODE>','probe_f_1047','Probe Text','', '', 'kaputt');
--   ROLLBACK TO SAVEPOINT s3;
--   RESET ROLE;
--   SELECT id, images, melder, kunde_status FROM public.defects WHERE id LIKE 'probe_%_1047';
-- ROLLBACK;
