-- ============================================================
-- OFFA / Juprowa Land-Feldname Probe · 2026-04-24
-- Phase 2 Pfad A · Vorbedingung
--
-- ZWECK: Den EXAKTEN Feldnamen für das Länderkürzel aus einer
-- echten Juprowa-Pull-Response extrahieren. Phase-1-Scan im
-- index.html hat 0 Treffer auf AK_*_LAND / AK_*_LKZ /
-- AK_*_COUNTRY geliefert — der Pull liest das Feld gar nicht.
--
-- Sebastian fuehrt manuell aus und liefert Output an CC.
-- CC wartet auf Output bevor Phase 2 Block B startet.
-- ============================================================

-- Query 1 · juprowa_raw-Keys die auf Land hindeuten
-- Erwartung: 1-4 Keys wie AK_BAUADR_LAND, RE_ADR_LAND, etc.
SELECT DISTINCT key
FROM public.arbeitsscheine, jsonb_object_keys(juprowa_raw) AS key
WHERE juprowa_raw IS NOT NULL
  AND (key ILIKE '%LAND%' OR key ILIKE '%LKZ%' OR key ILIKE '%COUNTRY%')
ORDER BY key;

-- Query 2 · Sample-Dump eines aktuellen juprowa_raw (komplett)
-- Bitte die Response fuer einen Schein mit gefuellter Adresse liefern.
-- Zeigt ALLE Keys + Werte, daraus ist Feldname + ob Einsatz/Rechnung
-- gleiche Struktur hat ersichtlich.
SELECT juprowa_id, nummer, juprowa_raw
FROM public.arbeitsscheine
WHERE juprowa_raw IS NOT NULL
  AND juprowa_raw ? 'AK_BAUADR_STR'       -- Einsatz-Adresse muss da sein
  AND juprowa_raw->>'AK_BAUADR_STR' <> ''
ORDER BY updated_at DESC NULLS LAST
LIMIT 1;

-- Query 3 · Fallback: alle keys die je in juprowa_raw vorkamen
-- Komplette Liste zur manuellen Sichtung bei unklarem Query-1-Ergebnis.
SELECT DISTINCT key
FROM public.arbeitsscheine, jsonb_object_keys(juprowa_raw) AS key
WHERE juprowa_raw IS NOT NULL
ORDER BY key;

-- Query 4 · Rechnungsadresse vs. Einsatzadresse: separat oder gleich?
-- Wenn unterschiedlich → Phase 2a darf RE_ADR_* NICHT aus kundStr/kundPlz/kundOrt
-- ableiten (Phase-2b-Follow-up noetig).
SELECT
  juprowa_id,
  juprowa_raw->>'AK_BAUADR_STR' AS einsatz_str,
  juprowa_raw->>'AK_BAUADR_PLZ' AS einsatz_plz,
  juprowa_raw->>'AK_BAUADR_ORT' AS einsatz_ort,
  juprowa_raw->>'RE_ADR_STR'    AS rechn_str,
  juprowa_raw->>'RE_ADR_PLZ'    AS rechn_plz,
  juprowa_raw->>'RE_ADR_ORT'    AS rechn_ort,
  CASE
    WHEN (juprowa_raw->>'AK_BAUADR_STR') = (juprowa_raw->>'RE_ADR_STR')
     AND (juprowa_raw->>'AK_BAUADR_PLZ') = (juprowa_raw->>'RE_ADR_PLZ')
     AND (juprowa_raw->>'AK_BAUADR_ORT') = (juprowa_raw->>'RE_ADR_ORT')
    THEN 'IDENTICAL'
    ELSE 'DIFFERENT'
  END AS adr_equality
FROM public.arbeitsscheine
WHERE juprowa_raw IS NOT NULL
  AND juprowa_raw ? 'AK_BAUADR_STR'
  AND juprowa_raw ? 'RE_ADR_STR'
LIMIT 20;

-- ============================================================
-- AN CC ZURUECKMELDEN:
--   Query 1 Output (exakte Feldnamen, 1:1)
--   Query 2 Output (juprowa_raw JSON eines Real-Scheins, vollstaendig)
--   Query 4 Output (IDENTICAL vs DIFFERENT Haeufigkeit)
--
-- CC entscheidet dann:
--   * Feldname fuer AK_BAUADR_LAND/...
--   * Ob RE_ADR_* = AK_BAUADR_* uebernommen werden kann
--     oder separate Behandlung noetig (→ Phase 2b)
-- ============================================================
