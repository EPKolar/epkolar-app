-- IDEMPOTENT
-- =====================================================================================
-- KAMERAS_v1_RUECKNAHME.sql  —  nimmt sql/KAMERAS_v1_ENTWURF.sql vollstaendig zurueck
--
-- STATUS: ENTWURF — nur durch Sebastian ueber das Tor. KEIN CASCADE: die Reihenfolge loest die
-- Abhaengigkeiten ausdruecklich auf (Policies -> abhaengige Tabellen -> kameras -> Funktionen).
-- DATEN: kameras / kamera_zugriff / kamera_backend / kamera_abruf_log gehen dabei VERLOREN.
-- Wer das Protokoll aufheben muss (Betriebsvereinbarung!), sichert vorher:
--   copy (select * from public.kamera_abruf_log order by ts) to stdout with csv header;
--   bzw. im Dashboard als CSV exportieren.
-- Die App (Flag aus) bemerkt das Fehlen der Tabellen und zeigt "Datenmodell noch nicht eingerichtet".
-- =====================================================================================

-- 1. Policies
drop policy if exists kameras_select on public.kameras;
drop policy if exists kameras_insert on public.kameras;
drop policy if exists kameras_update on public.kameras;
drop policy if exists kameras_delete on public.kameras;
drop policy if exists kamera_zugriff_admin on public.kamera_zugriff;
drop policy if exists kamera_abruf_log_select on public.kamera_abruf_log;

-- 2. Tabellen (abhaengige zuerst; Trigger und Indizes gehen mit der Tabelle)
drop table if exists public.kamera_abruf_log;
drop table if exists public.kamera_zugriff;
drop table if exists public.kamera_backend;
drop table if exists public.kameras;

-- 3. Funktionen (Policies, die sie nutzen, sind oben schon weg)
drop function if exists public.kamera_darf_sehen_bereich(text, timestamptz, timestamptz);
drop function if exists public.kamera_darf_sehen(text, timestamptz);
drop function if exists public.kamera_pruefen(uuid, text, timestamptz);
drop function if exists public.kamera_ist_verwalter();
drop function if exists public.kamera_fenster_trifft(integer[], time, time, integer, time);
drop function if exists public.kamera_touch();

-- NACHPRUEFUNG:
--   select count(*) from pg_class where relname in ('kameras','kamera_zugriff','kamera_backend','kamera_abruf_log');  -- erwartet 0
--   select count(*) from pg_proc where proname like 'kamera\_%';                                                        -- erwartet 0
-- =====================================================================================
