-- ✅ APPLIZIERT 2026-06-07 (CC, Bug-Hunt). supplier_articles_safe-View nachgereicht.
--
-- BUG: Das Frontend (v3.9.54 B-006) liest den Material-Katalog über die View `supplier_articles_safe`
--   (Z.12695: select id,supplier_id,art_nr,bezeichnung,langtext,mengeneinheit,ep_system,ep_gewerk,
--   ek_preis,listenpreis,dimension,rabatt_gruppe). Diese View wurde NIE in der DB angelegt → REST
--   lieferte 404 → Material-Tab leer für ALLE Rollen + die Monteur-EK-Preis-Verschleierung wirkungslos.
--   (Live-Befund Bug-Hunt: GET /rest/v1/supplier_articles_safe → 404.)
--
-- DESIGN (B-006): supplier_articles (Basistabelle) ist RLS-geschützt — Monteur darf NICHT direkt
--   selecten. Alle Rollen lesen den Katalog über diese View; ek_preis (Einkaufspreis) wird für
--   monteur/helfer NULL maskiert. → Definer-View (wie supplier_articles_public), umgeht die Basis-RLS.
--   current_user_role() (SECURITY DEFINER) liefert die Rolle des anfragenden Users via auth.uid().
--   Rollen verifiziert: monteur/projektleiter/buero/techniker/admin — EK-Rollen = alle außer monteur/helfer.
--   HINWEIS: Definer-View wird vom Supabase-Linter als security_definer_view geflaggt — hier INTENTIONAL
--   + nötig (Monteur hat keinen Basistabellen-Zugriff; security_invoker würde Monteur 0 Zeilen geben).
--
CREATE OR REPLACE VIEW public.supplier_articles_safe AS
SELECT
  id, supplier_id, art_nr, hersteller_art_nr, gtin, bezeichnung, langtext, mengeneinheit,
  listenpreis,
  CASE WHEN public.current_user_role() IN ('monteur','helfer') THEN NULL::real ELSE ek_preis END AS ek_preis,
  rabatt_prozent, warengruppe, ep_system, ep_gewerk, dimension, verfuegbar, bild_url, last_updated, rabatt_gruppe
FROM public.supplier_articles;

GRANT SELECT ON public.supplier_articles_safe TO authenticated;

-- VERIFY (appliziert + grün): SELECT count(*), count(ek_preis) FROM supplier_articles_safe; → 25121/25121
--   (als service/admin → ek_preis sichtbar). Live (eingeloggter Admin): REST 200, ek_preis=0.42 sichtbar.
--   Monteur-NULL-Maskierung = logikverifiziert (current_user_role() IN ('monteur','helfer')); voller
--   Beweis bräuchte eine Monteur-Session.
-- ROLLBACK: DROP VIEW IF EXISTS public.supplier_articles_safe;
