-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ═══════════════════════════════════════════════════════════════════════════
-- AUFGABE #4 — activity_log redundante anon-INSERT-Policy droppen (v3.9.213)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- VORLAGE / BASIS: sql/migrate_activity_log_anon_drop_v3110.sql (v3.10.5-Spec).
--   Diese Datei ist die SCHLANKE, IDEMPOTENTE Bestaetigungs-/Konsolidierungs-
--   Migration. Sie macht dasselbe re-runnable und ohne Snapshot-Tabellen-
--   Seiteneffekt. Falls die v3110-Migration bereits angewendet wurde, ist
--   diese Datei ein No-Op (DROP IF EXISTS + idempotenter CREATE).
--
-- ── CODE-PFAD-EVIDENZ (index.html @ v3.9.213, Commit fa9d37a) ───────────────
--   ALLE activity_log-Writes laufen AUTHENTICATED (Bearer <_authToken> via
--   _sbH→_sbWH/_sbPost). KEIN anon-INSERT-Pfad existiert:
--     Z2249  Login-Audit   _sbPost("activity_log",...)  — explizit `if(_authToken)`-gated, NACH GoTrue-Auth
--     Z2344  Error-Throttle fetch(... headers:_sbWH())  — authenticated
--     Z2954  juprowa_pull  _sbPost("activity_log",...)  — user-JWT
--     Z3134  juprowa_push  _sbPost("activity_log",...)  — user-JWT
--     Z4609  view_boundary fetch(... headers:_sbWH())   — authenticated
--     Z19246 react_error   fetch(... headers:_sbWH())   — authenticated
--   _sbH() injiziert immer "Authorization: Bearer "+_authToken (anon nur als
--   Fallback bei fehlendem Token; Login-Audit ist hart `if(_authToken)`-gated).
--   → Die anon-INSERT-Policy `activity_log_anon_insert` ist redundant/Leak-Flaeche.
--
-- ── ANNAHME / VERIFY-PFLICHT ────────────────────────────────────────────────
--   Es wird angenommen, dass die authenticated-INSERT-Policy entweder
--   `activity_log_insert_authenticated` heisst (wie in v3110 gesetzt) ODER hier
--   sicher (re-)erstellt wird. Falls in der Live-DB eine ABWEICHEND benannte
--   authenticated-INSERT-Policy existiert, bleibt sie unberuehrt (kein Conflict).
--   Operator: vor Apply einmal `\d+`/pg_policies pruefen (siehe VERIFY unten).

-- ── 1. Redundante anon-INSERT-Policy droppen (idempotent) ───────────────────
DROP POLICY IF EXISTS activity_log_anon_insert ON public.activity_log;

-- ── 2. Defense-in-Depth: authenticated-INSERT-Policy sicherstellen ──────────
--   "CREATE POLICY IF NOT EXISTS" ist KEIN gueltiges PostgreSQL (vgl. v3110-Lesson
--   v3.9.105). Daher DROP IF EXISTS + CREATE = idempotent & re-runnable.
DROP POLICY IF EXISTS activity_log_insert_authenticated ON public.activity_log;
CREATE POLICY activity_log_insert_authenticated
  ON public.activity_log
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFY (manuell nach Apply ausfuehren):
-- ═══════════════════════════════════════════════════════════════════════════
-- a) Policies inspizieren — es darf KEINE anon/public-INSERT-Policy mehr geben,
--    aber eine authenticated-INSERT-Policy muss existieren:
--      SELECT polname, roles, cmd, with_check
--      FROM pg_policies
--      WHERE schemaname='public' AND tablename='activity_log';
--    Erwartung: kein 'activity_log_anon_insert'; vorhandenes
--               'activity_log_insert_authenticated' (roles={authenticated}, cmd=INSERT).
--
-- b) anon POST → muss 403 liefern (anon-Key als apikey + Authorization):
--      curl -s -o /dev/null -w "%{http_code}\n" -X POST \
--        "$SUPABASE_URL/rest/v1/activity_log" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY" \
--        -H "Content-Type: application/json" \
--        -d '{"user_id":"00000000-0000-0000-0000-000000000000","action":"verify_anon"}'
--      Erwartung: 403  (bzw. 401/42501 — KEIN 201).
--
-- c) authenticated POST → muss 201 liefern (gueltiger User-JWT):
--      curl -s -o /dev/null -w "%{http_code}\n" -X POST \
--        "$SUPABASE_URL/rest/v1/activity_log" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $USER_JWT" \
--        -H "Content-Type: application/json" -H "Prefer: return=representation" \
--        -d '{"user_id":"<auth-user-uuid>","action":"verify_auth"}'
--      Erwartung: 201.
--
-- d) Login-Audit (index.html Z2249) laeuft weiter: nach echtem App-Login
--    erscheint eine neue Zeile action='login' in activity_log
--    (sie wird AUTHENTICATED geschrieben → Policy aus Schritt 2 deckt sie ab).
-- ═══════════════════════════════════════════════════════════════════════════
