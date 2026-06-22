-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar RLS-Härtung Welle 1 v4 — READY-TO-EXECUTE (2026-06-22)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ▶ STATUS DES LIVE-APPLYS (Stand 22.06.2026):
--     ✅ Block 0.5 is_hr() Bootstrap        — applied (12.06.2026)
--     ✅ Block 1.1 fahrzeuge                — applied
--     ✅ Block 1.2 time_entries             — applied
--     ⏳ Block 1.3 forms                    — KORRIGIERT in v4, wartet auf Apply
--     ⏳ Block 1.4 bautagebuch              — KORRIGIERT in v4, wartet auf Apply
--     🚫 Block 1.5 fz_schaeden              — ENTFÄLLT (Tabelle existiert NICHT)
--     ⏳ Block 1.6 fahrbewilligungen        — wartet auf Apply (Spalten OK)
--     ⏳ Block 1.7 anmeldungen              — wartet auf Apply (Pre-Check nötig)
--     ⏳ Block 1.8 finkzeit                 — wartet auf Apply
--
-- ▶ KORREKTUREN gegenüber v3 (DEPRECATED — siehe Header dort):
--   Chat-Claude Pre-Check (live, information_schema) am 22.06.2026 ergab:
--
--   v3 nutzte ...                       Real (information_schema) ...
--   ─────────────────────────────────   ─────────────────────────────────
--   worker_projects.monteur_id          worker_projects.worker_id
--   forms.pid                           forms.project_id
--   bautagebuch.pid                     bautagebuch.project_id
--   fz_schaeden (Tabelle)               EXISTIERT NICHT — Block 1.5 entfällt
--   fahrbewilligungen.worker_id         OK ✓ unverändert
--
--   anmeldungen.<spalte> und finkzeit.<spalte> wurden in v4 NICHT geändert
--   (Spaltennamen vor Apply mit information_schema-Pre-Check verifizieren).
--
-- ▶ HINTERGRUND zu fz_schaeden: laut v3.9.427/430 (App-Changelog) wurde der
--   Zweitspeicher fz_schaeden-Tabelle gedropped. Single-Source ist seither das
--   `fahrzeuge.schaeden` jsonb-Feld. Block 1.5 in v3 wäre auf eine nicht-
--   existente Tabelle gegangen und hätte den ganzen DO-Block crashen lassen.
--
-- ▶ KEIN DROP von Policies wie "fahrzeuge_update_driver" — die ist additiv und
--   bleibt. Loop droppt nur qual=true (= alle authentifizierten unrestricted).
--
-- ▶ Sebastian fuehrt im Supabase-SQL-Editor blockweise aus. Jeder Block in
--   BEGIN/COMMIT. Bei JEDEM Fehler ROLLBACK + Halt + Befund melden.
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- VORAB-VERIFIKATION (READ-ONLY) — pre-check VOR jedem Block
-- ───────────────────────────────────────────────────────────────────────────
--
-- 1) DB-Identität (Worker-Guard):
--    SELECT count(*) FROM public.workers;            -- Erwartet: 10
--    SELECT count(*) FROM public.supplier_articles;  -- Erwartet: ~25118
--    SELECT to_regclass('public.fahrzeuge') IS NOT NULL AS exists; -- Erwartet: t
--
-- 2) v4-Spalten-Verifikation (gegen v3-Mismatches):
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='worker_projects'
--    ORDER BY ordinal_position;
--    -- ERWARTET: id, worker_id, project_id, projects, role, assigned_at
--    -- (NICHT: monteur_id wie in v3 angenommen)
--
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='forms'
--    ORDER BY ordinal_position;
--    -- ERWARTET: id, project_id, name, form_type, ...
--    -- (NICHT: pid wie in v3 angenommen)
--
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='bautagebuch'
--    ORDER BY ordinal_position;
--    -- ERWARTET: id, project_id, datum, ...
--    -- (NICHT: pid wie in v3 angenommen)
--
--    SELECT to_regclass('public.fz_schaeden');
--    -- ERWARTET: NULL (Tabelle gedroppt seit v3.9.427/430 → Block 1.5 entfällt)
--
-- 3) Helper-Funktionen vorhanden:
--    SELECT proname, prosecdef, provolatile
--    FROM pg_proc WHERE proname IN ('is_hr','current_monteur_id','auth_role')
--      AND pronamespace = 'public'::regnamespace;
--    -- Erwartet: 3 rows, prosecdef=true, provolatile='s'.
--
-- 4) ID-Konsistenz-Check (KRITISCH — sonst sperren Policies Monteure aus):
--    SELECT public.current_monteur_id() AS my_monteur_id;
--    -- ERWARTET: text-ID wie 'w1', 'w4', 'mpxpwdhrht1b' (nicht numerisch).
--
--    SELECT DISTINCT worker_id FROM public.worker_projects LIMIT 5;
--    -- ERWARTET: dieselbe text-ID-Form wie current_monteur_id().
--    -- Falls worker_projects.worker_id numerisch/UUID ist → NICHT ANWENDEN,
--    -- sondern Mapping-Layer in Policy ergänzen (wp.worker_id::text vs ...).
--
-- 5) Owner-Mapping pro Test-Token (manuell als jeweiliger User einloggen):
--    SELECT public.current_monteur_id() AS my_monteur_id;
--    SELECT public.is_hr()              AS am_i_hr;
--    SELECT public.auth_role()          AS my_role;
--
-- 6) Snapshot-Tabelle (idempotent — existiert bereits seit Block 1.1):
CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3923 (
  ts timestamptz DEFAULT now(),
  tablename text,
  policyname text,
  roles text[],
  cmd text,
  qual text,
  with_check text,
  block text
);


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 0.5) is_hr() Helper-Bootstrap (idempotent)
-- STATUS: ✅ APPLIED am 12.06.2026.
-- ───────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.is_hr() RETURNS boolean AS $$
  SELECT EXISTS(
    SELECT 1 FROM public.users
    WHERE auth_user_id = auth.uid()
      AND role IN ('admin','buero','projektleiter')
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public, pg_temp;

GRANT EXECUTE ON FUNCTION public.is_hr() TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_hr() TO anon;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.1) fahrzeuge — STATUS: ✅ APPLIED am 12.06.2026. Unverändert.
-- ───────────────────────────────────────────────────────────────────────────
-- (kein Re-Apply nötig — Snapshot + Policies bereits in Prod)


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.2) time_entries — STATUS: ✅ APPLIED am 12.06.2026. Unverändert.
-- ───────────────────────────────────────────────────────────────────────────
-- (kein Re-Apply nötig)


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.3) forms — WRITE auf Projekt-Zuweisung (worker_projects) ODER Office
-- STATUS: ⏳ OFFEN.
-- v4-KORREKTUR: forms.pid → forms.project_id; wp.monteur_id → wp.worker_id.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.3_forms'
FROM pg_policies WHERE schemaname='public' AND tablename='forms';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='forms'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.forms', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='forms'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.forms', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY forms_select_authed ON public.forms
  FOR SELECT TO authenticated USING (true);

CREATE POLICY forms_write_assigned_or_office ON public.forms
  FOR ALL TO authenticated
  USING (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.worker_id = public.current_monteur_id()
                AND wp.project_id = forms.project_id)
  )
  WITH CHECK (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.worker_id = public.current_monteur_id()
                AND wp.project_id = forms.project_id)
  );

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.4) bautagebuch — analog forms (project_id join via worker_projects)
-- STATUS: ⏳ OFFEN.
-- v4-KORREKTUR: bautagebuch.pid → bautagebuch.project_id; wp.monteur_id → wp.worker_id.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.4_bautagebuch'
FROM pg_policies WHERE schemaname='public' AND tablename='bautagebuch';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='bautagebuch'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.bautagebuch', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='bautagebuch'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.bautagebuch', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY bautagebuch_select_authed ON public.bautagebuch
  FOR SELECT TO authenticated USING (true);

CREATE POLICY bautagebuch_write_assigned_or_office ON public.bautagebuch
  FOR ALL TO authenticated
  USING (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.worker_id = public.current_monteur_id()
                AND wp.project_id = bautagebuch.project_id)
  )
  WITH CHECK (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.worker_id = public.current_monteur_id()
                AND wp.project_id = bautagebuch.project_id)
  );

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.5) fz_schaeden — 🚫 ENTFÄLLT (Tabelle existiert NICHT in Prod)
-- ───────────────────────────────────────────────────────────────────────────
-- Hintergrund: laut App-Changelog v3.9.427 (Single-Source-Refactor) und v3.9.430
-- wurde die fz_schaeden-Tabelle gedropped. Schaden-Daten liegen seither in
-- fahrzeuge.schaeden (jsonb). Eine RLS-Policy auf eine nicht-existente Tabelle
-- würde den DO-Block crashen lassen und damit den ganzen Block-1.5-Apply
-- rollbacken. fahrzeuge selbst ist bereits durch Block 1.1 (✅ APPLIED) abgedeckt.
--
-- Falls jemand fz_schaeden später wieder anlegt, hier neu definieren — bis
-- dahin: NICHT AUSFÜHREN.
--
-- (Block-Inhalt aus v3 bewusst entfernt.)


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.6) fahrbewilligungen — SELECT auf own ODER Office
-- STATUS: ⏳ OFFEN. Spalten OK (worker_id verifiziert).
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.6_fahrbewilligungen'
FROM pg_policies WHERE schemaname='public' AND tablename='fahrbewilligungen';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrbewilligungen'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrbewilligungen', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrbewilligungen'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrbewilligungen', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY fahrbewilligungen_select_own_or_office ON public.fahrbewilligungen
  FOR SELECT TO authenticated
  USING (public.is_hr() OR worker_id = public.current_monteur_id());

CREATE POLICY fahrbewilligungen_write_office ON public.fahrbewilligungen
  FOR ALL TO authenticated
  USING (public.is_hr()) WITH CHECK (public.is_hr());

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.7) anmeldungen — own ODER Office
-- STATUS: ⏳ OFFEN.
-- ⚠️ PRE-CHECK PFLICHT vor Apply — Spaltenname `worker_id` in v3 angenommen,
-- aber im v3-Codepath NICHT live-verifiziert. Falls die Tabelle stattdessen
-- monteur_id oder workerId nutzt → analog Block 1.3/1.4-Bug.
-- ───────────────────────────────────────────────────────────────────────────
--
-- PRE-CHECK (READ-ONLY):
--   SELECT column_name FROM information_schema.columns
--   WHERE table_schema='public' AND table_name='anmeldungen'
--   ORDER BY ordinal_position;
--   -- → wenn 'worker_id' vorhanden: Block wie unten anwenden.
--   -- → wenn 'monteur_id' o.ä.: vor Apply hier `worker_id` ersetzen.
--   -- → wenn Tabelle fehlt (NULL bei to_regclass('public.anmeldungen')):
--      Block analog 1.5 entfernen.
--
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.7_anmeldungen'
FROM pg_policies WHERE schemaname='public' AND tablename='anmeldungen';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='anmeldungen'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.anmeldungen', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='anmeldungen'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.anmeldungen', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY anmeldungen_select_own_or_office ON public.anmeldungen
  FOR SELECT TO authenticated
  USING (public.is_hr() OR worker_id = public.current_monteur_id());

CREATE POLICY anmeldungen_write_office ON public.anmeldungen
  FOR ALL TO authenticated
  USING (public.is_hr()) WITH CHECK (public.is_hr());

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.8) finkzeit — SELECT nur Office (Standby seit 04.06.2026)
-- STATUS: ⏳ OFFEN. Keine Join-Spalten — sollte ohne weiteren Pre-Check laufen.
-- Hinweis: v3.10.5 P0-6 hat finkzeit u.U. BEREITS auf own_or_hr eingeschraenkt
-- (sql/migrate_finkzeit_bescheinigungen_v3109.sql). Pre-Check zeigt's. Falls
-- 'finkzeit_select_own_or_hr' bereits existiert → COMMIT ohne CREATE.
-- ───────────────────────────────────────────────────────────────────────────
--
-- PRE-CHECK:
--   SELECT to_regclass('public.finkzeit');  -- darf nicht NULL sein
--   SELECT policyname FROM pg_policies WHERE tablename='finkzeit';
--
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.8_finkzeit'
FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='finkzeit'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.finkzeit', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='finkzeit'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.finkzeit', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY finkzeit_select_office_only ON public.finkzeit
  FOR SELECT TO authenticated USING (public.is_hr());

COMMIT;


-- ═══════════════════════════════════════════════════════════════════════════
-- POST-BLOCK VERIFIKATION (nach jedem Block)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- 1. Aktive Policies pro Tabelle:
--    SELECT policyname, cmd, qual::text, with_check::text
--    FROM pg_policies WHERE schemaname='public' AND tablename='<table>'
--    ORDER BY cmd, policyname;
--
-- 2. Snapshot der vorherigen Policies (Rollback-Material):
--    SELECT tablename, policyname, cmd, qual, with_check
--    FROM public._rls_snapshot_v3923 WHERE block LIKE '1.%' ORDER BY block, policyname;
--
-- 3. Live-Smoke pro Block (als Monteur-Token einloggen):
--    - 1.3: SELECT/INSERT in forms für zugewiesenes Projekt → OK; fremdes → 0/Fail
--    - 1.4: dito für bautagebuch
--    - 1.6: SELECT in fahrbewilligungen → nur eigene
--    - 1.7: SELECT in anmeldungen → nur eigene
--    - 1.8: SELECT in finkzeit → 0 als Monteur, voll als HR
--
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK je Block (falls noetig)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- BEGIN;
-- DROP POLICY IF EXISTS "<new_name>" ON public.<table>;
-- -- Original aus _rls_snapshot_v3923 lesen + CREATE POLICY ... rekonstruieren.
-- COMMIT;
--
-- ═══════════════════════════════════════════════════════════════════════════
