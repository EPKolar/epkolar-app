-- DISPO PLANUNG v1 - RUECKNAHME
-- Entfernt Trigger, Funktion, Pruefregeln und die vier Planungsspalten aus DISPO_PLANUNG_v1_ENTWURF.sql.
-- ACHTUNG: DROP COLUMN verwirft offene Planungen (nicht bestaetigte Verschiebungen). Vorher sichern:
--   select id, nummer, dispo_datum, dispo_zeit, dispo_dauer, dispo_monteur from public.arbeitsscheine
--    where dispo_datum is not null or dispo_monteur is not null;
-- Bestaetigte Termine (termin_bestaetigt/termin_zeit/dauer/monteur) werden NICHT angefasst.
-- Reihenfolge: erst die App auf einen Stand ohne Planungsfelder zuruecksetzen (sonst meldet "Verschieben"
-- sichtbar "Datenbank kennt die Planungsfelder noch nicht" - sicher, aber nicht nutzbar).
-- Zustand danach = Stand 24.11.2026 (gemessen): einziger Trigger auf arbeitsscheine ist
-- trg_updated_at_arbeitsscheine; keine dispo-Spalte; public.as_dispo_planung_guard() existiert nicht.

DROP TRIGGER IF EXISTS trg_as_dispo_planung_guard ON public.arbeitsscheine;
DROP FUNCTION IF EXISTS public.as_dispo_planung_guard();
ALTER TABLE public.arbeitsscheine DROP CONSTRAINT IF EXISTS arbeitsscheine_dispo_datum_form;
ALTER TABLE public.arbeitsscheine DROP CONSTRAINT IF EXISTS arbeitsscheine_dispo_zeit_form;
ALTER TABLE public.arbeitsscheine DROP CONSTRAINT IF EXISTS arbeitsscheine_dispo_dauer_form;
ALTER TABLE public.arbeitsscheine
  DROP COLUMN IF EXISTS dispo_datum,
  DROP COLUMN IF EXISTS dispo_zeit,
  DROP COLUMN IF EXISTS dispo_dauer,
  DROP COLUMN IF EXISTS dispo_monteur;
NOTIFY pgrst, 'reload schema';

-- Nachmessen:
-- select column_name from information_schema.columns where table_schema='public' and table_name='arbeitsscheine' and column_name like 'dispo%';  -> 0 Zeilen
-- select tgname from pg_trigger where tgrelid='public.arbeitsscheine'::regclass and not tgisinternal;  -> nur trg_updated_at_arbeitsscheine
-- select to_regprocedure('public.as_dispo_planung_guard()');  -> NULL
