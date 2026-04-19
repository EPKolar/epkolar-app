-- ============================================================
-- B-020 FIX · DB-Teil · Sebastian führt manuell im Supabase SQL-Editor aus
-- ============================================================
-- Root-Cause: 4 User (u1 paschinger, u2 barger, u3 cracana, u7 schober) haben email=''
-- in public.users. GoTrue verwirft signInWithPassword({email:''}) mit 500 → App lief
-- in silent "eingeschränkter Modus" + renderte Dashboard mit anon-Key.
--
-- v3.6.3 Code-Fix (in index.html) wirft jetzt B20-F bei leerer Email → User sieht
-- klaren Error statt blank dashboard. Dieser SQL repariert den DB-State damit
-- echtes Login wieder möglich ist.
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 1. u7 Schober — Email setzen + auth_user_id auf echten GoTrue-User
--    Der GoTrue-Account info@ep-kolar.at existiert bereits (UUID 4f4a25c5-95ae-4168-9130-61a28388f2c0).
--    Die alte u7.auth_user_id=9d6c5ebd-e36d-419d-8ecf-5233fcbb70d8 ist ein ORPHAN.
-- ────────────────────────────────────────────────────────────
UPDATE public.users
SET email='info@ep-kolar.at',
    auth_user_id='4f4a25c5-95ae-4168-9130-61a28388f2c0'
WHERE id='u7' AND (email IS NULL OR email='');

-- Verify
SELECT id, username, email, auth_user_id, role FROM public.users WHERE id='u7';
-- Erwartet: email='info@ep-kolar.at', auth_user_id='4f4a25c5-...'

-- ────────────────────────────────────────────────────────────
-- 2. Optional: Orphan-Cleanup (NUR wenn 9d6c5ebd-... wirklich ungenutzt)
-- ────────────────────────────────────────────────────────────
-- Erst prüfen:
-- SELECT id, email, created_at, last_sign_in_at FROM auth.users WHERE id='9d6c5ebd-e36d-419d-8ecf-5233fcbb70d8';
-- Wenn email='' ODER NULL ODER kein last_sign_in_at → DELETE safe.
-- Wenn unsicher: lassen, schadet nicht.
-- DELETE FROM auth.users WHERE id='9d6c5ebd-e36d-419d-8ecf-5233fcbb70d8';

-- ────────────────────────────────────────────────────────────
-- 3. u1/u2/u3 — Brauchen NEUE GoTrue-Accounts
--    SQL kann das NICHT direkt (encrypted_password via bcrypt, email_confirmed_at etc).
--    Sebastian: Supabase Dashboard → Authentication → Users → "Add user" für jeden:
--      paschinger@ep-kolar.at / test1234
--      barger@ep-kolar.at / test1234
--      cracana@ep-kolar.at / test1234
--    Danach die auth.users.id kopieren und die UUID unten einsetzen.
-- ────────────────────────────────────────────────────────────
-- Nach Dashboard-Anlage: Ersetze '<NEUE_UUID>' durch die echten IDs.
UPDATE public.users SET email='paschinger@ep-kolar.at', auth_user_id='<NEUE_UUID_PASCHINGER>' WHERE id='u1';
UPDATE public.users SET email='barger@ep-kolar.at',     auth_user_id='<NEUE_UUID_BARGER>'     WHERE id='u2';
UPDATE public.users SET email='cracana@ep-kolar.at',    auth_user_id='<NEUE_UUID_CRACANA>'    WHERE id='u3';

-- ────────────────────────────────────────────────────────────
-- 4. Final verify — alle User aligned
-- ────────────────────────────────────────────────────────────
SELECT
  pu.id,
  pu.username,
  pu.email AS pu_email,
  pu.role,
  au.email AS au_email,
  au.last_sign_in_at,
  (pu.email IS NOT NULL AND pu.email='' ) AS bad_empty,
  (pu.auth_user_id IS NULL) AS no_auth_link,
  (au.id IS NULL) AS auth_missing
FROM public.users pu
LEFT JOIN auth.users au ON au.id = pu.auth_user_id
ORDER BY pu.id;

-- Erwartet (nach allen Updates):
-- alle User: pu_email != '', auth_user_id != NULL, auth_missing = false
-- bad_empty = false für alle Zeilen

-- ────────────────────────────────────────────────────────────
-- 5. Smoke nach Fix (im Browser Console als Admin):
-- ────────────────────────────────────────────────────────────
-- F5 → Login mit schober/test1234
-- Erwartung: Login-Success, Dashboard erscheint, _authToken ist JWT
--   localStorage.getItem('epkolar_token').length > 200
-- Falls Login bei u1/u2/u3 failt: UUIDs in Schritt 3 prüfen.
