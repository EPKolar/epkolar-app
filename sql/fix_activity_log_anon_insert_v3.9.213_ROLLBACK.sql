-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK fuer fix_activity_log_anon_insert_v3.9.213.sql
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ⚠️ WARNUNG: Dieses Rollback stellt eine anon-INSERT-Policy auf activity_log
--    WIEDER HER. Das oeffnet erneut einen anon-Schreibpfad (Telemetrie-DoS /
--    Spam-Flaeche) und sollte NUR ausgefuehrt werden, wenn ein unerwarteter
--    Regress (z.B. legitime anon-Writes, die NICHT existieren sollten) auftritt.
--
--    Die authenticated-INSERT-Policy bleibt fuer den normalen Betrieb bestehen;
--    sie wird hier NICHT entfernt, da der Login-Audit (index.html Z2249) und
--    alle anderen Writes sie zwingend brauchen.
--
-- ── EXAKTE LIVE-DEFINITION DER ANON-POLICY UNBEKANNT ────────────────────────
--   PFLICHT-CAPTURE vor Apply dieses Rollbacks:
--     Falls der v3110-Snapshot existiert, die Original-Def daraus ziehen:
--       SELECT polname, roles, cmd, qual, with_check
--       FROM public._rls_snapshot_v3110
--       WHERE tablename='activity_log' AND polname='activity_log_anon_insert';
--     Sonst: pg_policies VOR dem urspruenglichen Drop dokumentieren.
--   Der WITH-CHECK-Ausdruck unten ist eine REKONSTRUKTION (Annahme: offenes
--   `true`, wie bei einer reinen Telemetrie-anon-Insert-Policy ueblich) —
--   VOR APPLY GEGEN DEN SNAPSHOT / DIE LIVE-HISTORIE VERIFIZIEREN UND BEI
--   ABWEICHUNG DIE EXAKTE ORIGINAL-DEFINITION EINSETZEN.

DROP POLICY IF EXISTS activity_log_anon_insert ON public.activity_log;
CREATE POLICY activity_log_anon_insert
  ON public.activity_log
  FOR INSERT
  TO anon
  WITH CHECK (true);   -- REKONSTRUKTION — vor Apply gegen Live/Snapshot verifizieren

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFY (nach Rollback):
--   SELECT polname, roles, cmd, with_check FROM pg_policies
--   WHERE schemaname='public' AND tablename='activity_log';
--   Erwartung: 'activity_log_anon_insert' (roles={anon}) wieder vorhanden.
-- ═══════════════════════════════════════════════════════════════════════════
