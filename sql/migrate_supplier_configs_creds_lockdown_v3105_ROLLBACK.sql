-- v3.10.5 ROLLBACK supplier_configs Lockdown
DROP VIEW IF EXISTS public.supplier_configs_safe;
DROP POLICY IF EXISTS supplier_configs_modify_admin_pl_lager ON public.supplier_configs;
DROP POLICY IF EXISTS supplier_configs_update_admin_pl_lager ON public.supplier_configs;
DROP POLICY IF EXISTS supplier_configs_delete_admin_pl_lager ON public.supplier_configs;

-- Original wiederherstellen
CREATE POLICY authenticated_write_supplier_configs
  ON public.supplier_configs FOR ALL TO authenticated
  USING (true) WITH CHECK (true);

-- can_see_supplier_creds() bleibt erhalten (sprint-übergreifend nützlich)
