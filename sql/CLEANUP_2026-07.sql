-- ═══════════════════════════════════════════════════════════════════════════
-- CLEANUP_2026-07.sql
-- Gestagetes Supabase-Cleanup-Paket. Erzeugt von CC ohne Live-DB-Zugriff,
-- Stand 2026-07-15. Gegenstueck zu den Reads in
-- docs/db/HYGIENE_READ_QUERIES_2026-07.sql und dem Repo-Stand in
-- docs/db/RLS_SNAPSHOT_2026-07-15.md.
--
-- ┌─ HARTE REGEL (CLAUDE.md: „sql/ ist eine geladene Waffe") ─────────────────┐
-- │ Diese Datei muss ZU JEDEM ZEITPUNKT gefahrlos komplett ausfuehrbar sein.  │
-- │ JEDE destruktive Zeile (DROP/DELETE/ALTER DROP) ist AUSKOMMENTIERT und     │
-- │ wird erst nach dem passenden Read-Ergebnis + (bei S4) einem einzelnen      │
-- │ Sebastian-„ja" von Hand scharfgestellt. Nichts Destruktives ist scharf.   │
-- │ Was aktiv laeuft, wenn man „Run all" drueckt: NUR die read-only Nachweis-  │
-- │ SELECTs. Kein Schreibzugriff ohne bewusstes Ent-Kommentieren.             │
-- └───────────────────────────────────────────────────────────────────────────┘
--
-- Reihenfolge: harmlos → heikel. Jede Sektion ist idempotent und einzeln
-- ausfuehrbar. Jede destruktive Zeile traegt im Kommentar die ERWARTETE
-- Objekt-/Zeilenzahl aus dem zugehoerigen Read; weicht die Realitaet ab,
-- NICHT scharfstellen, sondern zurueck an die Reads.
-- ═══════════════════════════════════════════════════════════════════════════


-- ═══════════════════════════════════════════════════════════════════════════
-- S1  Tote / nie greifende app_metadata-Kiosk-Policies droppen
--     Risiko: MITTEL (Policy-Aenderung) — aber die Alt-Policies greifen laut
--     KIOSK_RESTRICTIVE_FIX_v1.sql ohnehin NIE (falsche Rollenquelle), und der
--     Ersatz *_no_kiosk deckt dasselbe wirksam ab.
--     VORAUSSETZUNG zum Scharfstellen (BEIDES muss aus Read #3 bestaetigt sein):
--       (a) Read #3a listet die *_no_lager_display-Policies noch als vorhanden.
--       (b) Read #3b bestaetigt die 7 *_no_kiosk-Ersatz-Policies als AKTIV
--           UND Read #3c bestaetigt is_kiosk_role() als vorhanden.
--     Ist (a) leer -> nichts zu tun. Ist (b)/(c) nicht erfuellt -> NICHT droppen
--     (sonst Loch). Ersatz-Nachweis: siehe RLS_SNAPSHOT_2026-07-15.md Abschnitt 1.
-- ═══════════════════════════════════════════════════════════════════════════

-- Read-only Vorab-Nachweis (laeuft gefahrlos mit): zeigt, ob ueberhaupt Alt-
-- Policies existieren und ob der Ersatz aktiv ist. ERWARTUNG: Spalte
-- alt_policies_offen listet 0..4 Namen; ersatz_no_kiosk_aktiv sollte 7 sein.
SELECT 'alt_app_metadata_policies' AS was,
       string_agg(tablename||'.'||policyname, ', ' ORDER BY tablename) AS treffer
FROM pg_policies
WHERE schemaname='public'
  AND (policyname LIKE '%no_lager_display%' OR qual ILIKE '%app_metadata%');

SELECT 'ersatz_no_kiosk_aktiv' AS was, count(*) AS anzahl_erwartet_7
FROM pg_policies
WHERE schemaname='public' AND policyname LIKE '%_no_kiosk%';

-- ── DESTRUKTIV — AUSKOMMENTIERT bis Read #3 bestaetigt (a)+(b)+(c). ──────────
-- Erwartete gedroppte Objekte: bis zu 4 Alt-Policies (fz_fahrten, fz_positions,
-- geo_cache, kunden je 1× *_no_lager_display). Namen 1:1 aus Read #3a einsetzen.
-- HINWEIS: KIOSK_RESTRICTIVE_FIX_v1.sql droppt diese Alt-Namen bereits selbst,
-- BEVOR es die *_no_kiosk anlegt. Wurde dieses Skript gelaufen, ist S1 leer.
-- Diese Sektion ist daher primaer ein Sicherungs-/Nachzieh-Schritt, falls
-- KIOSK_RESTRICTIVE_FIX_v1 NICHT lief, der Ersatz aber anderweitig existiert.
--
-- -- TODO nach Read #3 — erst ent-kommentieren, wenn (a)+(b)+(c) bestaetigt:
-- DROP POLICY IF EXISTS fz_fahrten_no_lager_display    ON public.fz_fahrten;
-- DROP POLICY IF EXISTS fz_positions_no_lager_display  ON public.fz_positions;
-- DROP POLICY IF EXISTS geo_cache_no_lager_display     ON public.geo_cache;
-- DROP POLICY IF EXISTS kunden_no_lager_display        ON public.kunden;
-- -- Falls Read #3a weitere app_metadata-Policies auf anderen Tabellen zeigt,
-- -- hier EINZELN mit exaktem Namen ergaenzen (kein Wildcard-Drop).


-- ═══════════════════════════════════════════════════════════════════════════
-- S2  Verwaiste Funktionen / Trigger
--     Risiko: MITTEL–HOCH. Nur mit 0-Referenz-Nachweis droppen.
--     0-Referenz = (i) Funktion haengt an KEINEM Trigger (Read #4a)
--                  UND (ii) Funktionsname steht NICHT in RLS_SNAPSHOT Abschnitt 4
--                       (Client-RPCs) UND nicht als String in index.html.
--     Die 5 guard_*-Funktionen + is_kiosk_role() + alle kiosk_*/juprowa_*/portal_*
--     /login_lookup/admin_*-RPCs sind NACHWEISLICH referenziert -> NIE droppen.
-- ═══════════════════════════════════════════════════════════════════════════

-- Read-only Vorab-Nachweis (gefahrlos): Funktionen im public-Schema, die an
-- KEINEM Trigger haengen. Das ist die ROH-Kandidatenliste — jeder Treffer muss
-- ZUSAETZLICH gegen index.html (RPC-Aufruf) geprueft werden, bevor er faellt.
SELECT p.proname AS funktion_ohne_trigger,
       pg_get_function_identity_arguments(p.oid) AS args
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
  AND p.prokind = 'f'
  AND NOT EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgfoid = p.oid)
  -- bekannt-referenzierte NICHT als Waisen zeigen:
  AND p.proname NOT IN (
    'is_kiosk_role','auth_role','is_staff',
    'guard_kontingent','guard_projects','guard_admin_only',
    'guard_urlaub_edit','guard_users_privilege',
    'kiosk_fahrzeuge','kiosk_field_workers','kiosk_week_absences',
    'kiosk_week_arbeitsscheine','stempel_terminal_workers',
    'juprowa_fetch_kunden','juprowa_fetch_monteure','juprowa_fetch_worksheets',
    'juprowa_get_config','juprowa_push_worksheet','juprowa_update_passport',
    'admin_create_user','admin_reset_password','login_lookup','portal_fetch'
  )
ORDER BY p.proname;
-- ERWARTUNG: idealerweise nur Helper (z.B. _uuid), die intern von anderen
-- Funktionen aufgerufen werden. So einen NICHT droppen. Ein echter Waise-Drop
-- kommt nur infrage, wenn der Name auch als String in index.html 0 Treffer hat.

-- ── DESTRUKTIV — AUSKOMMENTIERT: kein einziger 0-Referenz-Nachweis liegt vor
-- ── (CC hat keinen DB-Zugriff). Muster zum spaeteren, EINZELNEN Scharfstellen:
--
-- -- TODO nach Read #4 + index.html-0-Treffer-Nachweis, pro Objekt EINZELN:
-- -- DROP FUNCTION IF EXISTS public.<verwaiste_funktion>(<exakte_args>);
-- -- DROP TRIGGER  IF EXISTS <verwaister_trigger> ON public.<tabelle>;
-- -- (Args exakt aus Read #4 uebernehmen; ohne Signatur schlaegt DROP bei
-- --  ueberladenen Funktionen fehl. Guard-Trigger NIEMALS hier eintragen.)


-- ═══════════════════════════════════════════════════════════════════════════
-- S3  Waisen-Zeilen bereinigen
--     Risiko: HOCH (Datenverlust). Immer ERST Backup-SELECT, DANN Loeschung.
--     Alle DELETEs bleiben auskommentiert, bis Read #5 die Zahl bestaetigt.
-- ═══════════════════════════════════════════════════════════════════════════

-- 3.1  absences ohne existierenden Worker
-- Schritt A (gefahrlos, laeuft mit): Backup der betroffenen Zeilen ANZEIGEN.
-- Vor einem echten Lauf das Ergebnis als JSON nach docs/db/ sichern
-- (Muster: docs/db/orphan-tables-backup-2026-06-18.json).
SELECT a.*
FROM public.absences a
LEFT JOIN public.workers w ON w.id = a.worker_id
WHERE a.worker_id IS NOT NULL AND w.id IS NULL;

-- Schritt B — DESTRUKTIV, AUSKOMMENTIERT bis Read #5a die Zahl liefert.
-- Erwartete geloeschte Zeilen: == count aus Read #5a (absences_ohne_worker).
-- Weicht die Zahl beim echten Lauf ab -> abbrechen, neu pruefen.
--
-- -- TODO nach Read #5a + Backup-SELECT (Schritt A) gesichert:
-- DELETE FROM public.absences a
-- USING (
--   SELECT a2.id FROM public.absences a2
--   LEFT JOIN public.workers w ON w.id = a2.worker_id
--   WHERE a2.worker_id IS NOT NULL AND w.id IS NULL
-- ) orphan
-- WHERE a.id = orphan.id;

-- 3.2  weekplan_rows mit z-als-String (jsonb_typeof='string')
-- KEINE Loeschung — das ist ein MIGRATIONS-, kein Waisen-Fall. Nur Diagnose in
-- Read #5b. Wenn dort 'string'-Zeilen auftauchen, gehoert das in ein separates
-- Migrations-Skript (String -> jsonb-Objekt umbauen), NICHT in dieses Cleanup.
-- (Absichtlich keine ausfuehrbare Zeile hier.)

-- 3.3  stempel_log / fz_positions Retention
-- KEINE Loeschung in diesem Paket. Retention hat ein eigenes, gereviewtes Skript
-- (sql/GPS_RETENTION_v1.sql). Read #5c liefert nur die Groessenordnung.
-- (Absichtlich keine ausfuehrbare Zeile hier.)

-- 3.4  tank_log Base64-Reste
-- KEINE Loeschung/Nullung. Erst muss migrate_tankfotos.mjs die Bilder nach
-- Storage gebracht haben (Storage derzeit durch ES256-JWT-Blocker eingeschraenkt).
-- Read #5d diagnostiziert nur. (Absichtlich keine ausfuehrbare Zeile hier.)


-- ═══════════════════════════════════════════════════════════════════════════
-- S4  SCHWERE Struktur-Aenderungen — je EINZELN, je ein eigenes Sebastian-„ja"
--     Risiko: SEHR HOCH (irreversibler Tabellen-/Spalten-Verlust).
--     DEFAULT: KOMPLETT AUSKOMMENTIERT. Kein „Run all" darf das ausloesen.
--     Jede der beiden Zeilen braucht:
--       1) das zugehoerige Read-Ergebnis (Zeilen/Werte-Nachweis),
--       2) ein separates, ausdrueckliches „ja" von Sebastian NUR fuer DIESE Zeile,
--       3) vorher ein Voll-Backup der Tabelle nach docs/db/ (JSON).
-- ═══════════════════════════════════════════════════════════════════════════

-- ── S4-Frage 1 ──────────────────────────────────────────────────────────────
-- „Soll die Legacy-Tabelle public.weekplans ENDGUELTIG geloescht werden?"
-- Repo-Stand: Legacy seit v500; App schreibt in weekplan_rows. ABER die
-- KIOSK_RESTRICTIVE/weekplan-Kommentare im Code sagen ausdruecklich
-- „NICHT droppen / Legacy /api/weekplans-Endpoint bleibt". => Erst bestaetigen,
-- dass dieser Legacy-Endpoint stillgelegt ist UND Read #1/#2 die Tabelle als
-- unbeschrieben zeigt.
-- Nachweis vor Freigabe (gefahrlos ausfuehren):
--   SELECT count(*) AS weekplans_zeilen, max(updated_at) AS letzte_aenderung
--   FROM public.weekplans;   -- Spaltenname letzte_aenderung ggf. anpassen
-- Erwartung fuer „gefahrlos droppbar": keine frischen updated_at (nichts seit v500).
--
-- -- TODO — nur nach Sebastian-„ja" #1 + Backup public.weekplans -> docs/db/:
-- -- DROP TABLE IF EXISTS public.weekplans;

-- ── S4-Frage 2 ──────────────────────────────────────────────────────────────
-- „Soll die deprecated Spalte public.urlaubskontingent.urlaub geloescht werden?"
-- Repo-Stand: deprecated seit v648; Urlaub = absences + kontingent.stunden.
-- Nachweis vor Freigabe (gefahrlos, = Read #2-Zusatz):
--   SELECT count(*) FILTER (WHERE urlaub IS NOT NULL) AS zeilen_mit_urlaub_wert
--   FROM public.urlaubskontingent;
-- Erwartung fuer „gefahrlos droppbar": 0 Non-NULL-Werte ODER Werte nachweislich
-- nirgends (index.html) mehr gelesen. ACHTUNG: an urlaubskontingent haengt der
-- Trigger trg_guard_kontingent (guard_kontingent) — der DROP COLUMN ist davon
-- unberuehrt, aber vor dem Lauf gegenpruefen, dass keine Trigger-Logik die Spalte
-- referenziert.
--
-- -- TODO — nur nach Sebastian-„ja" #2 + Backup public.urlaubskontingent -> docs/db/:
-- -- ALTER TABLE public.urlaubskontingent DROP COLUMN IF EXISTS urlaub;


-- ═══════════════════════════════════════════════════════════════════════════
-- ENDE. Wenn diese Datei komplett „Run all" durchlaeuft, wurden AUSSCHLIESSLICH
-- read-only Nachweis-SELECTs ausgefuehrt. Alles Destruktive steht auskommentiert
-- und wartet auf Read-Ergebnisse (+ bei S4 je ein einzelnes Sebastian-„ja").
-- ═══════════════════════════════════════════════════════════════════════════
