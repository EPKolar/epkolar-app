-- IDEMPOTENT
-- =====================================================================================
-- KAMERA_GATEWAY_SEED_RUECKNAHME.sql  —  nimmt sql/KAMERA_GATEWAY_SEED_ENTWURF.sql zurueck (EPKolar, 20.11.2026)
--
-- STATUS: ENTWURF — nur durch Sebastian. Loescht GENAU die Gateway-Zeilen, sonst nichts:
--   1. kamera_zugriff  Regeln der Kameras elektrolager03/verkauf02/cam39/hochregal01 (+ Mobotix mob32..mob36, falls der
--                      zweite Block eingeschaltet war) mit bemerkung 'GATEWAY_SEED...'
--   2. kamera_backend  Zuordnungen dieser Kameras
--   3. kameras         diese Kameras
-- Mobotix-IDs, die nie angelegt wurden, treffen einfach 0 Zeilen.
-- Reihenfolge wegen Fremdschluessel ON DELETE RESTRICT: Regeln -> Zuordnung -> Kamera. KEIN CASCADE.
-- Hat der Admin in der App WEITERE Regeln fuer diese Kameras angelegt, bricht die Ruecknahme ab (nichts geloescht):
-- diese Regeln erst ansehen und bewusst in der App entfernen.
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
   where kamera_id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36')
     and (bemerkung is null or bemerkung not like 'GATEWAY\_SEED%');
  if fremd > 0 then
    raise exception 'Es gibt % weitere (nicht GATEWAY_SEED) Regeln fuer die Gateway-Kameras - abgebrochen, nichts geloescht', fremd;
  end if;

  -- 1. Regeln (nur die markierten Gateway-Regeln)
  delete from public.kamera_zugriff
   where kamera_id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36')
     and bemerkung like 'GATEWAY\_SEED%';
  -- 2. Backend-Zuordnung
  delete from public.kamera_backend
   where kamera_id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36');
  -- 3. Kameras
  delete from public.kameras
   where id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36');

  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  raise notice 'NACHHER: kameras=%, kamera_backend=%, kamera_zugriff=%', n_kam, n_be, n_z;
  if exists (select 1 from public.kameras
              where id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36')) then
    raise exception 'Kontrolle: Gateway-Kamera noch vorhanden - Transaktion verworfen';
  end if;
end $$;

commit;

-- PROBE: statt "commit;" oben "rollback;" schreiben - dann zeigen die NOTICE-Zeilen die Wirkung, ohne zu loeschen.
