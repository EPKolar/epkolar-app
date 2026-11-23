-- VERRECHNUNG v1 - ENTWURF (Human-Run-Gate; NICHT von CC ausgefuehrt). Erst PROBE, dann diese Datei EINZELN.
-- Zweck: Verrechnungsstand je Auftrag (Buero-Portal > Verrechnung). Ein Satz je Auftrag.
--   bezug_typ  as | stoerung | projekt | freitext
--   bezug_ref  arbeitsscheine.id | projects.id | normalisierter Freitext (trim, lower, Leerzeichen zusammengefasst, max 300)
--   Logik in der App: Eintrag verrechnet, wenn voll=true ODER Eintragsdatum <= verrechnet_bis; sonst offen.
-- Schreiben nur admin/buero (current_user_role), lesen alle angemeldeten ausser Kiosk. Kein CASCADE, keine Fremdschluessel
-- (Freitext hat kein Ziel; geloeschte Scheine/Projekte lassen nur einen toten Satz zurueck, der nichts zaehlt).
create table if not exists public.verrechnung (
  bezug_typ      text not null check (bezug_typ in ('as','stoerung','projekt','freitext')),
  bezug_ref      text not null check (length(bezug_ref) between 1 and 300),
  verrechnet_bis date null,
  voll           boolean not null default false,
  verrechnet_am  timestamptz not null default now(),
  verrechnet_von text null check (verrechnet_von is null or length(verrechnet_von) <= 200),
  primary key (bezug_typ, bezug_ref)
);
comment on table public.verrechnung is 'Verrechnungsstand je Auftrag (Buero-Portal). App: verrechnet = voll OR datum <= verrechnet_bis. OFFA schreibt die Rechnungen, hier nur der Stand.';

alter table public.verrechnung enable row level security;

revoke all on table public.verrechnung from public;
revoke all on table public.verrechnung from anon;
grant select, insert, update, delete on table public.verrechnung to authenticated;

create policy verrechnung_select on public.verrechnung for select to authenticated using (true);
create policy verrechnung_insert on public.verrechnung for insert to authenticated with check (public.current_user_role() in ('admin','buero'));
create policy verrechnung_update on public.verrechnung for update to authenticated using (public.current_user_role() in ('admin','buero')) with check (public.current_user_role() in ('admin','buero'));
create policy verrechnung_delete on public.verrechnung for delete to authenticated using (public.current_user_role() in ('admin','buero'));
-- Kiosk (lager_display u. a.) wie bei time_entries ausgesperrt
create policy verrechnung_no_kiosk on public.verrechnung as restrictive for all to authenticated using (not public.is_kiosk_role()) with check (not public.is_kiosk_role());
