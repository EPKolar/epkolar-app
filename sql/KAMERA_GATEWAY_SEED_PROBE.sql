-- IDEMPOTENT
-- =====================================================================================
-- KAMERA_GATEWAY_SEED_PROBE.sql  —  PROBE fuer die 4 Gateway-Kameras (aendert NICHTS dauerhaft)
--
-- Zuerst DIESE Datei im Supabase SQL-Editor ausfuehren, dann - wenn jede Zeile "OK" - die Anwendung
-- sql/KAMERA_GATEWAY_SEED_ENTWURF.sql (BEGIN ... COMMIT). Ruecknahme: sql/KAMERA_GATEWAY_SEED_RUECKNAHME.sql
--
-- Was passiert: BEGIN, dieselben Zeilen wie in der Anwendung anlegen, dann je Rolle pruefen, was sie sehen darf.
-- Am Ende bricht ein RAISE EXCEPTION die Transaktion ab - das Ergebnis steht in der FEHLERMELDUNG
-- "PROBE_ERGEBNIS ...". Danach ist garantiert nichts gespeichert.
-- Liegt der alte Pilot-Seed (kam_g3_01/kam_g3_lager03) noch in der DB, endet die Probe mit
-- "PROBE_ERGEBNIS ABBRUCH" -> zuerst sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql, dann diese Probe erneut.
-- Die Test-Konten werden per Rolle aus public.users gesucht (aktiv, mit Login) - keine IDs in diesem Repo.
-- Zeitpunkte: Montag und Samstag der NAECHSTEN Woche (Wiener Ortszeit), damit das Ergebnis nicht von der Uhrzeit abhaengt.
-- Jede Zeile: OK = wie erwartet, ABWEICHUNG = NICHT einspielen, Ausgabe an Chat-Claude/CC geben.
-- KEIN CASCADE. Nichts an bestehenden Tabellen ausser den 3 Kamera-Tabellen (nur in der Probe-Transaktion).
-- MOBOTIX (zweiter Block, Standard AUS): Schalter unten wie im Seed. 'true' prueft zusaetzlich mob32..mob36
-- (stream_typ webrtc ueber ffmpeg-H.264 auf der QNAP, gleiche Regeln) - vor dem Einschalten im Seed die Probe einmal mit 'true' laufen lassen.
-- =====================================================================================

begin;

-- MOBOTIX-SCHALTER: 'false' = nur die 4 G3 (Standard), 'true' = zusaetzlich 5 Mobotix (Probe, wird zurueckgerollt)
set local epk.mobotix_aktiv = 'false';

do $probe$
declare
  r      text := '';
  b      boolean;
  n      integer;
  a_adm  text; a_bue text; a_mon text; a_pl text;
  mob    boolean := coalesce(current_setting('epk.mobotix_aktiv', true), 'false') = 'true';
  ids    text[];
  mo     date := (date_trunc('week', (now() at time zone 'Europe/Vienna')::date + 7))::date;
  sa     date;
begin
  sa := mo + 5;
  if to_regclass('public.kamera_backend') is null then
    raise exception 'PROBE_ERGEBNIS ABBRUCH: Kamera-Tabellen fehlen';
  end if;
  if exists (select 1 from public.kameras where id in ('kam_g3_01','kam_g3_lager03'))
     or exists (select 1 from public.kamera_backend where stream_name in ('g3_01','g3_lager03')) then
    raise exception 'PROBE_ERGEBNIS ABBRUCH: Pilot-Seed noch eingespielt - zuerst sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql';
  end if;
  if exists (select 1 from public.kameras where id in ('cam37','cam38','cam39','hochregal01')) then
    r := r || 'HINWEIS Gateway-IDs schon vorhanden (Anwendung lief bereits?); ';
  end if;

  -- dieselben Zeilen wie die Anwendung (nur in dieser Transaktion)
  insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
    ('cam37','Kamera .37 (Name folgt)','Standort folgt','Ubiquiti','UVC G3 Dome',true,3),
    ('cam38','Kamera .38 (Name folgt)','Standort folgt','Ubiquiti','UVC G3 Dome',true,3),
    ('cam39','Kamera .39 (Name folgt)','Standort folgt','Ubiquiti','UVC G3 Dome',true,3),
    ('hochregal01','Kamera .61 (Name folgt)','Standort folgt','Ubiquiti','UVC G3 Dome',true,3)
  on conflict (id) do nothing;
  insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
    ('cam37','cam37',null,'webrtc'), ('cam38','cam38',null,'webrtc'),
    ('cam39','cam39',null,'webrtc'), ('hochregal01','hochregal01',null,'webrtc')
  on conflict (kamera_id) do nothing;
  insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
  select k, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'GATEWAY_SEED admin immer'
    from unnest(array['cam37','cam38','cam39','hochregal01']) k;
  insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
  select k, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'GATEWAY_SEED buero Mo-Fr 07-17'
    from unnest(array['cam37','cam38','cam39','hochregal01']) k;

  -- MOBOTIX-BLOCK (nur bei Schalter 'true'); SurvStation: .32 Hof, .33 Hochregal03, .34 Hochregal02,
  -- .35 Elektrolager01, .36 Elektrolager02 (nur Kommentar)
  ids := array['cam37','cam38','cam39','hochregal01'];
  if mob then
    insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
      ('mob32','Mobotix .32 (Name folgt)','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
      ('mob33','Mobotix .33 (Name folgt)','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
      ('mob34','Mobotix .34 (Name folgt)','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
      ('mob35','Mobotix .35 (Name folgt)','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
      ('mob36','Mobotix .36 (Name folgt)','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3)
    on conflict (id) do nothing;
    insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
      ('mob32','mob32',null,'webrtc'), ('mob33','mob33',null,'webrtc'), ('mob34','mob34',null,'webrtc'),
      ('mob35','mob35',null,'webrtc'), ('mob36','mob36',null,'webrtc')
    on conflict (kamera_id) do nothing;
    insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
    select k, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'GATEWAY_SEED admin immer'
      from unnest(array['mob32','mob33','mob34','mob35','mob36']) k;
    insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
    select k, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'GATEWAY_SEED buero Mo-Fr 07-17'
      from unnest(array['mob32','mob33','mob34','mob35','mob36']) k;
    select count(*) into n from public.kamera_backend
     where kamera_id in ('mob32','mob33','mob34','mob35','mob36') and stream_name = kamera_id and stream_typ = 'webrtc';
    r := r || 'mobotix_webrtc_id_gleich_stream=' || n || case when n = 5 then ' OK; ' else ' ABWEICHUNG; ' end;
    ids := ids || array['mob32','mob33','mob34','mob35','mob36'];
  else
    r := r || 'mobotix=aus (Schalter false); ';
  end if;

  select count(*) into n from public.kamera_backend
   where kamera_id in ('cam37','cam38','cam39','hochregal01') and stream_name = kamera_id
     and stream_typ = 'webrtc' and aufzeichnung_quelle is null;
  r := r || 'zuordnungen_id_gleich_stream=' || n || case when n = 4 then ' OK; ' else ' ABWEICHUNG; ' end;
  select count(*) into n from public.kamera_zugriff
   where kamera_id = any(ids) and bemerkung like 'GATEWAY\_SEED%';
  r := r || 'regeln=' || n || case when n = 2 * cardinality(ids) then ' OK; ' else ' ABWEICHUNG; ' end;

  -- Test-Konten je Rolle
  select auth_user_id::text into a_adm from public.users
   where lower(role::text)='admin' and auth_user_id is not null
     and coalesce(active::text,'1') in ('1','true','t') and coalesce(locked::text,'0') in ('0','false','f') limit 1;
  select auth_user_id::text into a_bue from public.users
   where lower(role::text)='buero' and auth_user_id is not null
     and coalesce(active::text,'1') in ('1','true','t') and coalesce(locked::text,'0') in ('0','false','f') limit 1;
  select auth_user_id::text into a_mon from public.users
   where lower(role::text)='monteur' and auth_user_id is not null
     and coalesce(active::text,'1') in ('1','true','t') and coalesce(locked::text,'0') in ('0','false','f') limit 1;
  select auth_user_id::text into a_pl from public.users
   where lower(role::text)='projektleiter' and auth_user_id is not null
     and coalesce(active::text,'1') in ('1','true','t') and coalesce(locked::text,'0') in ('0','false','f') limit 1;
  if a_adm is null or a_bue is null or a_mon is null then
    raise exception 'PROBE_ERGEBNIS ABBRUCH: es fehlt ein aktives Konto je Rolle (admin/buero/monteur)';
  end if;

  -- ADMIN: immer, alle 4 Kameras, Zuordnung gesperrt
  perform set_config('request.jwt.claims', json_build_object('sub',a_adm,'role','authenticated')::text, true);
  set local role authenticated;
  select bool_and(public.kamera_darf_sehen(k, ((sa + time '03:00') at time zone 'Europe/Vienna'))) into b
    from unnest(ids) k;
  r := r || 'admin_samstag_0300_alle=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select count(*) into n from public.kameras where id = any(ids);
  r := r || 'admin_sieht=' || n || case when n = cardinality(ids) then ' OK; ' else ' ABWEICHUNG; ' end;
  begin
    perform 1 from public.kamera_backend; r := r || 'admin_backend=OFFEN ABWEICHUNG; ';
  exception when insufficient_privilege then r := r || 'admin_backend=gesperrt OK; ';
  end;
  reset role;

  -- BUERO: Mo-Fr 07:00-17:00 (Grenzen auf ganzen Minuten)
  perform set_config('request.jwt.claims', json_build_object('sub',a_bue,'role','authenticated')::text, true);
  set local role authenticated;
  select bool_and(public.kamera_darf_sehen(k, ((mo + time '10:00') at time zone 'Europe/Vienna'))) into b
    from unnest(ids) k;
  r := r || 'buero_mo1000_alle=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select bool_or(public.kamera_darf_sehen(k, ((sa + time '10:00') at time zone 'Europe/Vienna'))) into b
    from unnest(ids) k;
  r := r || 'buero_samstag_alle=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('hochregal01', ((mo + time '07:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo0700=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('hochregal01', ((mo + time '06:59') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo0659=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('hochregal01', ((mo + time '16:59') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo1659=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('hochregal01', ((mo + time '17:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo1700=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('cam37', ((sa + time '10:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_samstag=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  reset role;

  -- MONTEUR: nie
  perform set_config('request.jwt.claims', json_build_object('sub',a_mon,'role','authenticated')::text, true);
  set local role authenticated;
  select bool_or(public.kamera_darf_sehen(k, ((mo + time '10:00') at time zone 'Europe/Vienna'))) into b
    from unnest(ids) k;
  r := r || 'monteur_darf=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select count(*) into n from public.kameras;
  r := r || 'monteur_sieht=' || n || case when n = 0 then ' OK; ' else ' ABWEICHUNG; ' end;
  reset role;

  -- PROJEKTLEITER: keine Regel im Seed -> nein (Konto optional)
  if a_pl is null then
    r := r || 'projektleiter=kein_konto (uebersprungen); ';
  else
    perform set_config('request.jwt.claims', json_build_object('sub',a_pl,'role','authenticated')::text, true);
    set local role authenticated;
    select bool_or(public.kamera_darf_sehen(k, ((mo + time '10:00') at time zone 'Europe/Vienna'))) into b
      from unnest(ids) k;
    r := r || 'projektleiter_darf=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
    reset role;
  end if;

  raise exception 'PROBE_ERGEBNIS %', r;   -- bricht ab = nichts gespeichert
end $probe$;

rollback;

-- Kontrolle danach (nur lesen) - erwartet 0, solange die Anwendung nicht lief:
-- select count(*) from public.kameras where id in ('cam37','cam38','cam39','hochregal01');
