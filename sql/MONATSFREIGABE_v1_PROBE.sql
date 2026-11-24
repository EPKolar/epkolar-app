-- MONATSFREIGABE_v1_PROBE.sql - GENERIERT von sql/_mf_probe_bauen.py. ENTWURF woertlich + Gegenmessung je Rolle
-- in EINER Transaktion; endet IMMER mit RAISE EXCEPTION 'PROBE_ERGEBNIS ...' -> nichts bleibt bestehen.
-- Zurueck zum Eigentuemer immer mit set_config('request.jwt.claims','{}',true) (nie '', guard_users_privilege parst JSON).
BEGIN;
-- =====================================================================================
-- MONATSFREIGABE_v1_ENTWURF.sql  -  Monatsfreigabe (Stempelstunden + Entfernungszulagen), GF-Auftrag 24.11.2026
-- NUR ENTWURF. NICHT eingespielt. Einspielen nur mit ausdruecklichem Ja von Sebastian.
-- ERSETZT den gestaffelten Paket-4-Entwurf sql/FINKZEIT_OHNE_PL_v1_* (Zweig sql/finkzeit-ohne-pl):
-- Projektleitung verliert den Zugriff auf finkzeit auch hier.
--
-- WAS ES AENDERT
--   1. finkzeit: neue Spalten (Frist, Admin-Freigabe, Monteur-Freigabe, Schnappschuss, Pfade, Gruende, Vermerk),
--      Status-CHECK (Alt-Werte entwurf/hochgeladen/genehmigt bleiben erlaubt - manueller Upload als Rueckfall),
--      eindeutig je Mitarbeiter und Monat fuer Freigabe-Zeilen.
--   2. finkzeit_verlauf: Protokoll (wer, wann, was) - nur Buero/Admin lesen, schreiben nur der Trigger.
--   3. monatsfreigabe_einstellungen: eine Zeile, erinnerung_tage (Abstand der Erinnerung vor der Frist).
--      Bewusst NICHT system_config: guard_admin_only erlaubt dem Buero dort nur die drei Zulagensaetze.
--   4. Policies auf finkzeit ERSETZT (alle TO authenticated, alle mit aktivem Konto):
--        finkzeit_buero_admin    ALL     Buero/Admin
--        finkzeit_monteur_select SELECT  Monteur/Helfer: NUR eigene Zeile, NUR ab zur_freigabe (zur_freigabe, freigegeben)
--        finkzeit_monteur_update UPDATE  Monteur/Helfer: NUR eigene Zeile in zur_freigabe (bzw. freigegeben ohne PDF)
--      Projektleitung, Techniker, Lager: kein Zugriff.
--   5. Trigger zz_finkzeit_monatsfreigabe (BEFORE INSERT/UPDATE/DELETE): Zustandsautomat, Feld-Whitelist je Rolle,
--      Admin-only-Uebergang, Frist nie in der Vergangenheit, Sperre nach Freigabe (nur Admin mit Vermerk).
--      Ohne JWT / service_role / Eigentuemer: frei (Muster Paket 1).
--   6. Storage epkolar-docs, Praefix monatsfreigabe/ (andere Ordner unveraendert, vorher/nachher im Bericht):
--      Monteur darf NUR seine Unterschrift (monatsfreigabe/<eigene monteur_id>/*_unterschrift_*.png) anlegen;
--      Projektleitung dort weder lesen noch schreiben; UPDATE/DELETE unter monatsfreigabe/ fuer NIEMANDEN
--      (abgelegte Unterschriften und PDFs sind unveraenderlich, Upload ohne Ueberschreiben).
--   Sicherheits-Review 24.11. (3x MEDIUM) eingearbeitet: Frist nach Admin-Freigabe nur verlaengerbar, Frist bei
--   Admin-Freigabe gespeichert (frist_bei_admin_freigabe), Pruefsumme freigabe_hash, PDF nur vom Buero/Admin.
--
-- STATUS (eine Spalte):
--   in_arbeit -> zur_admin_freigabe (Buero/Admin, Frist Pflicht, nicht in der Vergangenheit, Schnappschuss Pflicht)
--   zur_admin_freigabe -> zur_freigabe (NUR role admin; Frist >= heute + erinnerung_tage, sonst "zu knapp")
--   zur_admin_freigabe -> in_arbeit (Buero/Admin, Grund Pflicht)
--   zur_freigabe -> freigegeben (Monteur eigene Zeile, Unterschrift in Storage Pflicht;
--                                ODER Buero/Admin erst NACH Fristablauf -> ohne_monteur=true)
--   zur_freigabe -> in_arbeit (Monteur "Stimmt nicht" mit Grund; oder Buero/Admin mit Grund)
--   freigegeben: gesperrt. Nur Admin mit neuem Vermerk; einmalig darf der PDF-Pfad nachgetragen werden.
--   "Heute" = Datum Europe/Vienna.
-- RUECKNAHME: sql/MONATSFREIGABE_v1_RUECKNAHME.sql
-- =====================================================================================

-- 0. Vorpruefung
DO $vor$
BEGIN
  IF (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit') <> 1
     OR NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit' AND policyname='finkzeit_staff_all') THEN
    RAISE EXCEPTION 'Vorpruefung: erwartet genau die Policy finkzeit_staff_all auf finkzeit (Paket 4 schon eingespielt?)'; END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='finkzeit' AND column_name='freigabe_bis') THEN
    RAISE EXCEPTION 'Vorpruefung: Spalte freigabe_bis existiert schon - schon angewendet?'; END IF;
  IF EXISTS (SELECT 1 FROM public.finkzeit WHERE coalesce(status,'') NOT IN ('entwurf','hochgeladen','genehmigt','offen','')) THEN
    RAISE EXCEPTION 'Vorpruefung: unbekannte Statuswerte in finkzeit'; END IF;
  IF (SELECT count(*) FROM pg_policies WHERE schemaname='storage' AND tablename='objects'
        AND policyname IN ('epkolar_docs_select','epkolar_docs_insert','epkolar_docs_update','epkolar_docs_delete')) <> 4 THEN
    RAISE EXCEPTION 'Vorpruefung: erwartet die 4 Policies epkolar_docs_* auf storage.objects'; END IF;
END $vor$;

-- 1. Spalten
ALTER TABLE public.finkzeit
  ADD COLUMN freigabe_bis       date,
  ADD COLUMN admin_freigabe_am  timestamptz,
  ADD COLUMN admin_freigabe_von text,
  ADD COLUMN freigegeben_am     timestamptz,
  ADD COLUMN freigegeben_von    text,
  ADD COLUMN ohne_monteur       boolean NOT NULL DEFAULT false,
  ADD COLUMN beanstandung       text,
  ADD COLUMN rueckgabe_grund    text,
  ADD COLUMN snapshot           jsonb,
  ADD COLUMN signatur_pfad      text,
  ADD COLUMN pdf_pfad           text,
  ADD COLUMN admin_vermerk      text,
  ADD COLUMN frist_bei_admin_freigabe date,
  ADD COLUMN freigabe_hash      text;
UPDATE public.finkzeit SET status='entwurf' WHERE status IS NULL OR status='';
ALTER TABLE public.finkzeit ADD CONSTRAINT finkzeit_status_check CHECK (status IN
  ('entwurf','offen','hochgeladen','genehmigt','in_arbeit','zur_admin_freigabe','zur_freigabe','freigegeben'));
ALTER TABLE public.finkzeit ADD CONSTRAINT finkzeit_period_check CHECK (
  status NOT IN ('in_arbeit','zur_admin_freigabe','zur_freigabe','freigegeben') OR period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$');
CREATE UNIQUE INDEX finkzeit_freigabe_je_monat ON public.finkzeit (worker_id, period)
  WHERE status IN ('in_arbeit','zur_admin_freigabe','zur_freigabe','freigegeben');

-- 2. Verlauf
CREATE TABLE public.finkzeit_verlauf (
  id          bigserial PRIMARY KEY,
  finkzeit_id text NOT NULL,
  am          timestamptz NOT NULL DEFAULT now(),
  von         text,
  rolle       text,
  akt         text NOT NULL,
  alt         text,
  neu         text,
  text        text
);
CREATE INDEX finkzeit_verlauf_fz ON public.finkzeit_verlauf (finkzeit_id, am);
ALTER TABLE public.finkzeit_verlauf ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.finkzeit_verlauf FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.finkzeit_verlauf TO authenticated;
CREATE POLICY finkzeit_verlauf_buero_admin ON public.finkzeit_verlauf FOR SELECT TO authenticated
  USING ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('admin','buero'));

-- 3. Einstellungen
CREATE TABLE public.monatsfreigabe_einstellungen (
  id              smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  erinnerung_tage integer NOT NULL DEFAULT 3 CHECK (erinnerung_tage BETWEEN 0 AND 30),
  geaendert_am    timestamptz NOT NULL DEFAULT now(),
  geaendert_von   text
);
INSERT INTO public.monatsfreigabe_einstellungen (id, erinnerung_tage) VALUES (1, 3);
ALTER TABLE public.monatsfreigabe_einstellungen ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.monatsfreigabe_einstellungen FROM PUBLIC, anon, authenticated;
GRANT SELECT, UPDATE (erinnerung_tage) ON TABLE public.monatsfreigabe_einstellungen TO authenticated;
CREATE POLICY mf_einst_lesen ON public.monatsfreigabe_einstellungen FOR SELECT TO authenticated
  USING ((SELECT public.users_konto_aktiv()));
CREATE POLICY mf_einst_aendern ON public.monatsfreigabe_einstellungen FOR UPDATE TO authenticated
  USING ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('admin','buero'))
  WITH CHECK ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('admin','buero'));
CREATE OR REPLACE FUNCTION public._mf_einst_stempel()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $t$
BEGIN
  NEW.geaendert_am := now();
  NEW.geaendert_von := public.current_user_pk();
  RETURN NEW;
END $t$;
REVOKE ALL ON FUNCTION public._mf_einst_stempel() FROM PUBLIC, anon, authenticated;
CREATE TRIGGER zz_mf_einst_stempel BEFORE UPDATE ON public.monatsfreigabe_einstellungen
  FOR EACH ROW EXECUTE FUNCTION public._mf_einst_stempel();

-- 4. Policies finkzeit ERSETZT
DROP POLICY finkzeit_staff_all ON public.finkzeit;
CREATE POLICY finkzeit_buero_admin ON public.finkzeit FOR ALL TO authenticated
  USING ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('admin','buero'))
  WITH CHECK ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('admin','buero'));
CREATE POLICY finkzeit_monteur_select ON public.finkzeit FOR SELECT TO authenticated
  USING ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('monteur','helfer')
         AND worker_id = public.current_monteur_id() AND status IN ('zur_freigabe','freigegeben'));
CREATE POLICY finkzeit_monteur_update ON public.finkzeit FOR UPDATE TO authenticated
  USING ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('monteur','helfer')
         AND worker_id = public.current_monteur_id() AND status = 'zur_freigabe')
  WITH CHECK ((SELECT public.users_konto_aktiv()) AND public.current_user_role() IN ('monteur','helfer')
         AND worker_id = public.current_monteur_id() AND status IN ('zur_freigabe','freigegeben'));

-- 5. Zustandsautomat
CREATE OR REPLACE FUNCTION public._finkzeit_monatsfreigabe()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $t$
DECLARE
  v_neu_set constant text[] := ARRAY['in_arbeit','zur_admin_freigabe','zur_freigabe','freigegeben'];
  v_server constant text[] := ARRAY['admin_freigabe_am','admin_freigabe_von','freigegeben_am','freigegeben_von','ohne_monteur','signatur_pfad','pdf_pfad'];
  v_rolle text; v_pk text; v_heute date; v_n int; v_alt jsonb; v_neu jsonb; v_k text; v_erlaubt text[];
  v_grund text; v_pfx text;
BEGIN
  IF auth.uid() IS NULL OR coalesce(auth.role(),'') <> 'authenticated' THEN RETURN COALESCE(NEW, OLD); END IF;
  v_rolle := public.current_user_role();
  v_pk := public.current_user_pk();
  v_heute := (now() AT TIME ZONE 'Europe/Vienna')::date;
  SELECT erinnerung_tage INTO v_n FROM public.monatsfreigabe_einstellungen WHERE id = 1;
  v_n := coalesce(v_n, 3);

  IF TG_OP = 'DELETE' THEN
    IF OLD.status = ANY (v_neu_set) AND OLD.status <> 'in_arbeit' THEN
      RAISE EXCEPTION 'Monatsfreigabe: nur Abrechnungen in Arbeit duerfen geloescht werden' USING ERRCODE = '42501'; END IF;
    RETURN OLD;
  END IF;

  IF TG_OP = 'INSERT' THEN
    IF NOT (NEW.status = ANY (v_neu_set)) THEN RETURN NEW; END IF;   -- Alt-Weg (manueller Upload)
    IF NEW.status <> 'in_arbeit' THEN
      RAISE EXCEPTION 'Monatsfreigabe: neue Abrechnung beginnt in_arbeit' USING ERRCODE = '42501'; END IF;
    IF coalesce(NEW.worker_id,'') = '' THEN RAISE EXCEPTION 'Monatsfreigabe: Mitarbeiter fehlt'; END IF;
    IF NEW.freigabe_bis IS NOT NULL AND NEW.freigabe_bis < v_heute THEN
      RAISE EXCEPTION 'Monatsfreigabe: Frist liegt in der Vergangenheit'; END IF;
    NEW.admin_freigabe_am := NULL; NEW.admin_freigabe_von := NULL; NEW.freigegeben_am := NULL; NEW.freigegeben_von := NULL;
    NEW.ohne_monteur := false; NEW.signatur_pfad := NULL; NEW.pdf_pfad := NULL;
    INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, neu) VALUES (NEW.id, v_pk, v_rolle, 'angelegt', NEW.status);
    IF NEW.freigabe_bis IS NOT NULL THEN
      INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, neu) VALUES (NEW.id, v_pk, v_rolle, 'frist', NEW.freigabe_bis::text); END IF;
    RETURN NEW;
  END IF;

  -- UPDATE
  IF NOT (OLD.status = ANY (v_neu_set)) AND NOT (NEW.status = ANY (v_neu_set)) THEN RETURN NEW; END IF;  -- Alt-Weg
  IF (OLD.status = ANY (v_neu_set)) <> (NEW.status = ANY (v_neu_set)) THEN
    RAISE EXCEPTION 'Monatsfreigabe: Wechsel zwischen manuellem Upload und Freigabe nicht erlaubt' USING ERRCODE = '42501'; END IF;
  IF NEW.id IS DISTINCT FROM OLD.id OR NEW.worker_id IS DISTINCT FROM OLD.worker_id OR NEW.period IS DISTINCT FROM OLD.period THEN
    RAISE EXCEPTION 'Monatsfreigabe: Mitarbeiter/Monat sind fest' USING ERRCODE = '42501'; END IF;

  -- ---------- Monteur / Helfer ----------
  IF v_rolle IN ('monteur','helfer') THEN
    IF OLD.worker_id IS DISTINCT FROM public.current_monteur_id() THEN
      RAISE EXCEPTION 'Monatsfreigabe: fremde Abrechnung' USING ERRCODE = '42501'; END IF;
    v_pfx := 'monatsfreigabe/' || OLD.worker_id || '/';
    IF OLD.status = 'zur_freigabe' THEN
      v_erlaubt := ARRAY['status','signatur_pfad','beanstandung'];
      v_alt := to_jsonb(OLD); v_neu := to_jsonb(NEW);
      FOREACH v_k IN ARRAY v_erlaubt LOOP v_alt := v_alt - v_k; v_neu := v_neu - v_k; END LOOP;
      IF v_alt IS DISTINCT FROM v_neu THEN
        RAISE EXCEPTION 'Monatsfreigabe: Monteur darf nur freigeben oder beanstanden' USING ERRCODE = '42501'; END IF;
      IF NEW.status = 'freigegeben' THEN
        IF coalesce(NEW.signatur_pfad,'') = '' OR left(NEW.signatur_pfad, length(v_pfx)) <> v_pfx
           OR NOT EXISTS (SELECT 1 FROM storage.objects o WHERE o.bucket_id = 'epkolar-docs' AND o.name = NEW.signatur_pfad) THEN
          RAISE EXCEPTION 'Monatsfreigabe: Unterschrift fehlt' USING ERRCODE = '42501'; END IF;
        NEW.beanstandung := OLD.beanstandung;
        NEW.freigegeben_am := now(); NEW.freigegeben_von := v_pk; NEW.ohne_monteur := false;
        NEW.freigabe_hash := md5(coalesce(OLD.snapshot::text,'') || '|' || NEW.signatur_pfad || '|' || coalesce(OLD.freigabe_bis::text,''));
        INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, alt, neu) VALUES (NEW.id, v_pk, v_rolle, 'status', OLD.status, NEW.status);
        RETURN NEW;
      ELSIF NEW.status = 'in_arbeit' THEN
        v_grund := btrim(coalesce(NEW.beanstandung,''));
        IF length(v_grund) < 3 THEN RAISE EXCEPTION 'Monatsfreigabe: Begruendung fehlt' USING ERRCODE = '42501'; END IF;
        NEW.signatur_pfad := OLD.signatur_pfad; NEW.beanstandung := v_grund;
        INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, alt, neu, text) VALUES (NEW.id, v_pk, v_rolle, 'beanstandet', OLD.status, NEW.status, v_grund);
        RETURN NEW;
      END IF;
      RAISE EXCEPTION 'Monatsfreigabe: Uebergang nicht erlaubt' USING ERRCODE = '42501';
    END IF;  -- PDF legt nur Buero/Admin ab (aus Schnappschuss + Unterschrift), nie der Monteur
    RAISE EXCEPTION 'Monatsfreigabe: nach der Freigabe gesperrt' USING ERRCODE = '42501';
  END IF;

  -- ---------- Buero / Admin ----------
  IF v_rolle NOT IN ('buero','admin') THEN
    RAISE EXCEPTION 'Monatsfreigabe: keine Berechtigung' USING ERRCODE = '42501'; END IF;

  IF OLD.status = 'freigegeben' THEN
    -- PDF-Pfad nachtragen (einmalig), sonst nur Admin mit neuem Vermerk
    v_alt := to_jsonb(OLD) - 'pdf_pfad'; v_neu := to_jsonb(NEW) - 'pdf_pfad';
    IF v_alt IS NOT DISTINCT FROM v_neu AND coalesce(OLD.pdf_pfad,'') = '' AND coalesce(NEW.pdf_pfad,'') <> ''
       AND left(NEW.pdf_pfad, length('monatsfreigabe/' || OLD.worker_id || '/')) = 'monatsfreigabe/' || OLD.worker_id || '/'
       AND EXISTS (SELECT 1 FROM storage.objects o WHERE o.bucket_id = 'epkolar-docs' AND o.name = NEW.pdf_pfad) THEN
      RETURN NEW; END IF;
    IF v_rolle <> 'admin' OR btrim(coalesce(NEW.admin_vermerk,'')) = '' OR NEW.admin_vermerk IS NOT DISTINCT FROM OLD.admin_vermerk THEN
      RAISE EXCEPTION 'Monatsfreigabe: freigegeben und gesperrt (aendern nur Admin mit Vermerk)' USING ERRCODE = '42501'; END IF;
    INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, alt, neu, text) VALUES (NEW.id, v_pk, v_rolle, 'vermerk', OLD.status, NEW.status, btrim(NEW.admin_vermerk));
    RETURN NEW;
  END IF;

  -- Serverfelder sind fuer Buero/Admin nicht schreibbar
  NEW.admin_freigabe_am := OLD.admin_freigabe_am; NEW.admin_freigabe_von := OLD.admin_freigabe_von;
  NEW.freigegeben_am := OLD.freigegeben_am; NEW.freigegeben_von := OLD.freigegeben_von;
  NEW.ohne_monteur := OLD.ohne_monteur; NEW.signatur_pfad := OLD.signatur_pfad; NEW.pdf_pfad := OLD.pdf_pfad;
  NEW.frist_bei_admin_freigabe := OLD.frist_bei_admin_freigabe; NEW.freigabe_hash := OLD.freigabe_hash;

  -- Frist: nie in der Vergangenheit, jede Aenderung protokolliert
  IF NEW.freigabe_bis IS DISTINCT FROM OLD.freigabe_bis THEN
    IF NEW.freigabe_bis IS NULL AND NEW.status <> 'in_arbeit' THEN RAISE EXCEPTION 'Monatsfreigabe: Frist ist Pflicht'; END IF;
    IF NEW.freigabe_bis IS NOT NULL AND NEW.freigabe_bis < v_heute THEN RAISE EXCEPTION 'Monatsfreigabe: Frist liegt in der Vergangenheit'; END IF;
    IF OLD.status = 'zur_freigabe' AND NEW.freigabe_bis < OLD.freigabe_bis THEN
      RAISE EXCEPTION 'Monatsfreigabe: nach der Admin-Freigabe darf die Frist nur verlaengert werden' USING ERRCODE = '42501'; END IF;
    INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, alt, neu) VALUES (NEW.id, v_pk, v_rolle, 'frist', OLD.freigabe_bis::text, NEW.freigabe_bis::text);
  END IF;

  IF NEW.status = OLD.status THEN
    IF OLD.status = 'in_arbeit' THEN RETURN NEW; END IF;
    v_alt := to_jsonb(OLD) - 'freigabe_bis' - 'notiz'; v_neu := to_jsonb(NEW) - 'freigabe_bis' - 'notiz';
    IF v_alt IS DISTINCT FROM v_neu THEN
      RAISE EXCEPTION 'Monatsfreigabe: in diesem Stand nur die Frist aenderbar' USING ERRCODE = '42501'; END IF;
    RETURN NEW;
  END IF;

  IF OLD.status = 'in_arbeit' AND NEW.status = 'zur_admin_freigabe' THEN
    IF NEW.freigabe_bis IS NULL OR NEW.freigabe_bis < v_heute THEN RAISE EXCEPTION 'Monatsfreigabe: Frist fehlt oder liegt in der Vergangenheit'; END IF;
    IF NEW.snapshot IS NULL OR jsonb_typeof(NEW.snapshot) <> 'object' THEN RAISE EXCEPTION 'Monatsfreigabe: Zahlen fehlen'; END IF;
    NEW.rueckgabe_grund := NULL; NEW.beanstandung := NULL;
    NEW.admin_freigabe_am := NULL; NEW.admin_freigabe_von := NULL; NEW.frist_bei_admin_freigabe := NULL;
  ELSIF OLD.status = 'zur_admin_freigabe' AND NEW.status = 'zur_freigabe' THEN
    IF v_rolle <> 'admin' THEN RAISE EXCEPTION 'Monatsfreigabe: nur der Admin gibt an den Monteur frei' USING ERRCODE = '42501'; END IF;
    v_alt := to_jsonb(OLD) - 'freigabe_bis' - 'status'; v_neu := to_jsonb(NEW) - 'freigabe_bis' - 'status';
    IF v_alt IS DISTINCT FROM v_neu THEN RAISE EXCEPTION 'Monatsfreigabe: Admin-Freigabe aendert keine Zahlen' USING ERRCODE = '42501'; END IF;
    IF NEW.freigabe_bis IS NULL OR NEW.freigabe_bis < v_heute + v_n THEN
      RAISE EXCEPTION 'Monatsfreigabe: Frist abgelaufen oder zu knapp (mindestens % Tage) - bitte zuerst anpassen', v_n USING ERRCODE = '42501'; END IF;
    NEW.admin_freigabe_am := now(); NEW.admin_freigabe_von := v_pk; NEW.frist_bei_admin_freigabe := NEW.freigabe_bis;
  ELSIF OLD.status IN ('zur_admin_freigabe','zur_freigabe') AND NEW.status = 'in_arbeit' THEN
    v_grund := btrim(coalesce(NEW.rueckgabe_grund,''));
    IF length(v_grund) < 3 OR NEW.rueckgabe_grund IS NOT DISTINCT FROM OLD.rueckgabe_grund THEN
      RAISE EXCEPTION 'Monatsfreigabe: Grund fuer die Rueckgabe fehlt' USING ERRCODE = '42501'; END IF;
    NEW.rueckgabe_grund := v_grund;
    INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, alt, neu, text) VALUES (NEW.id, v_pk, v_rolle, 'zurueck', OLD.status, NEW.status, v_grund);
    RETURN NEW;
  ELSIF OLD.status = 'zur_freigabe' AND NEW.status = 'freigegeben' THEN
    IF OLD.freigabe_bis IS NULL OR OLD.freigabe_bis >= v_heute OR coalesce(OLD.frist_bei_admin_freigabe, OLD.freigabe_bis) >= v_heute THEN
      RAISE EXCEPTION 'Monatsfreigabe: ohne Monteur erst nach Ablauf der Frist' USING ERRCODE = '42501'; END IF;
    v_alt := to_jsonb(OLD) - 'status' - 'notiz'; v_neu := to_jsonb(NEW) - 'status' - 'notiz';
    IF v_alt IS DISTINCT FROM v_neu THEN RAISE EXCEPTION 'Monatsfreigabe: Freigabe aendert keine Zahlen' USING ERRCODE = '42501'; END IF;
    NEW.ohne_monteur := true; NEW.freigegeben_am := now(); NEW.freigegeben_von := v_pk;
    NEW.freigabe_hash := md5(coalesce(OLD.snapshot::text,'') || '|ohne_monteur|' || coalesce(OLD.freigabe_bis::text,''));
  ELSE
    RAISE EXCEPTION 'Monatsfreigabe: Uebergang % -> % nicht erlaubt', OLD.status, NEW.status USING ERRCODE = '42501';
  END IF;
  INSERT INTO public.finkzeit_verlauf (finkzeit_id, von, rolle, akt, alt, neu) VALUES (NEW.id, v_pk, v_rolle, 'status', OLD.status, NEW.status);
  RETURN NEW;
END $t$;
REVOKE ALL ON FUNCTION public._finkzeit_monatsfreigabe() FROM PUBLIC, anon, authenticated;
CREATE TRIGGER zz_finkzeit_monatsfreigabe BEFORE INSERT OR UPDATE OR DELETE ON public.finkzeit
  FOR EACH ROW EXECUTE FUNCTION public._finkzeit_monatsfreigabe();

-- 5b. Stimmt nicht: als RPC, weil die Zeile danach (in_arbeit) fuer den Monteur unsichtbar ist und ein direktes UPDATE
--     an der RLS-Pruefung der neuen Zeile scheitert (gemessen in der Probe 24.11.). Der Trigger prueft weiter (Rolle, Grund).
CREATE OR REPLACE FUNCTION public.monatsfreigabe_beanstanden(p_id text, p_grund text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $f$
BEGIN
  IF NOT public.users_konto_aktiv() OR coalesce(public.current_user_role(),'') NOT IN ('monteur','helfer') THEN
    RAISE EXCEPTION 'Monatsfreigabe: keine Berechtigung' USING ERRCODE = '42501'; END IF;
  UPDATE public.finkzeit SET status = 'in_arbeit', beanstandung = p_grund
   WHERE id = p_id AND worker_id = public.current_monteur_id() AND status = 'zur_freigabe';
  IF NOT FOUND THEN RAISE EXCEPTION 'Monatsfreigabe: Abrechnung nicht zur Freigabe' USING ERRCODE = '42501'; END IF;
END $f$;
REVOKE ALL ON FUNCTION public.monatsfreigabe_beanstanden(text, text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.monatsfreigabe_beanstanden(text, text) TO authenticated;

-- 6. Storage epkolar-docs: Praefix monatsfreigabe/
DROP POLICY epkolar_docs_select ON storage.objects;
DROP POLICY epkolar_docs_insert ON storage.objects;
DROP POLICY epkolar_docs_update ON storage.objects;
DROP POLICY epkolar_docs_delete ON storage.objects;
CREATE POLICY epkolar_docs_select ON storage.objects FOR SELECT TO authenticated
  USING (bucket_id = 'epkolar-docs'
         AND ((public.is_staff() AND NOT ((storage.foldername(name))[1] = 'monatsfreigabe' AND public.current_user_role() = 'projektleiter'))
              OR (storage.foldername(name))[2] = public.current_monteur_id()));
CREATE POLICY epkolar_docs_insert ON storage.objects FOR INSERT TO authenticated
  WITH CHECK (bucket_id = 'epkolar-docs' AND public.is_staff()
              AND NOT ((storage.foldername(name))[1] = 'monatsfreigabe' AND public.current_user_role() = 'projektleiter'));
CREATE POLICY epkolar_docs_update ON storage.objects FOR UPDATE TO authenticated
  USING (bucket_id = 'epkolar-docs' AND public.is_staff() AND (storage.foldername(name))[1] IS DISTINCT FROM 'monatsfreigabe')
  WITH CHECK (bucket_id = 'epkolar-docs' AND public.is_staff() AND (storage.foldername(name))[1] IS DISTINCT FROM 'monatsfreigabe');
CREATE POLICY epkolar_docs_delete ON storage.objects FOR DELETE TO authenticated
  USING (bucket_id = 'epkolar-docs' AND public.is_staff() AND (storage.foldername(name))[1] IS DISTINCT FROM 'monatsfreigabe');
CREATE POLICY monatsfreigabe_monteur_insert ON storage.objects FOR INSERT TO authenticated
  WITH CHECK (bucket_id = 'epkolar-docs' AND (SELECT public.users_konto_aktiv())
              AND public.current_user_role() IN ('monteur','helfer')
              AND (storage.foldername(name))[1] = 'monatsfreigabe'
              AND (storage.foldername(name))[2] = public.current_monteur_id()
              AND name LIKE ('monatsfreigabe/' || public.current_monteur_id() || '/%\_unterschrift\_%.png'));

-- 7. Nachpruefung
DO $nach$
BEGIN
  IF (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit') <> 3 THEN
    RAISE EXCEPTION 'Nachpruefung: erwartet 3 Policies auf finkzeit'; END IF;
  IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename IN ('finkzeit','finkzeit_verlauf','monatsfreigabe_einstellungen')
              AND NOT ('authenticated' = ANY (roles))) THEN
    RAISE EXCEPTION 'Nachpruefung: Policy nicht TO authenticated'; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid='public.finkzeit'::regclass AND tgname='zz_finkzeit_monatsfreigabe') THEN
    RAISE EXCEPTION 'Nachpruefung: Trigger fehlt'; END IF;
END $nach$;

DO $probe$
DECLARE r text := ''; v_n int; v_got text; v_msg text; v_ok int := 0; v_fail int := 0; v_h date := (now() AT TIME ZONE 'Europe/Vienna')::date;
  v_ua uuid; v_ub uuid; v_ubu uuid; v_uad uuid; v_ut uuid; v_upl uuid; v_a text; v_b text; v_pa text; v_pbu text; v_pad text;
BEGIN
  SELECT auth_user_id, monteur_id, id INTO v_ua, v_a, v_pa FROM public.users WHERE role='monteur' AND auth_user_id IS NOT NULL AND coalesce(monteur_id,'')<>'' AND coalesce(active,0)=1 AND coalesce(locked,0)=0 ORDER BY id LIMIT 1;
  SELECT auth_user_id, monteur_id INTO v_ub, v_b FROM public.users WHERE role='monteur' AND auth_user_id IS NOT NULL AND coalesce(monteur_id,'')<>'' AND monteur_id<>v_a ORDER BY id LIMIT 1;
  SELECT auth_user_id, id INTO v_ubu, v_pbu FROM public.users WHERE role='buero' AND auth_user_id IS NOT NULL AND coalesce(active,0)=1 AND coalesce(locked,0)=0 ORDER BY id LIMIT 1;
  SELECT auth_user_id, id INTO v_uad, v_pad FROM public.users WHERE role='admin' AND auth_user_id IS NOT NULL AND coalesce(active,0)=1 AND coalesce(locked,0)=0 ORDER BY id LIMIT 1;
  SELECT auth_user_id INTO v_ut FROM public.users WHERE role='techniker' AND auth_user_id IS NOT NULL ORDER BY id LIMIT 1;
  SELECT auth_user_id INTO v_upl FROM public.users WHERE role='projektleiter' AND auth_user_id IS NOT NULL ORDER BY id LIMIT 1;
  IF v_ua IS NULL OR v_ub IS NULL OR v_ubu IS NULL OR v_uad IS NULL OR v_ut IS NULL OR v_upl IS NULL THEN RAISE EXCEPTION 'PROBE_ERGEBNIS Konten fehlen'; END IF;
  PERFORM set_config('request.jwt.claims', '{}', true);
  EXECUTE 'INSERT INTO public.finkzeit(id,worker_id,period,jahr,monat,status,freigabe_bis,snapshot) VALUES (''p_a_zf'','||quote_literal(v_a)||',''1999-01'',1999,0,''zur_freigabe'','||quote_literal(v_h)||'::date'||'+10,''{"tage":[],"summe":{"min":0}}''::jsonb),(''p_a_zf2'','||quote_literal(v_a)||',''1999-02'',1999,1,''zur_freigabe'','||quote_literal(v_h)||'::date'||'+10,''{"tage":[],"summe":{"min":0}}''::jsonb),(''p_b_zf'','||quote_literal(v_b)||',''1999-01'',1999,0,''zur_freigabe'','||quote_literal(v_h)||'::date'||'+10,''{"tage":[],"summe":{"min":0}}''::jsonb),(''p_a_ia'','||quote_literal(v_a)||',''1999-03'',1999,2,''in_arbeit'',NULL,NULL),(''p_a_zaf'','||quote_literal(v_a)||',''1999-04'',1999,3,''zur_admin_freigabe'','||quote_literal(v_h)||'::date'||'+1,''{"tage":[],"summe":{"min":0}}''::jsonb),(''p_a_zaf2'','||quote_literal(v_a)||',''1999-05'',1999,4,''zur_admin_freigabe'','||quote_literal(v_h)||'::date'||'+10,''{"tage":[],"summe":{"min":0}}''::jsonb),(''p_a_fg'','||quote_literal(v_a)||',''1999-06'',1999,5,''freigegeben'','||quote_literal(v_h)||'::date'||'+10,''{"tage":[],"summe":{"min":0}}''::jsonb),(''p_b_ia'','||quote_literal(v_b)||',''1999-07'',1999,6,''in_arbeit'',NULL,NULL)';
  EXECUTE 'INSERT INTO storage.objects(bucket_id,name,owner) VALUES (''epkolar-docs'',''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_sig.png'','||quote_literal(v_ua)||')';
  EXECUTE 'UPDATE public.monatsfreigabe_einstellungen SET erinnerung_tage=3 WHERE id=1';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ua,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id LIKE ''p\_%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n3' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_sieht_eigene_ab_zur_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id IN (''p_a_ia'',''p_a_zaf'',''p_a_zaf2'')' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_sieht_nichts_vor_admin_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_b_zf''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_fremde_zeile_lesen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'',signatur_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_sig.png'' WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_fremde_zeile_freigeben=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_freigabe_ohne_unterschrift=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'',signatur_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/gibtsnicht.png'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_freigabe_unterschrift_nicht_in_storage=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'',signatur_pfad=''monatsfreigabe/''||'||quote_literal(v_b)||'||''/p_sig.png'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_freigabe_fremder_unterschriftspfad=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET snapshot=''{"x":1}''::jsonb WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_zahlen_aendern=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET freigabe_bis='||quote_literal(v_h)||'::date'||'+30 WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_frist_aendern=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'',signatur_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_sig.png'' WHERE id=''p_a_ia'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_freigabe_vor_zur_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_freigabe'' WHERE id=''p_a_zaf2'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_admin_uebergang=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''in_arbeit'',beanstandung=''Am 3. fehlt'' WHERE id=''p_a_zf2'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_beanstanden_direkt_update=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT public.monatsfreigabe_beanstanden(''p_a_zf2'','' '')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_beanstanden_ohne_grund=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT public.monatsfreigabe_beanstanden(''p_b_zf'',''Am 3. fehlt eine Stunde'')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_beanstanden_fremde=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT public.monatsfreigabe_beanstanden(''p_a_zf2'',''Am 3. fehlt eine Stunde'')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_beanstanden_mit_grund=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_a_zf2'' AND status=''in_arbeit'' AND beanstandung=''Am 3. fehlt eine Stunde''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_beanstandet=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ua,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'',signatur_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_sig.png'',freigegeben_von=''gefaelscht'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_freigabe_faelscht_serverfeld=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'',signatur_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_sig.png'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_freigabe_mit_unterschrift=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET beanstandung=''doch nicht'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_aenderung_nach_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET pdf_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_sig.png'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_pdf_pfad_nach_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_freigabe'' WHERE id=''p_a_fg'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_status_zurueck_nach_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_a_zf'' AND beanstandung IS NULL AND coalesce(pdf_pfad,'''')=''''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_monteur_aenderung_nicht_gespeichert=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_a_fg'' AND status=''freigegeben''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_freigegebene_bleibt_freigegeben=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ua,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'INSERT INTO public.finkzeit(id,worker_id,period,status) VALUES (''p_x'','||quote_literal(v_a)||',''1999-09'',''in_arbeit'')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_anlegen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'DELETE FROM public.finkzeit WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_loeschen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit_verlauf' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_verlauf_lesen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.monatsfreigabe_einstellungen SET erinnerung_tage=9 WHERE id=1'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_einstellung_aendern=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO storage.objects(bucket_id,name,owner) VALUES (''epkolar-docs'',''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_unterschrift_1.png'','||quote_literal(v_ua)||')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_storage_eigener_praefix=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO storage.objects(bucket_id,name,owner) VALUES (''epkolar-docs'',''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_freigabe.pdf'','||quote_literal(v_ua)||')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_storage_kein_pdf=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO storage.objects(bucket_id,name,owner) VALUES (''epkolar-docs'',''monatsfreigabe/''||'||quote_literal(v_b)||'||''/p_fremd.png'','||quote_literal(v_ua)||')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_storage_fremder_praefix=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO storage.objects(bucket_id,name,owner) VALUES (''epkolar-docs'',''docs/''||'||quote_literal(v_a)||'||''/p_doc.pdf'','||quote_literal(v_ua)||')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL mA_storage_docs_praefix=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_a_zf'' AND status=''freigegeben'' AND freigegeben_von='||quote_literal(v_pa)||' AND freigegeben_am IS NOT NULL AND ohne_monteur=false AND freigabe_hash IS NOT NULL AND coalesce(pdf_pfad,'''')=''''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_freigabe_server=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ut,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id LIKE ''p\_%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL tech_sieht=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET notiz=''x'' WHERE id LIKE ''p\_%'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL tech_aendert=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO public.finkzeit(id,worker_id,period,status) VALUES (''p_t'','||quote_literal(v_a)||',''1999-10'',''in_arbeit'')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL tech_anlegen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_upl,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id LIKE ''p\_%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pl_sieht=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET notiz=''x'' WHERE id LIKE ''p\_%'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pl_aendert=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO public.finkzeit(id,worker_id,period,status) VALUES (''p_p'','||quote_literal(v_a)||',''1999-10'',''in_arbeit'')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pl_anlegen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT count(*) FROM storage.objects WHERE bucket_id=''epkolar-docs'' AND name LIKE ''monatsfreigabe/%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pl_storage_lesen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO storage.objects(bucket_id,name,owner) VALUES (''epkolar-docs'',''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_pl.png'','||quote_literal(v_upl)||')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pl_storage_schreiben=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ubu,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id LIKE ''p\_%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n8' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_sieht_alle=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_freigabe'',freigabe_bis='||quote_literal(v_h)||'::date'||'+10 WHERE id=''p_a_zaf2'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_admin_uebergang_direkt=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET admin_freigabe_am=now(),admin_freigabe_von=''gefaelscht'',notiz=''n'' WHERE id=''p_a_ia'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_admin_felder_faelschen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_a_ia'' AND admin_freigabe_am IS NULL AND admin_freigabe_von IS NULL' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_admin_felder_unveraendert=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ubu,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_admin_freigabe'',freigabe_bis='||quote_literal(v_h)||'::date'||'-1,snapshot=''{"tage":[],"summe":{"min":0}}''::jsonb WHERE id=''p_a_ia'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_fertig_frist_vergangen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_admin_freigabe'',snapshot=''{"tage":[],"summe":{"min":0}}''::jsonb WHERE id=''p_a_ia'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_fertig_ohne_frist=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_admin_freigabe'',freigabe_bis='||quote_literal(v_h)||'::date'||'+10 WHERE id=''p_a_ia'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_fertig_ohne_zahlen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_admin_freigabe'',freigabe_bis='||quote_literal(v_h)||'::date'||'+10,snapshot=''{"tage":[],"summe":{"min":0}}''::jsonb WHERE id=''p_a_ia'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_fertig=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET freigabe_bis='||quote_literal(v_h)||'::date'||'-1 WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_frist_in_vergangenheit=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET freigabe_bis='||quote_literal(v_h)||'::date'||'+20 WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_frist_aendern=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET freigabe_bis='||quote_literal(v_h)||'::date'||'+15 WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_frist_vorziehen_nach_admin=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE storage.objects SET name=name WHERE bucket_id=''epkolar-docs'' AND name LIKE ''monatsfreigabe/%'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_storage_monatsfreigabe_aendern=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  EXECUTE 'SELECT set_config(''storage.allow_delete_query'',''true'',true)';
  EXECUTE 'INSERT INTO storage.objects(bucket_id,name) VALUES (''epkolar-docs'',''docs/''||'||quote_literal(v_a)||'||''/p_kontrolle.pdf'')';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ubu,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'DELETE FROM storage.objects WHERE bucket_id=''epkolar-docs'' AND name LIKE ''monatsfreigabe/%'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_storage_monatsfreigabe_loeschen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'DELETE FROM storage.objects WHERE bucket_id=''epkolar-docs'' AND name=''docs/''||'||quote_literal(v_a)||'||''/p_kontrolle.pdf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_storage_kontrolle_docs_loeschen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  EXECUTE 'SELECT set_config(''storage.allow_delete_query'',''false'',true)';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ubu,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'SELECT count(*) FROM storage.objects WHERE bucket_id=''epkolar-docs'' AND name LIKE ''monatsfreigabe/%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n2' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_storage_monatsfreigabe_lesen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET snapshot=''{"x":2}''::jsonb WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_zahlen_in_zur_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'' WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_ohne_monteur_vor_frist=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET notiz=''x'' WHERE id=''p_a_fg'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_aendert_freigegebene=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET admin_vermerk=''Buero will'' WHERE id=''p_a_fg'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_vermerk_freigegebene=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''in_arbeit'' WHERE id=''p_a_zaf2'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_zurueck_ohne_grund=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'DELETE FROM public.finkzeit WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_loescht_zur_freigabe=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT public.monatsfreigabe_beanstanden(''p_b_zf'',''Buero spielt Monteur'')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_rpc_beanstanden=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit_verlauf WHERE finkzeit_id IN (''p_b_zf'',''p_a_ia'')' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n3' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_verlauf_lesen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.monatsfreigabe_einstellungen SET erinnerung_tage=3 WHERE id=1'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_einstellung_aendern=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  EXECUTE 'UPDATE public.finkzeit SET freigabe_bis='||quote_literal(v_h)||'::date'||'-1,frist_bei_admin_freigabe='||quote_literal(v_h)||'::date'||'+10 WHERE id=''p_b_zf''';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ubu,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'' WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_ohne_monteur_frist_bei_admin_laeuft=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  EXECUTE 'UPDATE public.finkzeit SET freigabe_bis='||quote_literal(v_h)||'::date'||'-1,frist_bei_admin_freigabe='||quote_literal(v_h)||'::date'||'-1 WHERE id=''p_b_zf''';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ubu,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''freigegeben'' WHERE id=''p_b_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_ohne_monteur_nach_frist=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_b_zf'' AND ohne_monteur AND freigegeben_von='||quote_literal(v_pbu)||'' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_ohne_monteur=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ubu,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET pdf_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_sig.png'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_pdf_pfad_nachtragen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET pdf_pfad=''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_unterschrift_1.png'' WHERE id=''p_a_zf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL buero_pdf_pfad_ersetzen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_uad,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_freigabe'' WHERE id=''p_a_zaf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL admin_frist_zu_knapp=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''zur_freigabe'',freigabe_bis='||quote_literal(v_h)||'::date'||'+10 WHERE id=''p_a_zaf'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL admin_frist_anpassen_und_freigeben=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id=''p_a_zaf'' AND admin_freigabe_von='||quote_literal(v_pad)||' AND admin_freigabe_am IS NOT NULL' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_admin_freigabe_protokoll=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_uad,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET status=''in_arbeit'',rueckgabe_grund=''Tag 12 pruefen'' WHERE id=''p_a_zaf2'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL admin_zurueck_mit_grund=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'UPDATE public.finkzeit SET notiz=''x'' WHERE id=''p_a_fg'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL admin_aendert_freigegebene_ohne_vermerk=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  EXECUTE 'SELECT set_config(''storage.allow_delete_query'',''true'',true)';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_uad,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'DELETE FROM storage.objects WHERE bucket_id=''epkolar-docs'' AND name LIKE ''monatsfreigabe/%'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL admin_storage_monatsfreigabe_loeschen=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  BEGIN EXECUTE 'SELECT count(*) FROM storage.objects WHERE bucket_id=''epkolar-docs'' AND name LIKE ''monatsfreigabe/%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n2' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL pruef_storage_monatsfreigabe_vollstaendig=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'SELECT set_config(''storage.allow_delete_query'',''false'',true)';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_uad,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'UPDATE public.finkzeit SET admin_vermerk=''Korrektur Lohnbuero'',notiz=''x'' WHERE id=''p_a_fg'''; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'ok1' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL admin_vermerk_freigegebene=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  EXECUTE 'UPDATE public.users SET locked=1 WHERE auth_user_id='||quote_literal(v_ua)||'';
  PERFORM set_config('request.jwt.claims', json_build_object('sub',v_ua,'role','authenticated')::text, true);
  EXECUTE 'SET LOCAL ROLE authenticated';
  BEGIN EXECUTE 'SELECT count(*) FROM public.finkzeit WHERE id LIKE ''p\_%''' INTO v_n; v_got := 'n'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err:'||SQLSTATE; END;
  IF v_got LIKE 'n0' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL gesperrt_sieht=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  BEGIN EXECUTE 'INSERT INTO storage.objects(bucket_id,name,owner) VALUES (''epkolar-docs'',''monatsfreigabe/''||'||quote_literal(v_a)||'||''/p_gesperrt.png'','||quote_literal(v_ua)||')'; GET DIAGNOSTICS v_n = ROW_COUNT; v_got := 'ok'||v_n; EXCEPTION WHEN OTHERS THEN v_got := 'err'; v_msg := SQLERRM; END;
  IF v_got LIKE 'err' THEN v_ok := v_ok + 1; ELSE v_fail := v_fail + 1; r := r || ' | FAIL gesperrt_storage=' || v_got || coalesce(' ('||left(v_msg,80)||')',''); END IF; v_msg := NULL;
  EXECUTE 'RESET ROLE';
  PERFORM set_config('request.jwt.claims', '{}', true);
  RAISE EXCEPTION 'PROBE_ERGEBNIS ok=% fail=% %', v_ok, v_fail, r;
END $probe$;
ROLLBACK;
