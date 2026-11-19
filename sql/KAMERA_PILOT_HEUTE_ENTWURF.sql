-- IDEMPOTENT
-- =====================================================================================
-- KAMERA_PILOT_HEUTE_ENTWURF.sql  —  2 Pilot-Kameras anmelden (EPKolar, 19.11.2026)
--
-- STATUS: ENTWURF — NICHT eingespielt. Einspielen nur durch Sebastian (Supabase SQL-Editor) bzw. ueber das Tor.
-- Voraussetzung: sql/KAMERAS_v1_ENTWURF.sql ist eingespielt (Stand 19.11.: ja, Tabellen leer).
-- ERSETZT fuer den Pilot sql/KAMERAS_PILOT_SEED_ENTWURF.sql (alte Streamnamen g3_37 ... - NICHT zusaetzlich
-- einspielen) und die Anmeldevorlage ausserhalb des Repos. Ruecknahme: sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql
-- Anleitung: docs/kameras/PILOT_HEUTE.md (Schritt d), Pruefung: docs/kameras/PILOT_TESTLISTE.md
--
-- WAS HIER ENTSTEHT (genau diese Zeilen, sonst nichts):
--   kameras         kam_g3_01, kam_g3_lager03 (Ubiquiti UVC G3 Dome, aktiv, Aufbewahrung 3 Tage)
--   kamera_backend  Streamname = go2rtc-Streamname auf dem Video-Host (g3_01, g3_lager03), stream_typ webrtc,
--                   aufzeichnung_quelle = Frigate-Kameraname (gleich dem Streamnamen)
--   kamera_zugriff  je Kamera: admin immer; buero Mo-Fr 07:00-17:00 (ganze Minuten, bis exklusiv)
--                   Kennzeichen in bemerkung: 'PILOT_HEUTE' (die Ruecknahme loescht nur so markierte Regeln)
-- BEWUSST NICHT HIER: Kamera-Adressen, Ports, Benutzer, Kennwoerter, Protect-Tokens. Die Zuordnung
-- Streamname -> Kamera steht NUR in go2rtc.yaml/.env auf dem Video-Host.
-- Den Streamnamen (kamera_backend) kann die App absichtlich NICHT schreiben (keine Rechte fuer authenticated) -
-- deshalb dieses SQL. Namen/Standorte/Regeln lassen sich danach in der App (Kameras -> Verwaltung) aendern.
--
-- IDEMPOTENT: zweimal ausfuehren aendert nichts. Vorpruefung bricht ab, wenn eine Pilot-ID oder ein Pilot-
-- Streamname schon ANDERS belegt ist (dann nichts ueberschreiben, erst klaeren). KEIN CASCADE.
-- =====================================================================================

begin;

-- 0. Vorpruefung: Tabellen vorhanden; Pilot-IDs fehlen ODER sind genau so belegt wie hier vorgesehen
do $$
declare
  n_kam integer; n_be integer; n_z integer;
begin
  if to_regclass('public.kameras') is null or to_regclass('public.kamera_backend') is null
     or to_regclass('public.kamera_zugriff') is null or to_regclass('public.kamera_abruf_log') is null then
    raise exception 'Kamera-Tabellen fehlen - zuerst sql/KAMERAS_v1_ENTWURF.sql';
  end if;
  if not exists (select 1 from information_schema.columns where table_schema = 'public'
                   and table_name = 'kamera_backend' and column_name = 'stream_typ') then
    raise exception 'kamera_backend.stream_typ fehlt - Datenmodell Stand Phase 2 zuerst';
  end if;
  -- ID schon da, aber mit anderem Streamnamen -> Abbruch (nichts ueberschreiben)
  if exists (select 1 from public.kamera_backend b
              where (b.kamera_id = 'kam_g3_01' and b.stream_name <> 'g3_01')
                 or (b.kamera_id = 'kam_g3_lager03' and b.stream_name <> 'g3_lager03')) then
    raise exception 'Pilot-ID ist schon mit einem anderen Streamnamen belegt - abgebrochen, erst klaeren';
  end if;
  -- Streamname schon einer ANDEREN Kamera zugeordnet -> Abbruch
  if exists (select 1 from public.kamera_backend b
              where b.stream_name in ('g3_01', 'g3_lager03')
                and b.kamera_id not in ('kam_g3_01', 'kam_g3_lager03')) then
    raise exception 'Pilot-Streamname gehoert schon einer anderen Kamera - abgebrochen, erst klaeren';
  end if;
  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  raise notice 'VORHER: kameras=%, kamera_backend=%, kamera_zugriff=%', n_kam, n_be, n_z;
  if exists (select 1 from public.kameras where id in ('kam_g3_01', 'kam_g3_lager03')) then
    raise notice 'Pilot-IDs sind schon (passend) angelegt - fehlende Zeilen werden ergaenzt, nichts ueberschrieben';
  end if;
end $$;

-- 1. Stammdaten (Namen/Standorte spaeter in der App aenderbar)
insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
  ('kam_g3_01',      'G3 Dome 01',      'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', true, 3),
  ('kam_g3_lager03', 'Elektrolager 03', 'Elektrolager',   'Ubiquiti', 'UVC G3 Dome', true, 3)
on conflict (id) do nothing;

-- 2. Backend-Zuordnung (nur service_role liest; Streamname = go2rtc.yaml auf dem Video-Host)
insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
  ('kam_g3_01',      'g3_01',      'g3_01',      'webrtc'),
  ('kam_g3_lager03', 'g3_lager03', 'g3_lager03', 'webrtc')
on conflict (kamera_id) do nothing;

-- 3a. Zugriff: admin immer (alle Tage, ganztags = von/bis null)
insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'PILOT_HEUTE admin immer'
  from public.kameras k
 where k.id in ('kam_g3_01', 'kam_g3_lager03')
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'admin' and z.user_id is null
                      and z.von is null and z.bis is null and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5,6,7}');

-- 3b. Zugriff: buero Mo-Fr 07:00-17:00 (Wiener Ortszeit, 17:00 exklusiv, ganze Minuten)
insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'PILOT_HEUTE buero Mo-Fr 07-17'
  from public.kameras k
 where k.id in ('kam_g3_01', 'kam_g3_lager03')
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'buero' and z.user_id is null
                      and z.von = time '07:00' and z.bis = time '17:00' and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5}');

-- 4. Nachher-Zahlen und Kontrolle (erwartet: 2 Kameras, 2 Zuordnungen, 4 PILOT_HEUTE-Regeln)
do $$
declare
  n_kam integer; n_be integer; n_z integer; p_kam integer; p_be integer; p_z integer;
begin
  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  select count(*) into p_kam from public.kameras where id in ('kam_g3_01', 'kam_g3_lager03');
  select count(*) into p_be from public.kamera_backend where kamera_id in ('kam_g3_01', 'kam_g3_lager03');
  select count(*) into p_z from public.kamera_zugriff
   where kamera_id in ('kam_g3_01', 'kam_g3_lager03') and bemerkung like 'PILOT\_HEUTE%';
  raise notice 'NACHHER: kameras=%, kamera_backend=%, kamera_zugriff=%  (Pilot: %/%/%, erwartet 2/2/4)',
    n_kam, n_be, n_z, p_kam, p_be, p_z;
  if p_kam <> 2 or p_be <> 2 then
    raise exception 'Kontrolle: Pilot-Kameras/Zuordnungen nicht vollstaendig - Transaktion verworfen';
  end if;
end $$;

commit;

-- Sichtkontrolle danach (nur lesen):
-- select k.id, k.name, k.aktiv, b.stream_name, b.stream_typ, b.aufzeichnung_quelle
--   from public.kameras k join public.kamera_backend b on b.kamera_id = k.id order by k.id;
-- select kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung from public.kamera_zugriff order by 1, 2;

-- =====================================================================================
-- PROBE (BEGIN ... ROLLBACK - aendert nichts dauerhaft). Statt "begin; ... commit;" oben ausfuehren:
-- Abschnitte 0-4 oben einfuegen (ohne begin/commit), dann:
--   <AUTH_ADMIN>   auth.users.id eines aktiven Admins
--   <AUTH_BUERO>   auth.users.id eines aktiven Buero-Kontos
--   <AUTH_MONTEUR> auth.users.id eines Monteurs
--
-- begin;
--   ... Abschnitte 0-4 ...
--   set local role authenticated;
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_ADMIN>','role','authenticated')::text, true);
--   select public.kamera_darf_sehen('kam_g3_lager03', '2026-11-21 10:00 Europe/Vienna');  -- erwartet true  (Sa, admin immer)
--   savepoint b1; select count(*) from public.kamera_backend;                             -- erwartet ERROR 42501
--   rollback to savepoint b1;
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_BUERO>','role','authenticated')::text, true);
--   select public.kamera_darf_sehen('kam_g3_lager03', '2026-11-23 10:00 Europe/Vienna');  -- erwartet true  (Mo 10:00)
--   select public.kamera_darf_sehen('kam_g3_lager03', '2026-11-23 06:59 Europe/Vienna');  -- erwartet false (vor 07:00)
--   select public.kamera_darf_sehen('kam_g3_lager03', '2026-11-23 17:00 Europe/Vienna');  -- erwartet false (17:00 exklusiv)
--   select public.kamera_darf_sehen('kam_g3_lager03', '2026-11-21 10:00 Europe/Vienna');  -- erwartet false (Samstag)
--   select set_config('request.jwt.claims', json_build_object('sub','<AUTH_MONTEUR>','role','authenticated')::text, true);
--   select public.kamera_darf_sehen('kam_g3_lager03', '2026-11-23 10:00 Europe/Vienna');  -- erwartet false (Rolle)
--   select count(*) from public.kameras;                                                  -- erwartet 0
-- rollback;
-- =====================================================================================
