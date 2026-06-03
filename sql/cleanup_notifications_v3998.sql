-- ═══════════════════════════════════════════════════════════
-- v3.9.98 notifications Mass-Cleanup (5775 Rows bei 9 Usern)
-- Sebastian-Spec 2026-06-03: vorbereiten, NICHT runnen ohne Freigabe
-- ═══════════════════════════════════════════════════════════
--
-- KONTEXT:
-- - 5775 notifications-Rows bei 9 Usern (640 avg pro User)
-- - 2164 davon vor Mai 2026 (historische Akkumulation)
-- - KEIN Auto-Cleanup/TTL im Code (siehe BUG-VERFOLGUNG-v3998.md PRIO 2)
-- - pushNotif Fan-Out pro Target → N Rows pro Event
-- - localStorage-Cooldown 4h kann gecleared werden → Re-Fire möglich

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Diagnose vor Cleanup
-- ═══════════════════════════════════════════════════════════

-- 1.1 Verteilung pro User
-- SELECT user_id, count(*) AS total,
--        count(*) FILTER (WHERE read=1) AS read,
--        count(*) FILTER (WHERE read=0) AS unread,
--        min(created_at) AS earliest,
--        max(created_at) AS latest
-- FROM public.notifications
-- GROUP BY user_id
-- ORDER BY total DESC;

-- 1.2 Verteilung pro Type
-- SELECT type, count(*) AS total
-- FROM public.notifications
-- GROUP BY type
-- ORDER BY total DESC;

-- 1.3 Vor Mai 2026
-- SELECT count(*) FROM public.notifications WHERE created_at < '2026-05-01';

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: Backup zuerst
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.notifications_backup_v3998 AS
  SELECT * FROM public.notifications WHERE 1=0;

INSERT INTO public.notifications_backup_v3998
  SELECT * FROM public.notifications;

-- Verify
-- SELECT count(*) FROM public.notifications_backup_v3998;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: Cleanup-Strategien (3 Optionen — Sebastian-Decision)
-- ═══════════════════════════════════════════════════════════

-- ── OPTION A: Konservativ — read=true UND älter 30 Tage
-- (read=false bleibt, recent bleibt — minimal-Risiko)

-- DELETE FROM public.notifications
-- WHERE read = 1
--   AND created_at < (now() - interval '30 days');

-- Erwarteter Cleanup: ~2000 Rows
-- Restbestand: ~3700 Rows

-- ── OPTION B: Aggressiv — alles vor Mai 2026 löschen
-- (auch ungelesene)

-- DELETE FROM public.notifications
-- WHERE created_at < '2026-05-01';

-- Erwarteter Cleanup: 2164 Rows
-- Restbestand: 3611 Rows

-- ── OPTION C: Hybrid — alles read=true plus ungelesene älter 60 Tage
-- (sicherer Mittelweg, behält recent unread + alles read-cleared)

DELETE FROM public.notifications
WHERE read = 1
   OR (read = 0 AND created_at < (now() - interval '60 days'));

-- Erwarteter Cleanup: ~4000-5000 Rows
-- Restbestand: ~500-1000 Rows (nur recent unread)

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: Auto-Cleanup-Trigger (Future-Proofing)
-- ═══════════════════════════════════════════════════════════
-- TTL via scheduled job (pg_cron, falls verfügbar)

-- CREATE OR REPLACE FUNCTION public.cleanup_old_notifications()
-- RETURNS void AS $$
-- BEGIN
--   DELETE FROM public.notifications
--   WHERE read = 1
--     AND created_at < (now() - interval '30 days');
-- END;
-- $$ LANGUAGE plpgsql;

-- Scheduled (pg_cron extension nötig):
-- SELECT cron.schedule('cleanup-notifications', '0 3 * * *', 'SELECT public.cleanup_old_notifications();');

-- ALTERNATIV: Insert-Side Rate-Limit-Trigger
-- (max 1 pro user_id+type pro 4h-Fenster)
-- CREATE OR REPLACE FUNCTION public.notifications_rate_limit()
-- RETURNS trigger AS $$
-- BEGIN
--   IF EXISTS(
--     SELECT 1 FROM public.notifications
--     WHERE user_id = NEW.user_id
--       AND type = NEW.type
--       AND created_at > (now() - interval '4 hours')
--   ) THEN
--     RAISE NOTICE 'Rate-limited notification: user=%, type=%', NEW.user_id, NEW.type;
--     RETURN NULL;  -- Insert skip
--   END IF;
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;
--
-- CREATE TRIGGER tr_notifications_rate_limit
-- BEFORE INSERT ON public.notifications
-- FOR EACH ROW EXECUTE FUNCTION public.notifications_rate_limit();

-- ═══════════════════════════════════════════════════════════
-- VERIFY
-- ═══════════════════════════════════════════════════════════
-- SELECT count(*) AS total_remaining,
--        count(*) FILTER (WHERE read=0) AS unread,
--        max(created_at) AS latest
-- FROM public.notifications;

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK (nur wenn nötig)
-- ═══════════════════════════════════════════════════════════
/*
TRUNCATE public.notifications;
INSERT INTO public.notifications SELECT * FROM public.notifications_backup_v3998;
DROP TABLE public.notifications_backup_v3998;
*/
