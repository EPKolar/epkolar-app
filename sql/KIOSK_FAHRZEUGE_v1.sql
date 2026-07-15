-- ═══════════════════════════════════════════════════════════════════════════
-- KIOSK_FAHRZEUGE_v1.sql  (v3.9.706)  — Human-Run-Gate, Sebastian klickt Run.
-- ═══════════════════════════════════════════════════════════════════════════
-- ZWECK: Die Lager-Wandtafel (?screen=planung, Rolle lager_display) leitet ihre
-- 🚛-Spezialfahrzeug-Zeilen aus `fahrzeuge` ab. Falls lager_display die Tabelle
-- `fahrzeuge` per RLS NICHT lesen darf, liefert der rohe Read still [] -> die
-- 🚛-Zeilen fehlen. Diese RPC gibt dem Kiosk einen kontrollierten Lesepfad, der
-- NUR die fuer die Tafel noetigen Felder ausgibt — KEIN tank_log, km_stand,
-- fahrer, pickerl o.ae. (das Panel haengt oeffentlich am Werkstor).
--
-- HAUSMUSTER: exakt wie public.stempel_terminal_workers() (v3.9.695):
-- SECURITY DEFINER + harte Rollenpruefung im Body (auth_role()='lager_display'
-- ODER is_staff()), EXECUTE nur fuer authenticated. KEINE RLS-Policy wird
-- angelegt, geaendert oder geloescht.
--
-- ID-TYP-PARITAET: Rueckgabe als SETOF jsonb via jsonb_build_object — damit
-- traegt jedes Feld exakt den JSON-Typ des rohen PostgREST-Reads (int bleibt
-- Zahl, uuid/text bleibt String). Das ist wichtig, weil die Tafel per
-- z.<tag>.fz.indexOf(f.id) matcht: ein Typwechsel (Zahl vs. "Zahl") wuerde die
-- 🚛-Zuordnung still brechen. jsonb_build_object bewahrt die Paritaet.
--
-- IDEMPOTENT & GEFAHRLOS: nur CREATE OR REPLACE einer NEUEN Funktion +
-- REVOKE/GRANT darauf. Beruehrt keine bestehende Funktion, Tabelle oder Policy.
-- Mehrfach ausfuehrbar. Kein DROP, kein ALTER auf Fremdobjekte.
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.kiosk_fahrzeuge()
RETURNS SETOF jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO 'public', 'pg_temp'
AS $function$
BEGIN
  -- Wie stempel_terminal_workers(): Zugang nur fuer die Kiosk-Rolle oder Staff.
  IF NOT ( public.auth_role() = 'lager_display'
           OR public.is_staff() ) THEN
    RAISE EXCEPTION 'not authorized' USING errcode = '42501';
  END IF;
  RETURN QUERY
    SELECT jsonb_build_object(
             'id',          f.id,
             'kennzeichen', f.kennzeichen,
             'typ',         f.typ,
             'modell',      f.modell,
             'status',      f.status)
    FROM public.fahrzeuge f
    ORDER BY f.kennzeichen ASC;
END
$function$;

REVOKE ALL   ON FUNCTION public.kiosk_fahrzeuge() FROM public, anon;
GRANT EXECUTE ON FUNCTION public.kiosk_fahrzeuge() TO authenticated;

-- ── Selbst-Nachweis nach dem Run (read-only, gefahrlos) ─────────────────────
-- Soll: die Funktion existiert, ist SECURITY DEFINER, gibt >0 Zeilen mit genau
-- den 5 Feldern zurueck. Kontrollwert: fahrzeuge-Gesamtzahl muss zur RPC-Zahl
-- passen (die RPC filtert NICHT — sie gibt alle Fahrzeuge, die Tafel filtert
-- client-seitig auf das Spez-Praedikat).
--   SELECT proname, prosecdef  FROM pg_proc
--     WHERE pronamespace='public'::regnamespace AND proname='kiosk_fahrzeuge';  -- prosecdef=t
--   SELECT count(*) AS via_rpc   FROM public.kiosk_fahrzeuge();
--   SELECT count(*) AS via_table FROM public.fahrzeuge;                          -- muss gleich sein
--   SELECT public.kiosk_fahrzeuge() LIMIT 1;   -- ein jsonb-Objekt mit id/kennzeichen/typ/modell/status
