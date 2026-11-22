-- IDEMPOTENT
-- =====================================================================================
-- FZ_KM_LOG_DUPLIKATE_v1096_RUECKNAHME.sql  —  macht _ENTWURF.sql rueckgaengig.
-- Setzt hinter jedes der drei Elemente {km,date} (118250/2026-07-05, 118865/2026-07-14, 119200/2026-07-15) wieder
-- eine identische Zweitzeile - genau dort standen sie (gemessen 22.11.2026: jeweils direkt hintereinander).
-- Nur Elemente ohne id, nur wenn das Element genau EINMAL vorkommt - zweiter Lauf aendert nichts.
-- Kein anderes Fahrzeug, keine andere Spalte.
-- =====================================================================================

begin;

update public.fahrzeuge f
   set km_log = (select coalesce(jsonb_agg(e order by o, g), '[]'::jsonb)::text
                   from (select e, o, count(*) over (partition by e) n
                           from jsonb_array_elements(f.km_log::jsonb) with ordinality t(e, o)) y
                  cross join lateral generate_series(1,
                        case when n = 1 and not (e ? 'id')
                                  and (e->>'km', coalesce(e->>'date', e->>'datum')) in (('118250','2026-07-05'),('118865','2026-07-14'),('119200','2026-07-15'))
                             then 2 else 1 end) g)
 where f.id = 'fz1b';

select id, jsonb_array_length(km_log::jsonb) as n_km_log from public.fahrzeuge where id = 'fz1b';
-- erwartet nach ENTWURF + RUECKNAHME: n_km_log 20

commit;
