-- IDEMPOTENT
-- =====================================================================================
-- FLOTTE_AUSBAU_v1_ENTWURF.sql  —  ENTWURF, NICHT ANGEWENDET (19.11.2026)
-- Gehoert zu docs/flotte/AUSBAU_2026-11-19.md, Abschnitt 4 ("braucht DB").
-- Erst nach Freigabe durch Sebastian im SQL-Editor ausfuehren. Die App v1049 braucht
-- NICHTS hiervon - alle Lese-Ansichten laufen ohne diese Spalten.
--
-- Vor dem Lauf pruefen (Live-Schema ist von hier aus NICHT einsehbar):
--   1. Typ von fahrzeuge.id und monteure.id (die App vergibt uid()-Strings -> vermutlich text).
--   2. Bestehende RLS-Policies auf fahrzeuge (Rollen admin/projektleiter/buero/lagerleitung)
--      und die neue Tabelle daran angleichen - unten nur als Vorlage.
--   3. Leerstrings: die App schreibt aus Formularfeldern oft '' statt NULL. Jede CHECK-Liste
--      erlaubt deshalb '' ausdruecklich ('' ist nicht NULL).
-- Regel des Inhabers: keine Dateien in der DB - Nachweisfotos nur als Speicher-PFAD.
-- =====================================================================================

begin;

-- ── 1. Fahrzeug-Stammdaten fuer Fristen und Kosten ──────────────────────────────────
alter table public.fahrzeuge add column if not exists erstzulassung        date;
alter table public.fahrzeuge add column if not exists leasing_geber        text;
alter table public.fahrzeuge add column if not exists leasing_ende         date;
alter table public.fahrzeuge add column if not exists leasing_rate         numeric(10,2);
alter table public.fahrzeuge add column if not exists leasing_km_limit     integer;
alter table public.fahrzeuge add column if not exists versicherung_polizze text;
alter table public.fahrzeuge add column if not exists versicherung_ablauf  date;
alter table public.fahrzeuge add column if not exists versicherung_praemie numeric(10,2);
alter table public.fahrzeuge add column if not exists reifen_saison        text;
alter table public.fahrzeuge add column if not exists reifen_lager         text;
alter table public.fahrzeuge add column if not exists service_km_intervall integer;
alter table public.fahrzeuge add column if not exists naechst_service_km   integer;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'fahrzeuge_reifen_saison_chk') then
    alter table public.fahrzeuge add constraint fahrzeuge_reifen_saison_chk
      check (reifen_saison is null or reifen_saison in ('', 'sommer', 'winter', 'ganzjahr'));
  end if;
  if not exists (select 1 from pg_constraint where conname = 'fahrzeuge_leasing_werte_chk') then
    alter table public.fahrzeuge add constraint fahrzeuge_leasing_werte_chk
      check ((leasing_rate is null or leasing_rate >= 0)
         and (leasing_km_limit is null or leasing_km_limit >= 0)
         and (service_km_intervall is null or service_km_intervall > 0)
         and (naechst_service_km is null or naechst_service_km >= 0));
  end if;
end $$;

-- ── 2. Fuehrerscheinkontrolle (Halterpflicht: regelmaessige Sichtpruefung) ──────────
create table if not exists public.fz_fs_kontrollen (
  id           text primary key default gen_random_uuid()::text,
  monteur_id   text not null,               -- monteure.id; FK erst nach Typ-Pruefung (siehe oben)
  geprueft_am  date not null,
  ergebnis     text not null default 'ok',
  klassen      text,                         -- Komma-Liste wie monteure.fs
  gueltig_bis  date,                         -- Ablaufdatum laut Dokument (C/D: befristet)
  pruefer      text,
  nachweis_path text,                        -- NUR Speicher-Pfad (privater Bucket), nie Base64
  notiz        text,
  created_at   timestamptz not null default now(),
  constraint fz_fs_kontrollen_ergebnis_chk check (ergebnis in ('', 'ok', 'mangel', 'entzogen')),
  constraint fz_fs_kontrollen_kein_base64_chk check (nachweis_path is null or nachweis_path not like 'data:%')
);
create index if not exists fz_fs_kontrollen_monteur_idx on public.fz_fs_kontrollen (monteur_id, geprueft_am desc);

alter table public.fz_fs_kontrollen enable row level security;

-- VORLAGE - an die tatsaechlichen fahrzeuge-Policies angleichen, bevor das hier laeuft.
-- drop policy if exists fz_fs_kontrollen_select on public.fz_fs_kontrollen;
-- create policy fz_fs_kontrollen_select on public.fz_fs_kontrollen for select to authenticated
--   using ( <gleiche Bedingung wie fahrzeuge-Verwalter> );
-- drop policy if exists fz_fs_kontrollen_write on public.fz_fs_kontrollen;
-- create policy fz_fs_kontrollen_write on public.fz_fs_kontrollen for all to authenticated
--   using ( <Verwalter> ) with check ( <Verwalter> );

commit;

-- Gegenprobe nach dem Lauf (Gesamtzahl nachzaehlen, nicht nur "kein Fehler"):
-- select count(*) from information_schema.columns
--  where table_schema='public' and table_name='fahrzeuge'
--    and column_name in ('erstzulassung','leasing_geber','leasing_ende','leasing_rate','leasing_km_limit',
--                        'versicherung_polizze','versicherung_ablauf','versicherung_praemie',
--                        'reifen_saison','reifen_lager','service_km_intervall','naechst_service_km');  -- erwartet 12
-- select relrowsecurity from pg_class where relname='fz_fs_kontrollen';                                 -- erwartet true
