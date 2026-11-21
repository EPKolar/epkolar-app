-- IDEMPOTENT
-- =====================================================================================
-- KAMERA_MOBOTIX_SEED_ENTWURF.sql  —  5 Mobotix-Kameras am QNAP-Gateway anmelden (EPKolar, 21.11.2026)
--
-- STATUS: ENTWURF — NICHT eingespielt. ANWENDUNG (BEGIN ... COMMIT), nur durch Sebastian im SQL-Editor.
-- VORHER: sql/KAMERA_MOBOTIX_SEED_PROBE.sql ausfuehren (BEGIN ... ROLLBACK, jede Zeile OK).
-- Ruecknahme: sql/KAMERA_MOBOTIX_SEED_RUECKNAHME.sql. Anleitung: docs/kameras/MOBOTIX.md
-- Voraussetzung: sql/KAMERA_GATEWAY_SEED_ENTWURF.sql ist eingespielt (Stand 21.11.: ja, 4 G3, Mobotix-Schalter aus)
--                und go2rtc auf der QNAP liefert die 5 Streams (scripts/go2rtc_streams_pruefen.py = Exit 0).
--
-- ERSETZT den Mobotix-Block (mob32..mob36, Schalter epk.mobotix_aktiv) in sql/KAMERA_GATEWAY_SEED_ENTWURF.sql.
-- Dort bleibt der Schalter fuer immer 'false'. NIE BEIDE: liegen mob32..mob36 in der DB, bricht dieser Seed ab.
--
-- WAS HIER ENTSTEHT (genau diese Zeilen, sonst nichts):
--   kameras         hof01, hochregal03, hochregal02, elektrolager01, elektrolager02
--                   ID = go2rtc-Streamname (tools/kamera-proxy-auth/qnap/go2rtc.yaml), Namen laut Surveillance Station:
--                   Endung .32 Hof, .33 Hochregal03, .34 Hochregal02, .35 Elektrolager01, .36 Elektrolager02 (nur Kommentar).
--                   name = Klartext ('Hof', 'Hochregal 03', ...), aenderbar in der App. Mobotix, aktiv.
--                   aufbewahrung_tage 3 = nur der Pflichtwert der Spalte. Es wird NICHTS aufgezeichnet.
--   kamera_backend  stream_name = ID, stream_typ mjpeg (go2rtc reicht MJPEG ohne Umwandlung durch;
--                   App: Bild-Element auf /live/<s>/mjpeg -> Caddy -> go2rtc /api/stream.mjpeg?src=<s>),
--                   aufzeichnung_quelle NULL
--   kamera_zugriff  je Kamera: admin immer; buero Mo-Fr 07:00-17:00 (Wiener Ortszeit, ganze Minuten, bis exklusiv)
--                   Kennzeichen in bemerkung: 'MOBOTIX_SEED' (die Ruecknahme loescht nur so markierte Regeln)
-- BEWUSST NICHT HIER: Kamera-Adressen, Ports, Benutzer, Kennwoerter (nur kam.env auf der QNAP).
--
-- IDEMPOTENT: zweimal ausfuehren aendert nichts. KEIN CASCADE.
-- =====================================================================================

begin;

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
  -- alter Mobotix-Block des Gateway-Seeds (mob32..mob36) eingespielt -> NICHT beides
  if exists (select 1 from public.kameras where id in ('mob32', 'mob33', 'mob34', 'mob35', 'mob36'))
     or exists (select 1 from public.kamera_backend where stream_name in ('mob32', 'mob33', 'mob34', 'mob35', 'mob36')) then
    raise exception 'Alter Mobotix-Block (mob32..mob36) ist eingespielt - abgebrochen, erst mit Chat-Claude/CC klaeren (die Gateway-Ruecknahme loescht auch die 4 G3)';
  end if;
  -- ID schon da, aber mit anderem Streamnamen -> Abbruch (nichts ueberschreiben)
  if exists (select 1 from public.kamera_backend b
              where b.kamera_id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
                and (b.stream_name <> b.kamera_id or b.stream_typ <> 'mjpeg')) then
    raise exception 'Mobotix-ID ist schon mit anderem Streamnamen/Typ belegt - abgebrochen, erst klaeren';
  end if;
  -- Streamname schon einer ANDEREN Kamera zugeordnet -> Abbruch
  if exists (select 1 from public.kamera_backend b
              where b.stream_name in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
                and b.kamera_id not in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')) then
    raise exception 'Mobotix-Streamname gehoert schon einer anderen Kamera - abgebrochen, erst klaeren';
  end if;
  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  raise notice 'VORHER: kameras=%, kamera_backend=%, kamera_zugriff=%', n_kam, n_be, n_z;
  if exists (select 1 from public.kameras where id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')) then
    raise notice 'Mobotix-IDs sind schon (passend) angelegt - fehlende Zeilen werden ergaenzt, nichts ueberschrieben';
  end if;
end $$;

-- 1. Stammdaten (Anzeigename laut Surveillance Station, in der App aenderbar)
insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
  ('hof01',          'Hof',             'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3),
  ('hochregal03',    'Hochregal 03',    'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3),
  ('hochregal02',    'Hochregal 02',    'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3),
  ('elektrolager01', 'Elektrolager 01', 'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3),
  ('elektrolager02', 'Elektrolager 02', 'Standort folgt', 'Mobotix', 'Mobotix (Modell folgt)', true, 3)
on conflict (id) do nothing;

-- 2. Backend-Zuordnung (nur service_role liest; Streamname = go2rtc auf der QNAP; MJPEG; keine Aufzeichnung)
insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
  ('hof01',          'hof01',          null, 'mjpeg'),
  ('hochregal03',    'hochregal03',    null, 'mjpeg'),
  ('hochregal02',    'hochregal02',    null, 'mjpeg'),
  ('elektrolager01', 'elektrolager01', null, 'mjpeg'),
  ('elektrolager02', 'elektrolager02', null, 'mjpeg')
on conflict (kamera_id) do nothing;

-- 3a. Zugriff: admin immer (alle Tage, ganztags = von/bis null)
insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'MOBOTIX_SEED admin immer'
  from public.kameras k
 where k.id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'admin' and z.user_id is null
                      and z.von is null and z.bis is null and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5,6,7}');

-- 3b. Zugriff: buero Mo-Fr 07:00-17:00 (Wiener Ortszeit, 17:00 exklusiv, ganze Minuten)
insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
select k.id, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'MOBOTIX_SEED buero Mo-Fr 07-17'
  from public.kameras k
 where k.id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
   and not exists (select 1 from public.kamera_zugriff z
                    where z.kamera_id = k.id and z.rolle = 'buero' and z.user_id is null
                      and z.von = time '07:00' and z.bis = time '17:00' and z.erlaubt
                      and z.wochentage = '{1,2,3,4,5}');

-- 4. Nachher-Zahlen und Kontrolle (erwartet 5 Kameras, 5 Zuordnungen mjpeg, 10 MOBOTIX_SEED-Regeln)
do $$
declare
  n_kam integer; n_be integer; n_z integer; m_kam integer; m_be integer; m_z integer;
begin
  select count(*) into n_kam from public.kameras;
  select count(*) into n_be from public.kamera_backend;
  select count(*) into n_z from public.kamera_zugriff;
  select count(*) into m_kam from public.kameras
   where id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02') and aktiv;
  select count(*) into m_be from public.kamera_backend
   where kamera_id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
     and stream_name = kamera_id and stream_typ = 'mjpeg' and aufzeichnung_quelle is null;
  select count(*) into m_z from public.kamera_zugriff
   where kamera_id in ('hof01', 'hochregal03', 'hochregal02', 'elektrolager01', 'elektrolager02')
     and bemerkung like 'MOBOTIX\_SEED%';
  raise notice 'NACHHER: kameras=%, kamera_backend=%, kamera_zugriff=%  (Mobotix: %/%/%, erwartet 5/5/10)',
    n_kam, n_be, n_z, m_kam, m_be, m_z;
  if m_kam <> 5 or m_be <> 5 then
    raise exception 'Kontrolle: Mobotix-Kameras/Zuordnungen nicht vollstaendig - Transaktion verworfen';
  end if;
end $$;

commit;

-- Sichtkontrolle danach (nur lesen):
-- select k.id, k.name, k.aktiv, b.stream_name, b.stream_typ, b.aufzeichnung_quelle
--   from public.kameras k join public.kamera_backend b on b.kamera_id = k.id order by k.id;
-- select kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung from public.kamera_zugriff order by 1, 2;
