-- IDEMPOTENT
-- =====================================================================================
-- FZ_KM_LOG_DUPLIKATE_v1096_ENTWURF.sql  —  drei exakt doppelte km-Zeilen aus dem Kilometerprotokoll von fz1b entfernen
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Nur Sebastian, SQL-Editor, Projekt jiggujpruejkaomgxarp.
-- PROBE ZUERST: sql/FZ_KM_LOG_DUPLIKATE_v1096_PROBE.sql (gleiche Aenderung, endet mit ROLLBACK).
-- RUECKNAHME:   sql/FZ_KM_LOG_DUPLIKATE_v1096_RUECKNAHME.sql (setzt die Zweitzeilen wieder direkt hinter die erste).
--
-- ── BEFUND (read-only, 22.11.2026 gemessen) ─────────────────────────────────────────
--   Ganze Flotte durchsucht: GENAU DREI Paare identischer km_log-Elemente, alle in fz1b (20 Elemente):
--     {"km":118250,"date":"2026-07-05"} x2   {"km":118865,"date":"2026-07-14"} x2   {"km":119200,"date":"2026-07-15"} x2
--   Byte-gleich, ohne id, Form {km,date} = der km-Zweig in apiPatch (PUT fahrzeuge mit kmStand). Jede Zeile gehoert zu
--   genau EINER Tankung (tkmr7taf3m.. 05.07., tkmrke1f6m.. 14.07. 08:27 UTC, tkmrlynegr.. 15.07.) - tank_log hat diese
--   Tankungen je nur EINMAL. Ursache: dieselbe Sendung lief zweimal durch den km-Zweig (ohne kmLogId nicht idempotent);
--   behoben in v3.9.1096 (addTank schickt kmLogId km_<tankId>).
--   NICHT angefasst: 120210 am 2026-07-27 und 2026-08-03 (gleicher km-Stand, verschiedene Tage = zwei Tankungen,
--   07-27 und 08-02, beide mit km 120210 erfasst) und die Tankungen selbst (tank_log bleibt unveraendert).
--
-- ── WAS DAS SKRIPT TUT ──────────────────────────────────────────────────────────────
--   Behaelt von jedem der drei Paare das ERSTE Element, entfernt das zweite. Nur Elemente ohne id, nur diese drei
--   (km,date)-Paare. Reihenfolge der uebrigen bleibt. Zweiter Lauf: findet nichts, aendert nichts (NOTICE).
--   Bricht ab, wenn Vorher/Nachher nicht 20 -> 17 ist. Kein CASCADE, kein anderes Fahrzeug, keine andere Spalte.
--
-- ── NACHHER ──────────────────────────────────────────────────────────────────────────
--   fz1b: km_log 20 -> 17 Elemente, je (km,date) hoechstens einmal; km_stand 129453 unveraendert; tank_log unveraendert.
--   Gleicher Hinweis wie bei der fz5-Bereinigung: Geraete nach dem Lauf neu laden (addKm schickt das ganze lokale km_log).
-- =====================================================================================

begin;

do $$
declare
  v_vorher int; v_doppelt int; v_nachher int;
begin
  select jsonb_array_length(coalesce(nullif(km_log,''),'[]')::jsonb) into v_vorher
    from public.fahrzeuge where id = 'fz1b' for update;
  if v_vorher is null then raise exception 'fz1b nicht gefunden - Abbruch'; end if;

  select count(*) into v_doppelt
    from (select e, row_number() over (partition by e order by o) rn
            from public.fahrzeuge f, jsonb_array_elements(f.km_log::jsonb) with ordinality t(e, o)
           where f.id = 'fz1b') y
   where rn > 1 and not (e ? 'id')
     and (e->>'km', coalesce(e->>'date', e->>'datum')) in (('118250','2026-07-05'),('118865','2026-07-14'),('119200','2026-07-15'));

  raise notice 'VORHER fz1b: km_log % Elemente, davon % Zweitzeilen', v_vorher, v_doppelt;
  if v_doppelt = 0 then
    raise notice 'nichts zu tun (schon bereinigt)';
    return;
  end if;
  if v_vorher <> 20 or v_doppelt <> 3 then
    raise exception 'Zeile hat sich seit der Messung (20 Elemente, 3 Zweitzeilen) veraendert: % / % - Abbruch, neu messen', v_vorher, v_doppelt;
  end if;

  update public.fahrzeuge f
     set km_log = (select coalesce(jsonb_agg(e order by o), '[]'::jsonb)::text
                     from (select e, o, row_number() over (partition by e order by o) rn
                             from jsonb_array_elements(f.km_log::jsonb) with ordinality t(e, o)) y
                    where not (rn > 1 and not (e ? 'id')
                               and (e->>'km', coalesce(e->>'date', e->>'datum')) in (('118250','2026-07-05'),('118865','2026-07-14'),('119200','2026-07-15'))))
   where f.id = 'fz1b';

  select jsonb_array_length(km_log::jsonb) into v_nachher from public.fahrzeuge where id = 'fz1b';
  raise notice 'NACHHER fz1b: km_log % Elemente', v_nachher;
  if v_nachher <> v_vorher - 3 then
    raise exception 'erwartet % Elemente, sind % - Abbruch', v_vorher - 3, v_nachher;
  end if;
end $$;

select id, km_stand, jsonb_array_length(km_log::jsonb) as n_km_log,
       jsonb_array_length(tank_log::jsonb) as n_tank_log
  from public.fahrzeuge where id = 'fz1b';

commit;
