-- IDEMPOTENT
-- =====================================================================================
-- KAMERAS PILOT-SEED - ENTWURF (EPKolar Kameras Phase 2, 19.11.2026)
-- NICHT eingespielt. Erst nach sql/KAMERAS_v1_ENTWURF.sql (Stand Phase 2, mit kamera_backend.stream_typ).
--
-- Legt die 7 bei der Netzinventur am 19.11. gefundenen Kameras an (4x Ubiquiti UVC G3 Dome, 3x Mobotix).
-- Namen und Standorte sind PLATZHALTER - der Inhaber traegt die echten Bezeichnungen ein (App: Verwaltung).
--
-- BEWUSST NICHT HIER: Adressen, Ports, Benutzer, Kennwoerter der Kameras. kamera_backend kennt nur den
-- go2rtc-Streamnamen (z. B. g3_37); welcher Streamname zu welcher Kamera-Adresse gehoert, steht AUSSCHLIESSLICH
-- in der go2rtc-Konfiguration auf dem Video-Host (Vorlage C:/repos/epk-kamera-pilot/go2rtc.yaml, nicht im Repo).
-- Der Streamname nennt nur Bauart und Endung der Kamera-Adresse als Merkhilfe.
--
-- Pilot: nur kam_01 (G3, webrtc) und kam_05 (Mobotix, mjpeg) sind aktiv; die anderen bleiben aus, bis der
-- Pilot gemessen ist (PILOT.md). Aufbewahrung ueberall 3 Tage (72 h, DSG-Regelfall).
-- Mobotix: stream_typ mjpeg (Durchreichen) - Alternative snapshot (weniger Bandbreite) oder webrtc
-- (go2rtc transkodiert per ffmpeg nach H.264, kostet CPU). Entscheid beim Pilot.
-- Mobotix ohne Aufzeichnungsquelle: Frigate zeichnet MJPEG nur transkodiert auf - erst nach dem Pilot.
--
-- Zugriffsregeln legt der Admin in der App an (Verwaltung -> Zugriff je Kamera). Ohne Regel sieht NIEMAND ein
-- Bild, auch der Admin nicht (Standard-Nein). Beispiel unten auskommentiert.
-- =====================================================================================

begin;

-- Voraussetzung pruefen: Datenmodell Phase 2 vorhanden
do $$
begin
  if not exists (select 1 from information_schema.columns
                 where table_schema = 'public' and table_name = 'kamera_backend' and column_name = 'stream_typ') then
    raise exception 'kamera_backend.stream_typ fehlt - zuerst sql/KAMERAS_v1_ENTWURF.sql (Stand Phase 2) einspielen';
  end if;
end $$;

-- 1. Stammdaten (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage)
insert into public.kameras (id, name, standort, hersteller, modell, aktiv, aufbewahrung_tage) values
  ('kam_01', 'Kamera 01 (Name folgt)', 'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', true, 3),
  ('kam_02', 'Kamera 02 (Name folgt)', 'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', false, 3),
  ('kam_03', 'Kamera 03 (Name folgt)', 'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', false, 3),
  ('kam_04', 'Kamera 04 (Name folgt)', 'Standort folgt', 'Ubiquiti', 'UVC G3 Dome', false, 3),
  ('kam_05', 'Kamera 05 (Name folgt)', 'Standort folgt', 'Mobotix', 'Modell folgt', true, 3),
  ('kam_06', 'Kamera 06 (Name folgt)', 'Standort folgt', 'Mobotix', 'Modell folgt', false, 3),
  ('kam_07', 'Kamera 07 (Name folgt)', 'Standort folgt', 'Mobotix', 'Modell folgt', false, 3)
on conflict (id) do nothing;

-- 2. Backend-Zuordnung (nur service_role liest): kamera_id, stream_name, aufzeichnung_quelle, stream_typ
--    aufzeichnung_quelle = Frigate-Kameraname (gleich dem Streamnamen) oder null
insert into public.kamera_backend (kamera_id, stream_name, aufzeichnung_quelle, stream_typ) values
  ('kam_01', 'g3_37', 'g3_37', 'webrtc'),
  ('kam_02', 'g3_38', 'g3_38', 'webrtc'),
  ('kam_03', 'g3_39', 'g3_39', 'webrtc'),
  ('kam_04', 'g3_61', 'g3_61', 'webrtc'),
  ('kam_05', 'mx_32', null, 'mjpeg'),
  ('kam_06', 'mx_33', null, 'mjpeg'),
  ('kam_07', 'mx_36', null, 'mjpeg')
on conflict (kamera_id) do nothing;

-- 3. Beispiel Zugriffsregel fuer den Pilot (auskommentiert; Admin, immer):
-- insert into public.kamera_zugriff (kamera_id, rolle, wochentage, erlaubt, bemerkung)
--   values ('kam_01', 'admin', '{1,2,3,4,5,6,7}', true, 'Pilot');

-- Kontrolle: genau 7 Kameras, 7 Zuordnungen, 2 aktiv
-- select count(*) from public.kameras where id like 'kam_0%';          -- erwartet 7
-- select count(*) from public.kamera_backend where kamera_id like 'kam_0%'; -- erwartet 7
-- select id from public.kameras where id like 'kam_0%' and aktiv;      -- erwartet kam_01, kam_05

commit;

-- Ruecknahme (nur die Pilot-Zeilen; kamera_zugriff/kamera_abruf_log vorher pruefen, FK ist RESTRICT):
-- delete from public.kamera_backend where kamera_id in ('kam_01','kam_02','kam_03','kam_04','kam_05','kam_06','kam_07');
-- delete from public.kameras where id in ('kam_01','kam_02','kam_03','kam_04','kam_05','kam_06','kam_07');
