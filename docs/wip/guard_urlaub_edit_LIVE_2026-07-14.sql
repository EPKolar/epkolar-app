-- guard_urlaub_edit() — Live-Body aus der DB (pg_get_functiondef), 1:1, 2026-07-14.
-- Normalform (prosrc, ASCII-\s kollabiert, getrimmt): md5 284dc6f19d45f4a8804ddb69e74e8ef6 / 1746 Zeichen.
-- NICHT ausfuehren als Rekonstruktion — das ist die WAHRHEIT, Quelle fuer TERMINAL_FINAL_v3.

CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE c_role text; c_perms text; c_override text; c_sub text; c_monteur text;
BEGIN
  c_sub := current_setting('request.jwt.claims', true)::json->>'sub';
  IF c_sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;  -- service_role bypass
  SELECT u.role, u.permissions, u.perms_override, u.monteur_id
    INTO c_role, c_perms, c_override, c_monteur
    FROM public.users u WHERE u.auth_user_id::text = c_sub;
  -- v3.9.453: Voll-Zugriff (Genehmigen/Bearbeiten) = admin/projektleiter/buero (= canDo('abs_approve') im Frontend)
  -- ODER urlaub_edit-Perm via permissions ODER perms_override (Frontend gewaehrt es ueber perms_override).
  -- Vorher nur admin + permissions-Spalte -> buero/PL + perms_override-User (z.B. Schober) liefen in die Exception.
  IF c_role IN ('admin','projektleiter','buero')
     OR (c_perms    IS NOT NULL AND c_perms    LIKE '%"urlaub_edit"%')
     OR (c_override IS NOT NULL AND c_override LIKE '%"urlaub_edit":true%')
  THEN RETURN COALESCE(NEW, OLD); END IF;
  -- DELETE: only own + still beantragt
  IF TG_OP = 'DELETE' THEN
    IF OLD.worker_id = c_monteur AND OLD.status = 'beantragt' THEN RETURN OLD; END IF;
    RAISE EXCEPTION 'Nur eigene offene Antraege loeschbar';
  END IF;
  -- INSERT: only own, status must be beantragt
  IF TG_OP = 'INSERT' THEN
    IF NEW.worker_id = c_monteur AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;
    RAISE EXCEPTION 'Nur eigene Antraege im Status beantragt anlegbar';
  END IF;
  -- UPDATE: only own, only while beantragt, may not self-approve
  IF TG_OP = 'UPDATE' THEN
    IF OLD.worker_id = c_monteur AND OLD.status = 'beantragt' AND NEW.status IN ('beantragt','storniert') THEN RETURN NEW; END IF;
    RAISE EXCEPTION 'Nur eigene offene Antraege aenderbar, kein Selbst-Genehmigen';
  END IF;
  RETURN COALESCE(NEW, OLD);
END; $function$
