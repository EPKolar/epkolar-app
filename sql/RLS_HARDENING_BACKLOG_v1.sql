-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar RLS-Hardening-Backlog v1 (2026-06-12)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- DIESES FILE IST EINE REINE PLANUNGS-/REVIEW-DATEI.
-- KEIN EINZIGER STATEMENT IST AKTIV (alle CREATE/DROP/ALTER sind auskommentiert).
-- Sebastian führt selektiv per SQL-Editor aus — pro Tabelle einzeln + verifizieren.
--
-- Backlog-Quelle: bekannter Inventar-Stand ~15 Tabellen mit `qual = true` ALL-Policies
-- + 19 SELECT-Policies (interne operative Tabellen, die heute zu offen lesen/schreiben).
--
-- KONSERVATIV-Prinzip: Monteur-Grundfunktionen (Arbeitsscheine lesen, Zeiten
-- schreiben, EIGENES Fahrzeug aktualisieren, Mängel melden) DÜRFEN NICHT brechen.
-- Jede Verschärfung listet explizit: Wer verliert welchen Zugriff + Risiko-Stufe.
--
-- Konventionen:
--   * canDo()-Pendant in SQL: prüfen via JOIN auf `users` + Role-Check
--   * Field-Roles = monteur/helfer/techniker/obermonteur (haben i.d.R. eigenes Fz/Profil)
--   * Office-Roles = admin/projektleiter/buero (volle Lese-Rechte intern)
--   * Anon-Kontext (Kundenportal) → strenge Whitelists, kein direkter SELECT
--
-- Risiko-Stufen:
--   LOW    = ändert nur Office-/Admin-Bereich, Field-Roles unbetroffen
--   MEDIUM = Field-Roles verlieren Querblick, behalten eigene Records
--   HIGH   = bricht potentiell Monteur-Workflow ohne Re-Test → erst nach Pilot live
--
-- Vor jeder Aktivierung: 30-min-Smoke mit jeweils 1 Monteur + 1 Bürokraft.
-- Rollback: bei Auffälligkeit sofort `DROP POLICY <name> ON <table>;` + alte
-- Policy wiederherstellen (Vorlage siehe Sebastians DB-Audit-Notes Q1/2026).
--
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- 1) fahrzeuge — Fahrzeuge / Fuhrpark
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    ALL-Policy `qual=true` (alle authentifizierten lesen + schreiben alles)
-- PROBLEM:    Monteur konnte historisch fremde Fahrzeuge sehen UND updaten;
--             v3.9.x-Policy `fahrzeuge_update_driver` (additiv) löste das partiell.
-- VORSCHLAG:  SELECT bleibt für alle authenticated (Disponent muss alle sehen),
--             UPDATE nur für admin/projektleiter/buero ODER eigenen Eintrag.
-- VERLIERT:   Monteur kann fremde Fahrzeuge nicht mehr "versehentlich" updaten
--             (siehe v3.9.306 0-rows-Safeguard im Client = bereits gewarnt).
-- RISIKO:     LOW  — Disponent/Office unverändert, Monteur-Eigenfahrzeug bleibt.

-- DROP POLICY IF EXISTS "fahrzeuge_all" ON public.fahrzeuge;
-- CREATE POLICY "fahrzeuge_select_authed" ON public.fahrzeuge
--   FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "fahrzeuge_update_office_or_owner" ON public.fahrzeuge
--   FOR UPDATE TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero'))
--     OR fahrer = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--   );
-- CREATE POLICY "fahrzeuge_insert_office" ON public.fahrzeuge
--   FOR INSERT TO authenticated WITH CHECK (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero'))
--   );
-- CREATE POLICY "fahrzeuge_delete_admin" ON public.fahrzeuge
--   FOR DELETE TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter'))
--   );


-- ───────────────────────────────────────────────────────────────────────────
-- 2) entries — Zeiteinträge (time_entries)
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    ALL-Policy qual=true.
-- PROBLEM:    Monteur kann fremde Stundeneinträge updaten/löschen.
-- VORSCHLAG:  SELECT für alle authenticated (Querblick fuer Wochenplanung noetig),
--             INSERT/UPDATE/DELETE nur für Office ODER eigener worker_id.
-- VERLIERT:   Monteur kann fremde Entries nicht mehr editieren — Edit-Button
--             v3.9.307 ist canDo('zeit_other')-guarded → Office-Edit bleibt.
-- RISIKO:     LOW  — bestaetigt durch v3.9.307-Client-Guard + Edge-Smoke-Test.

-- DROP POLICY IF EXISTS "entries_all" ON public.entries;
-- CREATE POLICY "entries_select_authed" ON public.entries
--   FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "entries_write_own_or_office" ON public.entries
--   FOR INSERT TO authenticated WITH CHECK (
--     worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--     OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--               AND u.role IN ('admin','projektleiter','buero'))
--   );
-- CREATE POLICY "entries_update_own_or_office" ON public.entries
--   FOR UPDATE TO authenticated USING (
--     worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--     OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--               AND u.role IN ('admin','projektleiter','buero'))
--   );
-- CREATE POLICY "entries_delete_own_or_office" ON public.entries
--   FOR DELETE TO authenticated USING (
--     worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--     OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--               AND u.role IN ('admin','projektleiter'))
--   );


-- ───────────────────────────────────────────────────────────────────────────
-- 3) arbeitsscheine — OFFA-Scheine
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    ALL qual=true. Monteur sieht ALLE Scheine im Client-Filter.
-- VORSCHLAG:  SELECT bleibt offen (Disponent-Querblick), UPDATE/DELETE auf Office
--             ODER eigene Zuweisung (a.monteur = current user.monteur_id).
-- VERLIERT:   Monteur kann fremde Scheine nicht mehr statusen — er sieht sie noch.
-- RISIKO:     MEDIUM — bitte testen ob "Status setzen auf erledigt" bei
--             Monteur-Selbst-Schein durchlaeuft (sollte: monteur === own-id).

-- DROP POLICY IF EXISTS "arbeitsscheine_all" ON public.arbeitsscheine;
-- CREATE POLICY "as_select_authed" ON public.arbeitsscheine
--   FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "as_update_office_or_assigned" ON public.arbeitsscheine
--   FOR UPDATE TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero'))
--     OR monteur = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--   );
-- CREATE POLICY "as_insert_office" ON public.arbeitsscheine
--   FOR INSERT TO authenticated WITH CHECK (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero'))
--   );


-- ───────────────────────────────────────────────────────────────────────────
-- 4) projects — Projekte
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    ALL qual=true.
-- VORSCHLAG:  Field-Roles SELECT nur auf Projekte mit Zuweisung
--             (via monteurProjekte-Mapping); Office unbeschraenkt.
-- VERLIERT:   Monteur sieht keine "fremden" Projekt-Cards mehr in der Liste.
--             Statt 50 Projekten nur die zugewiesenen (analog _isFieldOnly-Filter
--             im Client, der bereits genau das macht).
-- RISIKO:     MEDIUM — wenn monteur_projekte-Mapping luckig ist, sieht der Monteur
--             gar keine Projekte. Bitte vorher mapping-Vollstaendigkeit pruefen.

-- DROP POLICY IF EXISTS "projects_all" ON public.projects;
-- CREATE POLICY "projects_select_office" ON public.projects
--   FOR SELECT TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero','pinger'))
--   );
-- CREATE POLICY "projects_select_assigned_monteur" ON public.projects
--   FOR SELECT TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.monteur_projekte mp
--            WHERE mp.monteur_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--            AND mp.project_id = projects.id)
--   );
-- CREATE POLICY "projects_write_office" ON public.projects
--   FOR ALL TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter'))
--   );


-- ───────────────────────────────────────────────────────────────────────────
-- 5) defects — Maengel
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    ALL qual=true (additiv: portal-rpc-defender greift fuer anon).
-- VORSCHLAG:  SELECT: anon nur via portal_fetch-RPC (NICHT direkt); authed sieht
--             eigene + zugewiesene + alle melder='Kunde' (für Office).
--             INSERT: anon via portal_submit_defect-RPC (bereits implementiert);
--             authed wenn melder im eigenen Rollen-Kontext zulaessig.
-- VERLIERT:   Anon-Zugriff auf direct-defects-table komplett weg (war eh nur
--             RPC-Fallback v3.9.156); Field-Role sieht fremde nicht.
-- RISIKO:     MEDIUM — RPCs muessen weiterhin SECURITY DEFINER haben.

-- DROP POLICY IF EXISTS "defects_all" ON public.defects;
-- CREATE POLICY "defects_select_office" ON public.defects
--   FOR SELECT TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero','pinger'))
--   );
-- CREATE POLICY "defects_select_assigned" ON public.defects
--   FOR SELECT TO authenticated USING (
--     zugewiesen = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--   );


-- ───────────────────────────────────────────────────────────────────────────
-- 6-11) forms — Sub-Tabellen: regie, sf, dh, ah, abnahme, checklisten
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    Pro Sub-Tabelle ALL qual=true.
-- VORSCHLAG:  EINHEITLICH: SELECT nur fuer authentifizierte, INSERT/UPDATE/DELETE
--             nur fuer Field-Roles die im Projekt zugewiesen sind ODER Office.
-- VERLIERT:   Fremder Monteur kann keine Regieberichte mehr im falschen Projekt
--             anlegen. Office-Wochenberichte unveraendert.
-- RISIKO:     LOW  — interne Tabellen ohne Anon-Zugriff.

-- TEMPLATE (gleiches Muster fuer regie / sf / dh / ah / abnahme / checklisten):
--   DROP POLICY IF EXISTS "<table>_all" ON public.<table>;
--   CREATE POLICY "<table>_select_authed" ON public.<table>
--     FOR SELECT TO authenticated USING (true);
--   CREATE POLICY "<table>_write_assigned_or_office" ON public.<table>
--     FOR ALL TO authenticated USING (
--       EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--              AND u.role IN ('admin','projektleiter','buero'))
--       OR EXISTS(SELECT 1 FROM public.monteur_projekte mp
--                 WHERE mp.monteur_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--                 AND mp.project_id = <table>.pid)
--     );


-- ───────────────────────────────────────────────────────────────────────────
-- 12) bautagebuch — Construction Journal
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    SELECT qual=true.
-- VORSCHLAG:  Wie forms-Familie: schreibend nur fuer Projektzuweisung oder Office.
-- RISIKO:     LOW — keine externen User.

-- (Siehe TEMPLATE bei forms.)


-- ───────────────────────────────────────────────────────────────────────────
-- 13) abs / absences — Urlaub & Krankenstand
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    ALL qual=true. Monteur sieht ALLE Urlaubsantraege.
-- VORSCHLAG:  SELECT: Office sieht alles, Monteur nur eigene.
--             INSERT/UPDATE: Office oder eigener Eintrag.
-- VERLIERT:   Team-Urlaubskalender fuer Monteur eingeschraenkt (zeigt nur eigene).
-- RISIKO:     MEDIUM — bitte abklaeren ob Monteure den Team-Kalender brauchen
--             (z.B. "wer hat naechste Woche Urlaub" fuer Vertretungsplanung).
--             Empfehlung: SELECT offen lassen, nur WRITE auf own.

-- DROP POLICY IF EXISTS "absences_all" ON public.absences;
-- CREATE POLICY "absences_select_authed" ON public.absences
--   FOR SELECT TO authenticated USING (true);
-- CREATE POLICY "absences_write_own_or_office" ON public.absences
--   FOR ALL TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero'))
--     OR monteur_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--   );


-- ───────────────────────────────────────────────────────────────────────────
-- 14) fahrbewilligungen / anmeldungen — Personalunterlagen
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    SELECT qual=true (alle authed lesen).
-- PROBLEM:    Mitarbeiter-PDFs anderer Monteure einsehbar.
-- VORSCHLAG:  SELECT nur Office oder eigene worker_id.
--             INSERT/UPDATE/DELETE nur Office (canDo("fahrbewilligung_edit")).
-- VERLIERT:   Monteur sieht eigene weiter (MitarbeiterView v3.9.312-Aggregator
--             zeigt eigene Karten); fremde nicht mehr.
-- RISIKO:     LOW  — Selbstzugriff bleibt, Office unbetroffen.

-- DROP POLICY IF EXISTS "fahrbewilligungen_select_all" ON public.fahrbewilligungen;
-- DROP POLICY IF EXISTS "anmeldungen_select_all" ON public.anmeldungen;
-- CREATE POLICY "fahrbewilligungen_select_own_or_office" ON public.fahrbewilligungen
--   FOR SELECT TO authenticated USING (
--     worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--     OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--               AND u.role IN ('admin','projektleiter','buero'))
--   );
-- CREATE POLICY "anmeldungen_select_own_or_office" ON public.anmeldungen
--   FOR SELECT TO authenticated USING (
--     worker_id = (SELECT monteur_id FROM public.users WHERE id = auth.uid())
--     OR EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--               AND u.role IN ('admin','projektleiter','buero'))
--   );


-- ───────────────────────────────────────────────────────────────────────────
-- 15) finkzeit — Monatsabrechnung (STANDBY seit 04.06.2026)
-- ───────────────────────────────────────────────────────────────────────────
-- AKTUELL:    SELECT qual=true (Standby — keine Writes mehr).
-- VORSCHLAG:  SELECT nur Office. Write komplett gesperrt (bereits standby).
-- RISIKO:     LOW — Feature ist standby, nur Doku-Zugriff.

-- DROP POLICY IF EXISTS "finkzeit_select_all" ON public.finkzeit;
-- CREATE POLICY "finkzeit_select_office_only" ON public.finkzeit
--   FOR SELECT TO authenticated USING (
--     EXISTS(SELECT 1 FROM public.users u WHERE u.id = auth.uid()
--            AND u.role IN ('admin','projektleiter','buero'))
--   );


-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLOUT-EMPFEHLUNG (Reihenfolge nach Risiko aufsteigend)
-- ═══════════════════════════════════════════════════════════════════════════
--
-- WELLE 1 (LOW-Risk, sofort kandidatentauglich):
--   * forms-Familie (regie/sf/dh/ah/abnahme/checklisten) — interne Tabellen
--   * bautagebuch — interne Tabelle
--   * finkzeit — standby, Doku-only
--   * fahrbewilligungen + anmeldungen — Self-Read bleibt, fremde weg
--   * entries — UPDATE/INSERT/DELETE einschraenken (SELECT offen)
--   * fahrzeuge — UPDATE einschraenken (SELECT offen)
--
-- WELLE 2 (MEDIUM-Risk, mit Pilot-Smoke):
--   * absences — SELECT offen, WRITE auf own (vorher Team-Kalender-Bedarf klaeren)
--   * arbeitsscheine — UPDATE auf assigned-or-office (Monteur-Status-Set testen)
--   * defects — Office-Querblick + assigned (RPC-Pfad fuer anon bleibt)
--
-- WELLE 3 (HIGH-Risk, erst nach Welle 1+2 stabil):
--   * projects — SELECT auf zugewiesene + Office (kann Monteur-UI komplett aendern)
--
-- ROLLBACK pro Tabelle bereit:
--   DROP POLICY IF EXISTS "<new_policy_name>" ON public.<table>;
--   CREATE POLICY "<table>_all" ON public.<table> FOR ALL TO authenticated USING (true);
--
-- Nach jeder Welle: 30-min-Smoke gemaess docs/SMOKE_v3.9.31x.md (Punkte a-m).
-- ═══════════════════════════════════════════════════════════════════════════
