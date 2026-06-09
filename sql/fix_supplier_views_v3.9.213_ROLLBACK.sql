-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ============================================================================
-- ROLLBACK fuer fix_supplier_views_v3.9.213.sql
--   Stellt die LIVE-Definition von supplier_articles_safe aus v3.9.54 wieder her
--   (Maske: ek_preis = NULL fuer monteur/helfer, sichtbar fuer alle anderen inkl. techniker).
--   Quelle: sql/supplier_articles_safe_view_v3.9.54.sql (Z.17-23, "APPLIZIERT 2026-06-07").
--   Supabase project_id: jiggujpruejkaomgxarp
-- ============================================================================

CREATE OR REPLACE VIEW public.supplier_articles_safe AS
SELECT
  id, supplier_id, art_nr, hersteller_art_nr, gtin, bezeichnung, langtext, mengeneinheit,
  listenpreis,
  CASE WHEN public.current_user_role() IN ('monteur','helfer') THEN NULL::real ELSE ek_preis END AS ek_preis,
  rabatt_prozent, warengruppe, ep_system, ep_gewerk, dimension, verfuegbar, bild_url, last_updated, rabatt_gruppe
FROM public.supplier_articles;

GRANT SELECT ON public.supplier_articles_safe TO authenticated;

-- supplier_articles_public: durch das Forward-Skript NICHT veraendert (nur Capture/Empfehlung,
--   DROP war auskommentiert). → KEIN Rollback noetig. Falls der Operator sie manuell gedroppt
--   hat, muss die Original-Def aus dem Live-Capture (pg_get_viewdef) wiederhergestellt werden —
--   sie liegt NICHT im Repo vor.

-- VERIFY (nach Rollback):
--   SELECT count(*), count(ek_preis) FROM public.supplier_articles_safe;
--   -- techniker-Session: ek_preis wieder sichtbar (alte Maske).
-- ============================================================================
