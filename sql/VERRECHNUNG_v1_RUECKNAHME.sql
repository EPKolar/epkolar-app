-- VERRECHNUNG v1 - RUECKNAHME (Human-Run-Gate). Entfernt die Tabelle samt Policies.
-- ACHTUNG: erfasste Verrechnungsstaende gehen verloren -> vorher sichern:
--   create table public._backup_verrechnung_<datum> as select * from public.verrechnung;
-- Die App faellt danach von selbst auf "Tabelle fehlt" zurueck (alles offen, OFFA-Vorbelegung), nichts bricht.
drop policy if exists verrechnung_no_kiosk on public.verrechnung;
drop policy if exists verrechnung_delete on public.verrechnung;
drop policy if exists verrechnung_update on public.verrechnung;
drop policy if exists verrechnung_insert on public.verrechnung;
drop policy if exists verrechnung_select on public.verrechnung;
drop table if exists public.verrechnung;  -- kein CASCADE: nichts haengt daran
