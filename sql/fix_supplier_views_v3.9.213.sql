-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ============================================================================
-- fix_supplier_views_v3.9.213.sql
-- AUFGABE #5 — supplier-Views: EK-Preis nur fuer admin/projektleiter/buero,
--   techniker/monteur/helfer maskiert (NULL). + security_invoker-Analyse.
--   Supabase project_id: jiggujpruejkaomgxarp
-- ============================================================================
--
-- ZIEL der Aenderung gegenueber LIVE (sql/supplier_articles_safe_view_v3.9.54.sql):
--   ALT-Maske: ek_preis = NULL wenn current_user_role() IN ('monteur','helfer')
--              (d.h. techniker SAH den EK-Preis — ungewollt).
--   NEU-Maske: ek_preis NUR sichtbar wenn current_user_role() IN ('admin','projektleiter','buero'),
--              sonst NULL → techniker/monteur/helfer ALLE maskiert.
--   Spalten + Reihenfolge + Definer-Charakter bleiben sonst IDENTISCH (nur CASE-Logik invertiert/positiv).
--
-- ----------------------------------------------------------------------------
-- 🔴🔴🔴 PFLICHT-PRE-APPLY-VERIFY (security_invoker / Base-RLS / anon)  🔴🔴🔴
-- ----------------------------------------------------------------------------
-- Diese View bleibt BEWUSST SECURITY DEFINER (Default, KEIN security_invoker=true).
-- BEGRUENDUNG aus Repo-Evidenz (sql/migrate_supplier_articles_safe_v3954.sql Z.53-57):
--   Base-Tabelle public.supplier_articles hat RLS ENABLED mit SELECT-Policy
--   `supplier_articles_select_ek_roles ... USING (can_see_ek())`.
--   can_see_ek() = role IN ('admin','projektleiter','buero','lager') (Z.19-25).
--   → monteur / techniker / helfer bekommen aus der BASIS-TABELLE 0 Zeilen.
--   → Mit security_invoker=true wuerde die View fuer monteur/techniker 0 Zeilen
--     liefern → Material-Katalog / Material-Suche BRICHT fuer diese Rollen
--     (index.html L12954 _sbGet supplier_articles_safe → leerer Katalog).
--   Deshalb MUSS die View Definer bleiben (umgeht Base-RLS), und die
--   Preis-Verschleierung passiert in der CASE-Spalte via current_user_role().
--
--   ⚠️ OPERATOR: VOR Apply die folgenden 3 Punkte LIVE pruefen (Supabase SQL-Editor):
--     (a) Base-RLS-SELECT-Policy bestaetigen:
--         SELECT polname, pg_get_expr(polqual, polrelid) AS using_expr
--           FROM pg_policy
--          WHERE polrelid = 'public.supplier_articles'::regclass AND polcmd='r';
--         ERWARTUNG: USING (can_see_ek()) — also monteur NICHT erlaubt.
--         → Falls die Base-RLS inzwischen monteur/techniker SELECT erlaubt (z.B. USING (true)
--           oder authenticated-weit), DANN — und nur dann — waere security_invoker=true
--           moeglich. Selbst dann ist DEFINER zulaessig; security_invoker NICHT zwingend.
--     (b) Kein anon/Portal liest die View:
--         SELECT grantee, privilege_type FROM information_schema.role_table_grants
--          WHERE table_schema='public' AND table_name='supplier_articles_safe';
--         ERWARTUNG: NUR 'authenticated' (+ ggf. service_role/postgres). KEIN 'anon'.
--         (Grep index.html: kein anon-Pfad liest supplier_articles_safe — alle Zugriffe
--          laufen ueber authentifiziertes _sbGet. Portal-anon nutzt diese View NICHT.)
--         → Falls 'anon' GRANT existiert: REVOKE SELECT ... FROM anon (siehe unten, auskommentiert).
--     (c) current_user_role() existiert + ist SECURITY DEFINER + STABLE + SET search_path:
--         SELECT pg_get_functiondef('public.current_user_role()'::regprocedure);
--         ERWARTUNG: liest users.role WHERE auth_user_id=auth.uid(); SECURITY DEFINER.
--
-- ----------------------------------------------------------------------------
-- HINWEIS zur Quelle dieser Definition:
--   Diese CREATE OR REPLACE VIEW basiert 1:1 auf der LIVE-Datei
--   sql/supplier_articles_safe_view_v3.9.54.sql (Z.17-23, im Repo als "APPLIZIERT 2026-06-07"
--   markiert) — d.h. Spaltenliste ist Repo-belegt, KEINE Rekonstruktion. Geaendert wird
--   AUSSCHLIESSLICH die CASE-Bedingung der ek_preis-Spalte.
-- ----------------------------------------------------------------------------

CREATE OR REPLACE VIEW public.supplier_articles_safe AS
SELECT
  id, supplier_id, art_nr, hersteller_art_nr, gtin, bezeichnung, langtext, mengeneinheit,
  listenpreis,
  -- NEU v3.9.213: EK-Preis nur fuer EK-berechtigte Office-Rollen sichtbar (positiv-Liste),
  -- alle anderen (techniker/monteur/helfer + unbekannt) → NULL.
  CASE WHEN public.current_user_role() IN ('admin','projektleiter','buero')
       THEN ek_preis
       ELSE NULL::real
  END AS ek_preis,
  rabatt_prozent, warengruppe, ep_system, ep_gewerk, dimension, verfuegbar, bild_url, last_updated, rabatt_gruppe
FROM public.supplier_articles;

GRANT SELECT ON public.supplier_articles_safe TO authenticated;

-- Optionaler anon-Schutz (NUR ausfuehren falls VERIFY-(b) einen anon-GRANT zeigt):
-- REVOKE SELECT ON public.supplier_articles_safe FROM anon;

-- ============================================================================
-- supplier_articles_public  —  BODY NICHT IM REPO (nur DROP-Referenzen in _archiv/).
-- ============================================================================
-- ⚠️ CAPTURE-PFLICHT vor JEDER Aenderung an dieser View:
--   Die LIVE-Definition von public.supplier_articles_public liegt NICHT im Repo vor.
--   Repo-Evidenz: docs/handoff/SECURITY-ADVISOR-BACKLOG-2026-06-07.md flaggt sie als
--   security_definer_view; _archiv/sql/*.sql enthalten nur `DROP VIEW IF EXISTS
--   public.supplier_articles_public`. → Status unklar (evtl. bereits gedroppt).
--
--   OPERATOR: Existenz + Body + Nutzer live ziehen, BEVOR irgendetwas geaendert wird:
--     SELECT pg_get_viewdef('public.supplier_articles_public'::regclass, true);
--     -- Existenz:
--     SELECT to_regclass('public.supplier_articles_public');
--     -- Grants (liest anon/authenticated diese View?):
--     SELECT grantee, privilege_type FROM information_schema.role_table_grants
--      WHERE table_schema='public' AND table_name='supplier_articles_public';
--
--   FRONTEND-EVIDENZ (Grep ueber index.html, gesamtes Repo 2026-06-09):
--     KEINE Nutzung von 'supplier_articles_public' in index.html. Das Frontend liest
--     den Material-Katalog AUSSCHLIESSLICH ueber 'supplier_articles_safe'
--     (index.html L7672, L12954, plus Diagnostic L810). Referenzen auf _public
--     existieren nur als DROP-Statements in _archiv/sql/ + 1 Doku-Kommentar.
--
--   EMPFEHLUNG: supplier_articles_public DROPPEN (sie wird vom Frontend nicht genutzt
--     und ist als security_definer_view ein offener Advisor-Lint).
--     NUR ausfuehren NACHDEM VERIFY (Grants) bestaetigt hat, dass KEIN anderer
--     Consumer (kein anon/Portal, kein Edge-Function, kein externer Client) sie liest:
--
--   -- DROP VIEW IF EXISTS public.supplier_articles_public;
--
--   (Bewusst auskommentiert — NICHT autonom droppen ohne Live-Grant-Verify.)

-- ============================================================================
-- VERIFY (nach Apply, im SQL-Editor):
-- ----------------------------------------------------------------------------
-- 1) View existiert + Spalten unveraendert (20 Spalten, ek_preis dabei):
--    SELECT column_name, data_type FROM information_schema.columns
--     WHERE table_schema='public' AND table_name='supplier_articles_safe'
--     ORDER BY ordinal_position;
--
-- 2) Als Admin-/Service-Sicht: ek_preis weiterhin befuellt (Gesamtzahl unveraendert):
--    SELECT count(*), count(ek_preis) FROM public.supplier_articles_safe;
--    -- ERWARTUNG (admin/projektleiter/buero-Session): count(ek_preis) > 0.
--
-- 3) Rollen-Maske (jeweils echte Session pro Rolle noetig):
--    -- admin/projektleiter/buero  → ek_preis sichtbar (NOT NULL fuer befuellte Artikel)
--    -- techniker/monteur/helfer   → ek_preis IMMER NULL
--    SELECT current_setting('request.jwt.claims', true);  -- Rolle der Session belegen
--    SELECT id, ek_preis FROM public.supplier_articles_safe LIMIT 5;
--
-- 4) Material-Katalog bricht NICHT fuer monteur/techniker (Zeilen kommen trotzdem,
--    nur ek_preis=NULL — Frontend faellt auf listenpreis/"—" zurueck):
--    -- (monteur-Session) SELECT count(*) FROM public.supplier_articles_safe; → > 0 erwartet.
-- ============================================================================
