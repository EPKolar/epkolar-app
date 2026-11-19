-- IDEMPOTENT
-- =====================================================================================
-- KAMERAS_v1_ENTWURF.sql  —  Kameras Phase 1: Datenmodell, Zugriffsregeln, RLS, Pruef-Funktion
--
-- STATUS: ENTWURF — NICHT APPLIZIERT. Einspielen nur durch Sebastian ueber das Tor (vorher Probe-Block unten
-- in einer Transaktion fahren). Zweig feature/kameras-phase1 (Basis v3.9.1052 = 525c606).
-- Freigabe Inhaber 19.11.2026 (Betriebsvereinbarung unterschrieben). Doku: docs/kameras/PHASE1_2026-11-19.md
-- Ruecknahme: sql/KAMERAS_v1_RUECKNAHME.sql
--
-- WAS HIER ENTSTEHT
--   kameras           Stammdaten (Name, Standort, Hersteller, Modell, aktiv, Aufbewahrung). KEINE Stream-Adresse,
--                     KEIN Zugangsdatum - diese Tabelle ist fuer berechtigte Nutzer lesbar.
--   kamera_backend    Zuordnung Kamera -> go2rtc-Streamname / Frigate-Kameraname. RLS AN, KEINE Policy,
--                     anon/authenticated ohne jedes Recht -> nur service_role (Edge Function kamera-stream).
--                     Passwoerter stehen NIRGENDS in der Datenbank und nirgends im Repo; sie liegen nur in der
--                     go2rtc-/Frigate-Konfiguration auf dem Video-Host.
--   kamera_zugriff    Regeln je Kamera x (Rolle ODER einzelner Nutzer) mit Wochentagen + Zeitfenster + erlaubt.
--   kamera_abruf_log  Protokoll jeder Stream-Anfrage (erteilt/abgelehnt). Schreibt nur die Edge Function
--                     (service_role); lesen nur Admin.
--
-- ROLLEN (gemessen in index.html v3.9.1052: users.role kennt admin, projektleiter, buero, lagerleitung, monteur,
--   helfer, techniker, obermonteur, lager_display, stempel_terminal; anon ueber auth_role()).
--   Kamerarollen = GENAU admin, projektleiter, buero, lagerleitung — als ausdrueckliche Liste, NICHT is_staff()
--   (is_staff() kennt lagerleitung nicht). Jede andere Rolle (insbesondere monteur/helfer/techniker/obermonteur)
--   bekommt NIE eine Kamera zu sehen, auch nicht ueber eine Nutzer-Ausnahme: die Rollenpruefung steht VOR den Regeln.
--   Massgeblich ist users.role, NICHT das Anzeigefeld users.rolle. (Offene Frage in der Doku: ein Konto mit
--   rolle='Lagerleitung' aber role='monteur' sieht KEINE Kamera — gewollt so, bis Sebastian anders entscheidet.)
--   Nutzer muss aktiv und nicht gesperrt sein (users.active / users.locked typ-agnostisch wie can_edit_urlaub()).
--
-- VORRANG (dokumentiert, in kamera_pruefen umgesetzt; ausgewertet zur Ortszeit Europe/Vienna):
--   0. Rolle nicht in der Kameraliste, Nutzer inaktiv/gesperrt, Kamera inaktiv/unbekannt   -> NEIN (hart)
--   1. Nutzer-Regel  erlaubt=false, Fenster trifft                                          -> NEIN
--   2. Nutzer-Regel  erlaubt=true,  Fenster trifft                                          -> JA
--   3. Rollen-Regel  erlaubt=false, Fenster trifft                                          -> NEIN
--   4. Rollen-Regel  erlaubt=true,  Fenster trifft                                          -> JA
--   5. sonst                                                                                -> NEIN (Standard)
--   Kurz: Nutzer-Sperre > Nutzer-Freigabe > Rollen-Sperre > Rollen-Freigabe > Standard-Nein.
--   Damit laesst sich ein einzelner Projektleiter je Kamera ausdruecklich aussperren (Nutzer-Regel erlaubt=false
--   ohne Fenster = immer), obwohl seine Rolle freigegeben ist.
--   Auch der Admin sieht eine Kamera NUR mit passender Regel (keine stille Admin-Ausnahme beim Ansehen);
--   verwalten (Stammdaten/Regeln) darf er immer.
--   Fenster: wochentage int[] (ISO 1=Mo .. 7=So); von/bis beide NULL = ganzer Tag, sonst von < bis,
--   bis exklusiv ('24:00' erlaubt = bis Mitternacht). Ueber Mitternacht = zwei Regeln.
--
-- KEIN CASCADE (Dauerregel). Fremdschluessel ON DELETE RESTRICT: eine Kamera mit Regeln/Zuordnung laesst sich nicht
-- versehentlich loeschen; die App bietet nur "deaktivieren" (aktiv=false).
-- =====================================================================================

-- 0. Hilfsfunktion: updated_at mitfuehren
create or replace function public.kamera_touch()
returns trigger language plpgsql set search_path = public, pg_temp as $$
begin
  new.updated_at := now();
  return new;
end $$;

-- 1. Stammdaten
create table if not exists public.kameras (
  id                 text primary key default gen_random_uuid()::text,
  name               text not null,
  standort           text,
  hersteller         text,
  modell             text,
  aktiv              boolean not null default true,
  aufbewahrung_tage  integer not null default 3,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  constraint kameras_name_chk check (length(btrim(name)) between 1 and 80),
  -- 72 h = DSG-Regelfall (§ 13 Abs. 3 DSG); laenger nur mit Begruendung, Obergrenze hart 30 Tage
  constraint kameras_aufbewahrung_chk check (aufbewahrung_tage > 0 and aufbewahrung_tage <= 30)
);
drop trigger if exists kameras_touch on public.kameras;
create trigger kameras_touch before update on public.kameras
  for each row execute function public.kamera_touch();

-- 2. Backend-Zuordnung (nur service_role)
create table if not exists public.kamera_backend (
  kamera_id           text primary key references public.kameras(id) on delete restrict,
  stream_name         text not null,
  aufzeichnung_quelle text,
  -- Phase 2: Adressart, die die Edge Function ausgibt (webrtc/llhls ueber go2rtc; mjpeg/snapshot fuer Altkameras
  -- wie Mobotix). Die Zuordnung Streamname -> Kamera-IP steht NUR in der go2rtc-Konfiguration auf dem Video-Host.
  stream_typ          text not null default 'webrtc',
  updated_at          timestamptz not null default now(),
  constraint kamera_backend_stream_chk check (stream_name ~ '^[A-Za-z0-9_-]{1,64}$'),
  constraint kamera_backend_quelle_chk check (aufzeichnung_quelle is null or aufzeichnung_quelle ~ '^[A-Za-z0-9_-]{1,64}$'),
  constraint kamera_backend_typ_chk check (stream_typ in ('webrtc','llhls','mjpeg','snapshot'))
);
drop trigger if exists kamera_backend_touch on public.kamera_backend;
create trigger kamera_backend_touch before update on public.kamera_backend
  for each row execute function public.kamera_touch();

-- 3. Zugriffsregeln
create table if not exists public.kamera_zugriff (
  id          text primary key default gen_random_uuid()::text,
  kamera_id   text not null references public.kameras(id) on delete restrict,
  rolle       text,
  user_id     text,
  wochentage  integer[] not null default '{1,2,3,4,5,6,7}',
  von         time,
  bis         time,
  erlaubt     boolean not null default true,
  bemerkung   text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint kamera_zugriff_ziel_chk check (num_nonnulls(rolle, user_id) = 1),
  constraint kamera_zugriff_rolle_chk check (rolle is null or rolle in ('admin','projektleiter','buero','lagerleitung')),
  constraint kamera_zugriff_user_chk check (user_id is null or length(btrim(user_id)) > 0),
  constraint kamera_zugriff_tage_chk check (cardinality(wochentage) between 1 and 7
    and wochentage <@ array[1,2,3,4,5,6,7] and array_position(wochentage, null) is null),
  constraint kamera_zugriff_zeit_chk check ((von is null and bis is null) or (von is not null and bis is not null and von < bis)),
  constraint kamera_zugriff_bemerkung_chk check (bemerkung is null or length(bemerkung) <= 200)
);
create index if not exists kamera_zugriff_kamera_idx on public.kamera_zugriff (kamera_id);
drop trigger if exists kamera_zugriff_touch on public.kamera_zugriff;
create trigger kamera_zugriff_touch before update on public.kamera_zugriff
  for each row execute function public.kamera_touch();

-- 4. Abruf-Protokoll (schreibt nur die Edge Function)
create table if not exists public.kamera_abruf_log (
  id         bigint generated always as identity primary key,
  ts         timestamptz not null default now(),
  user_id    text,
  kamera_id  text,
  scope      text,
  ergebnis   text not null,
  grund      text,
  constraint kamera_abruf_log_ergebnis_chk check (ergebnis in ('erteilt','abgelehnt')),
  constraint kamera_abruf_log_scope_chk check (scope is null or scope in ('live','aufzeichnung'))
);
create index if not exists kamera_abruf_log_ts_idx on public.kamera_abruf_log (ts desc);

-- 5. Funktionen
-- 5a. Zeitfenster (rein, ohne Tabellenzugriff)
create or replace function public.kamera_fenster_trifft(p_tage integer[], p_von time, p_bis time, p_dow integer, p_zeit time)
returns boolean language sql immutable set search_path = public, pg_temp as $$
  select coalesce(p_dow = any(coalesce(p_tage, array[1,2,3,4,5,6,7])), false)
     and (p_von is null or p_bis is null or (p_zeit >= p_von and p_zeit < p_bis));
$$;

-- 5b. Verwalter = aktiver Admin
create or replace function public.kamera_ist_verwalter()
returns boolean language sql stable security definer set search_path = public, pg_temp as $$
  select exists (
    select 1 from public.users u
     where u.auth_user_id::text = auth.uid()::text
       and coalesce(u.active::text, '1') in ('1','true','t')
       and coalesce(u.locked::text, 'false') in ('0','false','f')
       and lower(coalesce(u.role::text, '')) = 'admin'
  );
$$;

-- 5c. Kern: darf der Auth-Nutzer p_auth die Kamera p_kamera zum Zeitpunkt p_zeitpunkt sehen?
--     INTERN — kein Recht fuer anon/authenticated; aufgerufen ueber kamera_darf_sehen (SECURITY DEFINER).
create or replace function public.kamera_pruefen(p_auth uuid, p_kamera text, p_zeitpunkt timestamptz)
returns boolean language plpgsql stable security definer set search_path = public, pg_temp as $$
declare
  v_uid   text;
  v_role  text;
  v_local timestamp;
  v_dow   integer;
  v_zeit  time;
begin
  if p_auth is null or p_kamera is null or p_zeitpunkt is null then
    return false;
  end if;
  select u.id::text, lower(coalesce(u.role::text, ''))
    into v_uid, v_role
    from public.users u
   where u.auth_user_id::text = p_auth::text
     and coalesce(u.active::text, '1') in ('1','true','t')
     and coalesce(u.locked::text, 'false') in ('0','false','f')
   limit 1;
  if v_uid is null then
    return false;
  end if;
  -- 0. harte Rollenliste (ausdruecklich, NICHT is_staff())
  if v_role not in ('admin','projektleiter','buero','lagerleitung') then
    return false;
  end if;
  if not exists (select 1 from public.kameras k where k.id = p_kamera and k.aktiv) then
    return false;
  end if;
  v_local := p_zeitpunkt at time zone 'Europe/Vienna';
  v_dow   := extract(isodow from v_local)::integer;
  v_zeit  := v_local::time;
  -- 1. Nutzer-Sperre
  if exists (select 1 from public.kamera_zugriff z
              where z.kamera_id = p_kamera and z.user_id = v_uid and not z.erlaubt
                and public.kamera_fenster_trifft(z.wochentage, z.von, z.bis, v_dow, v_zeit)) then
    return false;
  end if;
  -- 2. Nutzer-Freigabe
  if exists (select 1 from public.kamera_zugriff z
              where z.kamera_id = p_kamera and z.user_id = v_uid and z.erlaubt
                and public.kamera_fenster_trifft(z.wochentage, z.von, z.bis, v_dow, v_zeit)) then
    return true;
  end if;
  -- 3. Rollen-Sperre
  if exists (select 1 from public.kamera_zugriff z
              where z.kamera_id = p_kamera and z.rolle = v_role and not z.erlaubt
                and public.kamera_fenster_trifft(z.wochentage, z.von, z.bis, v_dow, v_zeit)) then
    return false;
  end if;
  -- 4. Rollen-Freigabe
  if exists (select 1 from public.kamera_zugriff z
              where z.kamera_id = p_kamera and z.rolle = v_role and z.erlaubt
                and public.kamera_fenster_trifft(z.wochentage, z.von, z.bis, v_dow, v_zeit)) then
    return true;
  end if;
  -- 5. Standard
  return false;
end $$;

-- 5d. Oeffentliche Pruefung fuer den angemeldeten Nutzer (RLS + Edge Function mit dem JWT des Aufrufers)
create or replace function public.kamera_darf_sehen(p_kamera text, p_zeitpunkt timestamptz default now())
returns boolean language sql stable security definer set search_path = public, pg_temp as $$
  select public.kamera_pruefen(auth.uid(), p_kamera, p_zeitpunkt);
$$;

revoke all on function public.kamera_pruefen(uuid, text, timestamptz) from public, anon, authenticated;
revoke all on function public.kamera_darf_sehen(text, timestamptz) from public, anon;
grant execute on function public.kamera_darf_sehen(text, timestamptz) to authenticated;
revoke all on function public.kamera_ist_verwalter() from public, anon;
grant execute on function public.kamera_ist_verwalter() to authenticated;

-- 6. Tabellenrechte + RLS
revoke all on public.kameras, public.kamera_zugriff, public.kamera_backend, public.kamera_abruf_log from anon;
revoke all on public.kamera_backend from authenticated;
revoke all on public.kamera_abruf_log from authenticated;
grant select on public.kamera_abruf_log to authenticated;
grant select, insert, update, delete on public.kameras, public.kamera_zugriff to authenticated;

alter table public.kameras          enable row level security;
alter table public.kamera_zugriff   enable row level security;
alter table public.kamera_backend   enable row level security;
alter table public.kamera_abruf_log enable row level security;

-- kameras: lesen = Admin (Verwaltung) ODER wer die Kamera JETZT sehen darf; schreiben = nur Admin
drop policy if exists kameras_select on public.kameras;
create policy kameras_select on public.kameras for select to authenticated
  using (public.kamera_ist_verwalter() or public.kamera_darf_sehen(id));
drop policy if exists kameras_insert on public.kameras;
create policy kameras_insert on public.kameras for insert to authenticated
  with check (public.kamera_ist_verwalter());
drop policy if exists kameras_update on public.kameras;
create policy kameras_update on public.kameras for update to authenticated
  using (public.kamera_ist_verwalter()) with check (public.kamera_ist_verwalter());
drop policy if exists kameras_delete on public.kameras;
create policy kameras_delete on public.kameras for delete to authenticated
  using (public.kamera_ist_verwalter());

-- kamera_zugriff: lesen und schreiben nur Admin
drop policy if exists kamera_zugriff_admin on public.kamera_zugriff;
create policy kamera_zugriff_admin on public.kamera_zugriff for all to authenticated
  using (public.kamera_ist_verwalter()) with check (public.kamera_ist_verwalter());

-- kamera_backend: KEINE Policy -> nur service_role (umgeht RLS). Absichtlich leer.

-- kamera_abruf_log: lesen nur Admin; schreiben nur service_role (keine Insert-Policy)
drop policy if exists kamera_abruf_log_select on public.kamera_abruf_log;
create policy kamera_abruf_log_select on public.kamera_abruf_log for select to authenticated
  using (public.kamera_ist_verwalter());

-- =====================================================================================
-- NACHPRUEFUNG (nach dem Einspielen):
--   select relname, relrowsecurity from pg_class where relname in ('kameras','kamera_zugriff','kamera_backend','kamera_abruf_log');
--     -- erwartet 4 x true
--   select tablename, policyname, cmd, roles from pg_policies where tablename like 'kamera%' order by 1,2;
--     -- erwartet: kameras 4 Policies, kamera_zugriff 1 (ALL), kamera_abruf_log 1 (SELECT), kamera_backend KEINE
--   select grantee, privilege_type from information_schema.role_table_grants
--    where table_schema='public' and table_name='kamera_backend' and grantee in ('anon','authenticated');
--     -- erwartet 0 Zeilen
--   select routine_name, grantee from information_schema.routine_privileges
--    where routine_schema='public' and routine_name in ('kamera_pruefen','kamera_darf_sehen','kamera_ist_verwalter') order by 1,2;
--     -- erwartet: kamera_pruefen NICHT fuer anon/authenticated/PUBLIC; kamera_darf_sehen nur authenticated (+Eigentuemer)
--   select prosecdef, proconfig from pg_proc where proname in ('kamera_pruefen','kamera_darf_sehen','kamera_ist_verwalter');
--     -- erwartet prosecdef=true, proconfig enthaelt search_path=public, pg_temp
--
-- PROBE (BEGIN ... ROLLBACK — aendert nichts dauerhaft). Platzhalter ersetzen:
--   <AUTH_ADMIN>    auth.users.id eines aktiven Admins
--   <AUTH_PL>       auth.users.id eines aktiven Projektleiters  (users.id dazu = <UID_PL>)
--   <AUTH_PL2>      auth.users.id eines ZWEITEN Projektleiters (falls vorhanden; sonst Schritt (d2) auslassen)
--   <AUTH_MONTEUR>  auth.users.id eines Monteurs
--   <UID_MONTEUR>   users.id dieses Monteurs
--
-- begin;
--   -- (a) reine Fensterlogik
--   select public.kamera_fenster_trifft('{1,2,3,4,5}', '07:00', '17:00', 1, '07:00');   -- erwartet true  (von inklusiv)
--   select public.kamera_fenster_trifft('{1,2,3,4,5}', '07:00', '17:00', 1, '17:00');   -- erwartet false (bis exklusiv)
--   select public.kamera_fenster_trifft('{1,2,3,4,5}', '07:00', '17:00', 6, '10:00');   -- erwartet false (Samstag)
--   select public.kamera_fenster_trifft('{1,2,3,4,5,6,7}', null, null, 7, '03:00');     -- erwartet true  (ganzer Tag)
--   -- (b) Testdaten (als Eigentuemer; ROLLBACK nimmt sie zurueck)
--   insert into public.kameras (id, name, standort, aufbewahrung_tage) values ('__probe_kam__', 'Probe', 'Probe', 3);
--   insert into public.kamera_backend (kamera_id, stream_name) values ('__probe_kam__', 'probe_stream');
--   insert into public.kamera_zugriff (kamera_id, rolle, erlaubt) values ('__probe_kam__', 'projektleiter', true);
--   insert into public.kamera_zugriff (kamera_id, rolle, erlaubt) values ('__probe_kam__', 'admin', true);
--   insert into public.kamera_zugriff (kamera_id, user_id, erlaubt, bemerkung)
--     values ('__probe_kam__', '<UID_PL>', false, 'Probe: PL ausgesperrt');
--   -- Nutzer-Freigabe fuer einen Monteur darf NICHTS bewirken (Rollenliste ist hart):
--   insert into public.kamera_zugriff (kamera_id, user_id, erlaubt) values ('__probe_kam__', '<UID_MONTEUR>', true);
--   -- Fenster-Probe: Rollen-Freigabe nur Mo-Fr 07-17 fuer buero
--   insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt)
--     values ('__probe_kam__', 'buero', '{1,2,3,4,5}', '07:00', '17:00', true);
--   -- Constraint-Proben (je SAVEPOINT, weil ein Fehler sonst die Transaktion abbricht)
--   savepoint c1; insert into public.kameras (name, aufbewahrung_tage) values ('x', 0);    -- erwartet ERROR kameras_aufbewahrung_chk
--   rollback to savepoint c1;
--   savepoint c2; insert into public.kameras (name, aufbewahrung_tage) values ('x', 31);   -- erwartet ERROR kameras_aufbewahrung_chk
--   rollback to savepoint c2;
--   savepoint c3; insert into public.kamera_zugriff (kamera_id, rolle, user_id) values ('__probe_kam__', 'buero', 'u1');
--     -- erwartet ERROR kamera_zugriff_ziel_chk (genau eines von rolle/user_id)
--   rollback to savepoint c3;
--   savepoint c4; insert into public.kamera_zugriff (kamera_id, rolle) values ('__probe_kam__', 'monteur');
--     -- erwartet ERROR kamera_zugriff_rolle_chk
--   rollback to savepoint c4;
--   savepoint c5; insert into public.kamera_zugriff (kamera_id, rolle, wochentage) values ('__probe_kam__', 'buero', '{0,8}');
--     -- erwartet ERROR kamera_zugriff_tage_chk
--   rollback to savepoint c5;
--   savepoint c6; insert into public.kamera_zugriff (kamera_id, rolle, von, bis) values ('__probe_kam__', 'buero', '17:00', '07:00');
--     -- erwartet ERROR kamera_zugriff_zeit_chk
--   rollback to savepoint c6;
--   savepoint c7; delete from public.kameras where id = '__probe_kam__';
--     -- erwartet ERROR foreign key (RESTRICT, kein CASCADE)
--   rollback to savepoint c7;
--
--   -- (c) Admin: sieht die Kamera, darf_sehen = true (Rollen-Freigabe admin), sieht Regeln, sieht KEIN Backend
--   set local role authenticated;
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_ADMIN>','role','authenticated')::text, true);
--   select count(*) from public.kameras where id = '__probe_kam__';                -- erwartet 1
--   select public.kamera_darf_sehen('__probe_kam__');                               -- erwartet true
--   select count(*) from public.kamera_zugriff where kamera_id = '__probe_kam__';  -- erwartet 5
--   savepoint b1; select count(*) from public.kamera_backend;                      -- erwartet ERROR 42501 permission denied
--   rollback to savepoint b1;
--   -- (d) ausgesperrter PL: sieht NICHTS, obwohl die Rolle freigegeben ist
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_PL>','role','authenticated')::text, true);
--   select count(*) from public.kameras where id = '__probe_kam__';                -- erwartet 0
--   select public.kamera_darf_sehen('__probe_kam__');                               -- erwartet false
--   select count(*) from public.kamera_zugriff;                                     -- erwartet 0 (Regeln nur Admin)
--   savepoint d0; update public.kameras set name = 'hack' where id = '__probe_kam__';
--   rollback to savepoint d0;                                                        -- (trifft 0 Zeilen)
--   -- (d2) anderer PL: sieht die Kamera (Rollen-Freigabe)
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_PL2>','role','authenticated')::text, true);
--   select public.kamera_darf_sehen('__probe_kam__');                               -- erwartet true
--   -- Zeitpunkt-Probe (Wiener Ortszeit): Samstag 10:00 vs. Montag 10:00 fuer Rolle buero
--   -- (Buero-Konto <AUTH_BUERO> einsetzen, falls vorhanden)
--   -- select public.kamera_darf_sehen('__probe_kam__', '2026-11-21 10:00 Europe/Vienna');  -- erwartet false (Sa)
--   -- select public.kamera_darf_sehen('__probe_kam__', '2026-11-23 10:00 Europe/Vienna');  -- erwartet true  (Mo)
--   -- select public.kamera_darf_sehen('__probe_kam__', '2026-11-23 17:00 Europe/Vienna');  -- erwartet false (bis exklusiv)
--   -- (e) Monteur: NIE — trotz eigener Nutzer-Freigabe
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_MONTEUR>','role','authenticated')::text, true);
--   select count(*) from public.kameras;                                            -- erwartet 0
--   select public.kamera_darf_sehen('__probe_kam__');                               -- erwartet false
--   select count(*) from public.kamera_zugriff;                                     -- erwartet 0
--   select count(*) from public.kamera_abruf_log;                                   -- erwartet 0
--   savepoint e1; select count(*) from public.kamera_backend;                      -- erwartet ERROR 42501
--   rollback to savepoint e1;
--   savepoint e2; insert into public.kameras (name) values ('monteur-probe');       -- erwartet ERROR 42501 (RLS)
--   rollback to savepoint e2;
--   savepoint e3; select public.kamera_pruefen('<AUTH_MONTEUR>'::uuid, '__probe_kam__', now());
--     -- erwartet ERROR permission denied for function kamera_pruefen
--   rollback to savepoint e3;
--   -- (f) anon: nichts
--   reset role; set local role anon;
--   savepoint f1; select count(*) from public.kameras;                             -- erwartet ERROR 42501
--   rollback to savepoint f1;
--   savepoint f2; select public.kamera_darf_sehen('__probe_kam__');                -- erwartet ERROR permission denied
--   rollback to savepoint f2;
--   reset role;
--   -- (g) inaktive Kamera: auch der Admin sieht sie nicht mehr im Stream (Verwaltung zeigt sie weiter)
--   update public.kameras set aktiv = false where id = '__probe_kam__';
--   set local role authenticated;
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_ADMIN>','role','authenticated')::text, true);
--   select public.kamera_darf_sehen('__probe_kam__');                               -- erwartet false
--   select count(*) from public.kameras where id = '__probe_kam__';                -- erwartet 1 (Verwalter)
--   reset role;
-- rollback;
--   -- nach ROLLBACK: select count(*) from public.kameras where id='__probe_kam__';  -- erwartet 0
-- =====================================================================================
