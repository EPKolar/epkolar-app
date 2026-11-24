-- DISPO PLANUNG v1 - PROBE (rollt IMMER zurueck)
-- EIN DO-Block = EINE Transaktion: wendet den ENTWURF an (DDL-Text verbatim aus DISPO_PLANUNG_v1_ENTWURF.sql,
-- per sql/_dispo_planung_probe_bauen.py eingebettet), prueft
--   (1) den OFFA-Abgleich juprowa_apply_worksheets: ein Schein mit Planung bekommt aus OFFA einen neuen Termin -
--       der Termin aendert sich, die Planungsfelder bleiben,
--   (2) je Rolle (monteur, helfer, techniker, projektleiter, buero, admin) + no-JWT + service_role:
--       planen / leeren / normal / unveraendert,
-- und endet mit RAISE EXCEPTION -> alles (Spalten, Trigger, Funktion, Testschreibvorgaenge) wird verworfen.
-- Jeder Einzelfall laeuft in einem eigenen Unterblock (Savepoint).
-- Erwartet:
--   import: termin=2099-02-02 planung=2099-03-03/07:15/03:00/<monteur> (unveraendert)
--   monteur/helfer/techniker: planen=42501 leeren=42501 normal=OK(1) unveraendert=OK(1)
--   projektleiter/buero/admin: alle OK(1); nojwt planen=OK(1); service_role planen=OK(1)
-- Danach messen: keine dispo-Spalte, nur trg_updated_at_arbeitsscheine, to_regprocedure('public.as_dispo_planung_guard()') NULL.
-- ERGEBNIS:
--   GELAUFEN 24.11.2026 auf Prod (execute_sql, zurueckgerollt):
--   import [S075430] termin=2099-02-02 planung=2099-03-03/07:15/03:00/w1 aktualisiert=1
--   monteur [mpv7wxngtat6] planen=42501 leeren=42501 normal=OK(1) unveraendert=OK(1)
--   helfer KEIN-TESTFALL (kein Benutzer mit Rolle helfer und Login)
--   techniker [mu3zg26dyesc] planen=42501 leeren=42501 normal=OK(1) unveraendert=OK(1)
--   projektleiter/buero/admin: planen=OK(1) leeren=OK(1) normal=OK(1) unveraendert=OK(1)
--   nojwt planen=OK(1); service_role planen=OK(1)
--   Nachmessung: 0 dispo-Spalten, nur trg_updated_at_arbeitsscheine, Funktion NULL, 0 Constraints,
--   S075430 termin_bestaetigt unveraendert (leer), 0 Probe-Reste in notizen.
DO $probe$
DECLARE
  r_role text;
  v_uid uuid;
  v_as text;
  v_mon text;
  v_other text;
  v_n int;
  v_res text := '';
  v_case text;
  v_sql text;
  v_imp text; v_imp_nr text; v_raw jsonb; v_r jsonb;
  v_t text; v_d text; v_z text; v_dau text; v_m text;
BEGIN
  IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='public.arbeitsscheine'::regclass AND tgname='trg_as_dispo_planung_guard') THEN
    RAISE EXCEPTION 'PROBE-ABBRUCH: trg_as_dispo_planung_guard existiert bereits';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='arbeitsscheine' AND column_name='dispo_datum') THEN
    RAISE EXCEPTION 'PROBE-ABBRUCH: dispo_datum existiert bereits';
  END IF;

  -- ENTWURF anwenden (verbatim)
  EXECUTE $ddl$ALTER TABLE public.arbeitsscheine
  ADD COLUMN IF NOT EXISTS dispo_datum text,
  ADD COLUMN IF NOT EXISTS dispo_zeit text,
  ADD COLUMN IF NOT EXISTS dispo_dauer text,
  ADD COLUMN IF NOT EXISTS dispo_monteur text;

DO $chk$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'arbeitsscheine_dispo_datum_form') THEN
    ALTER TABLE public.arbeitsscheine ADD CONSTRAINT arbeitsscheine_dispo_datum_form
      CHECK (dispo_datum IS NULL OR dispo_datum ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'arbeitsscheine_dispo_zeit_form') THEN
    ALTER TABLE public.arbeitsscheine ADD CONSTRAINT arbeitsscheine_dispo_zeit_form
      CHECK (dispo_zeit IS NULL OR dispo_zeit ~ '^[0-9]{2}:[0-9]{2}(:[0-9]{2})?$');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'arbeitsscheine_dispo_dauer_form') THEN
    ALTER TABLE public.arbeitsscheine ADD CONSTRAINT arbeitsscheine_dispo_dauer_form
      CHECK (dispo_dauer IS NULL OR dispo_dauer ~ '^[0-9]{1,3}:[0-9]{2}(:[0-9]{2})?$');
  END IF;
END
$chk$;

COMMENT ON COLUMN public.arbeitsscheine.dispo_datum IS 'Dispo-Planung: geplanter Tag (YYYY-MM-DD). Nicht bestaetigt, nicht an OFFA. Termin bestaetigen kopiert nach termin_bestaetigt.';
COMMENT ON COLUMN public.arbeitsscheine.dispo_zeit IS 'Dispo-Planung: geplante Startzeit (HH:MM).';
COMMENT ON COLUMN public.arbeitsscheine.dispo_dauer IS 'Dispo-Planung: geplante Dauer (HH:MM).';
COMMENT ON COLUMN public.arbeitsscheine.dispo_monteur IS 'Dispo-Planung: geplanter Monteur (workers.id).';

CREATE OR REPLACE FUNCTION public.as_dispo_planung_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $fn$
DECLARE
  v_claims jsonb;
  v_aendert boolean;
BEGIN
  IF TG_OP = 'INSERT' THEN
    v_aendert := nullif(NEW.dispo_datum, '') IS NOT NULL OR nullif(NEW.dispo_zeit, '') IS NOT NULL
              OR nullif(NEW.dispo_dauer, '') IS NOT NULL OR nullif(NEW.dispo_monteur, '') IS NOT NULL;
  ELSE
    v_aendert := nullif(NEW.dispo_datum, '') IS DISTINCT FROM nullif(OLD.dispo_datum, '')
              OR nullif(NEW.dispo_zeit, '') IS DISTINCT FROM nullif(OLD.dispo_zeit, '')
              OR nullif(NEW.dispo_dauer, '') IS DISTINCT FROM nullif(OLD.dispo_dauer, '')
              OR nullif(NEW.dispo_monteur, '') IS DISTINCT FROM nullif(OLD.dispo_monteur, '');
  END IF;
  IF NOT v_aendert THEN
    RETURN NEW;
  END IF;
  -- Ausnahme 1: kein angemeldeter JWT-Benutzer (SQL-Editor, Cron, service_role ohne sub)
  IF auth.uid() IS NULL THEN
    RETURN NEW;
  END IF;
  -- Ausnahme 2: service_role ausdruecklich (Edge Functions)
  BEGIN
    v_claims := nullif(current_setting('request.jwt.claims', true), '')::jsonb;
  EXCEPTION WHEN others THEN
    v_claims := NULL;
  END;
  IF coalesce(v_claims->>'role', '') = 'service_role' THEN
    RETURN NEW;
  END IF;
  -- Ausnahme 3: Buero / Projektleiter / Admin
  IF public.is_staff() THEN
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'Arbeitsschein %: Dispo-Planung nur durch Buero, Projektleitung oder Admin', NEW.nummer
    USING ERRCODE = '42501';
END;
$fn$;

REVOKE ALL ON FUNCTION public.as_dispo_planung_guard() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.as_dispo_planung_guard() FROM anon, authenticated;

DROP TRIGGER IF EXISTS trg_as_dispo_planung_guard ON public.arbeitsscheine;
CREATE TRIGGER trg_as_dispo_planung_guard
  BEFORE INSERT OR UPDATE ON public.arbeitsscheine
  FOR EACH ROW EXECUTE FUNCTION public.as_dispo_planung_guard();

NOTIFY pgrst, 'reload schema';
$ddl$;

  -- (1) OFFA-Abgleich laesst die Planung stehen
  PERFORM set_config('request.jwt.claims', '{}', true);
  SELECT a.id, a.nummer, a.juprowa_raw INTO v_imp, v_imp_nr, v_raw
    FROM public.arbeitsscheine a
   WHERE a.juprowa_raw IS NOT NULL AND upper(coalesce(a.juprowa_raw->>'AK_SCHEINNR','')) = upper(coalesce(a.nummer,''))
     AND NOT coalesce(a.push_pending, false) AND coalesce(a.monteur,'') <> ''
   ORDER BY a.updated_at DESC LIMIT 1;
  IF v_imp IS NULL THEN
    v_res := 'import KEIN-TESTFALL | ';
  ELSE
    SELECT a.monteur INTO v_m FROM public.arbeitsscheine a WHERE a.id = v_imp;
    UPDATE public.arbeitsscheine SET dispo_datum = '2099-03-03', dispo_zeit = '07:15', dispo_dauer = '03:00', dispo_monteur = v_m WHERE id = v_imp;
    v_raw := jsonb_set(v_raw, '{AK_TERMIN}', to_jsonb('2099-02-02 00:00:00'::text), true);
    v_r := public.juprowa_apply_worksheets(jsonb_build_array(v_raw), false, false);
    SELECT termin_bestaetigt, dispo_datum, dispo_zeit, dispo_dauer, dispo_monteur INTO v_t, v_d, v_z, v_dau, v_m
      FROM public.arbeitsscheine WHERE id = v_imp;
    v_res := v_res || 'import [' || v_imp_nr || '] termin=' || coalesce(v_t,'-') || ' planung=' || coalesce(v_d,'-') || '/' || coalesce(v_z,'-')
      || '/' || coalesce(v_dau,'-') || '/' || coalesce(v_m,'-') || ' aktualisiert=' || coalesce(v_r->>'aktualisiert', v_r->>'error', '?') || ' | ';
  END IF;

  -- (2) Rollen
  FOREACH r_role IN ARRAY ARRAY['monteur','helfer','techniker','projektleiter','buero','admin','nojwt','service_role'] LOOP
    v_uid := NULL; v_as := NULL; v_mon := NULL; v_other := NULL;
    RESET ROLE;
    PERFORM set_config('request.jwt.claims', '{}', true);
    IF r_role IN ('monteur','helfer','techniker') THEN
      SELECT u.auth_user_id, a.id, a.monteur INTO v_uid, v_as, v_mon
        FROM public.users u JOIN public.arbeitsscheine a ON a.monteur = u.monteur_id
       WHERE u.role = r_role AND u.auth_user_id IS NOT NULL AND coalesce(a.scheinstatus,'') <> 'storniert'
       ORDER BY (a.scheinstatus IN ('aufgenommen','freigegeben','in_bearbeitung','aufgeschoben')) DESC, a.updated_at DESC
       LIMIT 1;
    ELSE
      IF r_role IN ('projektleiter','buero','admin') THEN
        SELECT u.auth_user_id INTO v_uid FROM public.users u
         WHERE u.role = r_role AND u.auth_user_id IS NOT NULL ORDER BY u.auth_user_id LIMIT 1;
      END IF;
      SELECT a.id, a.monteur INTO v_as, v_mon FROM public.arbeitsscheine a
       WHERE coalesce(a.scheinstatus,'') <> 'storniert' AND coalesce(a.monteur,'') <> ''
       ORDER BY a.updated_at DESC LIMIT 1;
    END IF;
    IF v_as IS NULL OR (r_role NOT IN ('nojwt','service_role') AND v_uid IS NULL) THEN
      v_res := v_res || r_role || ' KEIN-TESTFALL | ';
      CONTINUE;
    END IF;
    SELECT x.m INTO v_other FROM (SELECT DISTINCT a.monteur AS m FROM public.arbeitsscheine a
      WHERE coalesce(a.monteur,'') <> '' AND a.monteur IS DISTINCT FROM v_mon) x ORDER BY x.m LIMIT 1;
    v_res := v_res || r_role || ' [' || v_as || ']';

    FOREACH v_case IN ARRAY ARRAY['planen','leeren','normal','unveraendert'] LOOP
      IF r_role IN ('nojwt','service_role') AND v_case <> 'planen' THEN CONTINUE; END IF;
      v_sql := CASE v_case
        WHEN 'planen'       THEN 'UPDATE public.arbeitsscheine SET dispo_datum = ''2099-01-01'', dispo_zeit = ''08:00'', dispo_dauer = ''02:00'', dispo_monteur = $2 WHERE id = $1'
        WHEN 'leeren'       THEN 'UPDATE public.arbeitsscheine SET dispo_datum = NULL, dispo_zeit = NULL, dispo_dauer = NULL, dispo_monteur = NULL WHERE id = $1'
        WHEN 'normal'       THEN 'UPDATE public.arbeitsscheine SET notizen = coalesce(notizen,'''') || '' [probe]'' WHERE id = $1'
        WHEN 'unveraendert' THEN 'UPDATE public.arbeitsscheine SET dispo_datum = dispo_datum, dispo_zeit = dispo_zeit, dispo_dauer = dispo_dauer, dispo_monteur = dispo_monteur WHERE id = $1'
      END;
      BEGIN
        IF v_case = 'leeren' THEN
          -- Vorbedingung als Eigentuemer: eine Planung liegt vor
          UPDATE public.arbeitsscheine SET dispo_datum = '2099-05-05', dispo_zeit = '09:00' WHERE id = v_as;
        END IF;
        IF r_role = 'nojwt' THEN
          PERFORM set_config('request.jwt.claims', '{}', true);
        ELSIF r_role = 'service_role' THEN
          PERFORM set_config('request.jwt.claims', '{"role":"service_role"}', true);
          SET LOCAL ROLE service_role;
        ELSE
          PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
          SET LOCAL ROLE authenticated;
        END IF;
        EXECUTE v_sql USING v_as, coalesce(v_other, v_mon);
        GET DIAGNOSTICS v_n = ROW_COUNT;
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = '__OK__' || v_n;
      EXCEPTION WHEN others THEN
        IF SQLERRM LIKE '\_\_OK\_\_%' THEN
          v_res := v_res || ' ' || v_case || '=OK(' || substr(SQLERRM, 7) || ')';
        ELSE
          v_res := v_res || ' ' || v_case || '=' || SQLSTATE || '(' || left(SQLERRM, 70) || ')';
        END IF;
      END;
      RESET ROLE;
      PERFORM set_config('request.jwt.claims', '{}', true);
    END LOOP;
    v_res := v_res || ' | ';
  END LOOP;

  RAISE EXCEPTION 'PROBE-ERGEBNIS %', v_res;
END
$probe$;
