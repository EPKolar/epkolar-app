-- =====================================================================================
-- FZ_KM_LOG_DUPLIKATE_v1096_PROBE.sql  —  Probelauf zu _ENTWURF.sql: dieselbe Aenderung, am Ende ROLLBACK.
-- Aendert NICHTS. Erwartet: VORHER 20 Elemente / 3 Zweitzeilen, NACHHER 17 Elemente / 0 Zweitzeilen, tank_log 16 unveraendert.
-- =====================================================================================

begin;

-- VORHER
select id, km_stand, jsonb_array_length(km_log::jsonb) as n_km_log, jsonb_array_length(tank_log::jsonb) as n_tank_log,
       (select count(*) from (select e, row_number() over (partition by e order by o) rn
                                from jsonb_array_elements(km_log::jsonb) with ordinality t(e, o)) y where rn > 1) as n_zweitzeilen
  from public.fahrzeuge where id = 'fz1b';

update public.fahrzeuge f
   set km_log = (select coalesce(jsonb_agg(e order by o), '[]'::jsonb)::text
                   from (select e, o, row_number() over (partition by e order by o) rn
                           from jsonb_array_elements(f.km_log::jsonb) with ordinality t(e, o)) y
                  where not (rn > 1 and not (e ? 'id')
                             and (e->>'km', coalesce(e->>'date', e->>'datum')) in (('118250','2026-07-05'),('118865','2026-07-14'),('119200','2026-07-15'))))
 where f.id = 'fz1b';

-- NACHHER (nur innerhalb der Transaktion)
select id, km_stand, jsonb_array_length(km_log::jsonb) as n_km_log, jsonb_array_length(tank_log::jsonb) as n_tank_log,
       (select count(*) from (select e, row_number() over (partition by e order by o) rn
                                from jsonb_array_elements(km_log::jsonb) with ordinality t(e, o)) y where rn > 1) as n_zweitzeilen
  from public.fahrzeuge where id = 'fz1b';

rollback;
