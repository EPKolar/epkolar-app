-- IDEMPOTENT
-- =====================================================================================
-- FAHRZEUG_ARCHIV_v1059_ENTWURF.sql  —  Fahrzeuge archivieren statt hart loeschen (GF-Entscheidung 19.11.2026)
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Einspielen nur durch Sebastian im SQL-Editor (Projekt jiggujpruejkaomgxarp).
--   ZUERST ALS PROBE: die letzte Zeile "COMMIT;" durch "ROLLBACK;" ersetzen, ausfuehren, NOTICE-Zeilen lesen.
--   Danach beweisen, dass nichts stehen blieb (Abschnitt 6, Abfrage P) — erst dann mit COMMIT einspielen.
--
-- ANLASS: am 19.11.2026 13:18:41 / 13:19:05 UTC wurden fz6 (TU-516CP) und fz3 (TU-545BC, einziges Fahrzeug mit
--   GPS-Tracker) ueber die App hart geloescht (DELETE /rest/v1/fahrzeuge?id=eq.fz6 / fz3, HTTP 200). Die Zeile
--   fahrzeuge traegt Tankbuch, km-Log, Schaeden, Termine und Serviceheft als Text-Spalten — mit der Zeile war
--   all das weg. Wiederherstellung: FAHRZEUG_RESTORE_fz3_fz6_v1059_ENTWURF.sql (eigene Datei).
--
-- WAS ES AENDERT (nur public.fahrzeuge + kiosk_fahrzeuge(); KEIN CASCADE, keine Daten werden veraendert):
--   1. Spalten archiviert_am timestamptz NULL, archiviert_von text NULL (ohne Default; NULL = aktiv).
--   2. BEFORE-DELETE-Trigger trg_fahrzeuge_kein_hartloeschen: jeder DELETE, der ueber die API kommt
--      (auth.role() = authenticated/anon, also App/PostgREST — Admin eingeschlossen), bricht mit SQLSTATE 23001 ab.
--      Hart loeschen geht nur noch per SQL als Inhaber (SQL-Editor: auth.role() ist dort NULL) oder service_role.
--      Muster wie trg_workers_block_delete (WORKERS_DELETE_GUARD_v1, Loeschschutz 23./24.07.): Trigger statt
--      Policy-Aenderung, weil eine Policy USING(false) den DELETE STILL mit 0 Zeilen "gelingen" liesse
--      (Silent-Denial) — der Trigger meldet laut (HTTP 409), alte App-Staende sehen einen Fehler statt Erfolg.
--   3. BEFORE-INSERT/UPDATE-Trigger trg_fahrzeuge_archiv_nur_admin: archiviert_am/archiviert_von darf ueber die
--      API nur ein Admin (public.auth_role() = 'admin') setzen oder leeren. Noetig, weil die bestehende
--      UPDATE-Policy fahrzeuge_update_office_or_driver auch is_hr() (buero/projektleiter) UND dem eigenen
--      Fahrer (fahrer = current_monteur_id()) die ganze Zeile freigibt. Alle anderen Spalten: unveraendert.
--   4. kiosk_fahrzeuge() (SECURITY DEFINER, Lager-/Planungs-Kiosk): liefert archivierte Fahrzeuge nicht mehr
--      (die RPC gibt archiviert_am nicht mit, die App koennte dort sonst nicht filtern). Signatur unveraendert.
--
-- APP: ab v3.9.1059 ("Archivieren" statt "Loeschen", Admin-Archiv mit "Wiederherstellen"). Die App laeuft auch
--   VOR diesem Entwurf: fehlt die Spalte, gilt jedes Fahrzeug als aktiv und Archivieren meldet ehrlich
--   "erst nach dem DB-Update moeglich" — sie faellt NIE auf DELETE zurueck.
--
-- DATENSTAND (read-only 19.11.2026 gemessen): fahrzeuge 19 Zeilen, alle status 'aktiv'; KEINE Fremdschluessel
--   zeigen auf fahrzeuge (pg_constraint confrelid = 0 Treffer) -> nichts kaskadiert, nichts wird hier angefasst.
--   Bestehende Policies: fahrzeuge_select / _insert / _delete / _update_office_or_driver. Trigger vorher:
--   nur trg_updated_at_fahrzeuge (BEFORE UPDATE).
--
-- ROLLBACK: sql/FAHRZEUG_ARCHIV_v1059_ROLLBACK.sql
-- =====================================================================================

BEGIN;

-- 0. VORPRUEFUNG + VORHER (nur Zahlen)
DO $$
DECLARE v_n int; v_trg int; v_as int;
BEGIN
  IF to_regclass('public.fahrzeuge') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: public.fahrzeuge fehlt'; END IF;
  IF to_regprocedure('public.auth_role()') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: public.auth_role() fehlt'; END IF;
  IF to_regprocedure('auth.role()') IS NULL THEN RAISE EXCEPTION 'Vorpruefung: auth.role() fehlt'; END IF;
  SELECT count(*) INTO v_as FROM public.arbeitsscheine;
  SELECT count(*) INTO v_n FROM public.fahrzeuge;
  SELECT count(*) INTO v_trg FROM pg_trigger WHERE tgrelid = 'public.fahrzeuge'::regclass AND NOT tgisinternal;
  RAISE NOTICE 'VORHER: arbeitsscheine=%, fahrzeuge=%, Trigger auf fahrzeuge=%', v_as, v_n, v_trg;
END $$;

-- 1. SPALTEN (ohne Default; NULL = nicht archiviert)
ALTER TABLE public.fahrzeuge ADD COLUMN IF NOT EXISTS archiviert_am  timestamptz NULL;
ALTER TABLE public.fahrzeuge ADD COLUMN IF NOT EXISTS archiviert_von text        NULL;
COMMENT ON COLUMN public.fahrzeuge.archiviert_am  IS 'v1059: gesetzt = archiviert (in allen Listen ausgeblendet). NULL = aktiv. Nur Admin ueber die App.';
COMMENT ON COLUMN public.fahrzeuge.archiviert_von IS 'v1059: wer archiviert hat (App-Benutzer). NULL wenn aktiv.';

-- 2. KEIN HART-LOESCHEN UEBER DIE API
CREATE OR REPLACE FUNCTION public.fahrzeuge_kein_hartloeschen()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
  IF coalesce(auth.role(), '') IN ('authenticated', 'anon') THEN
    RAISE EXCEPTION 'Fahrzeug % (%) kann in der App nicht geloescht werden - bitte archivieren. Endgueltiges Loeschen nur per SQL durch den Inhaber.',
      coalesce(nullif(OLD.kennzeichen, ''), OLD.id), OLD.id
      USING ERRCODE = '23001';  -- restrict_violation, wie trg_workers_block_delete
  END IF;
  RETURN OLD;  -- SQL-Editor (Inhaber) / service_role: zugelassen
END;
$$;

DROP TRIGGER IF EXISTS trg_fahrzeuge_kein_hartloeschen ON public.fahrzeuge;
CREATE TRIGGER trg_fahrzeuge_kein_hartloeschen
  BEFORE DELETE ON public.fahrzeuge
  FOR EACH ROW
  EXECUTE FUNCTION public.fahrzeuge_kein_hartloeschen();

-- 3. ARCHIV-SPALTEN NUR FUER ADMIN
CREATE OR REPLACE FUNCTION public.fahrzeuge_archiv_nur_admin()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE v_geaendert boolean;
BEGIN
  IF TG_OP = 'INSERT' THEN
    v_geaendert := NEW.archiviert_am IS NOT NULL OR NEW.archiviert_von IS NOT NULL;
  ELSE
    v_geaendert := NEW.archiviert_am IS DISTINCT FROM OLD.archiviert_am
                OR NEW.archiviert_von IS DISTINCT FROM OLD.archiviert_von;
  END IF;
  IF v_geaendert
     AND coalesce(auth.role(), '') IN ('authenticated', 'anon')
     AND coalesce(public.auth_role(), '') <> 'admin' THEN
    RAISE EXCEPTION 'Fahrzeug %: Archivieren/Wiederherstellen ist nur fuer Admin erlaubt.', NEW.id
      USING ERRCODE = 'P0001';  -- bewusst nicht 42501: PostgREST 400 statt 403 (403 laeuft in der App ueber _onAuthFail)
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_fahrzeuge_archiv_nur_admin ON public.fahrzeuge;
CREATE TRIGGER trg_fahrzeuge_archiv_nur_admin
  BEFORE INSERT OR UPDATE ON public.fahrzeuge
  FOR EACH ROW
  EXECUTE FUNCTION public.fahrzeuge_archiv_nur_admin();

-- 4. KIOSK: archivierte nicht ausliefern (Signatur und Rechtepruefung woertlich wie bisher, nur WHERE neu)
CREATE OR REPLACE FUNCTION public.kiosk_fahrzeuge()
 RETURNS TABLE(id text, kennzeichen text, typ text, modell text, status text)
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
BEGIN
  IF NOT ( public.auth_role() = 'lager_display'
           OR public.is_staff() ) THEN
    RAISE EXCEPTION 'not authorized' USING errcode = '42501';
  END IF;
  RETURN QUERY
    SELECT f.id::text, f.kennzeichen::text, f.typ::text, f.modell::text, f.status::text
    FROM public.fahrzeuge f
    WHERE f.archiviert_am IS NULL
    ORDER BY f.kennzeichen ASC;
END
$function$;

-- 5. NACHHER (nur Zahlen)
DO $$
DECLARE v_spalten int; v_trg int; v_n int; v_arch int;
BEGIN
  SELECT count(*) INTO v_spalten FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'fahrzeuge' AND column_name IN ('archiviert_am', 'archiviert_von');
  SELECT count(*) INTO v_trg FROM pg_trigger
   WHERE tgrelid = 'public.fahrzeuge'::regclass AND tgname IN ('trg_fahrzeuge_kein_hartloeschen', 'trg_fahrzeuge_archiv_nur_admin');
  SELECT count(*), count(*) FILTER (WHERE archiviert_am IS NOT NULL) INTO v_n, v_arch FROM public.fahrzeuge;
  IF v_spalten <> 2 OR v_trg <> 2 THEN RAISE EXCEPTION 'NACHHER: Spalten=% Trigger=% (erwartet 2/2)', v_spalten, v_trg; END IF;
  RAISE NOTICE 'NACHHER: Spalten 2/2, Trigger 2/2, fahrzeuge=% (davon archiviert=%)', v_n, v_arch;
END $$;

COMMIT;

-- 6. NACH DEM LAUF PRUEFEN (read-only bzw. zurueckgerollt)
-- (P) nach einer PROBE (ROLLBACK) muss alles 0 sein:
--     select (select count(*) from information_schema.columns where table_schema='public' and table_name='fahrzeuge'
--               and column_name in ('archiviert_am','archiviert_von')) spalten,
--            (select count(*) from pg_trigger where tgname in ('trg_fahrzeuge_kein_hartloeschen','trg_fahrzeuge_archiv_nur_admin')) trigger,
--            (select count(*) from pg_proc where proname in ('fahrzeuge_kein_hartloeschen','fahrzeuge_archiv_nur_admin')) funktionen;
-- (a) App-DELETE ist gesperrt (als angemeldeter Benutzer simuliert, zurueckgerollt):
--     begin;
--       select set_config('request.jwt.claim.role','authenticated',true);
--       select set_config('request.jwt.claims','{"role":"authenticated"}',true);
--       delete from public.fahrzeuge where id = 'fz1';   -- erwartet: ERROR 23001 ... bitte archivieren ...
--     rollback;
-- (b) Inhaber per SQL bleibt frei (NICHT ausfuehren ohne echten Bedarf; zeigt nur die Logik):
--     begin; delete from public.fahrzeuge where id = '<id>'; rollback;
-- (c) Kiosk-Liste ohne Archiv:  select count(*) from public.fahrzeuge where archiviert_am is null;
