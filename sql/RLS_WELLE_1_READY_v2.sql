-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar RLS-Härtung Welle 1 v2 — READY-TO-EXECUTE (2026-06-12)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ▶ KORRIGIERT gegenüber v1 (DEPRECATED):
--   v1 hatte u.id = auth.uid() (TEXT vs UUID — Typ-Mismatch).
--   public.users.id ist TEXT (z.B. 'u1'..'u9'), auth.uid() ist UUID.
--   Korrekte Join-Spalte ist public.users.auth_user_id (UUID).
--
-- ▶ Verwendet die am 10.06 verifizierten Helper-Funktionen aus
--   sql/migrate_urlaubskontingent_hardening_v3106.sql + migrate_finkzeit_bescheinigungen_v3109.sql:
--     * public.is_hr()             — admin OR buero OR projektleiter
--     * public.current_monteur_id() — eigene monteur_id des Callers
--     * public.auth_role()         — Rolle als TEXT (Fallback 'anon')
--
-- ▶ Bestehende verifizierte Policy "fahrzeuge_update_driver" verwendet
--   das gleiche current_monteur_id()-Muster — wir spiegeln das exakt.
--
-- ▶ Sebastian fuehrt im Supabase-SQL-Editor blockweise aus.
-- ▶ Pro Block: BEGIN ... COMMIT. Bei Auffaelligkeit ROLLBACK statt COMMIT.
-- ▶ Snapshot der bestehenden Policies in _rls_snapshot_v3923 vor Drop.
-- ▶ Pro Block: 30-min-Smoke gemaess docs/SMOKE_v3.9.31x.md (Punkte a-q).
--
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- VORAB-VERIFIKATION (READ-ONLY — KEIN DDL) — vor jedem Block kurz pruefen
-- ───────────────────────────────────────────────────────────────────────────
--
-- 1) Helper existieren + sind STABLE + SECURITY DEFINER:
--    SELECT proname, prosecdef, provolatile, proconfig
--    FROM pg_proc WHERE proname IN ('is_hr','current_monteur_id','auth_role')
--      AND pronamespace = 'public'::regnamespace;
--    -- Erwartet: 3 rows, prosecdef=true, provolatile='s'.
--
-- 2) Mapping liefert je 1 Treffer fuer Monteur UND Office (als SQL-Editor mit JWT):
--    -- Als Monteur (z.B. paschinger, auth_user_id zugeordnet zu monteur_id='w1'):
--    SELECT auth.uid()                       AS my_auth_uid;
--    SELECT public.current_monteur_id()      AS my_monteur_id;   -- erwartet: 'w1'
--    SELECT public.is_hr()                   AS am_i_hr;          -- erwartet: false
--    SELECT public.auth_role()               AS my_role;          -- erwartet: 'monteur'
--    -- Als Buero (z.B. schober, monteur_id='w7', role='buero'):
--    SELECT public.current_monteur_id()      AS my_monteur_id;   -- erwartet: 'w7'
--    SELECT public.is_hr()                   AS am_i_hr;          -- erwartet: true
--    SELECT public.auth_role()               AS my_role;          -- erwartet: 'buero'
--
-- 3) Snapshot der aktuellen Policies (bleibt nach Rollout — Rollback-Material):
CREATE TABLE IF NOT EXISTS public._rls_snapshot_v3923 (
  ts timestamptz DEFAULT now(),
  tablename text,
  polname text,
  roles text[],
  cmd text,
  qual text,
  with_check text,
  block text
);
-- Befuellen vor Drop in jedem Block (siehe Bloecke 1.x).
-- Rollback eines Blocks:
--   DROP POLICY IF EXISTS "<new_name>" ON public.<table>;
--   -- Original aus _rls_snapshot_v3923 lesen + CREATE POLICY ... rekonstruieren.


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.1) fahrzeuge — UPDATE auf Office ODER eigenes Fahrzeug (fahrer)
-- Vorbild: bestehende Policy "fahrzeuge_update_driver" (Q1/2026 verifiziert).
-- Risiko: LOW. Disponent (is_hr()) sieht/updated alles; Monteur nur eigenes Fz.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.1_fahrzeuge'
FROM pg_policies WHERE schemaname='public' AND tablename='fahrzeuge';

-- Offene 'qual=true'-Policies fuer authenticated droppen
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrzeuge'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrzeuge', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
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
-- Risiko: LOW. v3.9.307-Edit-Button hat canDo('zeit_other')-Guard; Self-Edit bleibt.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.2_time_entries'
FROM pg_policies WHERE schemaname='public' AND tablename='time_entries';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='time_entries'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.time_entries', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
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
-- (regie/sf/dh/ah/abnahme/checklisten als sub-types via type-Spalte)
-- Risiko: LOW. Pre-Check: worker_projects.monteur_id Spalte muss existieren.
-- ───────────────────────────────────────────────────────────────────────────
-- PRE-CHECK:
--   SELECT column_name FROM information_schema.columns
--   WHERE table_schema='public' AND table_name='worker_projects';
--   -- Erwartet u.a.: monteur_id, project_id.
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.3_forms'
FROM pg_policies WHERE schemaname='public' AND tablename='forms';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='forms'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.forms', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
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
-- BLOCK 1.4) bautagebuch — analog forms
-- Risiko: LOW.
-- ───────────────────────────────────────────────────────────────────────────
-- PRE-CHECK:
--   SELECT column_name FROM information_schema.columns
--   WHERE table_schema='public' AND table_name='bautagebuch';
--   -- Erwartet u.a.: pid (project ID).
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.4_bautagebuch'
FROM pg_policies WHERE schemaname='public' AND tablename='bautagebuch';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='bautagebuch'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.bautagebuch', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
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
-- BLOCK 1.5) fz_schaeden — Schadensmeldung auf eigenes Fahrzeug ODER Office
-- Risiko: LOW. Monteur darf eigenes Fz melden (via fahrzeuge.fahrer).
-- ───────────────────────────────────────────────────────────────────────────
-- PRE-CHECK:
--   SELECT column_name FROM information_schema.columns
--   WHERE table_schema='public' AND table_name='fz_schaeden';
--   -- Erwartet u.a.: fz_id (vehicle ID).
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.5_fz_schaeden'
FROM pg_policies WHERE schemaname='public' AND tablename='fz_schaeden';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='fz_schaeden'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fz_schaeden', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
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
-- BLOCK 1.6) fahrbewilligungen — SELECT auf own (worker_id) ODER Office
-- Risiko: LOW. Self-Read bleibt fuer MitarbeiterView v3.9.312.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.6_fahrbewilligungen'
FROM pg_policies WHERE schemaname='public' AND tablename='fahrbewilligungen';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='fahrbewilligungen'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrbewilligungen', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
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
-- Risiko: LOW.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.7_anmeldungen'
FROM pg_policies WHERE schemaname='public' AND tablename='anmeldungen';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='anmeldungen'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.anmeldungen', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
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
-- Risiko: LOW. Feature ist standby, nur Doku-Zugriff fuer Office.
-- Hinweis: v3.10.5 P0-6 hat finkzeit BEREITS auf own_or_hr eingeschraenkt
-- (siehe sql/migrate_finkzeit_bescheinigungen_v3109.sql). Falls dieser Block
-- bereits angewandt wurde, ist 1.8 ein No-Op — Snapshot zeigt's.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, polname, roles, cmd, qual, with_check, block)
SELECT tablename, polname, roles, cmd, qual, with_check, '1.8_finkzeit'
FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit';

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT polname FROM pg_policies
    WHERE schemaname='public' AND tablename='finkzeit'
      AND (qual='true' OR qual IS NULL OR qual='(true)')
      AND 'authenticated'::text = ANY(roles)
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.finkzeit', pol.polname);
    RAISE NOTICE 'Dropped: %', pol.polname;
  END LOOP;
END $$;

-- Falls die v3109-Policies bereits da sind, NICHT ueberschreiben — Pre-Check:
--   SELECT polname FROM pg_policies WHERE schemaname='public' AND tablename='finkzeit';
-- Wenn 'finkzeit_select_own_or_hr' bereits existiert → COMMIT ohne CREATE.
CREATE POLICY finkzeit_select_office_only ON public.finkzeit
  FOR SELECT TO authenticated USING (public.is_hr());

COMMIT;


-- ═══════════════════════════════════════════════════════════════════════════
-- POST-WELLE-1 VERIFIKATION (nach jedem Block)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- 1. Aktive Policies pro Tabelle anzeigen:
--    SELECT polname, polcmd, polqual::text, polwithcheck::text
--    FROM pg_policies WHERE schemaname='public' AND tablename='<table>'
--    ORDER BY polcmd, polname;
--
-- 2. Snapshot der vorherigen Policies (Rollback-Material):
--    SELECT tablename, polname, cmd, qual, with_check
--    FROM public._rls_snapshot_v3923 WHERE block LIKE '1.%' ORDER BY block, polname;
--
-- 3. Smoke vom Client (Client-Toast v3.9.323 triggert bei 0-rows):
--    - Monteur eigenes Fz tanken         → ✅ "⛽ Tankung erfasst"
--    - Monteur fremdes Fz tanken         → ⚠️ "Fahrzeug-Aenderung NICHT gespeichert"
--    - Monteur eigene Zeit bearbeiten    → ✅
--    - Monteur fremde Zeit bearbeiten    → ⚠️ "Zeiteintrag NICHT gespeichert"
--    - Monteur eigene Fahrbewilligung    → ✅
--    - Monteur fremde Fahrbewilligung    → 0 rows / nicht sichtbar
--    - finkzeit-Tab fuer non-Office      → leer / Tab versteckt
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
