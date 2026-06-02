-- v3.9.59 Bernd Kiener — Neuer Monteur User-Setup (Schema-corrected nach Sebastian-Spec)
-- worker_id/user_id = u10/w10, username=kiener, role=monteur, name="Kiener Bernd"
-- Jahresurlaub 192,5h / 38,5h-Woche
-- public.users.password_hash mit auth.users.encrypted_password synchronisieren (bcrypt)
--
-- Voraussetzung: auth.users-Row existiert bereits (Sebastian-Action vorab):
--   Supabase Dashboard → Authentication → Users → Add user
--   Email: kiener@ep-kolar.at, Password: <Sebastian-Choice>, Auto Confirm: ON
--
-- DANN das hier ausführen (Sebastian ersetzt :AUTH_UUID mit der UUID aus auth.users):
--   sed -i 's/:AUTH_UUID/aaaa-bbbb-…/' migrate_user_kiener_v3959.sql
-- Oder via psql: \set AUTH_UUID 'aaaa-bbbb-…'
--
-- Idempotent — kann mehrfach ausgeführt werden (ON CONFLICT DO NOTHING/UPDATE).

-- ═══════════════════════════════════════════════════════════════════
-- BLOCK 1: workers (Monteur-Stammdaten)
-- Schema: id, name (kombiniert), role, email, active
-- HINWEIS: "woche" ist KEINE Spalte auf workers — siehe Sebastian-Reserve-Spec
-- ═══════════════════════════════════════════════════════════════════

INSERT INTO public.workers (id, name, role, email, active)
VALUES ('w10', 'Kiener Bernd', 'monteur', 'kiener@ep-kolar.at', 1)
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  role = EXCLUDED.role,
  email = EXCLUDED.email,
  active = EXCLUDED.active;

-- ═══════════════════════════════════════════════════════════════════
-- BLOCK 2: public.users (App-User)
-- auth_user_id wird mit der UUID aus auth.users verlinkt
-- ═══════════════════════════════════════════════════════════════════

INSERT INTO public.users (id, username, name, email, role, monteur_id, active, auth_user_id)
VALUES ('u10', 'kiener', 'Kiener Bernd', 'kiener@ep-kolar.at', 'monteur', 'w10', 1, ':AUTH_UUID')
ON CONFLICT (id) DO UPDATE SET
  username = EXCLUDED.username,
  name = EXCLUDED.name,
  email = EXCLUDED.email,
  role = EXCLUDED.role,
  monteur_id = EXCLUDED.monteur_id,
  active = EXCLUDED.active,
  auth_user_id = EXCLUDED.auth_user_id;

-- Falls :AUTH_UUID NICHT manuell ersetzt wurde, kann die Verknüpfung auch
-- per Email-Lookup nachgeholt werden:
UPDATE public.users u
SET auth_user_id = a.id
FROM auth.users a
WHERE u.id = 'u10' AND a.email = 'kiener@ep-kolar.at'
  AND (u.auth_user_id IS NULL OR u.auth_user_id::text = ':AUTH_UUID');

-- ═══════════════════════════════════════════════════════════════════
-- BLOCK 3: urlaubskontingent
-- Schema: id, worker_id, worker_name, jahr, urlaub (Tage), vorjahr,
--         stunden (192.5), woche (38.5)
-- 25 Tage × 7,7h (38,5h ÷ 5) = 192,5h
-- ═══════════════════════════════════════════════════════════════════

INSERT INTO public.urlaubskontingent
  (id, worker_id, worker_name, jahr, urlaub, vorjahr, stunden, woche)
VALUES ('u10', 'u10', 'Kiener Bernd', 2026, 25, 0, 192.5, 38.5)
ON CONFLICT (id) DO UPDATE SET
  worker_id = EXCLUDED.worker_id,
  worker_name = EXCLUDED.worker_name,
  jahr = EXCLUDED.jahr,
  urlaub = EXCLUDED.urlaub,
  vorjahr = EXCLUDED.vorjahr,
  stunden = EXCLUDED.stunden,
  woche = EXCLUDED.woche;

-- ═══════════════════════════════════════════════════════════════════
-- BLOCK 4: login_lookup (Username→Email für RPC B020-A login_lookup)
-- Optional, nur wenn diese Tabelle in deinem Schema existiert.
-- Falls Login direkt über auth.users.email läuft, ist BLOCK 4 nicht nötig.
-- ═══════════════════════════════════════════════════════════════════

-- INSERT INTO public.login_lookup (username, email, user_id, active)
-- VALUES ('kiener', 'kiener@ep-kolar.at', 'u10', 1)
-- ON CONFLICT (username) DO UPDATE SET
--   email = EXCLUDED.email, user_id = EXCLUDED.user_id, active = EXCLUDED.active;

-- ═══════════════════════════════════════════════════════════════════
-- BLOCK 5: password_hash Sync auth.users.encrypted_password → public.users
-- bcrypt-Hash für lokalen Offline-Login-Fallback (_OFFPW.verify nutzt diesen
-- wenn navigator.onLine=false UND _authToken fehlt)
-- ═══════════════════════════════════════════════════════════════════

UPDATE public.users u
SET password_hash = a.encrypted_password
FROM auth.users a
WHERE u.id = 'u10'
  AND a.email = 'kiener@ep-kolar.at'
  AND a.encrypted_password IS NOT NULL
  AND (u.password_hash IS NULL OR u.password_hash <> a.encrypted_password);

-- ═══════════════════════════════════════════════════════════════════
-- BLOCK 6: Verifikation (read-only — Output zur Kontrolle)
-- ═══════════════════════════════════════════════════════════════════

-- SELECT
--   u.id, u.username, u.name, u.email, u.role, u.active,
--   u.monteur_id, u.auth_user_id,
--   CASE WHEN u.password_hash IS NULL THEN '⚠ kein PW-Hash — auth.users existiert? encrypted_password gesetzt?'
--        ELSE '✓ PW-Hash gesynct' END AS pw_status,
--   w.name AS worker_name, w.role AS worker_role, w.active AS worker_active,
--   k.urlaub AS urlaub_tage, k.stunden AS urlaub_stunden, k.woche AS arbeitswoche_h, k.jahr,
--   a.email AS auth_email, a.created_at AS auth_created
-- FROM public.users u
-- LEFT JOIN public.workers w ON w.id = u.monteur_id
-- LEFT JOIN public.urlaubskontingent k ON k.worker_id = u.monteur_id AND k.jahr = 2026
-- LEFT JOIN auth.users a ON a.id = u.auth_user_id
-- WHERE u.id = 'u10';

-- ═══════════════════════════════════════════════════════════════════
-- ROLLBACK (manuell, NICHT automatisch — Reihenfolge wegen FK-Constraints):
-- DELETE FROM public.urlaubskontingent WHERE id='u10';
-- DELETE FROM public.users WHERE id='u10';
-- DELETE FROM public.workers WHERE id='w10';
-- -- auth.users separat im Dashboard löschen
-- ═══════════════════════════════════════════════════════════════════
