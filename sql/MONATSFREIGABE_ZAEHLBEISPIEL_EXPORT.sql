-- MONATSFREIGABE_ZAEHLBEISPIEL_EXPORT.sql - NUR LESEN. Liefert die Eingabe fuer scripts/mf_zaehlbeispiel.py
-- fuer EINEN Mitarbeiter (monteure-/workers-id, z. B. w4) und EINEN Monat. Vor dem Ausfuehren die zwei Werte unten setzen.
-- Ergebnis (eine JSON-Zeile) als Datei speichern und: python scripts/mf_zaehlbeispiel.py datei.json
-- Abwesenheiten (abs) sind optional: ohne sie schlaegt die Rechnung an genehmigten Abwesenheitstagen mit Stempelung
-- ueber 6 h ggf. klein vor, wo die App keinen Vorschlag machen wuerde. Gemessen 24.11.2026: stempel_log hat 0 Zeilen.
WITH p AS (SELECT 'w4'::text AS wid, '2026-10'::text AS ym),
g AS (SELECT wid, ym, (ym || '-01')::date AS von, ((ym || '-01')::date + interval '1 month')::date AS bis FROM p)
SELECT json_build_object(
  'worker', (SELECT json_build_object('id', w.id, 'name', coalesce(w.name, w.id), 'role', coalesce(w.role, ''))
               FROM public.workers w, g WHERE w.id = g.wid),
  'ym', (SELECT ym FROM g),
  'stempel_log', (SELECT coalesce(json_agg(json_build_object('worker_id', s.worker_id, 'ts', s.ts, 'direction', s.direction) ORDER BY s.ts), '[]'::json)
                    FROM public.stempel_log s, g
                   WHERE s.worker_id = g.wid AND s.ts >= (g.von::timestamp AT TIME ZONE 'Europe/Vienna') AND s.ts < (g.bis::timestamp AT TIME ZONE 'Europe/Vienna')),
  'pause_rules', (SELECT value::json FROM public.system_config WHERE key = 'stempel_pause_rules'),
  'ez_tage', (SELECT coalesce(json_agg(json_build_object('worker_id', e.worker_id, 'datum', e.datum, 'stufe', e.stufe, 'aktiv', e.aktiv)), '[]'::json)
                FROM public.entfernungszulage_tage e, g WHERE e.worker_id = g.wid AND e.datum >= g.von AND e.datum < g.bis)
) AS eingabe;
