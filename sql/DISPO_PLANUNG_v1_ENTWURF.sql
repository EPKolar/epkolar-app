-- DISPO PLANUNG v1 - ENTWURF ("Verschieben ist nicht bestaetigt", GF 24.11.2026, Weg B) - NICHT angewendet.
-- Nur auf ausdrueckliche Freigabe (Sebastian). Prod: jiggujpruejkaomgxarp (nie MOBOLog).
-- IDEMPOTENT
--
-- Zweck: eigene Planungsfelder an public.arbeitsscheine. Verschieben in der Dispo und "Uebernehmen" schreiben
-- ab App-Stand feature/dispo-mobil-planung NUR diese Felder (kein termin_bestaetigt, kein termin_zeit, keine
-- dauer, kein monteur -> kein Push an OFFA). Erst "Termin bestaetigen" kopiert die Planung in die Terminfelder
-- und meldet ueber den bestehenden Weg genau einmal an OFFA.
--   dispo_datum   text  'YYYY-MM-DD'          geplanter Tag
--   dispo_zeit    text  'HH:MM'               geplante Startzeit
--   dispo_dauer   text  'HH:MM'               geplante Dauer
--   dispo_monteur text  workers.id            geplanter Monteur (nur bei "Uebernehmen")
-- Typ text wie termin_bestaetigt/termin_zeit/dauer/monteur (gemessen 24.11.2026: alle text).
-- Bestehende Werte werden NICHT angefasst, keine Rueckrechnung, keine Datenmigration: alle neuen Spalten NULL.
--
-- Rechte: dieselbe Feldrollen-Regel wie fuer den Termin - nur Buero/Projektleitung/Admin (public.is_staff())
-- duerfen die Planungsfelder setzen oder aendern. Monteur, Helfer, Techniker, lager_display -> 42501 (HTTP 403).
-- Ausnahmen wie im Entwurf ARBEITSSCHEINE_FELDROLLEN_v1: kein JWT-Benutzer (SQL-Editor, Cron,
-- juprowa_apply_worksheets ohne sub), service_role, is_staff(). Leer und NULL gelten als gleich.
-- Der OFFA-Abgleich (juprowa_apply_worksheets, _juprowaSync im Browser) setzt nur benannte Spalten und
-- beruehrt die Planungsfelder nicht (im PROBE-Lauf auf der Datenbank geprueft).
--
-- Vorher messen:
--   select column_name from information_schema.columns where table_schema='public' and table_name='arbeitsscheine' and column_name like 'dispo%';  -> 0 Zeilen
--   select tgname from pg_trigger where tgrelid='public.arbeitsscheine'::regclass and not tgisinternal;          -> nur trg_updated_at_arbeitsscheine
--   select to_regprocedure('public.as_dispo_planung_guard()');                                                  -> NULL
-- Nachher messen:
--   4 Spalten dispo_datum/dispo_zeit/dispo_dauer/dispo_monteur (text), Trigger trg_as_dispo_planung_guard, Funktion vorhanden,
--   select count(*) from public.arbeitsscheine where dispo_datum is not null;  -> 0
--
-- Reihenfolge App/DB: die App liest die Spalten tolerant (fehlen sie, gibt es keine Planung). Schreiben der
-- Planung ohne Spalten scheitert in der App SICHTBAR ("Datenbank kennt die Planungsfelder noch nicht") und
-- schreibt nie ersatzweise Terminfelder. Also: erst dieses SQL, dann die App ausliefern - oder umgekehrt, beides sicher.

ALTER TABLE public.arbeitsscheine
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
