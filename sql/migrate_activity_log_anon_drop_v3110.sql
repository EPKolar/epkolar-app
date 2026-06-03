-- ═══════════════════════════════════════════════════════════
-- v3.10.5 activity_log_anon_insert DROP (Sebastian-Spec)
-- ═══════════════════════════════════════════════════════════
--
-- CODE-PFAD-ANALYSE: alle activity_log POSTs in index.html nutzen _sbWH() / _sbPost
--   (mit authenticated JWT). KEIN anon-Pfad gefunden:
--   Z2199 Login-Audit: _sbPost("activity_log",...) — NACH erfolgreichem Auth
--   Z2287 Error-Log-Throttle: _sbWH() — authenticated
--   Z2852/3032 Juprowa-Audits: _sbPost mit user-JWT
--   Z4432 view_boundary: _sbWH()
--   Z18489 react_error: _sbWH()
--
-- → activity_log_anon_insert NICHT vom Login-Pfad benötigt. Kann gedroppt werden.

CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3110 (
  ts timestamptz DEFAULT now(), tablename text, polname text, roles text[],
  cmd text, qual text, with_check text
);

INSERT INTO public._rls_snapshot_v3110 (tablename, polname, roles, cmd, qual, with_check)
SELECT tablename, polname, roles, cmd, qual, with_check
FROM pg_policies WHERE schemaname='public' AND tablename='activity_log';

-- Drop anon-INSERT
DROP POLICY IF EXISTS activity_log_anon_insert ON public.activity_log;

-- Defense-in-Depth: Ensure authenticated INSERT
CREATE POLICY IF NOT EXISTS activity_log_insert_authenticated
  ON public.activity_log FOR INSERT TO authenticated
  WITH CHECK (true);

-- VERIFY:
-- 1. anon POST /activity_log → 403
-- 2. authenticated POST /activity_log → 201
-- 3. Login-Audit Z2199 läuft weiter (authenticated)
