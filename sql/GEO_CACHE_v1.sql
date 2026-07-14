-- ═══════════════════════════════════════════════════════════════════
-- GEO_CACHE_v1.sql — Reverse-Geocoding-Cache (App v3.9.684, Phase F3)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — HUMAN-RUN-GATE.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Entscheid Sebastian 13.07.2026: Reverse-Geocoding via Nominatim (OSM),
-- gratis. Nominatim hat eine Nutzungspolitik, deren Verletzung eine
-- IP-Sperre nach sich zieht: max. 1 Request/Sekunde, kein Bulk-Geocoding,
-- kein Durchgeocoden von Historien.
--
-- DER CACHE IST DESHALB PFLICHT, NICHT KUER. Ohne ihn wuerde jede Anzeige
-- des Fahrtenbuchs dieselben Koordinaten erneut anfragen.
--
-- ── Warum 3 Dezimalstellen als Key ─────────────────────────────────
-- 3 Nachkommastellen ~ 110 m Gitterweite. Das Betriebsgebiet ist
-- Kirchberg + Umland: Baustellen, Lager, Werkstatt liegen weit genug
-- auseinander, dass 110 m sie nicht verschmelzen — und ein Fahrzeug, das
-- 50 m weiter parkt, soll NICHT einen zweiten Lookup ausloesen.
-- Feiner (4 Stellen ~ 11 m) waere fachlich sinnlos: die Anzeige ist
-- "Ort, Strasse Hausnr", und die aendert sich auf 11 m nicht — es gaebe
-- nur mehr Cache-Misses und damit mehr Nominatim-Last, also genau das,
-- was die Policy verbietet. Groeber (2 Stellen ~ 1,1 km) wuerde
-- benachbarte Baustellen zusammenwerfen.
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) Cache-Tabelle ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.geo_cache (
  geo_key    text PRIMARY KEY,        -- gerundete Koordinaten, z.B. "48.457,16.007"
  ort        text NOT NULL,           -- Anzeigeform "Ort, Strasse Hausnr"
  lat        double precision,        -- die gerundeten Koordinaten (Nachvollziehbarkeit)
  lon        double precision,
  created_at timestamptz DEFAULT now()
);

-- ── 2) RLS ──────────────────────────────────────────────────────────
-- Lesen: alle angemeldeten Nutzer. Der Cache enthaelt nur Adressen aus
-- oeffentlichen OSM-Daten — kein Personenbezug, keine Bewegungsprofile.
-- ABER: lager_display bleibt hart geblockt. Der Kiosk haengt oeffentlich
-- in der Halle; er hat mit Geodaten nichts zu tun (§96-Linie, konsistent
-- zu fz_positions/fz_fahrten).
ALTER TABLE public.geo_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS geo_cache_select_auth ON public.geo_cache;
CREATE POLICY geo_cache_select_auth ON public.geo_cache
  FOR SELECT TO authenticated USING (true);

-- Schreiben: nur Staff. Gefuellt wird der Cache aus dem Fahrtenbuch, und
-- das sieht ohnehin nur admin/projektleiter/buero.
DROP POLICY IF EXISTS geo_cache_insert_staff ON public.geo_cache;
CREATE POLICY geo_cache_insert_staff ON public.geo_cache
  FOR INSERT TO authenticated WITH CHECK (is_staff());

DROP POLICY IF EXISTS geo_cache_no_lager_display ON public.geo_cache;
CREATE POLICY geo_cache_no_lager_display ON public.geo_cache AS RESTRICTIVE
  FOR ALL USING ( ((auth.jwt() -> 'app_metadata') ->> 'role') IS DISTINCT FROM 'lager_display' );

-- ── 3) Ortsnamen an der Fahrt ───────────────────────────────────────
-- Nach dem ERSTEN Lookup wird der Ortsname an der Fahrt nachgetragen.
-- Folge-Anzeigen brauchen dann weder Nominatim noch den Cache — das ist
-- die eigentliche Bremse gegen Bulk-Traffic.
--
-- IF NOT EXISTS, weil FZ_FAHRTEN_v1.sql evtl. schon gelaufen ist. Die
-- dortige Fassung hatte start_adresse/end_adresse — falls die Tabelle so
-- existiert, bleiben jene Spalten schlicht ungenutzt (NULL). Ab jetzt
-- gilt start_ort/ziel_ort als der eine Name fuer die Sache.
ALTER TABLE public.fz_fahrten ADD COLUMN IF NOT EXISTS start_ort text;
ALTER TABLE public.fz_fahrten ADD COLUMN IF NOT EXISTS ziel_ort  text;

-- ── Verifikation nach dem Run ──────────────────────────────────────
--   select count(*) from public.geo_cache;                      -- 0
--   select column_name from information_schema.columns
--     where table_name='fz_fahrten' and column_name in ('start_ort','ziel_ort');
-- Die App erkennt eine fehlende geo_cache-Tabelle selbst (42P01/404) und
-- arbeitet dann ohne DB-Cache weiter (Session-Cache + Koordinaten-Fallback)
-- statt zu crashen.
