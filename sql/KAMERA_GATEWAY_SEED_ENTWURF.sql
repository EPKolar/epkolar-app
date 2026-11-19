-- IDEMPOTENT
-- =====================================================================================
-- KAMERA_GATEWAY_SEED_ENTWURF.sql  —  4 LIVE-Kameras am QNAP-Gateway anmelden (EPKolar, 20.11.2026)
--
-- STATUS: ENTWURF — NICHT eingespielt. ANWENDUNG (BEGIN ... COMMIT), nur durch Sebastian im SQL-Editor.
-- VORHER: sql/KAMERA_GATEWAY_SEED_PROBE.sql ausfuehren (BEGIN ... ROLLBACK, jede Zeile OK).
-- Ruecknahme: sql/KAMERA_GATEWAY_SEED_RUECKNAHME.sql. Anleitung: docs/kameras/PILOT_HEUTE.md, Pruefung: PILOT_TESTLISTE.md
-- Voraussetzung: sql/KAMERAS_v1_ENTWURF.sql ist eingespielt (Stand 19.11.: ja) inkl. kamera_backend.stream_typ.
--
-- ERSETZT den Pilot-Seed sql/KAMERA_PILOT_HEUTE_ENTWURF.sql (IDs kam_g3_01/kam_g3_lager03, Streams g3_01/g3_lager03).
-- NIE BEIDE: liegen die Pilot-IDs oder Pilot-Streams schon in der DB, bricht dieser Seed ab -> zuerst
-- sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql ausfuehren, dann diesen Seed.
--
-- WAS HIER ENTSTEHT (genau diese Zeilen, sonst nichts):
--   kameras         elektrolager03 (.37), verkauf02 (.38), cam39 (.39), hochregal01 (.61)
--                   ID = go2rtc-Streamname auf der QNAP (Entscheid GF 20.11.2026, stabil).
--                   name = Klartext: 'Elektrolager 03', 'Verkauf 02', 'Hochregal 01'; cam39 ist NICHT in Surveillance
--                   Station -> vorlaeufig 'Kamera .39 (Name folgt)', standort 'offen'. Aenderbar in der App.
--                   standort sonst "Standort folgt", Ubiquiti UVC G3 Dome, aktiv.
--                   aufbewahrung_tage 3 = nur der Pflichtwert der Spalte (DSG-Regelfall). Es wird NICHTS aufgezeichnet:
--                   go2rtc = nur Live-Ansicht; Surveillance Station + Aufnahmen der QNAP sind TABU und unberuehrt.
--   kamera_backend  stream_name = ID (elektrolager03, verkauf02, cam39, hochregal01), stream_typ webrtc,
--                   aufzeichnung_quelle NULL (keine Aufzeichnung -> Aufzeichnungsanfragen enden mit 503)
--   kamera_zugriff  je Kamera: admin immer; buero Mo-Fr 07:00-17:00 (Wiener Ortszeit, ganze Minuten, bis exklusiv)
--                   Kennzeichen in bemerkung: 'GATEWAY_SEED' (die Ruecknahme loescht nur so markierte Regeln)
-- BEWUSST NICHT HIER: Kamera-Adressen, Ports, Benutzer, Kennwoerter. Die Zuordnung Streamname -> Kamera steht NUR
-- in der go2rtc-Konfiguration auf der QNAP. Den Streamnamen kann die App absichtlich NICHT schreiben.
--
--
-- ZWEITER BLOCK - MOBOTIX (5 Stueck), STANDARD AUS. Schalter oben direkt nach "begin;":
--     set local epk.mobotix_aktiv = 'false';   -> heute: nur die 4 G3 entstehen
--     set local epk.mobotix_aktiv = 'true';    -> zusaetzlich mob32, mob33, mob34, mob35, mob36
--   Erst einschalten, wenn der Lese-Benutzer ("nur Live-Ansicht") auf JEDER Mobotix angelegt ist (macht der GF/Owner
--   am Geraet) und go2rtc auf der QNAP die mob-Streams liefert. Mobotix kann kein RTSP: go2rtc holt das
--   HTTP-MJPEG (cgi-bin/faststream.jpg) und reicht es OHNE Umwandlung durch (die ARM-CPU der QNAP nimmt bereits
--   auf) -> stream_typ 'mjpeg' (App: Bild-Element auf /live/<s>/mjpeg, Proxy -> go2rtc /api/stream.mjpeg?src=<s>).
--   Namen laut Surveillance Station (NUR als Kommentar, Anzeigename vorlaeufig "Mobotix .NN (Name folgt)"):
--     mob32 = Hof, mob33 = Hochregal03, mob34 = Hochregal02, mob35 = Elektrolager01, mob36 = Elektrolager02
--   Regeln wie G3: admin immer, buero Mo-Fr 07:00-17:00, Kennzeichen 'GATEWAY_SEED'.
--
-- IDEMPOTENT: zweimal ausfuehren aendert nichts. KEIN CASCADE.
-- =====================================================================================

begin;

-- MOBOTIX-SCHALTER (nur fuer diese Transaktion): 'false' = nur die 4 G3 (Standard), 'true' = zusaetzlich 5 Mobotix
set local epk.mobotix_aktiv = 'false';

-- 0. Vorpruefung (VOR dem ersten insert)
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
  -- Pilot-Seed liegt noch in der DB -> NICHT beides: erst die Pilot-Ruecknahme
  if exists (select 1 from public.kameras where id in ('kam_g3_01', 'kam_g3_lager03'))
     or exists (select 1 from public.kamera_backend where stream_name in ('g3_01', 'g3_lager03')) then
    raise exception 'Pilot-Seed ist noch eingespielt (kam_g3_01/kam_g3_lager03) - zuerst sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql ausfuehren, dann diesen Seed';
  end if;
  -- ID schon da, aber mit anderem Streamnamen -> Abbruch (nichts ueberschreiben)
  if exists (select 1 from public.kamera_backend b
              where b.kamera_id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36')
                and b.stream_name <> b.kamera_id) then
    raise exception 'Gateway-ID ist schon mit einem anderen Streamnamen belegt - abgebrochen, erst klaeren';
  end if;
  -- Streamname schon einer ANDEREN Kamera zugeordnet -> Abbruch
  if exists (select 1 from public.kamera_backend b
              where b.stream_name in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36')
                and b.kamera_id not in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01', 'mob32', 'mob33', 'mob34', 'mob35', 'mob36')) then
    raise exception 'Gateway-Streamname gehoert schon einer anderen Kamera - abgebrochen, erst klaeren';
  end if;
  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  raise notice 'VORHER: kameras=%, kamera_backend=%, kamera_zugriff=%  (Mobotix-Schalter: %)', n_kam, n_be, n_z,
    coalesce(current_setting('epk.mobotix_aktiv', true), 'false');
  if exists (select 1 from public.kameras where id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01')) then
    raise notice 'Gateway-IDs sind schon (passend) angelegt - fehlende Zeilen werden ergaenzt, nichts ueberschrieben';
  end if;
end $$;

-- 1. Stammdaten (Anzeigename vorlaeufig, in der App aenderbar)
insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
  ('elektrolager03', 'Elektrolager 03',         'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', true, 3),
  ('verkauf02',      'Verkauf 02',              'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', true, 3),
  ('cam39',          'Kamera .39 (Name folgt)', 'offen',          'Ubiquiti', 'UVC G3 Dome', true, 3),
  ('hochregal01',    'Hochregal 01',            'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', true, 3)
on conflict (id) do nothing;

-- 2. Backend-Zuordnung (nur service_role liest; Streamname = go2rtc auf der QNAP; keine Aufzeichnung)
insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
  ('elektrolager03', 'elektrolager03', null, 'webrtc'),
  ('verkauf02',      'verkauf02',      null, 'webrtc'),
  ('cam39',          'cam39',          null, 'webrtc'),
  ('hochregal01',    'hochregal01',    null, 'webrtc')
on conflict (kamera_id) do nothing;

-- 3a. Zugriff: admin immer (alle Tage, ganztags = von/bis null)
insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'GATEWAY_SEED admin immer'
  from public.kameras k
 where k.id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01')
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'admin' and z.user_id is null
                      and z.von is null and z.bis is null and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5,6,7}');

-- 3b. Zugriff: buero Mo-Fr 07:00-17:00 (Wiener Ortszeit, 17:00 exklusiv, ganze Minuten)
insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'GATEWAY_SEED buero Mo-Fr 07-17'
  from public.kameras k
 where k.id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01')
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'buero' and z.user_id is null
                      and z.von = time '07:00' and z.bis = time '17:00' and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5}');

-- 3c. MOBOTIX-BLOCK (zweiter Block) - wirkt NUR bei epk.mobotix_aktiv = 'true' (Schalter oben), sonst 0 Zeilen.
--     mob32 Hof, mob33 Hochregal03, mob34 Hochregal02, mob35 Elektrolager01, mob36 Elektrolager02 (SurvStation, nur Kommentar)
insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage)
select v.id, v.name, 'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3
  from (values ('mob32', 'Mobotix .32 (Name folgt)'), ('mob33', 'Mobotix .33 (Name folgt)'),
               ('mob34', 'Mobotix .34 (Name folgt)'), ('mob35', 'Mobotix .35 (Name folgt)'),
               ('mob36', 'Mobotix .36 (Name folgt)')) as v(id, name)
 where coalesce(current_setting('epk.mobotix_aktiv', true), 'false') = 'true'
on conflict (id) do nothing;

insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ)
select k.id, k.id, null, 'mjpeg'
  from public.kameras k
 where k.id in ('mob32', 'mob33', 'mob34', 'mob35', 'mob36')
   and coalesce(current_setting('epk.mobotix_aktiv', true), 'false') = 'true'
on conflict (kamera_id) do nothing;

insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'GATEWAY_SEED admin immer'
  from public.kameras k
 where k.id in ('mob32', 'mob33', 'mob34', 'mob35', 'mob36')
   and coalesce(current_setting('epk.mobotix_aktiv', true), 'false') = 'true'
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'admin' and z.user_id is null
                      and z.von is null and z.bis is null and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5,6,7}');

insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'GATEWAY_SEED buero Mo-Fr 07-17'
  from public.kameras k
 where k.id in ('mob32', 'mob33', 'mob34', 'mob35', 'mob36')
   and coalesce(current_setting('epk.mobotix_aktiv', true), 'false') = 'true'
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'buero' and z.user_id is null
                      and z.von = time '07:00' and z.bis = time '17:00' and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5}');

-- 4. Nachher-Zahlen und Kontrolle (erwartet G3: 4 Kameras, 4 Zuordnungen, 8 GATEWAY_SEED-Regeln;
--    Mobotix nur bei Schalter 'true': 5/5/10, sonst 0/0/0)
do $$
declare
  n_kam integer; n_be integer; n_z integer; g_kam integer; g_be integer; g_z integer;
  m_kam integer; m_be integer; m_soll integer;
begin
  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  select count(*) into g_kam from public.kameras where id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01');
  select count(*) into g_be from public.kamera_backend
   where kamera_id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01') and stream_name = kamera_id;
  select count(*) into g_z from public.kamera_zugriff
   where kamera_id in ('elektrolager03', 'verkauf02', 'cam39', 'hochregal01') and bemerkung like 'GATEWAY\_SEED%';
  select count(*) into m_kam from public.kameras where id in ('mob32', 'mob33', 'mob34', 'mob35', 'mob36');
  select count(*) into m_be from public.kamera_backend
   where kamera_id in ('mob32', 'mob33', 'mob34', 'mob35', 'mob36') and stream_name = kamera_id and stream_typ = 'mjpeg';
  m_soll := case when coalesce(current_setting('epk.mobotix_aktiv', true), 'false') = 'true' then 5 else 0 end;
  raise notice 'NACHHER: kameras=%, kamera_backend=%, kamera_zugriff=%  (G3: %/%/%, erwartet 4/4/8; Mobotix: %/%, erwartet %/%)',
    n_kam, n_be, n_z, g_kam, g_be, g_z, m_kam, m_be, m_soll, m_soll;
  if g_kam <> 4 or g_be <> 4 then
    raise exception 'Kontrolle: Gateway-Kameras/Zuordnungen nicht vollstaendig - Transaktion verworfen';
  end if;
  if m_soll = 5 and (m_kam <> 5 or m_be <> 5) then
    raise exception 'Kontrolle: Mobotix-Block eingeschaltet, aber nicht vollstaendig - Transaktion verworfen';
  end if;
end $$;

commit;

-- Sichtkontrolle danach (nur lesen):
-- select k.id, k.name, k.aktiv, b.stream_name, b.stream_typ, b.aufzeichnung_quelle
--   from public.kameras k join public.kamera_backend b on b.kamera_id = k.id order by k.id;
-- select kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung from public.kamera_zugriff order by 1, 2;
