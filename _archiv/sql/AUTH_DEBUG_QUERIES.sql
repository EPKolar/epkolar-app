-- ════════════════════════════════════════════════════════════════
-- AUTH DEBUG QUERIES — GoTrue 500 "Database error querying schema"
-- Reihenfolge: B → A → Trigger → Logs
-- ════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────
-- QUERY B (HÖCHSTE PRIORITÄT) — NULL-Trap in Token-Feldern
-- GoTrue erwartet '' (leerer String), nicht NULL.
-- Manueller INSERT in auth.users vergisst diese Felder fast immer.
-- ──────────────────────────────────────────────────────────────

SELECT email,
       confirmation_token IS NULL              AS conf_tok_null,
       recovery_token IS NULL                  AS recov_tok_null,
       email_change_token_current IS NULL      AS ec_curr_null,
       email_change_token_new IS NULL          AS ec_new_null,
       email_change IS NULL                    AS ec_str_null,
       phone_change_token IS NULL              AS pc_tok_null,
       phone_change IS NULL                    AS pc_str_null,
       reauthentication_token IS NULL          AS reauth_tok_null,
       email_confirmed_at IS NULL              AS no_email_confirm,
       confirmed_at IS NULL                    AS no_confirm,
       (aud IS NULL OR aud='')                 AS aud_missing,
       (role IS NULL OR role='')               AS role_missing,
       instance_id::text                       AS instance_id
FROM auth.users
WHERE email IN ('info@ep-kolar.at','office@ep-kolar.at','riedmann@ep-kolar.at')
ORDER BY email;
-- Smoking Gun: alle Spalten TRUE bei broken users, alle FALSE bei working user.

-- ──────────────────────────────────────────────────────────────
-- FIX B (wenn Query B NULL-Felder zeigt) — alle Token-Felder reparieren
-- ──────────────────────────────────────────────────────────────

UPDATE auth.users
SET confirmation_token            = COALESCE(confirmation_token,''),
    recovery_token                = COALESCE(recovery_token,''),
    email_change_token_current    = COALESCE(email_change_token_current,''),
    email_change_token_new        = COALESCE(email_change_token_new,''),
    email_change                  = COALESCE(email_change,''),
    phone_change_token            = COALESCE(phone_change_token,''),
    phone_change                  = COALESCE(phone_change,''),
    reauthentication_token        = COALESCE(reauthentication_token,''),
    email_confirmed_at            = COALESCE(email_confirmed_at, now()),
    confirmed_at                  = COALESCE(confirmed_at, now()),
    aud                           = COALESCE(NULLIF(aud,''), 'authenticated'),
    role                          = COALESCE(NULLIF(role,''), 'authenticated'),
    raw_app_meta_data             = COALESCE(raw_app_meta_data,
                                     jsonb_build_object('provider','email','providers',jsonb_build_array('email'))),
    raw_user_meta_data            = COALESCE(raw_user_meta_data, '{}'::jsonb),
    updated_at                    = now()
WHERE email IN ('info@ep-kolar.at','office@ep-kolar.at');

-- ──────────────────────────────────────────────────────────────
-- QUERY A — RLS auf auth.* Schema (rls_enabled UND rls_forced)
-- ──────────────────────────────────────────────────────────────

SELECT n.nspname AS schema, c.relname AS table,
       c.relrowsecurity         AS rls_enabled,
       c.relforcerowsecurity    AS rls_forced,
       (SELECT count(*) FROM pg_policies WHERE schemaname=n.nspname AND tablename=c.relname) AS policies
FROM pg_class c
JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE n.nspname='auth' AND c.relkind='r'
ORDER BY c.relname;
-- Erwartung: rls_enabled=false UND rls_forced=false auf allen auth.*-Tabellen

-- FIX (wenn Query A irrtümlich aktiviertes RLS zeigt):
DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['users','identities','sessions','refresh_tokens',
                            'mfa_factors','mfa_challenges','mfa_amr_claims',
                            'sso_providers','sso_domains','saml_providers',
                            'saml_relay_states','flow_state','one_time_tokens']
  LOOP
    BEGIN
      EXECUTE format('ALTER TABLE auth.%I DISABLE ROW LEVEL SECURITY', t);
      EXECUTE format('ALTER TABLE auth.%I NO FORCE ROW LEVEL SECURITY', t);
    EXCEPTION WHEN undefined_table THEN NULL; END;
  END LOOP;
END $$;

-- ──────────────────────────────────────────────────────────────
-- QUERY C — Trigger auf auth.users (Custom-Trigger-Crashes ausschließen)
-- ──────────────────────────────────────────────────────────────

SELECT
  t.tgname              AS trigger_name,
  CASE t.tgtype::int & 66
    WHEN 2 THEN 'BEFORE' WHEN 64 THEN 'INSTEAD OF' ELSE 'AFTER' END AS timing,
  CASE
    WHEN t.tgtype::int & 4  > 0 THEN 'INSERT'
    WHEN t.tgtype::int & 16 > 0 THEN 'UPDATE'
    WHEN t.tgtype::int & 8  > 0 THEN 'DELETE'
  END                   AS event,
  CASE t.tgenabled
    WHEN 'O' THEN 'ENABLED' WHEN 'D' THEN 'DISABLED'
    WHEN 'R' THEN 'REPLICA' WHEN 'A' THEN 'ALWAYS' END AS state,
  p.proname             AS function_name,
  n.nspname             AS function_schema,
  pg_get_userbyid(p.proowner) AS owner,
  t.tgisinternal        AS is_internal
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace cn ON cn.oid = c.relnamespace
JOIN pg_proc p ON p.oid = t.tgfoid
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE cn.nspname='auth' AND c.relname='users'
ORDER BY t.tgisinternal, t.tgname;

-- Source der Custom-Trigger-Functions
SELECT n.nspname || '.' || p.proname AS function,
       pg_get_functiondef(p.oid)     AS source
FROM pg_trigger t
JOIN pg_class c ON c.oid=t.tgrelid AND c.relname='users'
JOIN pg_namespace cn ON cn.oid=c.relnamespace AND cn.nspname='auth'
JOIN pg_proc p ON p.oid=t.tgfoid
JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE NOT t.tgisinternal
ORDER BY t.tgname;

-- TEST: User-Trigger temporär deaktivieren (mit ROLLBACK)
-- BEGIN;
--   ALTER TABLE auth.users DISABLE TRIGGER USER;
--   -- jetzt in Browser: await window._sbAuthLogin('info@...','test1234')
-- ROLLBACK;

-- ──────────────────────────────────────────────────────────────
-- QUERY D — Duplikate
-- ──────────────────────────────────────────────────────────────

SELECT email, count(*) AS dup_cnt
FROM auth.users
WHERE email IN ('info@ep-kolar.at','office@ep-kolar.at','riedmann@ep-kolar.at')
GROUP BY email HAVING count(*) > 1;

-- ──────────────────────────────────────────────────────────────
-- QUERY E — instance_id Konsistenz
-- ──────────────────────────────────────────────────────────────

SELECT email, instance_id
FROM auth.users
WHERE email IN ('info@ep-kolar.at','office@ep-kolar.at','riedmann@ep-kolar.at');
-- Alle 3 müssen dieselbe instance_id haben (Standard-Single-Tenant: 00000000-0000-0000-0000-000000000000)

-- ──────────────────────────────────────────────────────────────
-- QUERY F — Identity-Konsistenz (sub muss text sein, nicht uuid)
-- ──────────────────────────────────────────────────────────────

SELECT u.email,
       i.identity_data->>'sub'                  AS sub_in_data,
       u.id::text                               AS user_id_text,
       (i.identity_data->>'sub' = u.id::text)   AS sub_matches,
       i.provider, i.provider_id
FROM auth.users u
LEFT JOIN auth.identities i ON i.user_id = u.id
WHERE u.email IN ('info@ep-kolar.at','office@ep-kolar.at','riedmann@ep-kolar.at')
ORDER BY u.email;
-- sub_matches muss TRUE sein. Wenn FALSE:
-- UPDATE auth.identities
-- SET identity_data = jsonb_set(identity_data,'{sub}', to_jsonb(user_id::text))
-- WHERE user_id IN (SELECT id FROM auth.users WHERE email IN ('info@ep-kolar.at','office@ep-kolar.at'));

-- ──────────────────────────────────────────────────────────────
-- POST-FIX VERIFIKATION
-- Nach jedem FIX im Browser testen:
--   await window._sbAuthLogin('info@ep-kolar.at','test1234')
--   await window._sbAuthLogin('office@ep-kolar.at','test1234')
-- ──────────────────────────────────────────────────────────────
