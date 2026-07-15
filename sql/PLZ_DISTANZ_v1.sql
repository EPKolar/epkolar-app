-- ═══════════════════════════════════════════════════════════════════════════
-- PLZ_DISTANZ_v1.sql  ·  Dispo-Assistent Etappe 1  ·  Human-Run-Gate
-- ═══════════════════════════════════════════════════════════════════════════
-- Vorberechnete ECHTE Strassen-Distanzmatrix (km + Fahrminuten) je PLZ-Paar.
-- Kein Live-Routing zur Laufzeit -> keine Folgekosten. Einmal echt routen (OSRM
-- /table, oeffentliche Instanz, gebatcht/throttled, EINMALIG; Fallback ORS-Key),
-- Ergebnis hier ablegen, Laufzeit-Lookup kostenlos/offline/exakt.
-- Paare NORMALISIERT (plz_a < plz_b, symmetrisch) -> die Haelfte reicht.
-- Idempotent. KEINE Writes durch CC (OSRM-Lauf + INSERTs: Chat-Claude/Sebastian).
--
-- Laufzeit (Client): Lookup zuerst; fehlendes Paar -> Haversine x1,3-Fallback
-- SICHTBAR "~"; gleiche PLZ -> Konstante 5 min / 2 km. Admin-Button
-- "Distanzen aktualisieren" (isWAdm, online) holt fehlende Paare per REST-INSERT
-- nach (die Tabelle existiert dann schon -> App-Datenpfad, KEIN DDL).
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.plz_distanz (
  plz_a  text NOT NULL,
  plz_b  text NOT NULL,
  km     numeric,
  min    numeric,
  quelle text,
  stand  date,
  PRIMARY KEY (plz_a, plz_b),
  CHECK (plz_a < plz_b)          -- Normalform: nur eine Richtung speichern
);

ALTER TABLE public.plz_distanz ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS plz_distanz_select_authed ON public.plz_distanz;
CREATE POLICY plz_distanz_select_authed ON public.plz_distanz
  FOR SELECT TO authenticated USING (true);

-- INSERT/UPDATE (Nachziehen fehlender Paare) nur Staff.
DROP POLICY IF EXISTS plz_distanz_write_staff ON public.plz_distanz;
CREATE POLICY plz_distanz_write_staff ON public.plz_distanz
  FOR ALL TO authenticated USING (public.is_staff()) WITH CHECK (public.is_staff());

-- ── OSRM-Einmallauf (extern, durch Chat-Claude/Sebastian): pro Paar (a<b)
--    km + min holen, hier als INSERT ... ON CONFLICT (plz_a,plz_b) DO UPDATE ablegen,
--    quelle='osrm-demo'/'ors', stand=heute. Erwartung ~8 distinct PLZ aktuell -> ~28 Paare.
-- ── VALIDIERUNG (in den Report): 5 Kontrollstrecken (Kirchberg->Fels/Rohrendorf/
--    Tulln/Hollabrunn/Wien-Rand) Matrix-km vs. plausible Strassen-km, Ziel <10%.
