-- IDEMPOTENT
-- =====================================================================================
-- FZ_KM_LOG_BEREINIGUNG_v1096_ENTWURF.sql  —  den km-Stand -999999 aus dem Kilometerprotokoll von fz5 entfernen
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Nur Sebastian, SQL-Editor, Projekt jiggujpruejkaomgxarp.
-- PROBE ZUERST: sql/FZ_KM_LOG_BEREINIGUNG_v1096_PROBE.sql (gleiche Aenderung, endet mit ROLLBACK).
-- RUECKNAHME:   sql/FZ_KM_LOG_BEREINIGUNG_v1096_RUECKNAHME.sql (haengt genau diese Zeile wieder an).
--
-- ── BEFUND (read-only, 22.11.2026 gemessen) ─────────────────────────────────────────
--   fahrzeuge.km_log ist TEXT mit JSON-Array. Ganze Flotte durchsucht (km_log + tank_log aller Fahrzeuge):
--   GENAU EIN unplausibler km-Wert, fz5 km_log Element 3 von 3:
--     {"km":-999999,"datum":"2026-03-18","note":"","by":<Erfasser>}
--   Form {km,datum,note,by} = addKm (Fahrzeug -> km eintragen). Am 18.03.2026 war addKm nur
--   `const km=parseInt(kmVal)||0` ohne jede Pruefung (Stand d99400f); "kann nicht negativ sein" kam am 20.03. (0c364be).
--   fz5.km_stand = 184260 (richtig, NICHT angefasst). Kein anderes Fahrzeug, kein tank_log betroffen.
--
-- ── WAS DAS SKRIPT TUT ──────────────────────────────────────────────────────────────
--   Entfernt in fz5.km_log jedes Element mit km = -999999 UND Datum 2026-03-18 — sonst nichts.
--   Reihenfolge der uebrigen Elemente bleibt. Zweiter Lauf: findet nichts, aendert nichts (NOTICE).
--   Bricht ab, wenn Vorher/Nachher nicht genau 3 -> 2 ist (dann hat sich die Zeile seit der Messung veraendert).
--   Kein CASCADE, kein anderes Fahrzeug, keine andere Spalte (updated_at setzt der Trigger trg_updated_at_fahrzeuge).
--
-- ── NACHHER ──────────────────────────────────────────────────────────────────────────
--   fz5: km_log 3 -> 2 Elemente (184260 / 2026-11-11, 183736 / 2026-06-09), km_stand 184260 unveraendert.
--   HINWEIS: Geraete, die fz5 vor der Bereinigung geladen haben und dann per addKm einen km-Stand eintragen,
--   schicken ihr GANZES lokales km_log (Diff-PUT kmLog) und koennten die Zeile zurueckschreiben -> nach dem Lauf
--   die App auf den Geraeten neu laden (bzw. nachher die Abfrage unten erneut pruefen).
-- =====================================================================================

begin;

do $$
declare
  v_vorher int; v_treffer int; v_nachher int;
begin
  select jsonb_array_length(coalesce(nullif(km_log,''),'[]')::jsonb),
         (select count(*) from jsonb_array_elements(coalesce(nullif(km_log,''),'[]')::jsonb) e
           where e->>'km' = '-999999' and coalesce(e->>'datum', e->>'date') = '2026-03-18')
    into v_vorher, v_treffer
    from public.fahrzeuge where id = 'fz5' for update;

  if v_vorher is null then raise exception 'fz5 nicht gefunden - Abbruch'; end if;
  raise notice 'VORHER fz5: km_log % Elemente, davon % mit km=-999999/2026-03-18', v_vorher, v_treffer;

  if v_treffer = 0 then
    raise notice 'nichts zu tun (schon bereinigt)';
    return;
  end if;
  if v_vorher <> 3 or v_treffer <> 1 then
    raise exception 'Zeile hat sich seit der Messung (3 Elemente, 1 Treffer) veraendert: % / % - Abbruch, neu messen', v_vorher, v_treffer;
  end if;

  update public.fahrzeuge f
     set km_log = (select coalesce(jsonb_agg(e order by o), '[]'::jsonb)::text
                     from jsonb_array_elements(f.km_log::jsonb) with ordinality x(e, o)
                    where not (e->>'km' = '-999999' and coalesce(e->>'datum', e->>'date') = '2026-03-18'))
   where f.id = 'fz5';

  select jsonb_array_length(km_log::jsonb) into v_nachher from public.fahrzeuge where id = 'fz5';
  raise notice 'NACHHER fz5: km_log % Elemente', v_nachher;
  if v_nachher <> v_vorher - 1 then
    raise exception 'erwartet % Elemente, sind % - Abbruch', v_vorher - 1, v_nachher;
  end if;
end $$;

select id, km_stand, jsonb_array_length(km_log::jsonb) as n_km_log, km_log
  from public.fahrzeuge where id = 'fz5';

commit;
