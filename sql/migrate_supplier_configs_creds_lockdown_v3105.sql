-- ═══════════════════════════════════════════════════════════
-- v3.10.5 P0-2 supplier_configs Klartext-Passwörter Lockdown
-- Sebastian-Spec 2026-06-03
-- ═══════════════════════════════════════════════════════════
--
-- BEFUND: Monteur(barger) liest username+password von 5 Händlern
--   (Heinze/Impex/SHT/ÖAG/Holter) via authenticated_read_supplier_configs.
--
-- CODE-PFAD-ANALYSE:
--   Z7401 AdminPanel fetchSuppliers: _sbGet("supplier_configs","order=name.asc")
--         → KEIN select-Filter → fetched ALLE Spalten inkl. username/password
--         → Admin-Page (UI-only via Tab-Visibility), aber Monteur kann via DevTools direkt
--   Z12359 Material-Tab: _sbGet("supplier_configs","select=id,name,gewerk,...,interface_type&active=eq.true")
--         → EXPLICIT select ohne username/password ✓
--   Z7482 PATCH last_sync: Admin/PL-only (UI)
--
-- STRATEGIE: 2-stufiger Fix
--   STUFE 1 (jetzt, additiv): View `supplier_configs_safe` mit allen non-cred Spalten.
--     App-Code Patch (Sprint 83): Z12359 (und alle Monteur-erreichbaren Pfade) auf View.
--   STUFE 2 (nach Code-Patch): Policy supplier_configs restrict SELECT auf admin/PL.
--
-- DIESES SQL macht STUFE 1.
-- STUFE 2 separat in migrate_supplier_configs_policy_v3105b.sql nach Code-Sprint 83.

-- ═══════════════════════════════════════════════════════════
-- VORAUSSETZUNG: is_admin() Helper aus Sprint 53
-- ═══════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Snapshot
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3105 (
  ts timestamptz DEFAULT now(),
  tablename text, polname text, roles text[], cmd text,
  qual text, with_check text
);

INSERT INTO public._rls_snapshot_v3105 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename='supplier_configs';

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: Helper-Function can_see_supplier_creds()
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.can_see_supplier_creds() RETURNS boolean AS $$
  SELECT EXISTS(
    SELECT 1 FROM public.users
    WHERE auth_user_id = auth.uid()
      AND (role IN ('admin','projektleiter')
           OR LOWER(COALESCE(rolle,'')) = 'lagerleitung')
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: View supplier_configs_safe (ohne creds)
-- ═══════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW public.supplier_configs_safe AS
SELECT
  id, name, gewerk,
  -- Stamm + Schnittstellen-Config (non-cred):
  interface_type, base_url, unternehmen_id, shk_url, ids_shop_url,
  -- Konditionen:
  skonto_prozent, jahresbonus_prozent, zahlungskonditionen, firma_adresse,
  -- Sync-Status:
  active, last_sync, last_sync_status, last_sync_articles,
  created_at, updated_at,
  -- Maske credentials für non-admin:
  CASE WHEN can_see_supplier_creds() THEN username ELSE NULL END AS username,
  CASE WHEN can_see_supplier_creds() THEN password ELSE NULL END AS password,
  CASE WHEN can_see_supplier_creds() THEN config ELSE NULL END AS config
FROM public.supplier_configs;

GRANT SELECT ON public.supplier_configs_safe TO authenticated;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: Policy auf Basistabelle BEHALTEN ABER eingeschränkt
-- ═══════════════════════════════════════════════════════════
-- WICHTIG: Wir DROPPEN noch nicht die offene Policy, weil App-Code Z7401 + Z12359
-- noch nicht auf View umgestellt sind. Erst nach Sprint 83 (Code-Patch).
--
-- Statt dessen JETZT: nur UPDATE/INSERT/DELETE einschränken auf admin/PL/Lager.
-- Monteur darf weiter SELECT (für Material-Anforderung) — Stufe 2 ersetzt das.

DROP POLICY IF EXISTS authenticated_write_supplier_configs ON public.supplier_configs;

CREATE POLICY supplier_configs_modify_admin_pl_lager
  ON public.supplier_configs FOR INSERT TO authenticated
  WITH CHECK (can_see_supplier_creds());

CREATE POLICY supplier_configs_update_admin_pl_lager
  ON public.supplier_configs FOR UPDATE TO authenticated
  USING (can_see_supplier_creds())
  WITH CHECK (can_see_supplier_creds());

CREATE POLICY supplier_configs_delete_admin_pl_lager
  ON public.supplier_configs FOR DELETE TO authenticated
  USING (can_see_supplier_creds());

-- ═══════════════════════════════════════════════════════════
-- VERIFY (Sebastian-Smoke)
-- ═══════════════════════════════════════════════════════════
-- 1. View existiert + grants:
--    SELECT * FROM public.supplier_configs_safe LIMIT 1;
--    Als Monteur: username/password MUSS NULL sein.
--    Als Admin: username/password sichtbar.
--
-- 2. Basistabelle UPDATE-Test:
--    Als Monteur: PATCH /supplier_configs?id=eq.X body:{name:'test'}
--    → erwartet: 403
--    Als Admin: PATCH selber → 200
--
-- 3. App-Funktionalität:
--    Material-Tab als Monteur → Z12359-Call funktioniert noch (SELECT bleibt offen)
--    Admin-Settings-Page → fetchSuppliers Z7401 funktioniert (Admin)
--
-- STUFE 2 (NACH App-Code-Sprint 83):
--   migrate_supplier_configs_policy_v3105b.sql:
--     DROP authenticated_read_supplier_configs;
--     CREATE POLICY supplier_configs_select_admin_pl_lager ON public.supplier_configs
--       FOR SELECT TO authenticated USING (can_see_supplier_creds());
--   App Z7401 + Z12359 müssen vorher auf supplier_configs_safe migriert sein.

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK siehe migrate_supplier_configs_creds_lockdown_v3105_ROLLBACK.sql
-- ═══════════════════════════════════════════════════════════
