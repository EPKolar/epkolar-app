-- =====================================================================================
-- FZ_KM_LOG_BEREINIGUNG_v1096_PROBE.sql  —  Probelauf zu _ENTWURF.sql: dieselbe Aenderung, am Ende ROLLBACK.
-- Aendert NICHTS. Erwartet: VORHER 3 Elemente / 1 Treffer, NACHHER 2 Elemente, km_stand 184260.
-- =====================================================================================

begin;

-- VORHER
select id, km_stand, jsonb_array_length(km_log::jsonb) as n_km_log,
       (select count(*) from jsonb_array_elements(km_log::jsonb) e
         where e->>'km' = '-999999' and coalesce(e->>'datum', e->>'date') = '2026-03-18') as n_treffer
  from public.fahrzeuge where id = 'fz5';

update public.fahrzeuge f
   set km_log = (select coalesce(jsonb_agg(e order by o), '[]'::jsonb)::text
                   from jsonb_array_elements(f.km_log::jsonb) with ordinality x(e, o)
                  where not (e->>'km' = '-999999' and coalesce(e->>'datum', e->>'date') = '2026-03-18'))
 where f.id = 'fz5'
   and exists (select 1 from jsonb_array_elements(f.km_log::jsonb) e
                where e->>'km' = '-999999' and coalesce(e->>'datum', e->>'date') = '2026-03-18');

-- NACHHER (nur innerhalb der Transaktion)
select id, km_stand, jsonb_array_length(km_log::jsonb) as n_km_log, km_log
  from public.fahrzeuge where id = 'fz5';

rollback;
