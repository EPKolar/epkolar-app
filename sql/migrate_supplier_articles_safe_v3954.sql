-- v3.9.54 B-006 EK-Preise Security: Monteure dürfen ek_preis NICHT sehen
-- View supplier_articles_safe mit CASE-WHEN is_admin() Maskierung
--
-- Spalten der Basistabelle (aus Frontend select-Lists abgeleitet, index.html L7173/12125):
--   id, supplier_id, art_nr, bezeichnung, langtext, mengeneinheit,
--   ep_system, ep_gewerk, ek_preis, listenpreis, dimension, rabatt_gruppe
-- Mögliche zusätzliche Spalten (Sebastian bitte ergänzen wenn vorhanden):
--   created_at, updated_at, sync_quelle, ...
--
-- Sebastian-Action: In Supabase SQL-Editor ausführen. Backend jiggujpruejkaomgxarp.
-- Vor Ausführung: prüfen ob is_admin() schon aus v3.9.53-Migration vorhanden ist (CREATE OR REPLACE ist idempotent).

-- is_admin() Helper sicherheitshalber nochmal (idempotent via CREATE OR REPLACE)
CREATE OR REPLACE FUNCTION is_admin() RETURNS boolean AS $$
  SELECT EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role = 'admin');
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- Erweiterter Rollen-Check für EK-Sicht (Admin + PL + Lager)
CREATE OR REPLACE FUNCTION can_see_ek() RETURNS boolean AS $$
  SELECT EXISTS(
    SELECT 1 FROM public.users
    WHERE auth_user_id = auth.uid()
      AND role IN ('admin','projektleiter','buero','lager')
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- View: alle Spalten unverändert, ek_preis maskiert für non-EK-Rollen
-- (Monteure sehen NULL statt Preis.)
CREATE OR REPLACE VIEW public.supplier_articles_safe AS
SELECT
  id,
  supplier_id,
  art_nr,
  bezeichnung,
  langtext,
  mengeneinheit,
  ep_system,
  ep_gewerk,
  CASE WHEN can_see_ek() THEN ek_preis ELSE NULL END AS ek_preis,
  listenpreis,
  dimension,
  rabatt_gruppe
FROM public.supplier_articles;

-- Grant SELECT auf View an authenticated (View ist SECURITY INVOKER per default —
-- aber can_see_ek() läuft als SECURITY DEFINER → Monteur kommt durch View durch,
-- bekommt aber NULL bei ek_preis.)
GRANT SELECT ON public.supplier_articles_safe TO authenticated;

-- RLS auf Basistabelle: nur EK-berechtigte Rollen dürfen direkt selecten
-- (Frontend wechselt auf View → Monteur trifft Basistabelle nicht mehr direkt;
--  falls doch, blockiert die RLS.)
ALTER TABLE public.supplier_articles ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS supplier_articles_select_ek_roles
  ON public.supplier_articles FOR SELECT TO authenticated
  USING (can_see_ek());

-- INSERT/UPDATE/DELETE: nur Admin/Lager (für DATANORM-Import-Pfad in index.html L7238)
CREATE POLICY IF NOT EXISTS supplier_articles_write_admin_lager
  ON public.supplier_articles FOR INSERT TO authenticated
  WITH CHECK (
    EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role IN ('admin','lager'))
  );

CREATE POLICY IF NOT EXISTS supplier_articles_update_admin_lager
  ON public.supplier_articles FOR UPDATE TO authenticated
  USING (
    EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role IN ('admin','lager'))
  )
  WITH CHECK (
    EXISTS(SELECT 1 FROM public.users WHERE auth_user_id = auth.uid() AND role IN ('admin','lager'))
  );

CREATE POLICY IF NOT EXISTS supplier_articles_delete_admin
  ON public.supplier_articles FOR DELETE TO authenticated
  USING (is_admin());
