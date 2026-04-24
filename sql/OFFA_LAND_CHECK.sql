-- ============================================================
-- OFFA Land-Feld Schema-Check · 2026-04-24
-- Read-only. Sebastian fuehrt manuell aus und liefert Ergebnis an CC.
-- Zweck: Regression-Kategorie klaeren (REGRESSION / DISCONNECTED / GREENFIELD).
-- ============================================================

-- 1) Arbeitsscheine: gibt es Land-/Country-/Einsatz-Spalten?
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema='public'
  AND table_name='arbeitsscheine'
  AND (
      column_name ILIKE '%land%'
   OR column_name ILIKE '%country%'
   OR column_name ILIKE '%einsatz%'
   OR column_name ILIKE '%arbeitsort%'
   OR column_name ILIKE '%bauadr%'
  )
ORDER BY ordinal_position;

-- 2) Komplettes arbeitsscheine-Schema (damit wir sehen welche Adress-Felder existieren)
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_schema='public' AND table_name='arbeitsscheine'
ORDER BY ordinal_position;

-- 3) Existiert evtl. eine separate Adress-Tabelle fuer Rechnungs-/Einsatzadressen?
SELECT table_name
FROM information_schema.tables
WHERE table_schema='public'
  AND (table_name ILIKE '%adr%' OR table_name ILIKE '%address%' OR table_name ILIKE '%kunden%');

-- 4) Prüfung: gibt es bereits Rows mit nicht-leerem 'A' Länderkürzel irgendwo?
--    (Nur laufen lassen wenn Spalten-Treffer in Query 1)
-- BEISPIEL (erst ausfuehren wenn wir wissen wie das Feld heisst):
-- SELECT count(*) AS with_land, count(*) FILTER (WHERE <land_column>='A') AS with_A
-- FROM public.arbeitsscheine;

-- Output liefern an CC:
--   - Query 1: Spalten-Liste (kann leer sein → GREENFIELD-Indikator)
--   - Query 2: vollstaendiges Schema (zum Quer-Check gegen _mapBody-RENAME-Map)
--   - Query 3: Adress-Tabellen-Liste
