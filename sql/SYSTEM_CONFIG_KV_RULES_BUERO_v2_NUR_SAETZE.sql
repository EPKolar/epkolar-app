-- SYSTEM_CONFIG kv_rules Buero v2 - ANGEWENDET 24.11.2026 auf Prod (Migration system_config_kv_rules_buero_v2_nur_saetze).
-- Anlass: Security-Review zu v1 - v1 erlaubte dem Buero JEDE KV-Konstante in kv_rules (Zuschlaege, kmGeld, Urlaub ...).
-- GF hat nur die Zulagensaetze freigegeben ("sind ja jedes jahr andere"). v2:
--   * Buero darf kv_rules NUR aendern, nie anlegen (Upsert-Vorlauf nur, wenn die Zeile existiert), nie loeschen.
--   * Beim Aendern muss alles ausser taggeldAb6h (=klein), ezMittel, ezGross gleich bleiben; die drei Saetze Zahl 0..1000.
--   * kv_rules-Zeile einmalig angelegt mit den Werten von KV_RULES_FALLBACK der App (identisch, Rechnung unveraendert).
-- Probe 24.11. (zurueckgerollt, echte Rollen): buero nur Saetze -> erlaubt (12.10); buero kmGeld -> verweigert;
--   buero Satz -5 / "abc" -> verweigert; buero loeschen -> ohne Wirkung; monteur alles -> verweigert.
-- Policies aus v1 bleiben (system_config_kv_rules_buero_insert/_update) - der Trigger ist die eigentliche Feldsperre.
create or replace function public.guard_admin_only()
 returns trigger language plpgsql security definer set search_path to 'public','pg_temp' as $function$
DECLARE c_role text; c_sub text; o jsonb; n jsonb; k text;
BEGIN
  c_sub := current_setting('request.jwt.claims', true)::json->>'sub';
  IF c_sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
  SELECT u.role INTO c_role FROM public.users u WHERE u.auth_user_id::text = c_sub;
  IF c_role = 'admin' THEN RETURN COALESCE(NEW, OLD); END IF;
  IF c_role = 'buero' AND TG_OP = 'INSERT' AND NEW.key = 'kv_rules' AND EXISTS (SELECT 1 FROM public.system_config WHERE key = 'kv_rules') THEN RETURN NEW; END IF;
  IF c_role = 'buero' AND TG_OP = 'UPDATE' AND NEW.key = 'kv_rules' AND OLD.key = 'kv_rules' THEN
    o := OLD.value::jsonb; n := NEW.value::jsonb;
    IF (n - ARRAY['taggeldAb6h','ezMittel','ezGross']) IS DISTINCT FROM (o - ARRAY['taggeldAb6h','ezMittel','ezGross']) THEN RAISE EXCEPTION 'Buero darf in kv_rules nur die Zulagensaetze aendern'; END IF;
    FOREACH k IN ARRAY ARRAY['taggeldAb6h','ezMittel','ezGross'] LOOP
      IF jsonb_typeof(n->k) IS DISTINCT FROM 'number' OR (n->>k)::numeric < 0 OR (n->>k)::numeric > 1000 THEN RAISE EXCEPTION 'Zulagensatz % ungueltig (Zahl 0 bis 1000)', k; END IF;
    END LOOP;
    RETURN NEW;
  END IF;
  RAISE EXCEPTION 'Nur Admin darf system_config aendern';
END; $function$;
-- Seed (einmalig): insert into public.system_config(key,value,...) values ('kv_rules', <KV_RULES_FALLBACK als JSON>, ...) on conflict (key) do nothing;
-- RUECKNAHME: Funktion ohne buero-Zweig (nur admin) neu anlegen; Policies system_config_kv_rules_buero_* droppen.
--   Die kv_rules-Zeile kann bleiben (Werte = Fallback) oder vom Admin geloescht werden.
-- Hinweis: kommt spaeter ein NEUES Feld in KV_RULES_FALLBACK dazu, lehnt der Trigger das erste Speichern durchs Buero ab,
--   bis der Admin einmal unter Administration > KV-Konstanten gespeichert hat (dann steht das Feld in der Zeile).
