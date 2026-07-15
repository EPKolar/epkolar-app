-- ═══════════════════════════════════════════════════════════════════════════
-- KIOSK_FAHRZEUGE_v1.sql  (v3.9.708)  — Human-Run-Gate, Sebastian klickt Run.
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
-- WICHTIG v3.9.708 — RETURNS TABLE statt SETOF jsonb:
-- Die erste Fassung gab SETOF jsonb zurueck. PostgREST kann ein SETOF-SCALAR
-- unter dem Funktionsnamen VERSCHACHTELN ([{"kiosk_fahrzeuge":{...}}]) statt die
-- Objekte flach zu liefern — dann sieht der Client f.typ/f.modell als undefined,
-- das Spez-Praedikat trifft nie, und die 🚛-Zeile bleibt leer OBWOHL fahrzeuge
-- geladen ist (FZ:>0 · Spez:0). Darum jetzt RETURNS TABLE mit benannten Spalten —
-- exakt das bewaehrte Muster der drei laufenden Kiosk-RPCs (kiosk_field_workers,
-- kiosk_week_arbeitsscheine, kiosk_week_absences). Ergebnis: flaches
-- [{id,kennzeichen,typ,modell,status}], identische Form wie der rohe Read.
--
-- ID-TYP: fahrzeuge.id ist text (uuid v4 aus _uuid(); belegt durch
-- fz_positions.fahrzeug_id text NOT NULL). Rueckgabe als text -> String-Paritaet
-- zu z.<tag>.fz (dort steht dieselbe _uuid()-Zeichenkette) -> indexOf matcht.
--
-- IDEMPOTENT & GEFAHRLOS: nur CREATE OR REPLACE einer bestehenden/neuen Funktion
-- + REVOKE/GRANT darauf. Beruehrt keine andere Funktion, Tabelle oder Policy.
-- Mehrfach ausfuehrbar. Kein DROP, kein ALTER auf Fremdobjekte.
-- (CREATE OR REPLACE mit geaendertem Rueckgabetyp: falls Postgres wegen des
--  Typwechsels SETOF jsonb -> TABLE meckert, das vorangestellte DROP nutzen.)
-- ═══════════════════════════════════════════════════════════════════════════

-- Rueckgabetyp-Wechsel: CREATE OR REPLACE kann den Signatur-/Rueckgabetyp nicht
-- aendern -> zuerst die alte Fassung entfernen. Gefahrlos: es ist unsere eigene,
-- erst heute angelegte Funktion, kein Fremdobjekt.
DROP FUNCTION IF EXISTS public.kiosk_fahrzeuge();

CREATE OR REPLACE FUNCTION public.kiosk_fahrzeuge()
RETURNS TABLE(id text, kennzeichen text, typ text, modell text, status text)
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
    SELECT f.id::text, f.kennzeichen::text, f.typ::text, f.modell::text, f.status::text
    FROM public.fahrzeuge f
    ORDER BY f.kennzeichen ASC;
END
$function$;

REVOKE ALL   ON FUNCTION public.kiosk_fahrzeuge() FROM public, anon;
GRANT EXECUTE ON FUNCTION public.kiosk_fahrzeuge() TO authenticated;

-- ── Selbst-Nachweis nach dem Run (read-only, gefahrlos) ─────────────────────
-- Soll: Funktion existiert, SECURITY DEFINER, liefert flache Zeilen mit genau
-- den 5 Spalten. Kontrollwert: via_rpc == via_table (die RPC filtert NICHT).
--   SELECT proname, prosecdef FROM pg_proc
--     WHERE pronamespace='public'::regnamespace AND proname='kiosk_fahrzeuge';  -- prosecdef=t
--   SELECT count(*) AS via_rpc   FROM public.kiosk_fahrzeuge();
--   SELECT count(*) AS via_table FROM public.fahrzeuge;                          -- muss gleich sein
--   SELECT * FROM public.kiosk_fahrzeuge() LIMIT 1;   -- id,kennzeichen,typ,modell,status FLACH
