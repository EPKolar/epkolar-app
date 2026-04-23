-- =====================================================================
-- B-006b + B-007 FINAL — Ausgeführte Migration (17.04.2026 ~21:50)
-- Archivierte Fassung der Live-Ausführung via Browser-Chrome-MCP
-- in Supabase SQL-Editor Tab 1454480885.
-- DB-Verifikation: helpers=4, b007_total=22, rls_zero_left=0,
--   per_table={AS:2, TE:2, notif:4, urlaub:4, fb:2, chk:2, komm:4, komp:2}
-- Idempotent (kann mehrfach ausgeführt werden).
-- =====================================================================

-- ─── SCHRITT 0: CLEANUP — Alt-Policies sauber droppen ───────────────
-- Entfernt Reste aus v3.5.71→v3.5.85 RLS-Experimenten, bevor finale
-- Policies angelegt werden. Reine Bereinigung, keine Datenänderung.

DO $$ DECLARE t text; r record; BEGIN
  FOR r IN
    SELECT schemaname, tablename, policyname
    FROM pg_policies
    WHERE schemaname='public'
      AND tablename IN (
        'arbeitsscheine','time_entries','notifications','urlaubsantraege',
        'fahrtenbuch','as_checklist','as_kommentare','worker_kompetenzen',
        'users','projects','supplier_articles','supplier_configs',
        'material_items','material_orders','bautagebuch','project_documents',
        'fahrzeug_buchungen','activity_log','as_vorlagen','juprowa_log',
        'system_config','fahrzeuge','werkzeuge','monteure','abs',
        'project_plans','checklisten','photos'
      )
      AND policyname IN (
        'auth all','anon_read','Enable read access for all users',
        'role_filtered_as','role_filtered_te','role_filtered_urlaub',
        'own_notifications','own_notifs'
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I', r.policyname, r.tablename);
  END LOOP;
END $$;

DROP VIEW IF EXISTS public.supplier_articles_public;

-- ─── SCHRITT 1: B-006b — RLS + authenticated-Policies auf Base-Tables ─

DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY[
    'users','projects','supplier_articles','supplier_configs',
    'material_items','material_orders','bautagebuch','project_documents',
    'fahrzeug_buchungen','activity_log','as_vorlagen','juprowa_log',
    'system_config','fahrzeuge','werkzeuge','monteure','abs',
    'project_plans','checklisten','photos'
  ] LOOP
    BEGIN
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
      EXECUTE format('DROP POLICY IF EXISTS "anon_read" ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS "Enable read access for all users" ON public.%I', t);
      EXECUTE format('DROP POLICY IF EXISTS "authenticated_read_%s" ON public.%I', t, t);
      EXECUTE format('DROP POLICY IF EXISTS "authenticated_write_%s" ON public.%I', t, t);
      EXECUTE format('CREATE POLICY "authenticated_read_%s" ON public.%I FOR SELECT TO authenticated USING (true)', t, t);
      EXECUTE format('CREATE POLICY "authenticated_write_%s" ON public.%I FOR ALL TO authenticated USING (true) WITH CHECK (true)', t, t);
    EXCEPTION WHEN undefined_table THEN NULL; END;
  END LOOP;
END $$;

-- ─── SCHRITT 2: B-007 Helper-Funktionen (4×) ───────────────────────

CREATE OR REPLACE FUNCTION public.current_monteur_id() RETURNS text AS $$
  SELECT monteur_id FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE OR REPLACE FUNCTION public.current_user_role() RETURNS text AS $$
  SELECT role FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE OR REPLACE FUNCTION public.current_user_pk() RETURNS text AS $$
  SELECT id FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE OR REPLACE FUNCTION public.is_staff() RETURNS boolean AS $$
  SELECT (SELECT role FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1)
         IN ('admin','projektleiter','buero');
$$ LANGUAGE sql SECURITY DEFINER STABLE;

GRANT EXECUTE ON FUNCTION public.current_monteur_id() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_role()  TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_pk()    TO authenticated;
GRANT EXECUTE ON FUNCTION public.is_staff()           TO authenticated;

-- ─── SCHRITT 3: B-007 — arbeitsscheine (2 Policies) ────────────────

ALTER TABLE public.arbeitsscheine ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "authenticated_read"                 ON public.arbeitsscheine;
DROP POLICY IF EXISTS "authenticated_read_arbeitsscheine"  ON public.arbeitsscheine;
DROP POLICY IF EXISTS "authenticated_write_arbeitsscheine" ON public.arbeitsscheine;
DROP POLICY IF EXISTS "role_filtered_as"                   ON public.arbeitsscheine;
DROP POLICY IF EXISTS "role_filtered_as_read"              ON public.arbeitsscheine;
DROP POLICY IF EXISTS "role_filtered_as_write"             ON public.arbeitsscheine;

CREATE POLICY "role_filtered_as_read" ON public.arbeitsscheine
  FOR SELECT TO authenticated
  USING (public.is_staff() OR monteur = public.current_monteur_id());

CREATE POLICY "role_filtered_as_write" ON public.arbeitsscheine
  FOR ALL TO authenticated
  USING (public.is_staff() OR monteur = public.current_monteur_id())
  WITH CHECK (public.is_staff() OR monteur = public.current_monteur_id());

-- ─── SCHRITT 4: B-007 — time_entries (2 Policies) ──────────────────

ALTER TABLE public.time_entries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "authenticated_read"              ON public.time_entries;
DROP POLICY IF EXISTS "authenticated_read_time_entries" ON public.time_entries;
DROP POLICY IF EXISTS "authenticated_write_time_entries" ON public.time_entries;
DROP POLICY IF EXISTS "role_filtered_te_read"           ON public.time_entries;
DROP POLICY IF EXISTS "role_filtered_te_write"          ON public.time_entries;

CREATE POLICY "role_filtered_te_read" ON public.time_entries
  FOR SELECT TO authenticated
  USING (public.is_staff() OR worker_id = public.current_monteur_id());

CREATE POLICY "role_filtered_te_write" ON public.time_entries
  FOR ALL TO authenticated
  USING (public.is_staff() OR worker_id = public.current_monteur_id())
  WITH CHECK (public.is_staff() OR worker_id = public.current_monteur_id());

-- ─── SCHRITT 5: B-007 — notifications (4 Policies) ─────────────────

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "authenticated_read"               ON public.notifications;
DROP POLICY IF EXISTS "authenticated_read_notifications" ON public.notifications;
DROP POLICY IF EXISTS "authenticated_write_notifications" ON public.notifications;
DROP POLICY IF EXISTS "own_notifications"                ON public.notifications;
DROP POLICY IF EXISTS "own_notifs"                       ON public.notifications;
DROP POLICY IF EXISTS "own_notifs_read"                  ON public.notifications;
DROP POLICY IF EXISTS "own_notifs_write"                 ON public.notifications;
DROP POLICY IF EXISTS "own_notifs_update"                ON public.notifications;
DROP POLICY IF EXISTS "own_notifs_delete"                ON public.notifications;
DROP POLICY IF EXISTS "any_auth_insert"                  ON public.notifications;

CREATE POLICY "any_auth_insert" ON public.notifications
  FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "own_notifs_read" ON public.notifications
  FOR SELECT TO authenticated USING (user_id = public.current_user_pk());

CREATE POLICY "own_notifs_update" ON public.notifications
  FOR UPDATE TO authenticated
  USING (user_id = public.current_user_pk())
  WITH CHECK (user_id = public.current_user_pk());

CREATE POLICY "own_notifs_delete" ON public.notifications
  FOR DELETE TO authenticated USING (user_id = public.current_user_pk());

-- ─── SCHRITT 6: B-007 — urlaubsantraege (4 Policies) ───────────────

ALTER TABLE public.urlaubsantraege ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all"                            ON public.urlaubsantraege;
DROP POLICY IF EXISTS "authenticated_read_urlaubsantraege"  ON public.urlaubsantraege;
DROP POLICY IF EXISTS "authenticated_write_urlaubsantraege" ON public.urlaubsantraege;
DROP POLICY IF EXISTS "role_filtered_urlaub"                ON public.urlaubsantraege;
DROP POLICY IF EXISTS "urlaub_read"                         ON public.urlaubsantraege;
DROP POLICY IF EXISTS "urlaub_insert"                       ON public.urlaubsantraege;
DROP POLICY IF EXISTS "urlaub_update"                       ON public.urlaubsantraege;
DROP POLICY IF EXISTS "urlaub_delete"                       ON public.urlaubsantraege;

CREATE POLICY "urlaub_read" ON public.urlaubsantraege
  FOR SELECT TO authenticated
  USING (public.is_staff() OR worker_id = public.current_monteur_id());

CREATE POLICY "urlaub_insert" ON public.urlaubsantraege
  FOR INSERT TO authenticated
  WITH CHECK (worker_id = public.current_monteur_id() OR public.is_staff());

CREATE POLICY "urlaub_update" ON public.urlaubsantraege
  FOR UPDATE TO authenticated
  USING (public.is_staff() OR (worker_id = public.current_monteur_id() AND status = 'beantragt'))
  WITH CHECK (public.is_staff() OR (worker_id = public.current_monteur_id() AND status = 'beantragt'));

CREATE POLICY "urlaub_delete" ON public.urlaubsantraege
  FOR DELETE TO authenticated
  USING (public.is_staff() OR (worker_id = public.current_monteur_id() AND status = 'beantragt'));

-- ─── SCHRITT 7: B-007 — fahrtenbuch (2 Policies) ───────────────────

ALTER TABLE public.fahrtenbuch ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all"                        ON public.fahrtenbuch;
DROP POLICY IF EXISTS "authenticated_read_fahrtenbuch"  ON public.fahrtenbuch;
DROP POLICY IF EXISTS "authenticated_write_fahrtenbuch" ON public.fahrtenbuch;
DROP POLICY IF EXISTS "fahrtenbuch_read"                ON public.fahrtenbuch;
DROP POLICY IF EXISTS "fahrtenbuch_write"               ON public.fahrtenbuch;

CREATE POLICY "fahrtenbuch_read" ON public.fahrtenbuch
  FOR SELECT TO authenticated
  USING (public.is_staff() OR worker_id = public.current_monteur_id());

CREATE POLICY "fahrtenbuch_write" ON public.fahrtenbuch
  FOR ALL TO authenticated
  USING (public.is_staff() OR worker_id = public.current_monteur_id())
  WITH CHECK (public.is_staff() OR worker_id = public.current_monteur_id());

-- ─── SCHRITT 8: B-007 — as_checklist (2 Policies) ──────────────────

ALTER TABLE public.as_checklist ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all"                         ON public.as_checklist;
DROP POLICY IF EXISTS "authenticated_read_as_checklist"  ON public.as_checklist;
DROP POLICY IF EXISTS "authenticated_write_as_checklist" ON public.as_checklist;
DROP POLICY IF EXISTS "checklist_read"                   ON public.as_checklist;
DROP POLICY IF EXISTS "checklist_write"                  ON public.as_checklist;

CREATE POLICY "checklist_read" ON public.as_checklist
  FOR SELECT TO authenticated
  USING (public.is_staff() OR EXISTS(
    SELECT 1 FROM public.arbeitsscheine a
    WHERE a.id = as_id AND a.monteur = public.current_monteur_id()
  ));

CREATE POLICY "checklist_write" ON public.as_checklist
  FOR ALL TO authenticated
  USING (public.is_staff() OR EXISTS(
    SELECT 1 FROM public.arbeitsscheine a
    WHERE a.id = as_id AND a.monteur = public.current_monteur_id()
  ))
  WITH CHECK (public.is_staff() OR EXISTS(
    SELECT 1 FROM public.arbeitsscheine a
    WHERE a.id = as_id AND a.monteur = public.current_monteur_id()
  ));

-- ─── SCHRITT 9: B-007 — as_kommentare (4 Policies) ─────────────────

ALTER TABLE public.as_kommentare ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all"                          ON public.as_kommentare;
DROP POLICY IF EXISTS "authenticated_read_as_kommentare"  ON public.as_kommentare;
DROP POLICY IF EXISTS "authenticated_write_as_kommentare" ON public.as_kommentare;
DROP POLICY IF EXISTS "komm_read"                         ON public.as_kommentare;
DROP POLICY IF EXISTS "komm_insert"                       ON public.as_kommentare;
DROP POLICY IF EXISTS "komm_update_delete"                ON public.as_kommentare;
DROP POLICY IF EXISTS "komm_update"                       ON public.as_kommentare;
DROP POLICY IF EXISTS "komm_delete"                       ON public.as_kommentare;

CREATE POLICY "komm_read" ON public.as_kommentare
  FOR SELECT TO authenticated
  USING (public.is_staff() OR EXISTS(
    SELECT 1 FROM public.arbeitsscheine a
    WHERE a.id = as_id AND a.monteur = public.current_monteur_id()
  ));

CREATE POLICY "komm_insert" ON public.as_kommentare
  FOR INSERT TO authenticated
  WITH CHECK (autor_id = public.current_user_pk());

CREATE POLICY "komm_update" ON public.as_kommentare
  FOR UPDATE TO authenticated
  USING (public.is_staff() OR autor_id = public.current_user_pk())
  WITH CHECK (public.is_staff() OR autor_id = public.current_user_pk());

CREATE POLICY "komm_delete" ON public.as_kommentare
  FOR DELETE TO authenticated
  USING (public.is_staff() OR autor_id = public.current_user_pk());

-- ─── SCHRITT 10: B-007 — worker_kompetenzen (2 Policies) ───────────

ALTER TABLE public.worker_kompetenzen ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "auth all"                              ON public.worker_kompetenzen;
DROP POLICY IF EXISTS "authenticated_read_worker_kompetenzen"  ON public.worker_kompetenzen;
DROP POLICY IF EXISTS "authenticated_write_worker_kompetenzen" ON public.worker_kompetenzen;
DROP POLICY IF EXISTS "komp_read_all"                         ON public.worker_kompetenzen;
DROP POLICY IF EXISTS "komp_write_admin"                      ON public.worker_kompetenzen;

CREATE POLICY "komp_read_all" ON public.worker_kompetenzen
  FOR SELECT TO authenticated USING (true);

CREATE POLICY "komp_write_admin" ON public.worker_kompetenzen
  FOR ALL TO authenticated
  USING (public.is_staff())
  WITH CHECK (public.is_staff());

-- =====================================================================
-- VERIFIKATION
-- =====================================================================

-- Helper-Funktionen (Erwartet: 4)
SELECT routine_name FROM information_schema.routines
WHERE routine_schema='public'
  AND routine_name IN ('current_monteur_id','current_user_role','current_user_pk','is_staff')
ORDER BY routine_name;

-- B-007 Policies-Verteilung (Erwartet: 22 gesamt)
SELECT tablename, COUNT(*) AS policy_count
FROM pg_policies
WHERE schemaname='public'
  AND tablename IN ('arbeitsscheine','time_entries','notifications',
                    'urlaubsantraege','fahrtenbuch','as_checklist',
                    'as_kommentare','worker_kompetenzen')
GROUP BY tablename
ORDER BY tablename;

-- RLS-enabled Tabellen ohne Policies (Erwartet: 0)
SELECT t.tablename
FROM pg_tables t
LEFT JOIN pg_policies p ON p.schemaname=t.schemaname AND p.tablename=t.tablename
WHERE t.schemaname='public'
  AND t.rowsecurity=true
  AND p.policyname IS NULL;
