-- ═══════════════════════════════════════════════════════════════════════════
-- CLEANUP_2026-07.sql  ·  Stand 2026-07-15 (scharfgestellt nach Live-Inventur)
-- Gegenstueck zu docs/db/HYGIENE_READ_QUERIES_2026-07.sql + RLS_SNAPSHOT_2026-07-15.md.
-- Live-Reads #1–#7 sind am 15.07. ~19:0x (Chat-Claude) gelaufen; die Erwartungs-
-- zahlen unten stammen daraus.
--
-- ┌─ HARTE REGEL (CLAUDE.md: „sql/ ist eine geladene Waffe") ─────────────────┐
-- │ Diese Datei bleibt bei „Run all" GEFAHRLOS: es laufen NUR read-only        │
-- │ Nachweis-/Generator-SELECTs. Kein DROP/DELETE/ALTER ist hier scharf.        │
-- │ Das Loeschen selbst passiert sektionsweise ueber die von den Generatoren    │
-- │ ERZEUGTEN Statements — Chat-Claude/Sebastian prueft die Ausgabe (Zahl ==     │
-- │ Erwartung) und fuehrt sie dann bewusst aus. S4 zusaetzlich: je ein          │
-- │ einzelnes Sebastian-„ja". Reihenfolge S1 → (Kiosk+Login-Check) → S2 → S3.   │
-- └───────────────────────────────────────────────────────────────────────────┘
-- ═══════════════════════════════════════════════════════════════════════════


-- ═══════════════════════════════════════════════════════════════════════════
-- S1  63 tote app_metadata-Kiosk-Policies droppen  ·  Risiko: MITTEL
--     Live-Befund #3: 63 Policies auf 52 Tabellen pruefen app_metadata
--     (Familie lager_display_no_select/_no_update/_no_delete/_no_insert, alle
--     RESTRICTIVE) — waren NIE wirksam (falsche Rollenquelle, v695-Befund).
--     Ersatz AKTIV verifiziert: is_kiosk_role() existiert (1 Fn), 7 Policies
--     nutzen sie (KIOSK_RESTRICTIVE_FIX_v1 ist gelaufen). Drop daher gefahrlos.
-- ═══════════════════════════════════════════════════════════════════════════

-- 1a) Kontrolle vor dem Drop (gefahrlos) — ERWARTUNG: exakt 63.
SELECT count(*) AS s1_app_metadata_policies_ERWARTET_63
FROM pg_policies
WHERE schemaname='public' AND qual ILIKE '%app_metadata%';

-- 1b) Ersatz aktiv? — ERWARTUNG: no_kiosk = 7 UND is_kiosk_role = 1.
SELECT
  (SELECT count(*) FROM pg_policies WHERE schemaname='public' AND policyname LIKE '%_no_kiosk%') AS ersatz_no_kiosk_ERWARTET_7,
  (SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname='is_kiosk_role') AS is_kiosk_role_ERWARTET_1;

-- 1c) GENERATOR (gefahrlos): erzeugt exakt die 63 DROP-Statements. Chat-Claude/
--     Sebastian: Ausgabe pruefen (== 63 Zeilen, Namen plausibel), DANN ausfuehren.
--     Nur wenn 1a==63 UND 1b==(7,1). Weicht 1a ab -> STOPP, zurueck an Read #3.
SELECT string_agg(
         'DROP POLICY IF EXISTS '||quote_ident(policyname)||' ON public.'||quote_ident(tablename)||';',
         E'\n' ORDER BY tablename, policyname
       ) AS s1_drop_statements_zum_ausfuehren
FROM pg_policies
WHERE schemaname='public' AND qual ILIKE '%app_metadata%';

-- 1d) Nach dem Drop Gegenzaehlung (gefahrlos) — ERWARTUNG: 0.
--     SELECT count(*) FROM pg_policies WHERE schemaname='public' AND qual ILIKE '%app_metadata%';
--   → danach FUNKTIONS-CHECK vor S2: lager_display laedt (Kiosk ?screen=planung),
--     normaler Login geht. Erst dann S2.


-- ═══════════════════════════════════════════════════════════════════════════
-- S2  Verwaiste Funktionen  ·  Risiko: MITTEL–HOCH
--     Live-Befund #4: 34 Funktionen im public-Schema. Drop nur bei DREIFACH-0:
--       (i)  haengt an KEINEM Trigger (Read #4a),
--       (ii) ruft/aufgerufen von KEINER anderen DB-Funktion (pg_proc-Body-Scan,
--            Chat-Claude — „Fn ruft Fn" zaehlt NICHT als verwaist),
--       (iii) 0 Treffer als String/RPC in index.html (Client-Grep, CC).
--     guard_urlaub_edit + alle in 2a gelisteten NIE anfassen.
-- ═══════════════════════════════════════════════════════════════════════════

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

-- 2b) CLIENT-GREP-BEWEIS (CC, gegen den aktuellen index.html-Stand):
--     Fuer JEDEN Namen aus 2a im Arbeitsklon laufen lassen — nur 0 = droppbar:
--       grep -c "\b<name>\b" index.html        (0 = kein Client-Ref)
--       grep -c "/rpc/<name>" index.html        (0 = kein RPC-Aufruf)
--     Ergebnis je Kandidat hier als Kommentar eintragen, bevor gedroppt wird.
--     (Kandidatenliste steht erst nach Read #4a fest -> dann Grep -> dann Drop.)
--
-- 2c) DESTRUKTIV — bleibt AUSKOMMENTIERT bis (i)+(ii)+(iii) je Objekt erfuellt:
-- -- DROP FUNCTION IF EXISTS public.<verwaiste_fn>(<exakte_args_aus_2a>);
-- -- (Signatur exakt uebernehmen; Guard-Funktionen NIEMALS eintragen.)


-- ═══════════════════════════════════════════════════════════════════════════
-- S3  Daten-Reparatur (KEINE Massen-Loeschung)  ·  Risiko: NIEDRIG (1 Zeile)
--     Live-Befund #5: absences ohne Worker = 0  -> Sektion 3.1 ENTFAELLT.
--     weekplan_rows mit z-als-String = genau 1 Zeile (v502-Altlast) -> gezielt.
-- ═══════════════════════════════════════════════════════════════════════════

-- 3.1  absences-Waisen: Live-Befund = 0. Nichts zu tun. (Keine Zeile.)

-- 3.2  weekplan_rows: genau 1 Zeile hat z als JSON-STRING statt jsonb-Objekt.
-- Schritt A (gefahrlos): die eine Zeile identifizieren + fuer's Backup zeigen.
SELECT row_id, year, week, jsonb_typeof(z) AS z_typ, z
FROM public.weekplan_rows
WHERE jsonb_typeof(z) = 'string';   -- ERWARTUNG: genau 1 Zeile

-- Schritt B — Reparatur (den String einmal nach jsonb-Objekt aufloesen).
-- AUSKOMMENTIERT bis Schritt A die row_id zeigt UND die Zeile als
-- docs/db/cleanup-backup-2026-07-15-weekplan_z.json gesichert ist.
-- Nur diese EINE row_id einsetzen (kein tabellenweiter UPDATE):
-- -- UPDATE public.weekplan_rows
-- --   SET z = (z #>> '{}')::jsonb          -- JSON-String -> jsonb-Objekt
-- --   WHERE row_id = '<row_id_aus_Schritt_A>' AND jsonb_typeof(z)='string';
-- Gegenprobe nach dem Lauf (ERWARTUNG: 0):
-- --   SELECT count(*) FROM public.weekplan_rows WHERE jsonb_typeof(z)='string';

-- 3.3  stempel_log / fz_positions / tank_log: KEIN Cleanup hier.
--   - tank_log Base64 (9,3 MB, 7 FZ) laeuft ueber Performance-Fix 1, NICHT hier.
--   - Retention stempel_log/fz_positions = eigenes gereviewtes Skript, spaeter.


-- ═══════════════════════════════════════════════════════════════════════════
-- S4  SCHWERE Struktur-Aenderungen — je EINZELN, je ein Sebastian-„ja" + Backup.
--     DEFAULT KOMPLETT AUSKOMMENTIERT. „Run all" loest nichts aus.
-- ═══════════════════════════════════════════════════════════════════════════

-- ── S4-1  public.weekplans (Legacy) — Live-Befund: 11 Zeilen ────────────────
-- Backup ZUERST (gefahrlos): Ergebnis als docs/db/weekplans-final-backup-2026-07.json
-- sichern (11 Zeilen), damit der Drop jederzeit rueckholbar ist.
--   SELECT * FROM public.weekplans;    -- ERWARTUNG: 11 Zeilen
-- -- TODO — nur nach Sebastian-„ja" #1 + Backup-JSON im Repo:
-- -- DROP TABLE IF EXISTS public.weekplans;

-- ── S4-2  urlaubskontingent.urlaub (deprecated seit v648) — 0 Non-NULL ──────
-- Live-Befund: Spalte existiert, 0 Non-NULL-Werte -> gefahrlos droppbar.
-- Trigger trg_guard_kontingent (guard_kontingent) haengt an der Tabelle, ist vom
-- DROP COLUMN aber unberuehrt (referenziert die Spalte nicht) — vor dem Lauf
-- kurz gegenpruefen. Wartet auf Sebastians woertliches „droppen".
--   SELECT count(*) FILTER (WHERE urlaub IS NOT NULL) FROM public.urlaubskontingent;  -- ERWARTUNG: 0
-- -- TODO — nur nach Sebastian-„ja" #2:
-- -- ALTER TABLE public.urlaubskontingent DROP COLUMN IF EXISTS urlaub;

-- ── S4-3  _backup_arbeitsscheine_status_pre_a2_20260630 (NEU) ───────────────
-- Vergessene A2-Fix-Sicherung vom 30.06. — Live-Befund: 108 Zeilen, 264 kB.
-- Backup ZUERST (gefahrlos) nach docs/db/backup-arbeitsscheine-status-pre-a2.json (108 Z.),
-- dann Drop nach Einzel-OK.
--   SELECT * FROM public._backup_arbeitsscheine_status_pre_a2_20260630;  -- ERWARTUNG: 108 Zeilen
-- -- TODO — nur nach Sebastian-„ja" #3 + Backup-JSON:
-- -- DROP TABLE IF EXISTS public._backup_arbeitsscheine_status_pre_a2_20260630;

-- ── S4-FRAGEN an Sebastian (nur formuliert — NICHTS gebaut) ─────────────────
-- F-A) notifications: 739 Zeilen / 2,5 MB. Rotations-Regel gewuenscht?
--      (z.B. gelesene Notifs > 90 Tage loeschen.) -> dann eigenes Retention-Skript.
-- F-B) activity_log: 8.446 Zeilen / 1,9 MB. Rotations-Regel gewuenscht?
--      (z.B. Log-Eintraege > 6 Monate loeschen.) -> dann eigenes Retention-Skript.


-- ═══════════════════════════════════════════════════════════════════════════
-- NICHT ANFASSEN (Inventur bestaetigt behalten):
--   kunden (6.463, OFFA-Import) · finkzeit (0, Mirror bleibt) · fahrzeuge 9,3 MB
--   Base64 (7 FZ -> Performance-Fix 1, NICHT Cleanup) · Storage epkolar-files 8 /
--   epkolar-docs 16 Objekte (unauffaellig) · alles unter auth.*/storage.* ·
--   guard_urlaub_edit (v696-Baustelle) · plz_geo/plz_distanz/montagezulage_tage
--   (gestaged, warten auf Gate).
-- AUTH-HYGIENE: Live-Befund 0 NULL-Token-User -> alles sauber, keine Sektion noetig.
-- ═══════════════════════════════════════════════════════════════════════════
