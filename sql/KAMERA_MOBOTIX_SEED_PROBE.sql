-- IDEMPOTENT
-- =====================================================================================
-- KAMERA_MOBOTIX_SEED_PROBE.sql  —  PROBE fuer die 5 Mobotix-Kameras (aendert NICHTS dauerhaft)
--
-- Zuerst DIESE Datei im Supabase SQL-Editor ausfuehren, dann - wenn jede Zeile "OK" - die Anwendung
-- sql/KAMERA_MOBOTIX_SEED_ENTWURF.sql (BEGIN ... COMMIT). Ruecknahme: sql/KAMERA_MOBOTIX_SEED_RUECKNAHME.sql
--
-- Was passiert: BEGIN, dieselben Zeilen wie in der Anwendung anlegen, dann je Rolle pruefen, was sie sehen darf.
-- Am Ende bricht ein RAISE EXCEPTION die Transaktion ab - das Ergebnis steht in der FEHLERMELDUNG
-- "PROBE_ERGEBNIS ...". Danach ist garantiert nichts gespeichert.
-- Liegt der alte Mobotix-Block (mob32..mob36) in der DB, endet die Probe mit "PROBE_ERGEBNIS ABBRUCH".
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
  a_adm  text; a_bue text; a_mon text; a_pl text;
  ids    text[] := array['hof01','hochregal03','hochregal02','elektrolager01','elektrolager02'];
  mo     date := (date_trunc('week', (now() at time zone 'Europe/Vienna')::date + 7))::date;
  sa     date;
begin
  sa := mo + 5;
  if to_regclass('public.kamera_backend') is null then
    raise exception 'PROBE_ERGEBNIS ABBRUCH: Kamera-Tabellen fehlen';
  end if;
  if exists (select 1 from public.kameras where id in ('mob32','mob33','mob34','mob35','mob36'))
     or exists (select 1 from public.kamera_backend where stream_name in ('mob32','mob33','mob34','mob35','mob36')) then
    raise exception 'PROBE_ERGEBNIS ABBRUCH: alter Mobotix-Block (mob32..mob36) eingespielt - erst klaeren';
  end if;
  if exists (select 1 from public.kameras where id = any(ids)) then
    r := r || 'HINWEIS Mobotix-IDs schon vorhanden (Anwendung lief bereits?); ';
  end if;
  select count(*) into n from public.kamera_backend
   where kamera_id in ('elektrolager03','verkauf02','cam39','hochregal01') and stream_typ = 'webrtc';
  r := r || 'g3_vorhanden=' || n || case when n = 4 then ' OK; ' else ' ABWEICHUNG; ' end;

  -- dieselben Zeilen wie die Anwendung (nur in dieser Transaktion)
  insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
    ('hof01','Hof','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
    ('hochregal03','Hochregal 03','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
    ('hochregal02','Hochregal 02','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
    ('elektrolager01','Elektrolager 01','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3),
    ('elektrolager02','Elektrolager 02','Standort folgt','Mobotix','Mobotix (Modell folgt)',true,3)
  on conflict (id) do nothing;
  insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
    ('hof01','hof01',null,'mjpeg'), ('hochregal03','hochregal03',null,'mjpeg'),
    ('hochregal02','hochregal02',null,'mjpeg'), ('elektrolager01','elektrolager01',null,'mjpeg'),
    ('elektrolager02','elektrolager02',null,'mjpeg')
  on conflict (kamera_id) do nothing;
  insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
  select k, 'admin', '{1,2,3,4,5,6,7}', null, null, true, 'MOBOTIX_SEED admin immer'
    from unnest(ids) k;
  insert into public.kamera_zugriff (kamera_id, rolle, wochentage, von, bis, erlaubt, bemerkung)
  select k, 'buero', '{1,2,3,4,5}', time '07:00', time '17:00', true, 'MOBOTIX_SEED buero Mo-Fr 07-17'
    from unnest(ids) k;

  select count(*) into n from public.kamera_backend
   where kamera_id = any(ids) and stream_name = kamera_id and stream_typ = 'mjpeg' and aufzeichnung_quelle is null;
  r := r || 'mobotix_mjpeg_id_gleich_stream=' || n || case when n = 5 then ' OK; ' else ' ABWEICHUNG; ' end;
  select count(*) into n from public.kamera_zugriff
   where kamera_id = any(ids) and bemerkung like 'MOBOTIX\_SEED%';
  r := r || 'regeln=' || n || case when n = 10 then ' OK; ' else ' ABWEICHUNG; ' end;

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

  -- ADMIN: immer, alle 5 Kameras, Zuordnung gesperrt
  perform set_config('request.jwt.claims', json_build_object('sub',a_adm,'role','authenticated')::text, true);
  set local role authenticated;
  select bool_and(public.kamera_darf_sehen(k, ((sa + time '03:00') at time zone 'Europe/Vienna'))) into b
    from unnest(ids) k;
  r := r || 'admin_samstag_0300_alle=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select count(*) into n from public.kameras where id = any(ids);
  r := r || 'admin_sieht=' || n || case when n = 5 then ' OK; ' else ' ABWEICHUNG; ' end;
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
  select public.kamera_darf_sehen('hof01', ((mo + time '07:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo0700=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('hof01', ((mo + time '06:59') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo0659=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('hof01', ((mo + time '16:59') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo1659=' || b || case when b then ' OK; ' else ' ABWEICHUNG; ' end;
  select public.kamera_darf_sehen('hof01', ((mo + time '17:00') at time zone 'Europe/Vienna')) into b;
  r := r || 'buero_mo1700=' || b || case when not b then ' OK; ' else ' ABWEICHUNG; ' end;
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
-- select count(*) from public.kameras where id in ('hof01','hochregal03','hochregal02','elektrolager01','elektrolager02');
