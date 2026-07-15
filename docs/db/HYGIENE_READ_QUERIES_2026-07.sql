-- ═══════════════════════════════════════════════════════════════════════════
-- HYGIENE_READ_QUERIES_2026-07.sql
-- READ-ONLY Inventur fuer den Supabase SQL-Editor. Erzeugt von CC (kein Live-DB-
-- Zugriff), Stand 2026-07-15. Sebastian fuehrt Block fuer Block aus und gibt das
-- Ergebnis zurueck — daraus wird sql/CLEANUP_2026-07.sql scharfgestellt.
--
-- GARANTIE: Jeder Block ist ausschliesslich SELECT / pg_catalog-Lesen.
-- KEIN INSERT/UPDATE/DELETE/DROP/ALTER. Auth-Schema wird nur GELESEN, nie
-- veraendert (Block #7). Reihenfolge egal, Bloecke sind unabhaengig.
-- Jeder Block einzeln markieren + "Run". Die Kommentare sagen, was das
-- Ergebnis bedeutet und welche CLEANUP-Sektion daran haengt.
-- ═══════════════════════════════════════════════════════════════════════════


-- ─────────────────────────────────────────────────────────────────────────
-- #1  TABELLEN-GROESSE + ZEILEN (Top-down)  →  Prioritaet & Groessenordnung
-- ─────────────────────────────────────────────────────────────────────────
-- Bedeutung: Zeigt, welche Tabellen wirklich Volumen tragen. n_live_tup ist eine
-- Schaetzung aus dem Autovacuum-Statistiksammler (nach ANALYZE genau genug fuer
-- eine Inventur). total_bytes schliesst Indizes + TOAST ein. Grosse Tabellen mit
-- hohem n_dead_tup sind Bloat-/VACUUM-Kandidaten; kleine, uralte Legacy-Tabellen
-- (weekplans!) fallen hier als "viel Groesse, kaum/keine Reads" auf.
SELECT
  s.relname                                        AS tabelle,
  s.n_live_tup                                     AS zeilen_geschaetzt,
  s.n_dead_tup                                     AS tote_zeilen,
  s.seq_scan                                       AS seq_scans,
  s.idx_scan                                       AS idx_scans,
  pg_size_pretty(pg_total_relation_size(c.oid))    AS groesse_total,
  pg_total_relation_size(c.oid)                    AS bytes_total,
  s.last_autovacuum,
  s.last_analyze
FROM pg_stat_user_tables s
JOIN pg_class c ON c.oid = s.relid
WHERE s.schemaname = 'public'
ORDER BY pg_total_relation_size(c.oid) DESC;


-- ─────────────────────────────────────────────────────────────────────────
-- #2  TABELLEN-INVENTAR + CLEANUP-KANDIDATEN-MARKIERUNG
-- ─────────────────────────────────────────────────────────────────────────
-- Bedeutung: Vollstaendige Liste aller Basistabellen mit Spaltenzahl + RLS-Flag.
-- Die CASE-Spalte "cleanup_flag" markiert die zwei bekannten Altlasten aus dem
-- Repo-Wissen, damit sie im Ergebnis sofort ins Auge springen:
--   * weekplans           — Legacy-Wochenplanung. Seit v500 schreibt die App in
--                           weekplan_rows (einzelne SQ-Items) statt in das alte
--                           weekplans-Blob. Tabelle steht auf DROP-Kandidat (S4).
--   * urlaubskontingent    — die Spalte "urlaub" gilt seit v648 als deprecated
--                           (Urlaub kommt aus absences + kontingent.stunden).
--                           DROP COLUMN-Kandidat (S4). Hier nur: existiert die
--                           Spalte ueberhaupt noch, und traegt sie noch Werte?
SELECT
  t.tablename,
  (SELECT count(*) FROM information_schema.columns c
     WHERE c.table_schema='public' AND c.table_name=t.tablename) AS spalten,
  t.rowsecurity                                                  AS rls_aktiv,
  CASE
    WHEN t.tablename = 'weekplans'        THEN 'LEGACY seit v500 -> S4 DROP TABLE (Sebastian-ja)'
    WHEN t.tablename = 'urlaubskontingent' THEN 'Spalte urlaub deprecated seit v648 -> S4 DROP COLUMN (Sebastian-ja)'
    ELSE ''
  END                                                           AS cleanup_flag
FROM pg_tables t
WHERE t.schemaname = 'public'
ORDER BY cleanup_flag DESC, t.tablename;

-- Zusatz zu #2: existiert urlaubskontingent.urlaub noch, und hat sie Non-NULL-Werte?
SELECT
  EXISTS (SELECT 1 FROM information_schema.columns
          WHERE table_schema='public' AND table_name='urlaubskontingent'
            AND column_name='urlaub')                        AS spalte_urlaub_existiert,
  (SELECT count(*) FROM public.urlaubskontingent
     WHERE urlaub IS NOT NULL)                               AS zeilen_mit_urlaub_wert;
-- Erwartung/Bedeutung: Wenn spalte_urlaub_existiert=false -> S4-DROP-COLUMN
-- bereits erledigt, nichts zu tun. Wenn true UND zeilen_mit_urlaub_wert=0 ->
-- gefahrlos droppbar. Wenn >0 -> vor DROP klaeren, ob die Werte noch irgendwo
-- referenziert werden (App liest sie laut Repo nicht mehr).


-- ─────────────────────────────────────────────────────────────────────────
-- #3  RLS KOMPLETT  →  Kern der Policy-Bereinigung (S1 haengt daran!)
-- ─────────────────────────────────────────────────────────────────────────
-- Bedeutung: Der vollstaendige Live-Stand aller Policies. Das ist die WAHRHEIT,
-- gegen die docs/db/RLS_SNAPSHOT_2026-07-15.md (Repo-Behauptung) abgeglichen wird.
SELECT * FROM pg_policies
WHERE schemaname='public'
ORDER BY tablename, policyname;

-- #3a — Gezielt: gibt es noch die alten, NIE greifenden app_metadata-Sperren?
-- Hintergrund (sql/KIOSK_RESTRICTIVE_FIX_v1.sql, v695): mehrere Tabellen trugen
-- eine RESTRICTIVE-Policy "*_no_lager_display", die die Rolle ueber
-- ((auth.jwt()->'app_metadata')->>'role') prueft. Das ist die FALSCHE Quelle
-- (Rolle steht in public.users.role / auth_role()), der Claim ist an den Kiosk-
-- Accounts nicht gesetzt -> Vergleich lief gegen NULL -> Policy hat NIE gegriffen.
-- KIOSK_RESTRICTIVE_FIX_v1 ersetzt sie durch "*_no_kiosk" mit is_kiosk_role().
SELECT tablename, policyname, permissive, cmd, qual
FROM pg_policies
WHERE schemaname='public'
  AND (policyname LIKE '%no_lager_display%'
       OR qual ILIKE '%app_metadata%'
       OR with_check ILIKE '%app_metadata%')
ORDER BY tablename, policyname;
-- Bedeutung: Jede Zeile hier = eine tote/irrefuehrende Sperre. Namen (policyname,
-- tablename) 1:1 an CLEANUP S1 uebergeben. LEERE Ergebnismenge = KIOSK_RESTRICTIVE_
-- FIX_v1 wurde bereits gelaufen, S1 ist gegenstandslos (nichts zu droppen).

-- #3b — Sind die Ersatz-"_no_kiosk"-RESTRICTIVE-Policies aktiv? (Voraussetzung
-- dafuer, dass man die alten ueberhaupt droppen darf, ohne ein Loch zu reissen.)
SELECT tablename, policyname, permissive, cmd
FROM pg_policies
WHERE schemaname='public' AND policyname LIKE '%_no_kiosk%'
ORDER BY tablename;
-- Erwartet laut KIOSK_RESTRICTIVE_FIX_v1: fz_fahrten, fz_positions, geo_cache,
-- kunden, time_entries, forms, bautagebuch je eine RESTRICTIVE _no_kiosk-Policy
-- (7 Stueck). Sind die da -> der Ersatz ist aktiv -> S1 (Drop der Alt-Policies)
-- ist gefahrlos.

-- #3c — Helper-Funktion is_kiosk_role() vorhanden?
SELECT p.proname, pg_get_function_identity_arguments(p.oid) AS args,
       p.prosecdef AS security_definer
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' AND p.proname='is_kiosk_role';
-- Bedeutung: is_kiosk_role() ist die Bedingung ALLER _no_kiosk-Policies. Fehlt
-- sie, sind die Policies kaputt -> dann NICHT die alten droppen. Erwartet: 1 Zeile,
-- security_definer=true.

-- #3d — RPC kiosk_fahrzeuge() vorhanden? (v3.9.708, RETURNS TABLE)
SELECT p.proname, pg_get_function_result(p.oid) AS returns,
       p.prosecdef AS security_definer
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' AND p.proname='kiosk_fahrzeuge';
-- Bedeutung: index.html ruft /rpc/kiosk_fahrzeuge. Erwartet: 1 Zeile,
-- returns = TABLE(id text, kennzeichen text, typ text, modell text, status text),
-- security_definer=true. Fehlt sie -> 🚛-Zeilen der Lagertafel bleiben leer
-- (KIOSK_FAHRZEUGE_v1.sql noch nicht gelaufen). Kein Cleanup-Thema, nur Ist-Stand.


-- ─────────────────────────────────────────────────────────────────────────
-- #4  FUNKTIONEN + TRIGGER-DUMP  →  S2 (verwaiste Funktionen/Trigger)
-- ─────────────────────────────────────────────────────────────────────────
-- Bedeutung: Alle SECURITY-DEFINER-Funktionen und alle User-Trigger. Grundlage,
-- um verwaiste Funktionen (kein Trigger, keine RPC-Referenz im Client) zu finden.
SELECT p.proname                                   AS funktion,
       pg_get_function_identity_arguments(p.oid)   AS args,
       p.prosecdef                                 AS security_definer,
       l.lanname                                   AS sprache
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
JOIN pg_language  l ON l.oid = p.prolang
WHERE n.nspname = 'public'
ORDER BY p.proname;

-- #4a — Alle Trigger im public-Schema (Name, Tabelle, Funktion, Events)
SELECT c.relname                    AS tabelle,
       t.tgname                     AS trigger,
       p.proname                    AS funktion,
       pg_get_triggerdef(t.oid)     AS definition
FROM pg_trigger t
JOIN pg_class c ON c.oid = t.tgrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_proc p ON p.oid = t.tgfoid
WHERE n.nspname = 'public' AND NOT t.tgisinternal
ORDER BY c.relname, t.tgname;

-- #4b — guard_urlaub_edit-Stand exakt (Body-Hash-Abgleich gegen Repo-Wahrheit)
SELECT md5(regexp_replace(prosrc, '\s+', '', 'g')) AS body_hash_ohne_ws,
       length(prosrc)                              AS body_laenge
FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
WHERE n.nspname='public' AND p.proname='guard_urlaub_edit';
-- Bedeutung: docs/wip/guard_urlaub_edit_LIVE_2026-07-14.sql nennt als Normalform
-- md5 = 284dc6f19d45f4a8804ddb69e74e8ef6 (1746 Zeichen, ohne Whitespace).
-- Hinweis: obiges md5 kollabiert ALLEN Whitespace; die Repo-Angabe kollabiert
-- ASCII-\s. Weicht der Hash ab -> Live-Body != dokumentierte Wahrheit -> vor JEDER
-- Aenderung an diesem Trigger neu kalibrieren (CLAUDE.md: nie die Rekonstruktion
-- security_triggers_LIVE_v3911.sql als Quelle nehmen).
-- Erwartete 5 guard-Trigger laut security_triggers_LIVE: trg_guard_kontingent,
-- trg_guard_projects, trg_guard_system_config, trg_guard_urlaub_absences,
-- trg_guard_users_privilege (Funktionen guard_kontingent, guard_projects,
-- guard_admin_only, guard_urlaub_edit, guard_users_privilege).


-- ─────────────────────────────────────────────────────────────────────────
-- #5  WAISEN / DATEN-HYGIENE  →  S3 (Waisen-Zeilen)
-- ─────────────────────────────────────────────────────────────────────────
-- Bedeutung: Findet Zeilen ohne gueltigen Bezug bzw. mit falschem Typ. NUR ZAEHLEN.
-- Aus den Zahlen wird in CLEANUP S3 der (auskommentierte) DELETE scharfgestellt.

-- 5a — absences ohne existierenden Worker (worker_id zeigt ins Leere)
SELECT count(*) AS absences_ohne_worker
FROM public.absences a
LEFT JOIN public.workers w ON w.id = a.worker_id
WHERE a.worker_id IS NOT NULL AND w.id IS NULL;
-- Bedeutung: >0 = verwaiste Abwesenheiten (geloeschter Mitarbeiter). Kandidat fuer
-- S3-Loeschung NACH Backup-SELECT. =0 = sauber.

-- 5b — weekplan_rows: steht die Zuordnung z faelschlich als String-JSON statt
--      als jsonb-Objekt? (Migrations-Altlast). jsonb_typeof deckt es auf.
-- HINWEIS: Spaltenname der z-Nutzlast in weekplan_rows ggf. anpassen (siehe #2-
--   Spaltenliste). Haeufig 'zuordnung' / 'data' / 'z'. Beispiel mit 'zuordnung':
SELECT
  jsonb_typeof(to_jsonb(wr)->'zuordnung') AS typ_zuordnung, count(*)
FROM public.weekplan_rows wr
GROUP BY 1 ORDER BY 2 DESC;
-- Bedeutung: Erwartet 'object'. Taucht 'string' auf -> doppelt-serialisiertes JSON
-- (z als String abgelegt) -> Migrationsbedarf, KEIN Loeschen. Nur Diagnose.

-- 5c — Zeilenstand der Hochfrequenz-/Log-Tabellen (Retention-Blick, nur zaehlen)
SELECT 'stempel_log'  AS tabelle, count(*) AS zeilen, min(created_at) AS aeltest,
       max(created_at) AS neuest FROM public.stempel_log
UNION ALL
SELECT 'fz_positions', count(*), min(ts), max(ts) FROM public.fz_positions;
-- HINWEIS: Zeitspalten (created_at / ts) ggf. an das echte Schema anpassen.
-- Bedeutung: Gibt die Groessenordnung fuer eine spaetere Retention-Policy
-- (GPS_RETENTION_v1.sql existiert bereits). KEIN Cleanup hier — reiner Ist-Stand.

-- 5d — tank_log: Base64-Foto-Reste (Tankfoto-Migration lief laut Repo teils nicht)
SELECT
  count(*)                                                          AS zeilen_gesamt,
  count(*) FILTER (WHERE foto IS NOT NULL AND length(foto) > 200)   AS mit_base64_verdacht,
  pg_size_pretty(sum(length(coalesce(foto,''))))                    AS foto_bytes_grob
FROM public.tank_log;
-- HINWEIS: Spaltenname des Fotos ggf. anpassen (foto/photo/bild/base64).
-- Bedeutung: mit_base64_verdacht>0 = Inline-Base64-Bilder liegen noch in der
-- Tabelle (haetten nach migrate_tankfotos.mjs in Storage wandern sollen). KEIN
-- Loeschen hier — erst Migration abschliessen, dann Spalte nullen. Nur Diagnose.


-- ─────────────────────────────────────────────────────────────────────────
-- #6  STORAGE-BUCKETS  →  nur ZAEHLEN
-- ─────────────────────────────────────────────────────────────────────────
-- Bedeutung: Reine Bestandsaufnahme, welche Buckets existieren und wie viele
-- Objekte drinliegen. KEINE Loeschung, kein Cleanup-Vorschlag (Storage bleibt in
-- dieser Runde tabu, u.a. wegen des offenen ES256-JWT-Upload-Blockers).
SELECT b.id                       AS bucket,
       b.public                   AS ist_public,
       count(o.id)                AS objekte
FROM storage.buckets b
LEFT JOIN storage.objects o ON o.bucket_id = b.id
GROUP BY b.id, b.public
ORDER BY objekte DESC;


-- ─────────────────────────────────────────────────────────────────────────
-- #7  AUTH TOKEN-SPALTEN  →  NUR PRUEFEN. AUTH BLEIBT TABU.
-- ─────────────────────────────────────────────────────────────────────────
-- Bedeutung: Reines Zaehlen des bekannten ''-statt-NULL-Musters in auth.users.
-- Repo-Regel: leerer String '' = gesund, NULL = kaputt (Version-4-Token-Falle) —
-- HIER WIRD NICHTS GESCHRIEBEN. Kein UPDATE, kein CLEANUP an auth.*. Diese Abfrage
-- dient nur dazu, den Ist-Zustand zu dokumentieren; jede Reparatur laeuft separat
-- ueber die bestehenden fix_*_v3.9.213-Skripte und wird NICHT hier gebuendelt.
SELECT
  count(*)                                                     AS users_gesamt,
  count(*) FILTER (WHERE confirmation_token IS NULL)           AS conf_token_NULL_kaputt,
  count(*) FILTER (WHERE confirmation_token = '')              AS conf_token_leer_gesund,
  count(*) FILTER (WHERE recovery_token IS NULL)               AS recovery_NULL_kaputt,
  count(*) FILTER (WHERE email_change_token_new IS NULL)       AS emailchg_new_NULL_kaputt,
  count(*) FILTER (WHERE email_change_token_current IS NULL)   AS emailchg_cur_NULL_kaputt
FROM auth.users;
-- Bedeutung: Die "_NULL_kaputt"-Spalten >0 = Accounts, die beim naechsten
-- Token-Vorgang (Login/Reset) in die GoTrue-Falle laufen koennten. NUR MELDEN,
-- NICHT hier fixen. Auth bleibt in dieser Inventur tabu.
