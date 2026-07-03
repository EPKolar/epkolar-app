-- IDEMPOTENT
-- v3.9.663 Flotte-Datenpfad (Bug-Hunt-Subagent, Traccar-Vorbereitung)
-- Problem: die App zog Marker/Fleet-Liste aus fz_positions?order=ts.desc&limit=200 — ein
-- GLOBALER Deckel ueber ALLE Fahrzeuge. Sobald mehrere Tracker im 30s-Takt pingen, faellt die
-- neueste Zeile eines laenger stillstehenden Fahrzeugs aus den Top-200 → sein Marker verschwindet
-- und die Liste zeigt faelschlich "wartet / kein Signal" obwohl Daten da sind.
-- Loesung: View mit genau EINER (neuester) Zeile je fahrzeug_id. security_invoker=true → es gilt
-- die RLS von fz_positions (is_staff()-SELECT + lager_display RESTRICTIVE), KEINE eigene Policy noetig.
-- Rein additiv/lesend, jederzeit droppbar (DROP VIEW public.fz_latest;). Keine Datenmutation.

create or replace view public.fz_latest
  with (security_invoker = true)
as
select distinct on (fahrzeug_id)
  id, fahrzeug_id, ts, lat, lon, speed, ignition, raw, created_at
from public.fz_positions
order by fahrzeug_id, ts desc;

comment on view public.fz_latest is
  'v3.9.663: neueste Position je fahrzeug_id (DISTINCT ON). security_invoker → RLS von fz_positions greift. Marker/Fleet-Liste der Flotte-Ansicht.';
