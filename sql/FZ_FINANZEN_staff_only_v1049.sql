-- IDEMPOTENT
-- =====================================================================================
-- FZ_FINANZEN_staff_only_v1049.sql  —  Finanzdaten der Fahrzeuge server-seitig nur fuer Buero/PL/Admin
--
-- STATUS: BEREITS ANGEWENDET am 19.11.2026 (Migrationen `flotte_ausbau_v1_stammdaten_fs_kontrollen` und
-- `flotte_finanzen_eigene_tabelle_nur_hr`) unter Sebastians Freigabe "flotten datenbank machen, freigabe".
-- Diese Datei dokumentiert den LIVE-Stand 1:1 und ist idempotent (erneuter Lauf aendert nichts).
-- Zur Pruefung durch Chat-Claude nachgereicht (der CC-Auftrag sah "nur Datei + Probe" vor).
--
-- WARUM: Security-Review 19.11. — die zuerst in public.fahrzeuge angelegten Leasing-/Versicherungsfelder waren
--   * fuer JEDEN Angemeldeten lesbar (Policy fahrzeuge_select: auth.role()='authenticated') und
--   * fuer den FAHRER schreibbar (Policy fahrzeuge_update_office_or_driver: is_hr() OR fahrer=current_monteur_id()).
--   Spalten-Grants waeren keine Loesung, weil die App fahrzeuge mit select=* liest (ein Spalten-REVOKE wuerde
--   jeden Fahrzeug-Abruf brechen). Darum: eigene Tabelle, eigene Policy, alte Spalten weg.
-- DATEN: alle 7 Finanzspalten waren in 0 von 21 Zeilen befuellt -> kein Verlust.
-- Reifen (reifen_saison, reifen_lager) und Service-km (service_km_intervall, naechst_service_km) bleiben bewusst in
--   fahrzeuge: kein Finanzdatum, der Fahrer darf sie pflegen (bestehende Fahrer-Policy).
-- Rollen: is_hr() = users.role IN ('admin','buero','projektleiter') — identisch zur Menge in is_staff().
-- Kein FK/CASCADE (Dauerregel "kein CASCADE"); Bezug ueber fahrzeug_id wie fz_termine.
-- =====================================================================================

-- 1. alte Finanzspalten aus fahrzeuge entfernen
alter table public.fahrzeuge drop constraint if exists fahrzeuge_leasing_werte_chk;
alter table public.fahrzeuge
  drop column if exists leasing_geber,
  drop column if exists leasing_ende,
  drop column if exists leasing_rate,
  drop column if exists leasing_km_limit,
  drop column if exists versicherung_polizze,
  drop column if exists versicherung_ablauf,
  drop column if exists versicherung_praemie;

-- Service-km-Pruefung (vorher Teil von fahrzeuge_leasing_werte_chk)
do $$ begin
  if not exists (select 1 from pg_constraint where conname = 'fahrzeuge_service_km_chk') then
    alter table public.fahrzeuge add constraint fahrzeuge_service_km_chk
      check ((service_km_intervall is null or service_km_intervall > 0) and (naechst_service_km is null or naechst_service_km >= 0));
  end if;
end $$;

-- 2. Finanztabelle
create table if not exists public.fz_finanzen (
  fahrzeug_id          text primary key,
  leasing_geber        text,
  leasing_ende         date,
  leasing_rate         numeric(10,2),   -- pro Monat
  leasing_km_limit     integer,
  versicherung_polizze text,
  versicherung_ablauf  date,
  versicherung_praemie numeric(10,2),   -- pro Jahr (App: /12 je Monat) - GF-Bestaetigung offen
  updated_at           timestamptz not null default now(),
  constraint fz_finanzen_werte_chk check ((leasing_rate is null or leasing_rate >= 0)
    and (leasing_km_limit is null or leasing_km_limit >= 0) and (versicherung_praemie is null or versicherung_praemie >= 0))
);

-- 3. RLS: lesen UND schreiben nur Buero/PL/Admin; anon und Monteure nichts
alter table public.fz_finanzen enable row level security;
drop policy if exists fz_finanzen_hr on public.fz_finanzen;
create policy fz_finanzen_hr on public.fz_finanzen for all to authenticated
  using (is_hr()) with check (is_hr());
-- anon hat keine Policy -> sieht/aendert nichts.

-- =====================================================================================
-- VORHER (19.11., vor flotte_finanzen_eigene_tabelle_nur_hr):
--   fahrzeuge: 21 Zeilen, Finanzspalten vorhanden (7), 0 Zeilen befuellt
--   fahrzeuge-Policies: fahrzeuge_select [SELECT] authenticated | fahrzeuge_update_office_or_driver [UPDATE] is_hr() OR fahrer=current_monteur_id()
--                       | fahrzeuge_delete [DELETE] admin/PL/buero/lagerleitung | fahrzeuge_insert [INSERT] admin/PL/buero
-- NACHHER (gemessen):
--   fahrzeuge: 21 Zeilen, 0 Spalten like 'leasing%'/'versicherung_%' (alte Freitext-Spalte "versicherung" text bleibt unberuehrt)
--   fz_finanzen: relrowsecurity=true, 1 Policy (fz_finanzen_hr FOR ALL is_hr())
-- GEGENPROBE (je in Transaktion mit Testzeile '__probe__', ROLLBACK):
--   anon:     sieht 0, UPDATE trifft 0 Zeilen
--   Monteur:  sieht 0, UPDATE trifft 0 Zeilen, INSERT -> ERROR 42501 new row violates row-level security policy
--   Buero:    sieht 1 (die Testzeile)
-- Nachpruefung:
--   select count(*) from information_schema.columns where table_schema='public' and table_name='fahrzeuge'
--     and column_name like any(array['leasing%','versicherung_%']);                 -- erwartet 0
--   select policyname, cmd, roles, qual, with_check from pg_policies where tablename='fz_finanzen';  -- erwartet 1 Zeile
-- =====================================================================================
