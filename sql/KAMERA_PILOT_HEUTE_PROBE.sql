-- IDEMPOTENT
-- !!! SUPERSEDED / ABGELOEST 20.11.2026 durch sql/KAMERA_GATEWAY_SEED_ENTWURF.sql (QNAP-Gateway, IDs = go2rtc-
-- !!! Streamnamen cam37/cam38/cam39/hochregal01). NICHT mehr einspielen - nie beide Seeds. Probe dazu: KAMERA_GATEWAY_SEED_PROBE.sql

-- =====================================================================================
-- KAMERA_PILOT_HEUTE_PROBE.sql  —  PROBE fuer die 2 Pilot-Kameras (aendert NICHTS dauerhaft)
--
-- Zuerst DIESE Datei im Supabase SQL-Editor ausfuehren, dann - wenn alles "OK" - die Anwendung
-- sql/KAMERA_PILOT_HEUTE_ENTWURF.sql (BEGIN ... COMMIT). Ruecknahme: sql/KAMERA_PILOT_HEUTE_RUECKNAHME.sql
--
-- Was passiert: BEGIN, dieselben Zeilen wie in der Anwendung anlegen, dann je Rolle pruefen, was sie sehen darf.
-- Am Ende bricht ein RAISE EXCEPTION die Transaktion ab - das Ergebnis steht in der FEHLERMELDUNG
-- "PROBE_ERGEBNIS ...". Danach ist garantiert nichts gespeichert (Kontrolle unten).
-- Die Test-Konten werden per Rolle aus public.users gesucht (aktiv, mit Login) - keine IDs in diesem Repo.
-- Zeitpunkte: Montag und Samstag der NAECHSTEN Woche (Wiener Ortszeit), damit das Ergebnis nicht von der Uhrzeit abhaengt.
-- Jede Zeile: OK = wie erwartet, ABWEICHUNG = NICHT einspielen, Ausgabe an Chat-Claude/CC geben.
-- KEIN CASCADE. Nichts an bestehenden Tabellen ausser den 3 Kamera-Tabellen (nur in der Probe-Transaktion).
-- =====================================================================================

begin;

do $probe$
declare
  r      text := '';
  b      boolean;
  n      integer;
  a_adm  text; a_bue text; a_mon text;
  mo     date := (date_trunc('week', (now() at time zone 'Europe/Vienna')::date + 7))::date;
  sa     date;
  function_ok text;
begin
  sa := mo + 5;
  if to_regclass('public.kamera_backend') is null then
    raise exception 'PROBE_ERGEBNIS ABBRUCH: Kamera-Tabellen fehlen';
  end if;
  if exists (select 1 from public.kameras where id in ('kam_g3_01','kam_g3_lager03')) then
    r := r || 'HINWEIS Pilot-IDs schon vorhanden (Anwendung lief bereits?); ';
  end if;

  -- dieselben Zeilen wie die Anwendung (nur in dieser Transaktion)
  insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
    ('kam_g3_01','G3 Dome 01','Standort folgt','Ubiquiti','UVC G3 Dome',true,3),
    ('kam_g3_lager03','Elektrolager 03','Elektrolager','Ubiquiti','UVC G3 Dome',true,3)
  on conflict (id) do nothing;
  insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
    ('kam_g3_01','g3_01','g3_01','webrtc'), ('kam_g3_lager03','g3_lager03','g3_lager03','webrtc')
  on conflict (kamera_id) do nothing;
  insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
  select k, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'PILOT_HEUTE admin immer'
    from unnest(array['kam_g3_01','kam_g3_lager03']) k;
  insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
  select k, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'PILOT_HEUTE buero Mo-Fr 07-17'
    from unnest(array['kam_g3_01','kam_g3_lager03']) k;

  select count(*) into n from public.kamera_backend where kamera_id in ('kam_g3_01','kam_g3_lager03');
  r := r || 'zuordnungen=' || n || case when n = 2 then ' OK; ' else ' ABWEICHUNG; ' end;

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
  if a_adm is null or a_bue is null or a_mon is null then
    raise exception 'PROBE_ERGEBNIS ABBRUCH: es fehlt ein aktives Konto je Rolle (admin/buero/monteur)';
  end if;

  -- ADMIN: immer
  perform set_config('request.jwt.claims', json_build_object('sub',a_adm,'role','authenticated')::text, true);
  set local role authenticated;
  select public.kamera_darf_sehen('kam_g3_lager03', ((sa + time '10:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'admin_samstag=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select count(*) into n from public.kameras where id in ('kam_g3_01','kam_g3_lager03');
  r := r || 'admin_sieht=' || n || case when n = 2 then ' OK; ' else ' ABWEICHUNG; ' end;
  begin
    perform 1 from public.kamera_backend; r := r || 'admin_backend=OFFEN ABWEICHUNG; ';
  exception when insufficient_privilege then r := r || 'admin_backend=gesperrt OK; ';
  end;
  reset role;

  -- BUERO: Mo-Fr 07:00-17:00
  perform set_config('request.jwt.claims', json_build_object('sub',a_bue,'role','authenticated')::text, true);
  set local role authenticated;
  select public.kamera_darf_sehen('kam_g3_lager03', ((mo + time '10:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo1000=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('kam_g3_lager03', ((mo + time '06:59') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo0659=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('kam_g3_lager03', ((mo + time '17:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo1700=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('kam_g3_lager03', ((sa + time '10:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_samstag=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  reset role;

  -- MONTEUR: nie
  perform set_config('request.jwt.claims', json_build_object('sub',a_mon,'role','authenticated')::text, true);
  set local role authenticated;
  select public.kamera_darf_sehen('kam_g3_lager03', ((mo + time '10:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'monteur_darf=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select count(*) into n from public.kameras;
  r := r || 'monteur_sieht=' || n || case when n = 0 then ' OK; ' else ' ABWEICHUNG; ' end;
  reset role;

  raise exception 'PROBE_ERGEBNIS %', r;   -- bricht ab = nichts gespeichert
end $probe$;

rollback;

-- Kontrolle danach (nur lesen) - erwartet 0 Pilot-Zeilen, solange die Anwendung nicht lief:
-- select count(*) from public.kameras where id in ('kam_g3_01','kam_g3_lager03');
