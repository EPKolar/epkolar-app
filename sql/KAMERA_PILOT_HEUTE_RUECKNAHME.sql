-- IDEMPOTENT
-- !!! SUPERSEDED / ABGELOEST 20.11.2026 durch sql/KAMERA_GATEWAY_SEED_ENTWURF.sql (QNAP-Gateway, IDs = go2rtc-
-- !!! Streamnamen cam37/cam38/cam39/hochregal01). NICHT mehr einspielen - nie beide Seeds. Diese Ruecknahme bleibt GUELTIG:
-- !!! war der Pilot eingespielt, ZUERST sie ausfuehren, dann den Gateway-Seed.

-- =====================================================================================
-- KAMERA_PILOT_HEUTE_RUECKNAHME.sql  —  nimmt sql/KAMERA_PILOT_HEUTE_ENTWURF.sql zurueck (EPKolar, 19.11.2026)
--
-- STATUS: ENTWURF — nur durch Sebastian. Loescht GENAU die Pilot-Zeilen, sonst nichts:
--   1. kamera_zugriff  Regeln der Kameras kam_g3_01 / kam_g3_lager03 mit bemerkung 'PILOT_HEUTE...'
--   2. kamera_backend  Zuordnungen kam_g3_01 / kam_g3_lager03
--   3. kameras         kam_g3_01 / kam_g3_lager03
-- Reihenfolge wegen Fremdschluessel ON DELETE RESTRICT: Regeln -> Zuordnung -> Kamera. KEIN CASCADE.
-- Hat der Admin in der App WEITERE Regeln fuer diese Kameras angelegt, bricht die Ruecknahme ab (nichts geloescht):
-- diese Regeln erst ansehen und bewusst in der App entfernen.
-- kamera_abruf_log bleibt unangetastet (keine FK; Protokoll nach Betriebsvereinbarung aufbewahren).
-- Das Datenmodell (sql/KAMERAS_v1_ENTWURF.sql) bleibt; ganz zurueck nur mit sql/KAMERAS_v1_RUECKNAHME.sql.
-- Lieber nicht loeschen? In der App die Kameras auf "inaktiv" setzen - dann sieht niemand ein Bild.
-- =====================================================================================

begin;

do $$
declare
  n_kam integer; n_be integer; n_z integer; fremd integer;
begin
  if to_regclass('public.kameras') is null then
    raise notice 'Kamera-Tabellen fehlen - nichts zu tun';
    return;
  end if;
  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  raise notice 'VORHER: kameras=%, kamera_backend=%, kamera_zugriff=%', n_kam, n_be, n_z;
  select count(*) into fremd from public.kamera_zugriff
   where kamera_id in ('kam_g3_01', 'kam_g3_lager03')
     and (bemerkung is null or bemerkung not like 'PILOT\_HEUTE%');
  if fremd > 0 then
    raise exception 'Es gibt % weitere (nicht PILOT_HEUTE) Regeln fuer die Pilot-Kameras - abgebrochen, nichts geloescht', fremd;
  end if;

  -- 1. Regeln (nur die markierten Pilot-Regeln)
  delete from public.kamera_zugriff
   where kamera_id in ('kam_g3_01', 'kam_g3_lager03') and bemerkung like 'PILOT\_HEUTE%';
  -- 2. Backend-Zuordnung
  delete from public.kamera_backend where kamera_id in ('kam_g3_01', 'kam_g3_lager03');
  -- 3. Kameras
  delete from public.kameras where id in ('kam_g3_01', 'kam_g3_lager03');

  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  raise notice 'NACHHER: kameras=%, kamera_backend=%, kamera_zugriff=%', n_kam, n_be, n_z;
  if exists (select 1 from public.kameras where id in ('kam_g3_01', 'kam_g3_lager03')) then
    raise exception 'Kontrolle: Pilot-Kamera noch vorhanden - Transaktion verworfen';
  end if;
end $$;

commit;

-- PROBE: statt "commit;" oben "rollback;" schreiben - dann zeigen die NOTICE-Zeilen die Wirkung, ohne zu loeschen.
