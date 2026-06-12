-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar RLS-Härtung Welle 1 v3 — READY-TO-EXECUTE (2026-06-12)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ▶ STATUS DES LIVE-APPLYS (Stand 12.06.2026 abends):
--     ✅ Block 0.5 is_hr() Bootstrap        — applied
--     ✅ Block 1.1 fahrzeuge                — applied, Snapshot 5 Zeilen
--     ✅ Block 1.2 time_entries             — applied (additiv auf bestehende
--                                              te_read/te_write Policies)
--     ⏳ Block 1.3-1.8 (forms / bautagebuch / fz_schaeden / fahrbewilligungen
--                       / anmeldungen / finkzeit) — offen, warten auf Smoke-OK.
--
-- ▶ KORREKTUREN gegenüber v2 (DEPRECATED):
--     1) pg_policies hat die Spalte `policyname`, NICHT `polname` (polname ist
--        nur im pg_policy-Katalog). v2 wäre überall mit 'column polname does
--        not exist' gestorben.
--     2) Doppel-Loop fuer DROP: pg_policies hat fuer INSERT-Policies qual=NULL
--        und nur with_check. Ein qual-Filter killt INSERT-Policies entweder
--        irrtuemlich (qual IS NULL) oder gar nicht. Lösung:
--          Loop 1: cmd<>'INSERT' mit qual='true'/'(true)' Filter.
--          Loop 2: cmd='INSERT' mit with_check='true'/'(true)' Filter.
--     3) is_hr() existierte in Prod NICHT (Migration v3106 lief nie). Block 0.5
--        legt sie idempotent an (CREATE OR REPLACE).
--     4) `_rls_snapshot_v3923.polname` umbenannt zu `policyname` fuer Konsistenz
--        mit pg_policies. Block 1.1+1.2 bereits live mit dieser Spalte applied.
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
-- 1) DB-Identität (Worker-Guard — angepasst auf aktuellen Stand 12.06.2026):
--    SELECT count(*) FROM public.workers;            -- Erwartet: 10
--      -- 10. worker = 'mpxpwdhrht1b' Kiener Bernd (Monteur).
--    SELECT count(*) FROM public.supplier_articles;  -- Erwartet: ~25118
--    SELECT to_regclass('public.fahrzeuge') IS NOT NULL AS exists; -- Erwartet: t
--
-- 2) Helper-Funktionen vorhanden:
--    SELECT proname, prosecdef, provolatile
--    FROM pg_proc WHERE proname IN ('is_hr','current_monteur_id','auth_role')
--      AND pronamespace = 'public'::regnamespace;
--    -- Erwartet: 3 rows, prosecdef=true, provolatile='s'.
--    -- Falls is_hr fehlt → Block 0.5 ZUERST anwenden.
--
-- 3) Owner-Mapping pro Test-Token (manuell als jeweiliger User einloggen):
--    SELECT public.current_monteur_id() AS my_monteur_id;
--    SELECT public.is_hr()              AS am_i_hr;
--    SELECT public.auth_role()          AS my_role;
--
-- 4) Snapshot-Tabelle (idempotent — existiert bereits seit Block 1.1):
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
-- STATUS: ✅ APPLIED am 12.06.2026 (vorher fehlte die Funktion in Prod).
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

-- Verify:
--   SELECT proname, prosecdef FROM pg_proc
--   WHERE proname='is_hr' AND pronamespace='public'::regnamespace;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.1) fahrzeuge — UPDATE auf Office ODER eigenes Fahrzeug (fahrer)
-- STATUS: ✅ APPLIED am 12.06.2026. fahrzeuge_update_driver erhalten,
--         Snapshot 5 Zeilen, qual=true-Policy gedroppt.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.1_fahrzeuge'
FROM pg_policies WHERE schemaname='public' AND tablename='fahrzeuge';

DO $$
DECLARE pol RECORD;
BEGIN
  -- Loop 1: non-INSERT qual=true
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrzeuge'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrzeuge', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  -- Loop 2: INSERT with_check=true
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrzeuge'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrzeuge', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY fahrzeuge_select_authed ON public.fahrzeuge
  FOR SELECT TO authenticated USING (true);

CREATE POLICY fahrzeuge_update_office_or_driver ON public.fahrzeuge
  FOR UPDATE TO authenticated
  USING (public.is_hr() OR fahrer = public.current_monteur_id())
  WITH CHECK (public.is_hr() OR fahrer = public.current_monteur_id());

CREATE POLICY fahrzeuge_insert_office ON public.fahrzeuge
  FOR INSERT TO authenticated WITH CHECK (public.is_hr());

CREATE POLICY fahrzeuge_delete_office ON public.fahrzeuge
  FOR DELETE TO authenticated USING (public.is_hr());

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.2) time_entries — WRITE auf own (worker_id) ODER Office
-- STATUS: ✅ APPLIED am 12.06.2026. Tabelle hatte BEREITS restriktive te_read /
--         te_write (is_staff() OR own); neue Policies sind ADDITIV — kein Lockout.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.2_time_entries'
FROM pg_policies WHERE schemaname='public' AND tablename='time_entries';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='time_entries'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.time_entries', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='time_entries'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.time_entries', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY time_entries_select_authed ON public.time_entries
  FOR SELECT TO authenticated USING (true);

CREATE POLICY time_entries_insert_own_or_office ON public.time_entries
  FOR INSERT TO authenticated
  WITH CHECK (public.is_hr() OR worker_id = public.current_monteur_id());

CREATE POLICY time_entries_update_own_or_office ON public.time_entries
  FOR UPDATE TO authenticated
  USING (public.is_hr() OR worker_id = public.current_monteur_id())
  WITH CHECK (public.is_hr() OR worker_id = public.current_monteur_id());

CREATE POLICY time_entries_delete_own_or_office ON public.time_entries
  FOR DELETE TO authenticated
  USING (public.is_hr() OR worker_id = public.current_monteur_id());

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.3) forms — WRITE auf Projekt-Zuweisung (worker_projects) ODER Office
-- STATUS: ⏳ OFFEN. Pre-Check column worker_projects (siehe weiter unten).
-- ───────────────────────────────────────────────────────────────────────────
-- PRE-CHECK (READ-ONLY):
--   SELECT column_name FROM information_schema.columns
--   WHERE table_schema='public' AND table_name='worker_projects';
--   -- Erwartet u.a.: monteur_id, project_id.
--   SELECT column_name FROM information_schema.columns
--   WHERE table_schema='public' AND table_name='forms';
--   -- Erwartet u.a.: pid (project ID).
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
              WHERE wp.monteur_id = public.current_monteur_id()
                AND wp.project_id = forms.pid)
  )
  WITH CHECK (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.monteur_id = public.current_monteur_id()
                AND wp.project_id = forms.pid)
  );

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.4) bautagebuch — analog forms (pid join via worker_projects)
-- STATUS: ⏳ OFFEN.
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
              WHERE wp.monteur_id = public.current_monteur_id()
                AND wp.project_id = bautagebuch.pid)
  )
  WITH CHECK (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.worker_projects wp
              WHERE wp.monteur_id = public.current_monteur_id()
                AND wp.project_id = bautagebuch.pid)
  );

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.5) fz_schaeden — Schadensmeldung auf eigenes Fz ODER Office
-- STATUS: ⏳ OFFEN.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.5_fz_schaeden'
FROM pg_policies WHERE schemaname='public' AND tablename='fz_schaeden';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fz_schaeden'
      AND cmd<>'INSERT'
      AND (qual='true' OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fz_schaeden', pol.policyname);
    RAISE NOTICE 'Dropped (qual): %', pol.policyname;
  END LOOP;
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fz_schaeden'
      AND cmd='INSERT'
      AND (with_check='true' OR with_check='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fz_schaeden', pol.policyname);
    RAISE NOTICE 'Dropped (with_check): %', pol.policyname;
  END LOOP;
END $$;

CREATE POLICY fz_schaeden_select_authed ON public.fz_schaeden
  FOR SELECT TO authenticated USING (true);

CREATE POLICY fz_schaeden_write_owner_or_office ON public.fz_schaeden
  FOR ALL TO authenticated
  USING (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.fahrzeuge f
              WHERE f.id = fz_schaeden.fz_id
                AND f.fahrer = public.current_monteur_id())
  )
  WITH CHECK (
    public.is_hr()
    OR EXISTS(SELECT 1 FROM public.fahrzeuge f
              WHERE f.id = fz_schaeden.fz_id
                AND f.fahrer = public.current_monteur_id())
  );

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.6) fahrbewilligungen — SELECT auf own ODER Office
-- STATUS: ⏳ OFFEN.
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
-- BLOCK 1.7) anmeldungen — analog fahrbewilligungen
-- STATUS: ⏳ OFFEN.
-- ───────────────────────────────────────────────────────────────────────────
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
-- STATUS: ⏳ OFFEN. Hinweis: v3.10.5 P0-6 hat finkzeit u.U. BEREITS auf
--   own_or_hr eingeschraenkt (sql/migrate_finkzeit_bescheinigungen_v3109.sql).
--   Pre-Check zeigt's. Falls 'finkzeit_select_own_or_hr' bereits existiert →
--   COMMIT ohne CREATE.
-- ───────────────────────────────────────────────────────────────────────────
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
