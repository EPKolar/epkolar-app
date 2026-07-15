-- ═══════════════════════════════════════════════════════════════════════════
-- PLZ_GEO_v1.sql  ·  Dispo-Assistent Etappe 1  ·  Human-Run-Gate (Sebastian/Chat-Claude)
-- ═══════════════════════════════════════════════════════════════════════════
-- Geo-Fundament fuer die Vorschlagsplanung: PLZ -> Koordinaten (Zentroid).
-- Idempotent (CREATE TABLE IF NOT EXISTS + RLS additiv). KEINE Writes durch CC.
-- Firma-Anker (Start/Ende jeder Route): Marktplatz 17, 3470 Kirchberg am Wagram.
--
-- DATEN-BEFUELLUNG (separat, durch Chat-Claude/Sebastian): die relevanten PLZ
-- kommen aus arbeitsscheine.arbeitsort (Regex \m\d{4}\M) + projects + Firma; die
-- Zentroid-Koordinaten aus einem OFFENEN oesterr. PLZ-Verzeichnis (Quelle+Datum
-- im INSERT-Kommentar belegen). Client cached die Tabelle einmalig (klein).
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.plz_geo (
  plz  text PRIMARY KEY,
  ort  text,
  lat  double precision,
  lon  double precision
);

ALTER TABLE public.plz_geo ENABLE ROW LEVEL SECURITY;

-- SELECT fuer alle eingeloggten User (reine Geo-Referenz, kein PII).
DROP POLICY IF EXISTS plz_geo_select_authed ON public.plz_geo;
CREATE POLICY plz_geo_select_authed ON public.plz_geo
  FOR SELECT TO authenticated USING (true);

-- Schreiben nur Staff (Nachtrag-Button "Distanzen/Geo aktualisieren").
DROP POLICY IF EXISTS plz_geo_write_staff ON public.plz_geo;
CREATE POLICY plz_geo_write_staff ON public.plz_geo
  FOR ALL TO authenticated USING (public.is_staff()) WITH CHECK (public.is_staff());

-- ── DATEN (Beispiel-Muster; echte Zeilen aus dem PLZ-Verzeichnis nachziehen) ──
-- Firma-Anker zuerst (Koordinaten Kirchberg am Wagram, Marktplatz — verifizieren):
-- INSERT INTO public.plz_geo(plz,ort,lat,lon) VALUES
--   ('3470','Kirchberg am Wagram', 48.4269, 15.7386)   -- Quelle/Datum belegen
-- ON CONFLICT (plz) DO UPDATE SET ort=EXCLUDED.ort, lat=EXCLUDED.lat, lon=EXCLUDED.lon;
--
-- Selbst-Nachweis nach dem Befuellen (read-only): SELECT count(*) FROM public.plz_geo;
