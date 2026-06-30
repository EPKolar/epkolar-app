-- =============================================================================
-- BAUPROVISORIEN_SCHEMA_stage.sql   (2026-06-30)   project-ref: jiggujpruejkaomgxarp
-- =============================================================================
-- Feature "Bauprovisorien" (Kern). DDL — Human-Run-Gate: Sebastian fuehrt aus.
-- REIHENFOLGE: dieses SQL ZUERST ausfuehren, DANN den Client-Push (sonst fehlt die
-- Tabelle, der neue View laueft ins Leere).
-- Idempotent (if not exists / drop policy if exists). projects.id = text (verifiziert).
-- RLS-Muster gespiegelt von geschuetzten Tabellen: PERMISSIVE is_staff() (admin/buero/
-- projektleiter) fuer alle CMDs + RESTRICTIVE lager_display-Block (Finanzdaten, gleiche
-- Lehre wie Kiosk-PII-Leck: von Anfang an dicht).
-- =============================================================================

-- ── Tabelle: bauprovisorien ──────────────────────────────────────────────────
create table if not exists public.bauprovisorien (
  id               text primary key,
  project_id       text references public.projects(id),     -- nullable
  kunde_nummer     text,
  kunde_name       text,
  bezeichnung      text not null,
  typ              text,
  standort_text    text,
  foto_path        text,
  errichtung_datum date not null,
  abbau_datum      date,
  miete_pro_jahr   numeric,
  status           text default 'aufgestellt',
  notizen          text,
  created_at       timestamptz default now(),
  updated_at       timestamptz default now(),
  constraint bauprovisorien_kunde_chk check (project_id is not null or kunde_nummer is not null)
);
create index if not exists bauprovisorien_project_idx on public.bauprovisorien(project_id);
create index if not exists bauprovisorien_kunde_idx   on public.bauprovisorien(kunde_nummer);
create index if not exists bauprovisorien_status_idx  on public.bauprovisorien(status);

-- ── Tabelle: bauprovisorien_mieten (1 Zeile je Provisorium+Jahr) ─────────────
create table if not exists public.bauprovisorien_mieten (
  id               text primary key,
  provisorium_id   text not null references public.bauprovisorien(id) on delete cascade,
  jahr             int not null,
  verrechnet       boolean default false,
  verrechnet_datum date,
  rechnung_path    text,
  betrag           numeric,
  notiz            text,
  created_at       timestamptz default now(),
  constraint bauprovisorien_mieten_uniq unique (provisorium_id, jahr)
);
create index if not exists bauprovisorien_mieten_prov_idx on public.bauprovisorien_mieten(provisorium_id);

-- ── RLS: bauprovisorien ──────────────────────────────────────────────────────
alter table public.bauprovisorien enable row level security;

drop policy if exists bauprovisorien_select_staff on public.bauprovisorien;
create policy bauprovisorien_select_staff on public.bauprovisorien
  for select to authenticated using (is_staff());
drop policy if exists bauprovisorien_insert_staff on public.bauprovisorien;
create policy bauprovisorien_insert_staff on public.bauprovisorien
  for insert to authenticated with check (is_staff());
drop policy if exists bauprovisorien_update_staff on public.bauprovisorien;
create policy bauprovisorien_update_staff on public.bauprovisorien
  for update to authenticated using (is_staff()) with check (is_staff());
drop policy if exists bauprovisorien_delete_staff on public.bauprovisorien;
create policy bauprovisorien_delete_staff on public.bauprovisorien
  for delete to authenticated using (is_staff());
-- Defense-in-depth: lager_display (Kiosk) hart blocken (Finanzdaten)
drop policy if exists lager_display_no_select on public.bauprovisorien;
create policy lager_display_no_select on public.bauprovisorien
  as restrictive for select to authenticated
  using ((((auth.jwt() -> 'app_metadata') ->> 'role') is distinct from 'lager_display'));

-- ── RLS: bauprovisorien_mieten ───────────────────────────────────────────────
alter table public.bauprovisorien_mieten enable row level security;

drop policy if exists bauprovisorien_mieten_select_staff on public.bauprovisorien_mieten;
create policy bauprovisorien_mieten_select_staff on public.bauprovisorien_mieten
  for select to authenticated using (is_staff());
drop policy if exists bauprovisorien_mieten_insert_staff on public.bauprovisorien_mieten;
create policy bauprovisorien_mieten_insert_staff on public.bauprovisorien_mieten
  for insert to authenticated with check (is_staff());
drop policy if exists bauprovisorien_mieten_update_staff on public.bauprovisorien_mieten;
create policy bauprovisorien_mieten_update_staff on public.bauprovisorien_mieten
  for update to authenticated using (is_staff()) with check (is_staff());
drop policy if exists bauprovisorien_mieten_delete_staff on public.bauprovisorien_mieten;
create policy bauprovisorien_mieten_delete_staff on public.bauprovisorien_mieten
  for delete to authenticated using (is_staff());
drop policy if exists lager_display_no_select on public.bauprovisorien_mieten;
create policy lager_display_no_select on public.bauprovisorien_mieten
  as restrictive for select to authenticated
  using ((((auth.jwt() -> 'app_metadata') ->> 'role') is distinct from 'lager_display'));

-- ── Verify (read-only, nach dem Lauf) ────────────────────────────────────────
-- select tablename, count(*) from pg_policies where schemaname='public'
--   and tablename in ('bauprovisorien','bauprovisorien_mieten') group by 1;   -- je 5 erwartet
-- select relname, relrowsecurity from pg_class
--   where relname in ('bauprovisorien','bauprovisorien_mieten');              -- beide t
