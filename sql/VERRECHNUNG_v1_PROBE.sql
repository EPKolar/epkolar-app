-- VERRECHNUNG v1 - PROBE (Human-Run-Gate, Buero-Portal Reiter "Verrechnung", GF 23.11.2026)
-- Laeuft komplett in einer Transaktion und wird ZURUECKGEROLLT. Nichts bleibt in der DB.
-- Vorher: Pflicht-Verify (Prod jiggujpruejkaomgxarp, nie MOBOLog).
select count(*) as arbeitsscheine from public.arbeitsscheine;             -- erwartet ~233 (23.11.)
select to_regclass('public.verrechnung') as gibt_es_schon;              -- erwartet NULL
select proname from pg_proc where proname in ('current_user_role','is_kiosk_role') and pronamespace='public'::regnamespace; -- beide da

begin;
\i sql/VERRECHNUNG_v1_ENTWURF.sql
-- Nachmessen (innerhalb der Transaktion)
select policyname, cmd, permissive, roles, qual, with_check from pg_policies where tablename='verrechnung' order by policyname;
select grantee, privilege_type from information_schema.role_table_grants where table_schema='public' and table_name='verrechnung' order by grantee, privilege_type;
-- erwartet: authenticated SELECT/INSERT/UPDATE/DELETE; KEIN anon, KEIN public
select has_table_privilege('anon','public.verrechnung','select') as anon_select,      -- false
       has_table_privilege('authenticated','public.verrechnung','select') as auth_select; -- true
select conname, pg_get_constraintdef(oid) from pg_constraint where conrelid='public.verrechnung'::regclass;
rollback;
-- Danach: select to_regclass('public.verrechnung'); -> wieder NULL
