-- AUTH_FIX_buero_gotrue_2b.sql  (2026-06-29)
-- Punkt 2b der Inventur: lindhuber + schober (beide buero) haben ein gesetztes
-- public.users.auth_user_id, das ins Leere zeigt (kein GoTrue-User per ID/Email)
-- -> Login unmoeglich (GoTrue ist alleiniger Auth-Pfad, index.html:2444).
-- Fix: GoTrue-User mit den BEREITS hinterlegten auth_user_id-UUIDs anlegen
--      (=> kein Relink in public.users noetig). Muster 1:1 aus admin_create_user-RPC.
-- Standard-PW: 34kolar70.  Projekt-Ref: jiggujpruejkaomgxarp.
--
-- Idempotent: legt nur an, wenn die auth.users-Zeile (per id) noch fehlt.

do $$
declare
  _r record;
  _pw text := '34kolar70';
begin
  for _r in
    select u.auth_user_id::uuid as uid, lower(trim(u.email)) as email
    from public.users u
    where u.username in ('lindhuber','schober')
      and u.auth_user_id is not null
  loop
    -- nur anlegen, wenn dieser GoTrue-User noch nicht existiert
    if not exists (select 1 from auth.users a where a.id = _r.uid) then
      insert into auth.users (
        instance_id, id, aud, role, email, encrypted_password,
        email_confirmed_at, created_at, updated_at,
        raw_app_meta_data, raw_user_meta_data,
        confirmation_token, recovery_token, email_change,
        email_change_token_new, email_change_token_current,
        phone_change, phone_change_token, reauthentication_token,
        is_sso_user, is_anonymous
      ) values (
        '00000000-0000-0000-0000-000000000000', _r.uid, 'authenticated', 'authenticated',
        _r.email, extensions.crypt(_pw, extensions.gen_salt('bf')),
        now(), now(), now(),
        jsonb_build_object('provider','email','providers',jsonb_build_array('email'),'role','buero'),
        '{}'::jsonb,
        '', '', '', '', '', '', '', '',
        false, false
      );

      insert into auth.identities (
        id, user_id, identity_data, provider, provider_id,
        last_sign_in_at, created_at, updated_at
      ) values (
        gen_random_uuid(), _r.uid,
        jsonb_build_object('sub', _r.uid::text, 'email', _r.email, 'email_verified', false, 'phone_verified', false),
        'email', _r.uid::text,
        now(), now(), now()
      );

      raise notice 'GoTrue angelegt: % (%)', _r.email, _r.uid;
    else
      raise notice 'GoTrue existiert bereits: % (%)', _r.email, _r.uid;
    end if;
  end loop;
end $$;

-- Verify
select u.username, u.email, (a.id is not null) as has_gotrue, a.email_confirmed_at is not null as confirmed
from public.users u
left join auth.users a on a.id = u.auth_user_id
where u.username in ('lindhuber','schober');
