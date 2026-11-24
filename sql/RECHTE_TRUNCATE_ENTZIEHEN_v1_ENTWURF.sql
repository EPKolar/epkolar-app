-- RECHTE-HAERTUNG v1 - ANGEWENDET 24.11.2026 auf Prod (Freigabe GF 'rechte haertung unbedingt erledigen', Migration
--   rechte_truncate_entziehen_v1). Nachmessung: anon/authenticated TRUNCATE 0, REFERENCES 0; SELECT 68/INSERT 67/anon SELECT 63 unveraendert.
-- Gemessen vorher 24.11.2026:
--   62 von 69 Tabellen in public: anon hat TRUNCATE/REFERENCES/TRIGGER (Supabase-Standardrechte), authenticated auf 66.
--   TRUNCATE umgeht RLS. Ueber PostgREST (App, REST) ist TRUNCATE NICHT aufrufbar - Risiko nur bei direktem DB-Zugang
--   mit diesen Rollen. Die App braucht nur SELECT/INSERT/UPDATE/DELETE (RLS entscheidet). Nichts an RLS/Policies.
-- Wirkung: entzieht NUR TRUNCATE, REFERENCES, TRIGGER - SELECT/INSERT/UPDATE/DELETE bleiben exakt wie sie sind.
-- Probe zuerst (begin ... rollback) mit der Nachmessung unten; danach EINZELN anwenden.
do $$
declare t record;
begin
  for t in select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
           where n.nspname='public' and c.relkind='r' loop
    execute format('revoke truncate, references, trigger on table public.%I from anon, authenticated', t.relname);
  end loop;
end $$;
-- Kuenftige Tabellen (vom Rollen-Eigentuemer postgres angelegt) bekommen die drei Rechte nicht mehr automatisch:
alter default privileges in schema public revoke truncate, references, trigger on tables from anon, authenticated;

-- Nachmessung (erwartet 0 | 0 und unveraenderte Zahl fuer SELECT):
-- select count(*) filter (where has_table_privilege('anon',c.oid,'TRUNCATE')) anon_tr,
--        count(*) filter (where has_table_privilege('authenticated',c.oid,'TRUNCATE')) auth_tr,
--        count(*) filter (where has_table_privilege('authenticated',c.oid,'SELECT')) auth_select
-- from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r';
-- RUECKNAHME: grant truncate, references, trigger on all tables in schema public to anon, authenticated;
--             alter default privileges in schema public grant truncate, references, trigger on tables to anon, authenticated;
