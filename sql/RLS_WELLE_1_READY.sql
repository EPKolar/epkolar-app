-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar RLS-Härtung Welle 1 — READY-TO-EXECUTE (2026-06-12)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ▶ KEINE Automation. Sebastian fuehrt im Supabase-SQL-Editor blockweise aus.
-- ▶ Pro Block: BEGIN ... COMMIT. Bei Auffaelligkeit ROLLBACK statt COMMIT.
-- ▶ Nach jedem Block: 30-min-Smoke gemaess docs/SMOKE_v3.9.31x.md (Punkte a-p).
-- ▶ Welle 1 = LOW-Risk. Verschaerft Schreibrechte fuer Tabellen ohne
--   Anon-Zugriff und ohne Auswirkung auf Monteur-Grundfunktionen.
--
-- AUSGANGSLAGE (Annahme):
--   * Eine ALL-Policy `<table>_all` mit qual=true existiert pro Tabelle ODER
--   * Eine SELECT-Policy `<table>_select_all` (oder aehnlich) lesend offen.
--
-- VOR EINFUEHRUNG je Block:
--   SELECT polname, polcmd, polqual FROM pg_policies WHERE schemaname='public' AND tablename='<table>';
--   → Existierende Policies dokumentieren, fuer Rollback merken.
--
-- ROLLBACK je Block (falls noetig):
--   DROP POLICY IF EXISTS "<new_name>" ON public.<table>;
--   CREATE POLICY "<table>_all" ON public.<table> FOR ALL TO authenticated USING (true);
--
-- CLIENT-SEITE (v3.9.323):
--   _RLS_SILENT_DENIAL_LABELS in index.html Z.~1885 deckt fahrzeuge, time_entries,
--   forms, bautagebuch, fz_schaeden ab → 0-rows-Toast ohne stillen Verlust.
--
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.1) fahrzeuge — UPDATE auf Office ODER eigenen Eintrag
-- Risiko: LOW (Disponent-Querblick + Monteur-Eigenfahrzeug erhalten)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "fahrzeuge_all" ON public.fahrzeuge;
CREATE POLICY "fahrzeuge_select_authed" ON public.fahrzeuge
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "fahrzeuge_update_office_or_owner" ON public.fahrzeuge
  FOR UPDATE TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
    OR fahrer = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
  );
CREATE POLICY "fahrzeuge_insert_office" ON public.fahrzeuge
  FOR INSERT TO authenticated WITH CHECK (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
  );
CREATE POLICY "fahrzeuge_delete_admin" ON public.fahrzeuge
  FOR DELETE TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter'))
  );
COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.2) time_entries — WRITE auf own ODER Office
-- Risiko: LOW (v3.9.307-Client-Edit-Button hat canDo('zeit_other')-Guard)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "time_entries_all" ON public.time_entries;
DROP POLICY IF EXISTS "entries_all" ON public.time_entries;
CREATE POLICY "time_entries_select_authed" ON public.time_entries
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "time_entries_insert_own_or_office" ON public.time_entries
  FOR INSERT TO authenticated WITH CHECK (
    worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
    OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
              AND u.role IN ('admin','projektleiter','buero'))
  );
CREATE POLICY "time_entries_update_own_or_office" ON public.time_entries
  FOR UPDATE TO authenticated USING (
    worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
    OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
              AND u.role IN ('admin','projektleiter','buero'))
  );
CREATE POLICY "time_entries_delete_own_or_office" ON public.time_entries
  FOR DELETE TO authenticated USING (
    worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
    OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
              AND u.role IN ('admin','projektleiter'))
  );
COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.3) forms — WRITE auf Projekt-Zuweisung ODER Office
-- (regie/sf/dh/ah/abnahme/checklisten sind sub-types via type-Spalte)
-- Risiko: LOW (interne Tabelle, kein Anon-Zugriff)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "forms_all" ON public.forms;
CREATE POLICY "forms_select_authed" ON public.forms
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "forms_write_assigned_or_office" ON public.forms
  FOR ALL TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.monteur_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
              AND wp.project_id = forms.pid)
  );
COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.4) bautagebuch — analog forms
-- Risiko: LOW
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "bautagebuch_all" ON public.bautagebuch;
CREATE POLICY "bautagebuch_select_authed" ON public.bautagebuch
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "bautagebuch_write_assigned_or_office" ON public.bautagebuch
  FOR ALL TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.monteur_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
              AND wp.project_id = bautagebuch.pid)
  );
COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.5) fz_schaeden — Schadensmeldungen auf eigenes Fahrzeug ODER Office
-- Risiko: LOW (Monteur darf eigenes Fahrzeug melden, kein Quertest)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "fz_schaeden_all" ON public.fz_schaeden;
CREATE POLICY "fz_schaeden_select_authed" ON public.fz_schaeden
  FOR SELECT TO authenticated USING (true);
CREATE POLICY "fz_schaeden_write_owner_or_office" ON public.fz_schaeden
  FOR ALL TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
    OR EXISTS(SELECT 1 FROM public.fahrzeuge f WHERE f.id = fz_schaeden.fz_id
              AND f.fahrer = (SELECT monteur_id FROM public.users WHERE id = auth.uid()))
  );
COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.6) fahrbewilligungen — SELECT auf own ODER Office
-- Risiko: LOW (Self-Zugriff bleibt, MitarbeiterView-Aggregator v3.9.312 funktioniert)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "fahrbewilligungen_select_all" ON public.fahrbewilligungen;
DROP POLICY IF EXISTS "fahrbewilligungen_all" ON public.fahrbewilligungen;
CREATE POLICY "fahrbewilligungen_select_own_or_office" ON public.fahrbewilligungen
  FOR SELECT TO authenticated USING (
    worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
    OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
              AND u.role IN ('admin','projektleiter','buero'))
  );
CREATE POLICY "fahrbewilligungen_write_office" ON public.fahrbewilligungen
  FOR ALL TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
  );
COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.7) anmeldungen — analog fahrbewilligungen
-- Risiko: LOW
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "anmeldungen_select_all" ON public.anmeldungen;
DROP POLICY IF EXISTS "anmeldungen_all" ON public.anmeldungen;
CREATE POLICY "anmeldungen_select_own_or_office" ON public.anmeldungen
  FOR SELECT TO authenticated USING (
    worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
    OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
              AND u.role IN ('admin','projektleiter','buero'))
  );
CREATE POLICY "anmeldungen_write_office" ON public.anmeldungen
  FOR ALL TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
  );
COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.8) finkzeit — SELECT nur Office (Standby seit 04.06.2026)
-- Risiko: LOW (Feature ist standby, nur Doku-Zugriff fuer Office)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;
DROP POLICY IF EXISTS "finkzeit_select_all" ON public.finkzeit;
DROP POLICY IF EXISTS "finkzeit_all" ON public.finkzeit;
CREATE POLICY "finkzeit_select_office_only" ON public.finkzeit
  FOR SELECT TO authenticated USING (
    EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
           AND u.role IN ('admin','projektleiter','buero'))
  );
COMMIT;


-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFIKATIONS-QUERIES (nach jedem Block ausfuehren)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Welche Policies sind aktiv:
--   SELECT polname, polcmd, polqual::text AS qual
--   FROM pg_policies WHERE schemaname='public' AND tablename='<table>'
--   ORDER BY polcmd, polname;
--
-- Test als Monteur (mit Test-Account):
--   SET LOCAL ROLE authenticated;
--   SET LOCAL "request.jwt.claim.sub" TO '<monteur-uuid>';
--   UPDATE public.fahrzeuge SET kmStand = kmStand + 1 WHERE fahrer = '<fremd>';
--   → Erwartung: 0 Zeilen aktualisiert (RLS lehnt ab).
--
-- ═══════════════════════════════════════════════════════════════════════════
-- POST-WELLE-1 SMOKE (vom Client aus):
-- ═══════════════════════════════════════════════════════════════════════════
--
-- 1. Als Monteur in der App einloggen.
-- 2. Eigenes Fahrzeug → ⛽ Tankung → speichern. → Toast "⛽ Tankung erfasst".
-- 3. Fremdes Fahrzeug oeffnen → ⛽ Tankung → speichern.
--    → Erwartung Toast "⚠️ Fahrzeug-Aenderung NICHT gespeichert — keine Schreibberechtigung"
-- 4. Eigenen Zeiteintrag bearbeiten → Stunden aendern → speichern → ok.
-- 5. Fremden Zeiteintrag bearbeiten (Admin schaltet Office-Edit fuer Monteur ab) →
--    Erwartung Toast "⚠️ Zeiteintrag NICHT gespeichert — keine Schreibberechtigung"
-- 6. Fahrbewilligung des Kollegen oeffnen via Direkt-URL → leer/403.
-- 7. Finkzeit-Tab nicht sichtbar fuer Nicht-Office (oder leer).
--
-- Alle 7 Punkte gruen → Welle 1 stabil → Welle 2 vorbereiten (siehe BACKLOG_v1).
-- ═══════════════════════════════════════════════════════════════════════════
