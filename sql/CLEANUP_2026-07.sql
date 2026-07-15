-- CLEANUP_2026-07.sql  v2  ·  Stand 2026-07-15 (Live-Inventur + verifizierte Namen)
-- Gegenstueck zu docs/db/HYGIENE_READ_QUERIES_2026-07.sql + RLS_SNAPSHOT_2026-07-15.md.
-- Live-Reads #1-7 (Chat-Claude 15.07. ~19:1x) gelaufen; Zahlen unten daraus.
--
-- HARTE REGEL (CLAUDE.md: sql/ ist eine geladene Waffe): bei Run-all laeuft NUR
-- read-only (die Nachweis-SELECTs). JEDE DROP/DELETE/UPDATE/ALTER-Zeile ist
-- AUSKOMMENTIERT. Ausfuehrung sektionsweise durch Chat-Claude/Sebastian: pro
-- Sektion Backup -> Verify-SELECT (== Erwartung) -> Block ent-kommentieren +
-- ausfuehren -> Gegenzaehlung. Reihenfolge S1 -> (Kiosk+Login-Check) -> S2 -> S3.
-- S4 je einzelnes Sebastian-ja.
-- ============================================================================


-- ============================================================================
-- S1  63 tote lager_display_no_<cmd>-Policies droppen  ·  Risiko: MITTEL
-- ★ AUSGEFUEHRT 15.07.2026 ~19:5x (Chat-Claude): 63/63 gedroppt, Gegenzaehlung 0/0,
--   Ersatz 7 no_kiosk + is_kiosk_role/kiosk_fahrzeuge/login_lookup vorhanden, Kiosk-
--   Funktionscheck gruen (v711, FZ:21·Spez:1, 🚛 rendert). Backup: docs/db/policies-backup-2026-07-15.json. ERLEDIGT.
--     Live-Befund #3: 63 RESTRICTIVE-Policies pruefen app_metadata (falsche
--     Rollenquelle) -> waren NIE wirksam (v695). Ersatz AKTIV: is_kiosk_role()=1,
--     7 *_no_kiosk-Policies. Namen verifiziert (51x no_select + je 4x no_delete/
--     insert/update auf arbeitsscheine/projects/weekplan_rows/workers).
--     BACKUP zuerst: pg_policies-Volldump -> docs/db/policies-backup-2026-07-15.json.
-- ============================================================================

-- 1a) Verify (gefahrlos) -- ERWARTUNG: 63.
SELECT count(*) AS s1_policies_ERWARTET_63
FROM pg_policies
WHERE schemaname='public'
  AND (policyname LIKE 'lager_display_no_%'
       OR qual ILIKE '%app_metadata%' OR with_check ILIKE '%app_metadata%');

-- 1b) Ersatz aktiv? -- ERWARTUNG: no_kiosk=7, is_kiosk_role=1.
SELECT
  (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND policyname LIKE '%_no_kiosk%') AS no_kiosk_ERWARTET_7,
  (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='is_kiosk_role') AS is_kiosk_role_ERWARTET_1;

-- 1c) DIE 63 DROPS -- zum Ausfuehren diesen Block ent-kommentieren (nach 1a==63, 1b==(7,1)).
-- DROP POLICY IF EXISTS lager_display_no_select ON public.absence_files;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.absences;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.activity_log;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.anmeldungen;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.arbeitsscheine;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.as_checklist;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.as_kommentare;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.as_vorlagen;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.bauprovisorien;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.bauprovisorien_mieten;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.bautagebuch;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.bescheinigungen;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.checklists;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.defects;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.exports;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.fahrbewilligungen;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.fahrtenbuch;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.fahrzeug_buchungen;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.fahrzeuge;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.finkzeit;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.forms;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.fz_termine;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.gefahrstoff_files;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.gefahrstoff_folders;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.juprowa_config;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.juprowa_log;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.kunden;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.material_catalogs;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.material_items;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.material_orders;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.notifications;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.photos;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.plans;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.project_documents;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.project_folders;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.projects;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.supplier_articles;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.supplier_configs;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.supplier_orders;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.system_config;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.tickets;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.time_entries;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.urlaubsantraege;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.urlaubskontingent;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.users;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.weekplans;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.werkzeuge;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.worker_kompetenzen;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.worker_projects;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.workers;
-- DROP POLICY IF EXISTS lager_display_no_select ON public.wz_service;
-- --
-- DROP POLICY IF EXISTS lager_display_no_delete ON public.arbeitsscheine;
-- DROP POLICY IF EXISTS lager_display_no_delete ON public.projects;
-- DROP POLICY IF EXISTS lager_display_no_delete ON public.weekplan_rows;
-- DROP POLICY IF EXISTS lager_display_no_delete ON public.workers;
-- --
-- DROP POLICY IF EXISTS lager_display_no_insert ON public.arbeitsscheine;
-- DROP POLICY IF EXISTS lager_display_no_insert ON public.projects;
-- DROP POLICY IF EXISTS lager_display_no_insert ON public.weekplan_rows;
-- DROP POLICY IF EXISTS lager_display_no_insert ON public.workers;
-- --
-- DROP POLICY IF EXISTS lager_display_no_update ON public.arbeitsscheine;
-- DROP POLICY IF EXISTS lager_display_no_update ON public.projects;
-- DROP POLICY IF EXISTS lager_display_no_update ON public.weekplan_rows;
-- DROP POLICY IF EXISTS lager_display_no_update ON public.workers;

-- 1d) Gegenzaehlung nach dem Drop (gefahrlos) -- ERWARTUNG: 0.
--   SELECT count(*) FROM pg_policies WHERE schemaname='public'
--     AND (policyname LIKE 'lager_display_no_%' OR qual ILIKE '%app_metadata%');
-- -> danach FUNKTIONS-CHECK vor S2: lager_display laedt (?screen=planung), Login geht.


-- ============================================================================
-- S2  Verwaiste Funktionen  ·  Risiko: MITTEL-HOCH  ·  Live #4: 34 Fn public.
--     Drop nur bei DREIFACH-0: (i) kein Trigger (Read #4a) UND (ii) keine
--     Fn->Fn/Trigger-Crossref (pg_proc-Body-Scan, Chat-Claude beim S2-Lauf) UND
--     (iii) 0 Treffer als String/RPC in index.html (Client-Grep, CC).
--     Ohne beidseitigen 0-Beweis bleibt die Funktion STEHEN. guard_urlaub_edit tabu.
-- ============================================================================

-- 2a) Roh-Kandidaten (gefahrlos): Fn ohne Trigger, ohne die bekannt-referenzierten.
SELECT p.proname AS kandidat, pg_get_function_identity_arguments(p.oid) AS args
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' AND p.prokind='f'
  AND NOT EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgfoid=p.oid)
  AND p.proname NOT IN (
    'is_kiosk_role','auth_role','is_staff',
    'guard_kontingent','guard_projects','guard_admin_only','guard_urlaub_edit','guard_users_privilege',
    'kiosk_fahrzeuge','kiosk_field_workers','kiosk_week_absences','kiosk_week_arbeitsscheine',
    'stempel_terminal_workers','admin_create_user','admin_reset_password','login_lookup','portal_fetch',
    'juprowa_fetch_kunden','juprowa_fetch_monteure','juprowa_fetch_worksheets',
    'juprowa_get_config','juprowa_push_worksheet','juprowa_update_passport'
  )
ORDER BY p.proname;
-- 2b) CLIENT-GREP (CC, je Kandidat aus 2a): grep -c "\b<name>\b" index.html == 0
--     UND grep -c "/rpc/<name>" index.html == 0. Ergebnis hier eintragen.
-- 2c) DROP erst nach (i)+(ii)+(iii): -- DROP FUNCTION IF EXISTS public.<fn>(<args>);


-- ============================================================================
-- S3  Daten-Reparatur  ·  Live #5
-- ============================================================================

-- 3.1  absences-Waisen: Live-Befund = 0. GEPRUEFT, SAUBER. Nichts zu tun.

-- 3.2  weekplan_rows: genau 1 Zeile mit z als JSON-STRING (v502-Altlast).
--      row_id = cef82eae-fc46-4103-930e-d9644f2877d4.
-- ★ AUSGEFUEHRT 15.07.2026 (Chat-Claude): repariert (string->object), Rest-Strings 0.
--   Inhalt war ein leeres KW26-Raster (Backup docs/db/cleanup-backup-2026-07-15-weekplan_z.json belegt). ERLEDIGT.
-- Schritt A (gefahrlos): Zeile fuer's Backup -> docs/db/cleanup-backup-2026-07-15-weekplan_z.json.
SELECT row_id, year, week, jsonb_typeof(z) AS z_typ, z
FROM public.weekplan_rows
WHERE row_id='cef82eae-fc46-4103-930e-d9644f2877d4';   -- ERWARTUNG: 1 Zeile, z_typ=string
-- Schritt B -- Reparatur (nach Backup ent-kommentieren) -- ERWARTUNG: 1 Zeile.
-- -- UPDATE public.weekplan_rows SET z=(z #>> '{}')::jsonb
-- --   WHERE row_id='cef82eae-fc46-4103-930e-d9644f2877d4' AND jsonb_typeof(z)='string';
-- Gegenprobe (ERWARTUNG: 0):
-- --   SELECT count(*) FROM public.weekplan_rows WHERE jsonb_typeof(z)='string';

-- 3.3  tank_log Base64 (9,3 MB / 7 FZ) -> Performance-Fix 1, NICHT hier.
--      stempel_log/fz_positions-Retention -> eigenes Skript, spaeter.


-- ============================================================================
-- S4  Struktur-Aenderungen -- je EINZELN, je ein Sebastian-ja + Backup. AUS.
-- ============================================================================

-- S4-1  public.weekplans (Legacy) -- Live: 11 Zeilen.
-- Staleness-Check (gefahrlos, updated_at existiert):
--   SELECT count(*) AS zeilen, max(updated_at) AS letzte_aenderung FROM public.weekplans;  -- ERW: 11
-- Backup -> docs/db/weekplans-final-backup-2026-07.json (11 Zeilen).
-- -- TODO nach Sebastian-ja #1 + Backup:  DROP TABLE IF EXISTS public.weekplans;

-- S4-2  urlaubskontingent.urlaub (deprecated seit v648) -- 0 Non-NULL -> gefahrlos.
-- Live: 0 Non-NULL-Werte. Praezisionscheck (Chat-Claude, \m/\M + NEW./OLD.-Match auf prosrc):
-- der Trigger guard_kontingent referenziert die SPALTE urlaub NICHT -- die Treffer waren der
-- Tabellenname 'urlaubskontingent'. Kein Trigger-Fix noetig, DROP COLUMN gefahrlos.
--   SELECT count(*) FILTER (WHERE urlaub IS NOT NULL) FROM public.urlaubskontingent;  -- ERW: 0
-- -- TODO nach Sebastians woertlichem "droppen" (+ Backup):
-- -- ALTER TABLE public.urlaubskontingent DROP COLUMN IF EXISTS urlaub;

-- S4-3  _backup_arbeitsscheine_status_pre_a2_20260630 (NEU) -- Live: 108 Zeilen, 264 kB.
-- Backup -> docs/db/backup-arbeitsscheine-status-pre-a2.json (108 Zeilen).
--   SELECT count(*) FROM public._backup_arbeitsscheine_status_pre_a2_20260630;  -- ERW: 108
-- -- TODO nach Sebastian-ja #3 + Backup:
-- -- DROP TABLE IF EXISTS public._backup_arbeitsscheine_status_pre_a2_20260630;

-- S4-4  Retention-FRAGEN an Sebastian (nur formuliert, kein Code):
-- F-A) notifications 739 Zeilen / 2,5 MB -- Vorschlag: gelesene Notifs > 90 Tage loeschen?
-- F-B) activity_log 8.446 Zeilen / 1,9 MB -- Vorschlag: Eintraege > 6 Monate loeschen?
--      -> bei ja je ein eigenes, gereviewtes Retention-Skript.


-- ============================================================================
-- BEHALTEN: kunden (6.463, OFFA) · finkzeit (0, Mirror) · fahrzeuge 9,3 MB (-> Perf-Fix 1)
--   · Storage epkolar-files 8/epkolar-docs 16 · auth.*/storage.* · guard_urlaub_edit
--   · plz_geo/plz_distanz/montagezulage_tage (gestaged).
-- AUTH-HYGIENE: Live 0 NULL-Token-User -> sauber, erledigt.
-- ============================================================================
