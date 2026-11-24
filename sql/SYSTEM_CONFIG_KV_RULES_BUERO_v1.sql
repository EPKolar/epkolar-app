-- SYSTEM_CONFIG kv_rules fuer das Buero - ANGEWENDET 24.11.2026 auf Prod (Migration system_config_kv_rules_buero_v1),
-- Freigabe GF 24.11.: "ja auch die saetze duerfen geaendert werden, sind ja jedes jahr andere".
-- Probe vorher (zurueckgerollt): buero kv_rules anlegen/aendern erlaubt; anderer Schluessel + loeschen ohne Wirkung;
-- monteur/projektleiter anlegen P0001, aendern 0 Zeilen (RLS), loeschen ohne Wirkung.
create or replace function public.guard_admin_only()
 returns trigger language plpgsql security definer set search_path to 'public','pg_temp' as $function$
DECLARE c_role text; c_sub text;
BEGIN
  c_sub := current_setting('request.jwt.claims', true)::json->>'sub';
  IF c_sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
  SELECT u.role INTO c_role FROM public.users u WHERE u.auth_user_id::text = c_sub;
  IF c_role = 'admin' THEN RETURN COALESCE(NEW, OLD); END IF;
  -- GF 24.11.2026: Buero pflegt die Zulagensaetze (jedes Jahr andere) - NUR Schluessel kv_rules, nur anlegen/aendern, nie loeschen
  IF c_role = 'buero' AND TG_OP IN ('INSERT','UPDATE') AND NEW.key = 'kv_rules' AND (TG_OP = 'INSERT' OR OLD.key = 'kv_rules') THEN RETURN NEW; END IF;
  RAISE EXCEPTION 'Nur Admin darf system_config aendern';
END; $function$;
create policy system_config_kv_rules_buero_insert on public.system_config for insert to authenticated with check (key = 'kv_rules' and public.current_user_role() in ('admin','buero'));
create policy system_config_kv_rules_buero_update on public.system_config for update to authenticated using (key = 'kv_rules' and public.current_user_role() in ('admin','buero')) with check (key = 'kv_rules' and public.current_user_role() in ('admin','buero'));

-- RUECKNAHME:
-- drop policy if exists system_config_kv_rules_buero_insert on public.system_config;
-- drop policy if exists system_config_kv_rules_buero_update on public.system_config;
-- und guard_admin_only ohne den buero-Zweig neu anlegen (nur admin).
