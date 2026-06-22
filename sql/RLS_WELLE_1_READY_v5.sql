-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar RLS-Härtung Welle 1 v5 — READY-TO-EXECUTE (2026-06-22)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ▶ STATUS DES LIVE-APPLYS (Stand 22.06.2026):
--     ✅ Block 0.5 is_hr() Bootstrap        — applied (12.06.2026)
--     ⚠️ Block 1.1 fahrzeuge                — applied 12.06, PFLICHT-REVERIFY
--     ⚠️ Block 1.2 time_entries             — applied 12.06, PFLICHT-REVERIFY
--     ⏳ Block 1.3 forms                    — wartet auf Apply
--     ⏳ Block 1.4 bautagebuch              — wartet auf Apply
--     🚫 Block 1.5 fz_schaeden              — ENTFÄLLT (Tabelle existiert NICHT)
--     ⏳ Block 1.6 fahrbewilligungen        — wartet auf Apply
--     ⏳ Block 1.7 anmeldungen              — wartet auf Apply (Pre-Check Spalten)
--     ⏳ Block 1.8 finkzeit                 — wartet auf Apply
--
-- ▶ KORREKTUR gegenüber v4 (DEPRECATED):
--   Chat-Claude Live-Verify (pg_policies, 22.06.2026) ergab: der DROP-Loop in
--   v3/v4 filtert nur auf `qual='true' OR qual='(true)'`. Die REALEN offenen
--   Policies auf forms (und vermutlich anderen Tabellen) haben aber
--   `qual=(auth.role()='authenticated'::text)` — NICHT 'true'. Folge: Loop
--   droppte NICHTS, die neuen restriktiven Policies wurden nur ADDITIV
--   angelegt, PostgreSQL OR-verknüpft PERMISSIVE Policies → offene Policy
--   gewinnt → Härtung WIRKUNGSLOS.
--
--   v5 fix:
--     1. DROP-Loop-Filter erweitert um qual LIKE '%auth.role()%' (Sebastian-
--        Vorschlag). Plus zusätzlich expliziter Drop der typischen offenen
--        Policy-Namen pro Tabelle (`<table>_select|insert|update|delete`,
--        `<table>_authed`, alte `_authenticated`-Suffixe). DROP POLICY IF
--        EXISTS ist idempotent.
--     2. Block 1.0a (NEU): Repair-Sektion für 1.1/1.2 — droppt eventuelle
--        Rest-offene auth.role()-Policies auf fahrzeuge / time_entries, ohne
--        die additiven Härtungs-Policies (fahrzeuge_update_driver,
--        time_entries_*_own_or_office) anzutasten.
--     3. fz_schaeden bleibt ENTFÄLLT (aus v4).
--
-- ▶ Sebastian fuehrt im Supabase-SQL-Editor blockweise aus. Jeder Block in
--   BEGIN/COMMIT. Bei JEDEM Fehler ROLLBACK + Halt + Befund melden.
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- VORAB-VERIFIKATION (READ-ONLY) — pre-check VOR jedem Block
-- ───────────────────────────────────────────────────────────────────────────
--
-- 0) IST-Policies komplett auflisten (CRITICAL — v4-Lehre):
--    SELECT tablename, policyname, cmd, qual::text, with_check::text, roles
--    FROM pg_policies
--    WHERE schemaname='public'
--      AND tablename IN ('fahrzeuge','time_entries','forms','bautagebuch',
--                        'fahrbewilligungen','anmeldungen','finkzeit')
--    ORDER BY tablename, cmd, policyname;
--    -- Pro Tabelle prüfen: gibt es offene Policies (qual=true ODER
--    -- qual LIKE '%auth.role()%authenticated%')? Wenn ja → v5 droppt sie.
--    -- Welche additiven (z.B. fahrzeuge_update_driver) MÜSSEN bleiben?
--
-- 1) DB-Identität (Worker-Guard):
--    SELECT count(*) FROM public.workers;            -- Erwartet: 10
--    SELECT count(*) FROM public.supplier_articles;  -- Erwartet: ~25118
--
-- 2) Spalten-Verifikation (gegen v3-Mismatches, aus v4 übernommen):
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='worker_projects'
--    ORDER BY ordinal_position;
--    -- ERWARTET: id, worker_id, project_id, projects, role, assigned_at
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
--    SELECT to_regclass('public.fz_schaeden');  -- ERWARTET: NULL
--
-- 3) Helper-Funktionen vorhanden:
--    SELECT proname, prosecdef, provolatile
--    FROM pg_proc WHERE proname IN ('is_hr','current_monteur_id','auth_role')
--      AND pronamespace = 'public'::regnamespace;
--
-- 4) ID-Konsistenz (KRITISCH):
--    SELECT public.current_monteur_id() AS my_monteur_id;
--    SELECT DISTINCT worker_id FROM public.worker_projects LIMIT 5;
--    -- Beide MÜSSEN dieselbe text-ID-Form haben (w1, mpxpwdhrht1b, ...).
--
-- 5) Anmeldungen-Spalte verifizieren (Pre-Check für Block 1.7):
--    SELECT column_name FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='anmeldungen'
--    ORDER BY ordinal_position;
--    -- Wenn 'worker_id' fehlt → Block 1.7 anpassen oder entfernen.
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


-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK 1.0a) REPAIR fahrzeuge + time_entries (Block 1.1/1.2-Nachverifikation)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- v4-Lehre: DROP-Loop filterte nur qual='true'/'(true)' — eventuelle offene
-- auth.role()-Policies blieben daneben stehen. PostgreSQL OR-Logik:
-- permissive offene Policy gewinnt → Härtung wirkungslos.
--
-- PRE-CHECK BEVOR APPLY (mehrfach in v3 schon applied — Stand erst LIVE prüfen):
--   SELECT policyname, cmd, qual::text, with_check::text
--   FROM pg_policies WHERE schemaname='public'
--     AND tablename IN ('fahrzeuge','time_entries')
--   ORDER BY tablename, cmd, policyname;
--
-- Wenn dort z.B. `fahrzeuge_select` mit qual=(auth.role()='authenticated'::text)
-- daneben steht — DAS ist der Bug. v3-Härtung war ineffektiv.
--
-- HINWEIS: `fahrzeuge_update_driver` MUSS erhalten bleiben (additive Policy
-- für Selbst-Edit des eigenen FZ — Sebastian explizit). v5 droppt sie NICHT.
-- ───────────────────────────────────────────────────────────────────────────
BEGIN;

INSERT INTO public._rls_snapshot_v3923 (tablename, policyname, roles, cmd, qual, with_check, block)
SELECT tablename, policyname, roles, cmd, qual, with_check, '1.0a_repair'
FROM pg_policies WHERE schemaname='public' AND tablename IN ('fahrzeuge','time_entries');

DO $$
DECLARE pol RECORD;
BEGIN
  -- v5: erweiterter Filter — auch auth.role()-basierte offene Policies fangen
  FOR pol IN SELECT tablename, policyname FROM pg_policies
    WHERE schemaname='public'
      AND tablename IN ('fahrzeuge','time_entries')
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
      -- additive Härtungs-Policies NICHT droppen
      AND policyname NOT IN (
        'fahrzeuge_update_driver',
        'fahrzeuge_select_authed','fahrzeuge_update_office_or_driver',
        'fahrzeuge_insert_office','fahrzeuge_delete_office',
        'time_entries_select_authed','time_entries_insert_own_or_office',
        'time_entries_update_own_or_office','time_entries_delete_own_or_office',
        'te_read','te_write'
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', pol.policyname, pol.tablename);
    RAISE NOTICE 'Repair-dropped: %.%', pol.tablename, pol.policyname;
  END LOOP;
END $$;

COMMIT;


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.1) fahrzeuge — STATUS: ✅ APPLIED am 12.06.2026 (Policies erhalten).
-- 1.0a hat die ineffektiven offenen Policies daneben entfernt. Falls v3 die
-- restriktiven Policies NICHT angelegt hatte (sollte aber): folgende re-apply
-- idempotent. DROP-Filter v5-erweitert.
-- ───────────────────────────────────────────────────────────────────────────
-- Idempotenz-Check vor Re-Apply:
--   SELECT policyname FROM pg_policies WHERE schemaname='public' AND tablename='fahrzeuge'
--     AND policyname IN ('fahrzeuge_select_authed','fahrzeuge_update_office_or_driver',
--                        'fahrzeuge_insert_office','fahrzeuge_delete_office');
-- Wenn alle 4 vorhanden → diesen Block SKIPPEN (nur 1.0a-Repair war nötig).


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.2) time_entries — STATUS: ✅ APPLIED am 12.06.2026 (Policies erhalten).
-- 1.0a hat die ineffektiven offenen Policies daneben entfernt.
-- ───────────────────────────────────────────────────────────────────────────
-- Idempotenz-Check vor Re-Apply:
--   SELECT policyname FROM pg_policies WHERE schemaname='public' AND tablename='time_entries'
--     AND policyname IN ('time_entries_select_authed','time_entries_insert_own_or_office',
--                        'time_entries_update_own_or_office','time_entries_delete_own_or_office',
--                        'te_read','te_write');
-- Mindestens die restriktiven 4 (oder das te_read/te_write-Paar) MÜSSEN da sein.


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.3) forms — WRITE auf Projekt-Zuweisung (worker_projects) ODER Office
-- STATUS: ⏳ OFFEN.
-- v4-KORREKTUR: forms.pid → forms.project_id; wp.monteur_id → wp.worker_id.
-- v5-KORREKTUR: DROP-Filter erweitert um auth.role()-Pattern.
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
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.forms', pol.policyname);
    RAISE NOTICE 'Dropped: %', pol.policyname;
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
-- v5-KORREKTUR: DROP-Filter erweitert.
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
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.bautagebuch', pol.policyname);
    RAISE NOTICE 'Dropped: %', pol.policyname;
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
-- Hintergrund: laut App-Changelog v3.9.427/430 gedroppt. Single-Source ist
-- fahrzeuge.schaeden (jsonb). fahrzeuge selbst ist durch Block 1.1+1.0a
-- abgedeckt. Block-Inhalt bewusst entfernt.


-- ───────────────────────────────────────────────────────────────────────────
-- BLOCK 1.6) fahrbewilligungen — SELECT auf own ODER Office
-- STATUS: ⏳ OFFEN. Spalten OK (worker_id verifiziert).
-- v5-KORREKTUR: DROP-Filter erweitert.
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
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.fahrbewilligungen', pol.policyname);
    RAISE NOTICE 'Dropped: %', pol.policyname;
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
-- ⚠️ PRE-CHECK PFLICHT — Spalte `worker_id` in v4 angenommen, vor Apply
-- gegen information_schema verifizieren.
-- v5-KORREKTUR: DROP-Filter erweitert.
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
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.anmeldungen', pol.policyname);
    RAISE NOTICE 'Dropped: %', pol.policyname;
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
-- STATUS: ⏳ OFFEN.
-- v5-KORREKTUR: DROP-Filter erweitert.
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
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
      -- finkzeit_select_own_or_hr (falls von v3.10.5 P0-6 schon eingespielt) erhalten
      AND policyname NOT IN ('finkzeit_select_own_or_hr','finkzeit_select_office_only')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.finkzeit', pol.policyname);
    RAISE NOTICE 'Dropped: %', pol.policyname;
  END LOOP;
END $$;

-- Falls finkzeit_select_own_or_hr bereits aus v3.10.5 existiert → SKIP CREATE.
-- Sonst neu anlegen (Office-only-Variante):
DO $$
BEGIN
  IF NOT EXISTS(SELECT 1 FROM pg_policies
    WHERE schemaname='public' AND tablename='finkzeit'
      AND policyname IN ('finkzeit_select_own_or_hr','finkzeit_select_office_only'))
  THEN
    CREATE POLICY finkzeit_select_office_only ON public.finkzeit
      FOR SELECT TO authenticated USING (public.is_hr());
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
--    -- WICHTIG: prüfen dass KEINE offene auth.role()-Policy mehr daneben steht.
--
-- 2. Snapshot der vorherigen Policies (Rollback-Material):
--    SELECT tablename, policyname, cmd, qual, with_check
--    FROM public._rls_snapshot_v3923
--    WHERE block IN ('1.0a_repair','1.3_forms','1.4_bautagebuch',
--                    '1.6_fahrbewilligungen','1.7_anmeldungen','1.8_finkzeit')
--    ORDER BY block, policyname;
--
-- 3. Live-Smoke pro Block (als Monteur-Token einloggen):
--    - 1.0a: fahrzeuge / time_entries — Monteur sieht/schreibt nur eigene
--    - 1.3:  forms für zugewiesenes Projekt → OK; fremdes → 0/Fail
--    - 1.4:  dito für bautagebuch
--    - 1.6:  fahrbewilligungen → nur eigene
--    - 1.7:  anmeldungen → nur eigene
--    - 1.8:  finkzeit → 0 als Monteur, voll als HR
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
