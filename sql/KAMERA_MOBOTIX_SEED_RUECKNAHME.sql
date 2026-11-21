-- IDEMPOTENT
-- =====================================================================================
-- KAMERA_MOBOTIX_SEED_RUECKNAHME.sql  —  nimmt sql/KAMERA_MOBOTIX_SEED_ENTWURF.sql zurueck (EPKolar, 21.11.2026)
--
-- STATUS: ENTWURF — nur durch Sebastian. Loescht GENAU die Mobotix-Zeilen, sonst nichts (die 4 G3 bleiben):
--   1. kamera_zugriff  Regeln der Kameras hof01/hochregal03/hochregal02/elektrolager01/elektrolager02
--                      mit bemerkung 'MOBOTIX_SEED...'
--   2. kamera_backend  Zuordnungen dieser Kameras
--   3. kameras         diese Kameras
-- Reihenfolge wegen Fremdschluessel ON DELETE RESTRICT: Regeln -> Zuordnung -> Kamera. KEIN CASCADE.
-- Hat der Admin in der App WEITERE Regeln fuer diese Kameras angelegt, bricht die Ruecknahme ab (nichts geloescht).
-- kamera_abruf_log bleibt unangetastet (keine FK; Protokoll nach Betriebsvereinbarung aufbewahren).
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
   where kamera_id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
     and (bemerkung is null or bemerkung not like 'MOBOTIX\_SEED%');
  if fremd > 0 then
    raise exception 'Es gibt % weitere (nicht MOBOTIX_SEED) Regeln fuer die Mobotix-Kameras - abgebrochen, nichts geloescht', fremd;
  end if;

  -- 1. Regeln (nur die markierten Mobotix-Regeln)
  delete from public.kamera_zugriff
   where kamera_id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
     and bemerkung like 'MOBOTIX\_SEED%';
  -- 2. Backend-Zuordnung
  delete from public.kamera_backend
   where kamera_id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02');
  -- 3. Kameras
  delete from public.kameras
   where id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02');

  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  raise notice 'NACHHER: kameras=%, kamera_backend=%, kamera_zugriff=%', n_kam, n_be, n_z;
  if exists (select 1 from public.kameras
              where id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')) then
    raise exception 'Kontrolle: Mobotix-Kamera noch vorhanden - Transaktion verworfen';
  end if;
end $$;

commit;

-- PROBE: statt "commit;" oben "rollback;" schreiben - dann zeigen die NOTICE-Zeilen die Wirkung, ohne zu loeschen.
