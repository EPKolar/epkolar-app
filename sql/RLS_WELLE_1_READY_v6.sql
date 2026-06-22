-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar RLS-Härtung Welle 1 v6 — READY-TO-EXECUTE (2026-06-22)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ▶ ZUSAMMENFASSUNG der Fixes ggü v5 (DEPRECATED — alle Mängel aus Chat-Claude-Review):
--
--   v6-Fix Nr. 1 — Pattern-basiertes Drop statt fragiler Allowlist
--     v5 hat `te_read`/`te_write` per Namens-Allowlist erhalten in der Annahme
--     sie seien restriktiv. Wenn sie offen sind, würden sie überleben →
--     Härtung wirkungslos. v6 prüft NICHT mehr per Namen, sondern droppt
--     ALLES was offene Pattern hat (`qual='true'` ODER
--     `qual LIKE '%auth.role()%authenticated%'`). Additive Policies wie
--     `fahrzeuge_update_driver` (restriktive Logik, kein offenes Pattern)
--     werden vom Pattern-Filter naturgemäß NICHT erfasst und bleiben erhalten.
--
--   v6-Fix Nr. 2 — Block 1.1 + 1.2 idempotent integriert (kein separates 1.0a-Repair mehr)
--     v5 hatte ein zusätzliches 1.0a-Repair und nahm an, die restriktiven
--     Härtungs-Policies aus dem v3-Apply (12.06.) seien noch da. Nicht
--     verifizierbar im SQL. v6 macht Block 1.1 + 1.2 idempotent:
--       (a) Pattern-Drop für offene Policies
--       (b) DROP IF EXISTS für unsere restriktiven Härtungs-Policies (clean re-create)
--       (c) CREATE der restriktiven Policies neu
--     Damit ist die Endlage deterministisch — egal in welchem Zustand
--     (gar nichts | nur offene | nur restriktive | gemischt) v6 anfängt,
--     nachher steht der korrekte Satz. `fahrzeuge_update_driver` (additive,
--     nicht im DROP IF EXISTS) bleibt unangetastet.
--
--   v6-Fix Nr. 3 — Block 1.7 anmeldungen conditional
--     v5 hatte nur Pre-Check-Kommentar; das CREATE nahm `anmeldungen.worker_id`
--     hart an. Wenn die Spalte fehlt → Block-Crash. v6 prüft via
--     information_schema und SKIPPED Block 1.7 mit RAISE NOTICE wenn die Spalte
--     fehlt — kein Crash, kein Apply.
--
--   v6-Fix Nr. 4 (Notiz aus v5) — Snapshot-Dedup
--     v5-Snapshot-Inserts würden bei wiederholtem Re-Apply Duplikate sammeln.
--     v6 inserted nur wenn (tablename, policyname, block) noch nicht im
--     Snapshot existiert — pro Block idempotent.
--
-- ▶ STATUS DES LIVE-APPLYS (Stand 22.06.2026):
--     ✅ Block 0.5 is_hr() Bootstrap        — applied 12.06., bleibt idempotent
--     ⚠️ Block 1.1 fahrzeuge                — nominell applied 12.06., v6 macht
--                                              clean idempotent re-apply
--     ⚠️ Block 1.2 time_entries             — analog
--     ⏳ Block 1.3 forms                    — wartet
--     ⏳ Block 1.4 bautagebuch              — wartet
--     🚫 Block 1.5 fz_schaeden              — ENTFÄLLT (Tabelle existiert NICHT)
--     ⏳ Block 1.6 fahrbewilligungen        — wartet
--     ⏳ Block 1.7 anmeldungen              — conditional auf worker_id-Spalte
--     ⏳ Block 1.8 finkzeit                 — wartet, erkennt v3.10.5-P0-6-Policy
--
-- ▶ Sebastian fuehrt im Supabase-SQL-Editor blockweise aus. Jeder Block in
--   BEGIN/COMMIT. Bei JEDEM Fehler ROLLBACK + Halt + Befund melden.
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- VORAB-VERIFIKATION (READ-ONLY) — pre-check VOR jedem Block
-- ───────────────────────────────────────────────────────────────────────────
--
-- 0) IST-Policies komplett auflisten:
--    SELECT tablename, policyname, cmd, qual::text, with_check::text, roles
--    FROM pg_policies
--    WHERE schemaname='public'
--      AND tablename IN ('fahrzeuge','time_entries','forms','bautagebuch',
--                        'fahrbewilligungen','anmeldungen','finkzeit')
--    ORDER BY tablename, cmd, policyname;
--
-- 1) Spalten-Verifikation (gegen v3-Mismatches):
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='worker_projects'
--    ORDER BY ordinal_position;
--    -- ERWARTET: id, worker_id, project_id, ...
--
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='forms'
--    ORDER BY ordinal_position;
--    -- ERWARTET: id, project_id, name, form_type, ...
--
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='bautagebuch'
--    ORDER BY ordinal_position;
--    -- ERWARTET: id, project_id, datum, ...
--
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='anmeldungen'
--    ORDER BY ordinal_position;
--    -- → wenn `worker_id` fehlt: Block 1.7 SKIPPED sich automatisch.
--
--    SELECT to_regclass('public.fz_schaeden');  -- ERWARTET: NULL
--
-- 2) Helper-Funktionen vorhanden:
--    SELECT proname, prosecdef, provolatile
--    FROM pg_proc WHERE proname IN ('is_hr','current_monteur_id','auth_role')
--      AND pronamespace = 'public'::regnamespace;
--
-- 3) ID-Konsistenz (KRITISCH):
--    SELECT public.current_monteur_id() AS my_monteur_id;
--    SELECT DISTINCT worker_id FROM public.worker_projects LIMIT 5;
--    -- Beide MÜSSEN dieselbe text-ID-Form haben (w1, mpxpwdhrht1b, ...).
--
-- 4) Snapshot-Tabelle (idempotent):
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
-- BLOCK 1.1) fahrzeuge — UPDATE auf Office ODER eigenes Fahrzeug
-- v6: pattern-basiertes Drop + idempotenter Re-Create der restriktiven Policies
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

-- Snapshot (dedup via NOT EXISTS):
INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT p.tablename, p.policyname, p.roles, p.cmd, p.qual, p.with_check, '1.1_fahrzeuge'
FROM pg_policies p
WHERE p.schemaname='public' AND p.tablename='fahrzeuge'
  AND NOT EXISTS(SELECT 1 FROM public._rls_snapshot_v3923 s
    WHERE s.tablename=p.tablename AND s.policyname=p.policyname AND s.block='1.1_fahrzeuge');

-- (a) Pattern-Drop für offene Policies (egal welcher Name):
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrzeuge'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrzeuge', pol.policyname);
    RAISE NOTICE 'fahrzeuge: dropped open: %', pol.policyname;
  END LOOP;
END $$;

-- (b) Explizit-Drop der bekannten restriktiven Policies (clean re-create):
DROP POLICY IF EXISTS fahrzeuge_select_authed              ON public.fahrzeuge;
DROP POLICY IF EXISTS fahrzeuge_update_office_or_driver    ON public.fahrzeuge;
DROP POLICY IF EXISTS fahrzeuge_insert_office              ON public.fahrzeuge;
DROP POLICY IF EXISTS fahrzeuge_delete_office              ON public.fahrzeuge;
-- HINWEIS: fahrzeuge_update_driver bleibt — additive Policy, bewusst NICHT droppen.

-- (c) Re-Create restriktive:
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
-- v6: pattern-basiertes Drop räumt auch te_read/te_write auf wenn sie offen sind
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT p.tablename, p.policyname, p.roles, p.cmd, p.qual, p.with_check, '1.2_time_entries'
FROM pg_policies p
WHERE p.schemaname='public' AND p.tablename='time_entries'
  AND NOT EXISTS(SELECT 1 FROM public._rls_snapshot_v3923 s
    WHERE s.tablename=p.tablename AND s.policyname=p.policyname AND s.block='1.2_time_entries');

-- (a) Pattern-Drop für offene Policies:
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='time_entries'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.time_entries', pol.policyname);
    RAISE NOTICE 'time_entries: dropped open: %', pol.policyname;
  END LOOP;
END $$;

-- (b) Explizit-Drop der bekannten restriktiven Policies + alte te_read/te_write:
DROP POLICY IF EXISTS time_entries_select_authed             ON public.time_entries;
DROP POLICY IF EXISTS time_entries_insert_own_or_office      ON public.time_entries;
DROP POLICY IF EXISTS time_entries_update_own_or_office      ON public.time_entries;
DROP POLICY IF EXISTS time_entries_delete_own_or_office      ON public.time_entries;
-- te_read/te_write werden ENTWEDER vom Pattern-Drop in (a) erfasst (wenn offen),
-- ODER bleiben hier explizit erhalten (wenn sie restriktive Logik haben).
-- KEIN expliziter DROP — wir wollen restriktive Vorgänger-Policies erhalten.

-- (c) Re-Create restriktive:
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
-- BLOCK 1.3) forms — WRITE auf Projekt-Zuweisung ODER Office
-- v6: pattern-basiertes Drop + saubere Re-Create.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT p.tablename, p.policyname, p.roles, p.cmd, p.qual, p.with_check, '1.3_forms'
FROM pg_policies p
WHERE p.schemaname='public' AND p.tablename='forms'
  AND NOT EXISTS(SELECT 1 FROM public._rls_snapshot_v3923 s
    WHERE s.tablename=p.tablename AND s.policyname=p.policyname AND s.block='1.3_forms');

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='forms'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.forms', pol.policyname);
    RAISE NOTICE 'forms: dropped open: %', pol.policyname;
  END LOOP;
END $$;

DROP POLICY IF EXISTS forms_select_authed              ON public.forms;
DROP POLICY IF EXISTS forms_write_assigned_or_office   ON public.forms;

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
-- BLOCK 1.4) bautagebuch — analog forms (project_id via worker_projects)
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT p.tablename, p.policyname, p.roles, p.cmd, p.qual, p.with_check, '1.4_bautagebuch'
FROM pg_policies p
WHERE p.schemaname='public' AND p.tablename='bautagebuch'
  AND NOT EXISTS(SELECT 1 FROM public._rls_snapshot_v3923 s
    WHERE s.tablename=p.tablename AND s.policyname=p.policyname AND s.block='1.4_bautagebuch');

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='bautagebuch'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.bautagebuch', pol.policyname);
    RAISE NOTICE 'bautagebuch: dropped open: %', pol.policyname;
  END LOOP;
END $$;

DROP POLICY IF EXISTS bautagebuch_select_authed              ON public.bautagebuch;
DROP POLICY IF EXISTS bautagebuch_write_assigned_or_office   ON public.bautagebuch;

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
-- BLOCK 1.5) fz_schaeden — 🚫 ENTFÄLLT (Tabelle existiert NICHT, gedroppt v3.9.427)
-- ───────────────────────────────────────────────────────────────────────────


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.6) fahrbewilligungen — SELECT auf own ODER Office
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT p.tablename, p.policyname, p.roles, p.cmd, p.qual, p.with_check, '1.6_fahrbewilligungen'
FROM pg_policies p
WHERE p.schemaname='public' AND p.tablename='fahrbewilligungen'
  AND NOT EXISTS(SELECT 1 FROM public._rls_snapshot_v3923 s
    WHERE s.tablename=p.tablename AND s.policyname=p.policyname AND s.block='1.6_fahrbewilligungen');

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrbewilligungen'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrbewilligungen', pol.policyname);
    RAISE NOTICE 'fahrbewilligungen: dropped open: %', pol.policyname;
  END LOOP;
END $$;

DROP POLICY IF EXISTS fahrbewilligungen_select_own_or_office ON public.fahrbewilligungen;
DROP POLICY IF EXISTS fahrbewilligungen_write_office         ON public.fahrbewilligungen;

CREATE POLICY fahrbewilligungen_select_own_or_office ON public.fahrbewilligungen
  FOR SELECT TO authenticated
  USING (public.is_hr() OR worker_id = public.current_monteur_id());

CREATE POLICY fahrbewilligungen_write_office ON public.fahrbewilligungen
  FOR ALL TO authenticated
  USING (public.is_hr()) WITH CHECK (public.is_hr());

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.7) anmeldungen — own ODER Office
-- v6: Conditional auf anmeldungen.worker_id-Existenz. Block SKIPPED sich mit
-- RAISE NOTICE wenn die Spalte fehlt (kein Crash).
-- ───────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
  has_worker_id boolean;
  pol RECORD;
BEGIN
  -- Pre-Check: Spalte vorhanden?
  SELECT EXISTS(SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='anmeldungen' AND column_name='worker_id')
  INTO has_worker_id;

  IF NOT has_worker_id THEN
    RAISE NOTICE 'BLOCK 1.7 SKIP: anmeldungen.worker_id existiert nicht (information_schema). Manueller Pre-Check + Anpassung erforderlich.';
    RETURN;
  END IF;

  -- Snapshot (dedup):
  INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
  SELECT p.tablename, p.policyname, p.roles, p.cmd, p.qual, p.with_check, '1.7_anmeldungen'
  FROM pg_policies p
  WHERE p.schemaname='public' AND p.tablename='anmeldungen'
    AND NOT EXISTS(SELECT 1 FROM public._rls_snapshot_v3923 s
      WHERE s.tablename=p.tablename AND s.policyname=p.policyname AND s.block='1.7_anmeldungen');

  -- Pattern-Drop offene Policies:
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='anmeldungen'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.anmeldungen', pol.policyname);
    RAISE NOTICE 'anmeldungen: dropped open: %', pol.policyname;
  END LOOP;

  -- Explizit-Drop + Re-Create (via EXECUTE da innerhalb DO):
  EXECUTE 'DROP POLICY IF EXISTS anmeldungen_select_own_or_office ON public.anmeldungen';
  EXECUTE 'DROP POLICY IF EXISTS anmeldungen_write_office         ON public.anmeldungen';

  EXECUTE $sql$
    CREATE POLICY anmeldungen_select_own_or_office ON public.anmeldungen
      FOR SELECT TO authenticated
      USING (public.is_hr() OR worker_id = public.current_monteur_id())
  $sql$;

  EXECUTE $sql$
    CREATE POLICY anmeldungen_write_office ON public.anmeldungen
      FOR ALL TO authenticated
      USING (public.is_hr()) WITH CHECK (public.is_hr())
  $sql$;

  RAISE NOTICE 'BLOCK 1.7 OK: anmeldungen Policies neu angelegt.';
END $$;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.8) finkzeit — SELECT nur Office
-- v6: Falls v3.10.5-P0-6 die strengere `finkzeit_select_own_or_hr` schon
-- eingespielt hat → erkennen + NICHT überschreiben.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT p.tablename, p.policyname, p.roles, p.cmd, p.qual, p.with_check, '1.8_finkzeit'
FROM pg_policies p
WHERE p.schemaname='public' AND p.tablename='finkzeit'
  AND NOT EXISTS(SELECT 1 FROM public._rls_snapshot_v3923 s
    WHERE s.tablename=p.tablename AND s.policyname=p.policyname AND s.block='1.8_finkzeit');

DO $$
DECLARE
  pol RECORD;
  has_strict boolean;
BEGIN
  -- Pattern-Drop offene Policies:
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='finkzeit'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.finkzeit', pol.policyname);
    RAISE NOTICE 'finkzeit: dropped open: %', pol.policyname;
  END LOOP;

  -- Falls schon eine restriktive SELECT-Policy aus v3.10.5 existiert → SKIP
  SELECT EXISTS(SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='finkzeit'
      AND policyname IN ('finkzeit_select_own_or_hr','finkzeit_select_office_only'))
  INTO has_strict;

  IF has_strict THEN
    RAISE NOTICE 'BLOCK 1.8: restriktive SELECT-Policy existiert bereits — kein Re-Create.';
  ELSE
    EXECUTE $sql$
      CREATE POLICY finkzeit_select_office_only ON public.finkzeit
        FOR SELECT TO authenticated USING (public.is_hr())
    $sql$;
    RAISE NOTICE 'BLOCK 1.8 OK: finkzeit_select_office_only angelegt.';
  END IF;
END $$;

COMMIT;


-- ═══════════════════════════════════════════════════════════════════════════
-- POST-BLOCK VERIFIKATION (nach jedem Block — UNBEDINGT)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- 1. Aktive Policies pro Tabelle:
--    SELECT policyname, cmd, qual::text, with_check::text
--    FROM pg_policies WHERE schemaname='public' AND tablename='<table>'
--    ORDER BY cmd, policyname;
--    -- WICHTIG: KEINE offene auth.role()-Policy mehr daneben.
--
-- 2. Snapshot der vorherigen Policies (Rollback-Material):
--    SELECT tablename, policyname, cmd, qual, with_check, block
--    FROM public._rls_snapshot_v3923
--    WHERE block IN ('1.1_fahrzeuge','1.2_time_entries','1.3_forms','1.4_bautagebuch',
--                    '1.6_fahrbewilligungen','1.7_anmeldungen','1.8_finkzeit')
--    ORDER BY block, policyname;
--
-- 3. Live-Smoke pro Block (als Monteur-Token einloggen):
--    - 1.1/1.2: fahrzeuge/time_entries — Monteur sieht/schreibt nur eigene
--    - 1.3:    forms für zugewiesenes Projekt → OK; fremdes → 0/Fail
--    - 1.4:    bautagebuch — dito
--    - 1.6:    fahrbewilligungen → nur eigene
--    - 1.7:    anmeldungen → nur eigene (falls Block nicht geSKIPPed)
--    - 1.8:    finkzeit → 0 als Monteur, voll als HR
--
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK je Block (falls nötig)
-- ═══════════════════════════════════════════════════════════════════════════
-- BEGIN;
-- DROP POLICY IF EXISTS "<new_name>" ON public.<table>;
-- -- Original aus _rls_snapshot_v3923 lesen + CREATE POLICY ... rekonstruieren.
-- COMMIT;
-- ═══════════════════════════════════════════════════════════════════════════
