-- VERRECHNUNG_HAKEN v1 - ANGEWENDET 24.11.2026 auf Prod (Migration verrechnung_haken_v1), Freigabe GF 24.11.
-- Zweck: Haekchen je KW (art='kw', schluessel 'KW n/JJJJ' wie _vrKW) bzw. spaeter je Eintrag (art='eintrag') in der
-- Verrechnung. Ergaenzt verrechnung.verrechnet_bis/voll, hebt sie nie auf (Regel in _vrIstVerrechnet).
-- Probe vorher (zurueckgerollt, echte Rollen): monteur/projektleiter anlegen 42501, sehen 0; buero anlegen/sehen/loeschen ok;
-- TRUNCATE fuer alle 42501. Nachmessung: RLS an, 5 Policies, anon ohne Zugriff.
create table if not exists public.verrechnung_haken (
  bezug_typ text not null check (bezug_typ in ('as','stoerung','projekt','freitext')),
  bezug_ref text not null check (length(bezug_ref) between 1 and 300),
  art text not null check (art in ('kw','eintrag')),
  schluessel text not null check (length(schluessel) between 1 and 100),
  gesetzt_von text null check (gesetzt_von is null or length(gesetzt_von) <= 200),
  gesetzt_am timestamptz not null default now(),
  primary key (bezug_typ, bezug_ref, art, schluessel));
alter table public.verrechnung_haken enable row level security;
revoke all on table public.verrechnung_haken from public;
revoke all on table public.verrechnung_haken from anon;
revoke all on table public.verrechnung_haken from authenticated;
grant select, insert, update, delete on table public.verrechnung_haken to authenticated;
create policy verrechnung_haken_select on public.verrechnung_haken for select to authenticated using (public.current_user_role() in ('admin','buero'));
create policy verrechnung_haken_insert on public.verrechnung_haken for insert to authenticated with check (public.current_user_role() in ('admin','buero'));
create policy verrechnung_haken_update on public.verrechnung_haken for update to authenticated using (public.current_user_role() in ('admin','buero')) with check (public.current_user_role() in ('admin','buero'));
create policy verrechnung_haken_delete on public.verrechnung_haken for delete to authenticated using (public.current_user_role() in ('admin','buero'));
create policy verrechnung_haken_no_kiosk on public.verrechnung_haken as restrictive for all to authenticated using (not public.is_kiosk_role()) with check (not public.is_kiosk_role());
-- RUECKNAHME (Haekchen gehen verloren, vorher sichern):
--   create table public._backup_verrechnung_haken_<datum> as select * from public.verrechnung_haken;
--   drop table public.verrechnung_haken;   -- kein CASCADE; die App zeigt dann "Haekchen nicht verfuegbar", das Datum funktioniert weiter
