-- IDEMPOTENT
-- =====================================================================================
-- FZ_KM_LOG_BEREINIGUNG_v1096_RUECKNAHME.sql  —  macht _ENTWURF.sql rueckgaengig.
-- Haengt die entfernte Zeile wieder ans ENDE von fz5.km_log (dort stand sie: Element 3 von 3), woertlich wie gemessen
-- am 22.11.2026. Nur wenn sie fehlt - zweiter Lauf aendert nichts. Kein anderes Fahrzeug, keine andere Spalte.
-- =====================================================================================

begin;

update public.fahrzeuge f
   set km_log = (coalesce(nullif(f.km_log,''),'[]')::jsonb
                 || jsonb_build_array(jsonb_build_object('km', -999999, 'datum', '2026-03-18', 'note', '', 'by', 'Wolfgang Schmid')))::text
 where f.id = 'fz5'
   and not exists (select 1 from jsonb_array_elements(coalesce(nullif(f.km_log,''),'[]')::jsonb) e
                    where e->>'km' = '-999999' and coalesce(e->>'datum', e->>'date') = '2026-03-18');

select id, km_stand, jsonb_array_length(km_log::jsonb) as n_km_log from public.fahrzeuge where id = 'fz5';
-- erwartet: n_km_log 3

commit;
