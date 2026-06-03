-- ═══════════════════════════════════════════════════════════
-- v3.9.99 Kiener-Reparatur (Sebastian-Spec 2026-06-03)
-- IST: users.kiener exists aber monteur_id=NULL + auth_user_id=NULL
--      workers.id='mpxpwdhrht1b' (Random-ID) separat angelegt
--      Namen inkonsistent: workers="Kiener" vs users="Bernd Kiener"
-- SOLL: konsistente Verknüpfung + Naming-Konvention "Nachname Vorname"
-- ═══════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════
-- BLOCK 0: Diagnose (read-only, VOR Run prüfen)
-- ═══════════════════════════════════════════════════════════

-- 0.1 Kiener users-Row
-- SELECT id, username, name, email, role, monteur_id, auth_user_id, active
-- FROM public.users WHERE username='kiener';

-- 0.2 Kiener workers-Row
-- SELECT id, name, role, email, active
-- FROM public.workers WHERE name ILIKE '%kiener%';

-- 0.3 Auth-User für kiener
-- SELECT id, email, encrypted_password IS NOT NULL AS has_pw
-- FROM auth.users WHERE email='kiener@ep-kolar.at';

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Falls auth.users-Row EXISTIERT → users.auth_user_id setzen
-- ═══════════════════════════════════════════════════════════

UPDATE public.users u
SET auth_user_id = a.id
FROM auth.users a
WHERE u.username = 'kiener'
  AND a.email = 'kiener@ep-kolar.at'
  AND (u.auth_user_id IS NULL OR u.auth_user_id <> a.id);

-- Verify:
-- SELECT username, auth_user_id FROM public.users WHERE username='kiener';
-- Falls auth_user_id immer noch NULL → auth.users-Row fehlt!
-- → Via Supabase Dashboard Auth → Add user kiener@ep-kolar.at mit Test1234! + auto-confirm
-- → Dann diesen UPDATE-Block erneut ausführen

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: users.monteur_id auf workers.id verknüpfen
-- ═══════════════════════════════════════════════════════════

-- Sebastian-Spec: workers.id = 'mpxpwdhrht1b' (live verifiziert)
UPDATE public.users
SET monteur_id = 'mpxpwdhrht1b'
WHERE username = 'kiener'
  AND (monteur_id IS NULL OR monteur_id <> 'mpxpwdhrht1b');

-- Auto-discovery fallback (falls workers-ID anders):
-- UPDATE public.users u SET monteur_id = w.id
-- FROM public.workers w
-- WHERE u.username='kiener' AND w.name ILIKE '%kiener%' AND u.monteur_id IS NULL;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: Naming-Konvention "Nachname Vorname"
-- ═══════════════════════════════════════════════════════════

UPDATE public.workers
SET name = 'Kiener Bernd'
WHERE id = 'mpxpwdhrht1b'
  AND name <> 'Kiener Bernd';

UPDATE public.users
SET name = 'Kiener Bernd'
WHERE username = 'kiener'
  AND name <> 'Kiener Bernd';

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: Verify
-- ═══════════════════════════════════════════════════════════

-- SELECT
--   u.id AS user_id, u.username, u.name AS user_name, u.email, u.role, u.active,
--   u.monteur_id, u.auth_user_id,
--   w.id AS worker_id, w.name AS worker_name, w.role AS worker_role,
--   a.id AS auth_id, a.encrypted_password IS NOT NULL AS auth_has_pw,
--   CASE
--     WHEN u.auth_user_id IS NOT NULL AND u.monteur_id IS NOT NULL AND u.name = w.name
--     THEN '✓ KOMPLETT'
--     ELSE '⚠ unvollständig'
--   END AS status
-- FROM public.users u
-- LEFT JOIN public.workers w ON w.id = u.monteur_id
-- LEFT JOIN auth.users a ON a.id = u.auth_user_id
-- WHERE u.username = 'kiener';

-- Erwartet nach Run: status='✓ KOMPLETT'

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK
-- ═══════════════════════════════════════════════════════════
/*
UPDATE public.users SET monteur_id = NULL, auth_user_id = NULL
WHERE username = 'kiener';
UPDATE public.workers SET name = 'Kiener' WHERE id = 'mpxpwdhrht1b';
UPDATE public.users SET name = 'Bernd Kiener' WHERE username = 'kiener';
*/
