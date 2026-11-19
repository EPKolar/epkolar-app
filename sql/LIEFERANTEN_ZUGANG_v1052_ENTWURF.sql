-- IDEMPOTENT
-- =====================================================================================
-- LIEFERANTEN_ZUGANG_v1052_ENTWURF.sql  —  Haendler-Zugangsdaten aus supplier_configs heraus (Klartext fuer alle Angemeldeten)
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Pruefung durch Chat-Claude, Einspielen nur durch Sebastian ueber das Tor.
-- Zweig fix/lieferanten-passwoerter (Basis live v3.9.1051). Die App ab v3.9.1052 erkennt selbst, ob die Tabelle da ist:
-- antwortet /supplier_credentials mit 404 (42P01/PGRST205), liest der Admin die Zugangsdaten bis zum Neuladen wie bisher
-- aus supplier_configs. Reihenfolge daher beliebig; empfohlen: erst App ausliefern, dann dieses SQL.
--
-- BEFUND (Prod, lesend geprueft 19.11.2026, C:/repos/epk-datanorm-ssrf-vorpruefung-2026-11-19.md HOCH-1):
--   * supplier_configs.username / supplier_configs.password stehen im KLARTEXT (5 von 9 Haendlern befuellt).
--   * Policy supplier_configs_read_auth: FOR SELECT USING (auth.role() = 'authenticated') -> JEDER Angemeldete
--     (auch Monteur) liest per GET /rest/v1/supplier_configs?select=name,username,password alle Portal-Zugaenge.
--   * public.can_see_supplier_creds() und die Sicht supplier_configs_safe (sql/migrate_supplier_configs_creds_lockdown_v3105.sql)
--     EXISTIEREN IN PROD NICHT. Nichts darf sich auf sie verlassen - auch kuenftiger Server-Code nicht.
--   * Ein Spalten-REVOKE wirkt nicht, solange authenticated SELECT auf der ganzen Tabelle hat, und alte Apps (<= v1051)
--     lesen mit select=* -> der Schutz muss an den DATEN sitzen, nicht an der Spalte.
--
-- SCHREIBWEGE, die heute username/password an supplier_configs senden (gemessen im Code):
--   1. App index.html saveSupplier -> _supplierSaveBody -> SQ.push PUT /api/supplier-configs/<id> (nur wenn im Formular
--      NEU eingetragen) bzw. POST /api/supplier-configs (Anlegen: immer username:'' und password:'').
--      Der Weg laeuft ueber die Warteschlange (SyncQueue): ein 400 dort bleibt haengen bzw. wird verworfen.
--   2. Edge-Function supplier-sync (supabase/functions/supplier-sync/index.ts, live laut Pruefbericht):
--      action set-credentials -> .update({username, password, updated_at}) auf supplier_configs;
--      action sync -> .select("... username, password, active") auf supplier_configs.
--   -> Die Spalten zu LOESCHEN (DROP COLUMN) wuerde beide Wege brechen: alte Apps bekaemen 400 (PGRST204) beim Anlegen
--      und beim Kennwort-Eintragen, die Function bekaeme bei JEDEM sync/set-credentials einen Spaltenfehler.
--
-- GEWAEHLTE LOESUNG (Spalten bleiben, sind aber immer NULL):
--   1. Neue Tabelle public.supplier_credentials (supplier_id = Typ von supplier_configs.id, uuid), RLS an,
--      EINE Policy FOR ALL TO authenticated USING/WITH CHECK (public.auth_role() = 'admin').
--      Spaltenrechte: authenticated darf password SCHREIBEN, aber NIE LESEN (SELECT nur supplier_id, username,
--      has_password, updated_at). Das Kennwort verlaesst die Datenbank damit auch fuer den Admin nie mehr ueber REST;
--      die App braucht nur "hinterlegt ja/nein" (has_password, berechnete Spalte).
--      anon: REVOKE ALL. Kein Fremdschluessel (keine Kaskade, keine Reihenfolge-Abhaengigkeit zur Warteschlange);
--      Aufraeumen beim Loeschen eines Haendlers ueber einen AFTER-DELETE-Trigger.
--   2. Kopie username/password -> supplier_credentials (ON CONFLICT DO NOTHING), danach Abgleich (bricht ab, wenn
--      ein Wert nicht angekommen ist), ERST DANN UPDATE supplier_configs SET username=NULL, password=NULL.
--   3. BEFORE-INSERT/UPDATE-Trigger auf supplier_configs: schreibt ein angemeldeter Admin (alte App) oder direktes
--      SQL ohne Anfrage-Identitaet username/password in supplier_configs, wandert der Wert in supplier_credentials;
--      die Zeile in supplier_configs behaelt IMMER NULL. Alte Apps laufen ohne 400 weiter. Von allen anderen
--      (anon, service_role, andere Rollen) wird der Wert verworfen. service_role wird bewusst NICHT vertraut:
--      die Function supplier-sync (set-credentials) prueft selbst "aktiver Admin" und schreibt dann direkt nach
--      supplier_credentials (Fassung auf diesem Zweig) -> sie MUSS mit/vor diesem SQL deployt werden, sonst verwirft
--      der Trigger die Schreibversuche der alten live-Fassung.
--   4. CHECK-Riegel supplier_configs_kein_klartext (username IS NULL AND password IS NULL) als zweite Linie:
--      faellt der Trigger je weg, scheitert das Schreiben laut, statt wieder Klartext abzulegen.
--
-- WARUM NUR ADMIN (nicht projektleiter/lagerleitung wie die nie angelegte can_see_supplier_creds()):
--   * Die Eingabefelder Benutzername/Passwort zeigt die App seit v3.9.1016 nur dem Admin; das Kennwort selbst zeigt
--     sie niemandem. Niemand ausser dem Admin braucht die Werte in der App.
--   * Der Server-Abgleich (supplier-sync) laeuft mit service_role und umgeht RLS - er braucht keine Policy.
--   * Kleinste Rechte: ein Leck ueber eine weitere Rolle (geteiltes Tablet, Lager-PC) wird so ausgeschlossen.
--   Folge: Projektleitung/Lagerleitung sehen auf der Haendlerkarte keinen Benutzernamen mehr (Kopierknopf entfaellt).
--
-- SERVER-CODE (NICHT Teil dieses Entwurfs, Edge-Functions bleiben unberuehrt):
--   supplier-sync (Fassung auf diesem Zweig, NICHT deployt): action sync liest die Zugangsdaten mit service_role aus
--   public.supplier_credentials (supplier_id = supplier_configs.id); action set-credentials nur fuer aktive Admins,
--   schreibt per upsert nach supplier_credentials, 503 wenn die Tabelle fehlt (nie Klartext-Rueckfall).
--   Die live-Fassung (v2) schreibt noch nach supplier_configs -> nach dem Apply verworfen (Trigger). Heute ohne
--   praktische Wirkung: downloadArticles ist fuer keinen Haendler umgesetzt, die App ruft set-credentials nicht auf,
--   und der Zweig feature/datanorm-sync sendet Zugangsdaten derzeit nie (cred_host nicht selektiert) - er muss
--   beim Zusammenfuehren die supplier_credentials-Lesung dieses Zweigs uebernehmen.
--   Die Autorisierung dort darf sich NICHT auf can_see_supplier_creds() stuetzen (existiert nicht).
--   sync_supplier (Dashboard-Function, verify_jwt=false) ist NICHT im Repo; ob sie supplier_configs.username/password
--   liest, ist unbekannt -> vor dem Apply im Dashboard pruefen (TABU fuer Agenten, Entscheidung Sebastian).
--
-- NACH DEM APPLY: Sebastian ROTIERT die 5 Kennwoerter (Heinze, Holter, Impex, OeAG, SHT) bei den Haendlern und traegt
--   die neuen in der App (Admin -> Haendler -> Bearbeiten) ein. Die alten waren monatelang fuer jeden Angemeldeten
--   lesbar und muessen als bekannt gelten. Zusaetzlich: alte Sicherungen/Exporte der Tabelle enthalten sie weiterhin.
--
-- ROLLBACK (bewusst nicht als Datei): Daten zurueck mit
--   ALTER TABLE public.supplier_configs DROP CONSTRAINT IF EXISTS supplier_configs_kein_klartext;
--   DROP TRIGGER IF EXISTS trg_supplier_zugang_umleiten ON public.supplier_configs;
--   UPDATE public.supplier_configs s SET username = c.username, password = c.password
--     FROM public.supplier_credentials c WHERE c.supplier_id = s.id;
--   (Tabelle supplier_credentials danach erst loeschen, wenn der Rueckweg geprueft ist.)
-- =====================================================================================

BEGIN;

-- 0. VORPRUEFUNG (bricht ab, wenn die Annahmen nicht stimmen — dann NICHT weiter, sondern melden)
DO $$
DECLARE v_t text;
BEGIN
  SELECT data_type INTO v_t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='supplier_configs' AND column_name='id';
  IF v_t IS DISTINCT FROM 'uuid' THEN
    RAISE EXCEPTION 'Vorpruefung: supplier_configs.id ist %, erwartet uuid', v_t; END IF;
  SELECT data_type INTO v_t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='supplier_configs' AND column_name='username';
  IF v_t IS NULL OR v_t NOT IN ('text','character varying') THEN
    RAISE EXCEPTION 'Vorpruefung: supplier_configs.username ist %, erwartet text/varchar', v_t; END IF;
  SELECT data_type INTO v_t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='supplier_configs' AND column_name='password';
  IF v_t IS NULL OR v_t NOT IN ('text','character varying') THEN
    RAISE EXCEPTION 'Vorpruefung: supplier_configs.password ist %, erwartet text/varchar', v_t; END IF;
  IF to_regprocedure('public.auth_role()') IS NULL THEN
    RAISE EXCEPTION 'Vorpruefung: public.auth_role() fehlt'; END IF;
  -- Gibt es supplier_credentials schon (zweiter Lauf), muss supplier_id uuid sein
  SELECT data_type INTO v_t FROM information_schema.columns
   WHERE table_schema='public' AND table_name='supplier_credentials' AND column_name='supplier_id';
  IF v_t IS NOT NULL AND v_t <> 'uuid' THEN
    RAISE EXCEPTION 'Vorpruefung: supplier_credentials.supplier_id ist %, erwartet uuid', v_t; END IF;
END $$;

-- 0b. Stand VORHER (nur Zahlen, nie Werte)
DO $$
DECLARE v_alle int; v_pw int; v_un int; v_cfg int;
BEGIN
  SELECT count(*), count(*) FILTER (WHERE coalesce(password,'') <> ''),
         count(*) FILTER (WHERE nullif(btrim(coalesce(username,'')),'') IS NOT NULL)
    INTO v_alle, v_pw, v_un FROM public.supplier_configs;
  RAISE NOTICE 'VORHER supplier_configs: % Zeilen, % mit Kennwort, % mit Benutzername', v_alle, v_pw, v_un;
  -- Hinweis (bricht NICHT ab): steht in config etwas, das nach Zugangsdaten aussieht?
  SELECT count(*) INTO v_cfg FROM public.supplier_configs
   WHERE config IS NOT NULL AND config::text ~* '(pass|kennw|secret|token|pwd)';
  IF v_cfg > 0 THEN
    RAISE NOTICE 'HINWEIS: % Zeilen tragen in config Schluessel wie pass/token/secret - von Hand pruefen (bleibt lesbar!)', v_cfg;
  END IF;
END $$;

-- 1. Tabelle
CREATE TABLE IF NOT EXISTS public.supplier_credentials (
  supplier_id  uuid PRIMARY KEY,
  username     text,
  password     text,
  has_password boolean GENERATED ALWAYS AS (coalesce(password,'') <> '') STORED,
  updated_at   timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE public.supplier_credentials IS
  'v3.9.1052 Haendler-Portal-Zugangsdaten. Nur Admin (RLS), password nie per REST lesbar (Spaltenrecht). Server: service_role.';

-- 2. Rechte: erst alles weg, dann gezielt
ALTER TABLE public.supplier_credentials ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.supplier_credentials FROM PUBLIC;
REVOKE ALL ON TABLE public.supplier_credentials FROM anon;
REVOKE ALL ON TABLE public.supplier_credentials FROM authenticated;
GRANT SELECT (supplier_id, username, has_password, updated_at) ON public.supplier_credentials TO authenticated;
GRANT INSERT (supplier_id, username, password) ON public.supplier_credentials TO authenticated;
GRANT UPDATE (username, password) ON public.supplier_credentials TO authenticated;
GRANT DELETE ON public.supplier_credentials TO authenticated;
GRANT ALL ON TABLE public.supplier_credentials TO service_role;

DROP POLICY IF EXISTS supplier_credentials_nur_admin ON public.supplier_credentials;
CREATE POLICY supplier_credentials_nur_admin ON public.supplier_credentials
  FOR ALL TO authenticated
  USING (public.auth_role() = 'admin')
  WITH CHECK (public.auth_role() = 'admin');

-- updated_at bei jeder Aenderung
CREATE OR REPLACE FUNCTION public._supplier_credentials_stempel()
RETURNS trigger LANGUAGE plpgsql SET search_path = public, pg_temp AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS trg_supplier_credentials_stempel ON public.supplier_credentials;
CREATE TRIGGER trg_supplier_credentials_stempel BEFORE UPDATE ON public.supplier_credentials
  FOR EACH ROW EXECUTE FUNCTION public._supplier_credentials_stempel();

-- 3. KOPIE (vor dem Leeren!) — nur Zeilen, in denen etwas steht
INSERT INTO public.supplier_credentials (supplier_id, username, password)
SELECT s.id, nullif(btrim(coalesce(s.username,'')),''), nullif(coalesce(s.password,''),'')
  FROM public.supplier_configs s
 WHERE coalesce(s.password,'') <> '' OR nullif(btrim(coalesce(s.username,'')),'') IS NOT NULL
ON CONFLICT (supplier_id) DO NOTHING;

-- 3b. ABGLEICH: jeder Wert, der gleich geleert wird, muss in supplier_credentials stehen (sonst Abbruch, nichts geleert)
DO $$
DECLARE v_fehlt int;
BEGIN
  SELECT count(*) INTO v_fehlt
    FROM public.supplier_configs s
    LEFT JOIN public.supplier_credentials c ON c.supplier_id = s.id
   WHERE (coalesce(s.password,'') <> '' AND c.password IS DISTINCT FROM s.password)
      OR (nullif(btrim(coalesce(s.username,'')),'') IS NOT NULL AND c.username IS DISTINCT FROM btrim(s.username));
  IF v_fehlt > 0 THEN
    RAISE EXCEPTION 'Abgleich: % Haendler haben Zugangsdaten, die in supplier_credentials NICHT gleich stehen (schon vorhandene Zeile?) - nichts geleert, melden', v_fehlt;
  END IF;
END $$;

-- 4. UMLEITUNG fuer alte Apps und die Edge-Function (vor dem Leeren angelegt; beim Leeren selbst ist nichts umzuleiten)
CREATE OR REPLACE FUNCTION public._supplier_zugang_umleiten()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE v_un text; v_pw text; v_darf boolean;
BEGIN
  v_un := nullif(btrim(coalesce(NEW.username,'')),'');
  v_pw := nullif(coalesce(NEW.password,''),'');
  IF v_un IS NOT NULL OR v_pw IS NOT NULL THEN
    -- Erlaubt NUR: (a) angemeldeter Admin (alte App <= v1051) oder (b) direktes SQL ohne jede Anfrage-Identitaet
    -- (SQL-Editor/Migration: keine request.jwt.claims, nicht ueber PostgREST/authenticator, keine API-Rolle gesetzt).
    -- NICHT erlaubt: anon (auth.uid() ist dort auch NULL!), service_role (die Function supplier-sync schreibt nach
    -- ihrer eigenen Admin-Pruefung direkt nach supplier_credentials), alle anderen Rollen -> Wert verworfen.
    v_darf := (coalesce(auth.role(),'') = 'authenticated' AND public.auth_role() = 'admin')
           OR (coalesce(nullif(current_setting('request.jwt.claims', true),''),'') = ''
               AND session_user::text <> 'authenticator'
               AND coalesce(nullif(current_setting('role', true),''),'none') NOT IN ('anon','authenticated','service_role'));
    IF v_darf THEN
      INSERT INTO public.supplier_credentials AS c (supplier_id, username, password)
      VALUES (NEW.id, v_un, v_pw)
      ON CONFLICT (supplier_id) DO UPDATE
        SET username = coalesce(EXCLUDED.username, c.username),
            password = coalesce(EXCLUDED.password, c.password);
    END IF;
  END IF;
  NEW.username := NULL;
  NEW.password := NULL;
  RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION public._supplier_zugang_umleiten() FROM PUBLIC, anon, authenticated;

DROP TRIGGER IF EXISTS trg_supplier_zugang_umleiten ON public.supplier_configs;
CREATE TRIGGER trg_supplier_zugang_umleiten BEFORE INSERT OR UPDATE ON public.supplier_configs
  FOR EACH ROW EXECUTE FUNCTION public._supplier_zugang_umleiten();

-- Haendler geloescht -> seine Zugangsdaten mit (kein FK, daher Trigger)
CREATE OR REPLACE FUNCTION public._supplier_zugang_aufraeumen()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  DELETE FROM public.supplier_credentials WHERE supplier_id = OLD.id;
  RETURN OLD;
END $$;
REVOKE ALL ON FUNCTION public._supplier_zugang_aufraeumen() FROM PUBLIC, anon, authenticated;
DROP TRIGGER IF EXISTS trg_supplier_zugang_aufraeumen ON public.supplier_configs;
CREATE TRIGGER trg_supplier_zugang_aufraeumen AFTER DELETE ON public.supplier_configs
  FOR EACH ROW EXECUTE FUNCTION public._supplier_zugang_aufraeumen();

-- 5. LEEREN (erst nach Kopie + Abgleich). NOT NULL waere hier hinderlich -> idempotent entfernen.
ALTER TABLE public.supplier_configs ALTER COLUMN username DROP NOT NULL;
ALTER TABLE public.supplier_configs ALTER COLUMN password DROP NOT NULL;
UPDATE public.supplier_configs SET username = NULL, password = NULL
 WHERE username IS NOT NULL OR password IS NOT NULL;

-- 6. Riegel: nie wieder Klartext in supplier_configs
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                  WHERE conname = 'supplier_configs_kein_klartext'
                    AND conrelid = 'public.supplier_configs'::regclass) THEN
    ALTER TABLE public.supplier_configs
      ADD CONSTRAINT supplier_configs_kein_klartext CHECK (username IS NULL AND password IS NULL);
  END IF;
END $$;

-- 7. Stand NACHHER (bricht ab, wenn noch Klartext steht)
DO $$
DECLARE v_rest int; v_cred int; v_pw int;
BEGIN
  SELECT count(*) INTO v_rest FROM public.supplier_configs WHERE username IS NOT NULL OR password IS NOT NULL;
  SELECT count(*), count(*) FILTER (WHERE has_password) INTO v_cred, v_pw FROM public.supplier_credentials;
  RAISE NOTICE 'NACHHER supplier_configs mit Zugangsdaten: % (soll 0); supplier_credentials: % Zeilen, % mit Kennwort', v_rest, v_cred, v_pw;
  IF v_rest > 0 THEN RAISE EXCEPTION 'Nachpruefung: % Zeilen in supplier_configs tragen noch Zugangsdaten', v_rest; END IF;
END $$;

COMMIT;

-- =====================================================================================
-- PROBE (nach dem Apply, eigener Lauf; aendert nichts: BEGIN ... ROLLBACK). Gibt NIE Werte aus, nur Zahlen.
-- Erwartung: monteur/buero/projektleiter sehen 0 Zeilen und koennen nichts schreiben; admin sieht alle Zeilen,
-- kann password aber NICHT lesen (Spaltenrecht); anon darf gar nichts; Umleitung legt Werte in supplier_credentials.
-- =====================================================================================
-- BEGIN;
-- DO $probe$
-- DECLARE v_uid uuid; v_n int; v_rolle text; v_soll int; v_sid uuid;
-- BEGIN
--   SELECT count(*) INTO v_soll FROM public.supplier_credentials;
--   SELECT id INTO v_sid FROM public.supplier_configs ORDER BY name LIMIT 1;
--   FOREACH v_rolle IN ARRAY ARRAY['monteur','buero','projektleiter','admin'] LOOP
--     v_uid := NULL;
--     SELECT auth_user_id INTO v_uid FROM public.users WHERE role = v_rolle AND auth_user_id IS NOT NULL LIMIT 1;
--     IF v_uid IS NULL THEN RAISE NOTICE 'Probe %: kein Nutzer mit dieser Rolle', v_rolle; CONTINUE; END IF;
--     PERFORM set_config('request.jwt.claims', json_build_object('sub', v_uid, 'role', 'authenticated')::text, true);
--     EXECUTE 'SET LOCAL ROLE authenticated';
--     SELECT count(*) INTO v_n FROM public.supplier_credentials;
--     IF v_rolle = 'admin' THEN
--       IF v_n <> v_soll THEN RAISE EXCEPTION 'PROBE FEHLER admin sieht % statt % Zeilen', v_n, v_soll; END IF;
--       BEGIN
--         EXECUTE 'SELECT count(password) FROM public.supplier_credentials';
--         RAISE EXCEPTION 'PROBE FEHLER admin kann password LESEN';
--       EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe admin: password nicht lesbar - ok';
--       END;
--       -- Umleitung: alte App schreibt Kennwort in supplier_configs
--       UPDATE public.supplier_configs SET password = '__probe__' WHERE id = v_sid;
--       SELECT count(*) INTO v_n FROM public.supplier_configs WHERE id = v_sid AND password IS NOT NULL;
--       IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER Klartext blieb in supplier_configs'; END IF;
--       SELECT count(*) INTO v_n FROM public.supplier_credentials WHERE supplier_id = v_sid AND has_password;
--       IF v_n <> 1 THEN RAISE EXCEPTION 'PROBE FEHLER Umleitung kam nicht an'; END IF;
--     ELSE
--       IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER % sieht % Zeilen (soll 0)', v_rolle, v_n; END IF;
--       SELECT count(*) INTO v_n FROM public.supplier_configs WHERE username IS NOT NULL OR password IS NOT NULL;
--       IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER % sieht Klartext in supplier_configs', v_rolle; END IF;
--       BEGIN
--         INSERT INTO public.supplier_credentials (supplier_id, password) VALUES (gen_random_uuid(), 'x');
--         RAISE EXCEPTION 'PROBE FEHLER % durfte supplier_credentials schreiben', v_rolle;
--       EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe %: Schreiben abgewiesen - ok', v_rolle;
--       END;
--     END IF;
--     RAISE NOTICE 'Probe %: ok', v_rolle;
--     EXECUTE 'RESET ROLE';
--   END LOOP;
--   -- service_role ueber PostgREST: Umleitung verwirft den Wert (nur die Function schreibt, nach Admin-Pruefung)
--   SELECT s.id INTO v_sid FROM public.supplier_configs s
--    WHERE NOT EXISTS (SELECT 1 FROM public.supplier_credentials c WHERE c.supplier_id = s.id) LIMIT 1;
--   IF v_sid IS NOT NULL THEN
--     PERFORM set_config('request.jwt.claims', '{"role":"service_role"}', true);
--     EXECUTE 'SET LOCAL ROLE service_role';
--     UPDATE public.supplier_configs SET password = '__probe__' WHERE id = v_sid;
--     EXECUTE 'RESET ROLE';
--     SELECT count(*) INTO v_n FROM public.supplier_credentials WHERE supplier_id = v_sid;
--     IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER service_role-Schreiben wurde umgeleitet (soll verworfen werden)'; END IF;
--     SELECT count(*) INTO v_n FROM public.supplier_configs WHERE id = v_sid AND password IS NOT NULL;
--     IF v_n <> 0 THEN RAISE EXCEPTION 'PROBE FEHLER Klartext blieb in supplier_configs (service_role)'; END IF;
--     RAISE NOTICE 'Probe service_role: verworfen - ok';
--   END IF;
--   -- anon: keinerlei Recht auf der Tabelle
--   PERFORM set_config('request.jwt.claims', '{"role":"anon"}', true);
--   EXECUTE 'SET LOCAL ROLE anon';
--   BEGIN
--     EXECUTE 'SELECT count(*) FROM public.supplier_credentials';
--     RAISE EXCEPTION 'PROBE FEHLER anon kann supplier_credentials lesen';
--   EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'Probe anon: abgewiesen - ok';
--   END;
--   EXECUTE 'RESET ROLE';
-- END $probe$;
-- ROLLBACK;
