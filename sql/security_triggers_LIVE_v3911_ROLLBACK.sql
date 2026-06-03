-- ============================================================================
-- ROLLBACK der 5 Live-Security-Trigger (security_triggers_LIVE_v3911.sql)
-- Sebastian/Chat-Claude, Service-Role. Entfernt Trigger + Funktionen.
-- ⚠️ Danach sind absences/urlaubskontingent/users/system_config/projects NICHT mehr
--    trigger-geschützt (RLS bleibt ggf. aktiv). Nur im Notfall ausführen.
-- ============================================================================
BEGIN;

DROP TRIGGER IF EXISTS trg_guard_urlaub_absences ON public.absences;
DROP TRIGGER IF EXISTS trg_guard_kontingent      ON public.urlaubskontingent;
DROP TRIGGER IF EXISTS trg_guard_users_privilege ON public.users;
DROP TRIGGER IF EXISTS trg_guard_system_config   ON public.system_config;
DROP TRIGGER IF EXISTS trg_guard_projects        ON public.projects;

DROP FUNCTION IF EXISTS public.guard_urlaub_edit();
DROP FUNCTION IF EXISTS public.guard_kontingent();
DROP FUNCTION IF EXISTS public.guard_users_privilege();
DROP FUNCTION IF EXISTS public.guard_admin_only();
DROP FUNCTION IF EXISTS public.guard_projects();

COMMIT;
