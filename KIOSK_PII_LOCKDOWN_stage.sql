-- =============================================================================
-- KIOSK_PII_LOCKDOWN_stage.sql   (2026-06-29)   project-ref: jiggujpruejkaomgxarp
-- =============================================================================
-- ⛔ VORBEDINGUNG — NICHT AUSFUEHREN bevor die index.html-RPC-Umstellung LIVE ist
--    UND die Lager-Tafel (?screen=monteure + ?screen=planung) verifiziert wurde.
--    Diese Datei sperrt die direkten workers-/projects-/arbeitsscheine-Reads fuer
--    lager_display. Laeuft sie, BEVOR der Client auf kiosk_field_workers /
--    kiosk_week_arbeitsscheine umgestellt+deployed ist, liest der Kiosk leer →
--    TAFEL DUNKEL. Reihenfolge: KIOSK_PII_RPCS_stage.sql → Client live → DIESE Datei.
-- =============================================================================
-- SCHRITT 2 von 2 (HIGH-Fund A-1). Idempotent (drop policy if exists + create),
-- self-guarding. Muster 1:1 aus den bereits gesperrten Tabellen.
-- weekplan_rows / weekplans bleiben bewusst lesbar (Tafel-Kern) — hier keine Aenderung.
-- =============================================================================


-- B1) workers: lager_display SELECT sperren. Ersatz live: kiosk_field_workers().
drop policy if exists lager_display_no_select on public.workers;
create policy lager_display_no_select on public.workers
  as restrictive for select to authenticated
  using ((((auth.jwt() -> 'app_metadata') ->> 'role') is distinct from 'lager_display'));

-- B2) projects: lager_display SELECT sperren. Kein Ersatz-RPC noetig
--     (Tafel rendert keine Projekt-Felder; bvh kommt aus weekplan_rows).
drop policy if exists lager_display_no_select on public.projects;
create policy lager_display_no_select on public.projects
  as restrictive for select to authenticated
  using ((((auth.jwt() -> 'app_metadata') ->> 'role') is distinct from 'lager_display'));

-- B3) arbeitsscheine: explizite lager_display_read-GRANT entfernen + Restrictive
--     setzen. Ersatz live: kiosk_week_arbeitsscheine(p_from,p_to).
drop policy if exists lager_display_read on public.arbeitsscheine;
drop policy if exists lager_display_no_select on public.arbeitsscheine;
create policy lager_display_no_select on public.arbeitsscheine
  as restrictive for select to authenticated
  using ((((auth.jwt() -> 'app_metadata') ->> 'role') is distinct from 'lager_display'));


-- ── Verify (read-only, nach dem Lauf) ────────────────────────────────────────
-- select tablename, policyname, cmd, permissive from pg_policies
--  where schemaname='public' and tablename in ('workers','projects','arbeitsscheine')
--    and policyname like 'lager_display%' order by tablename;
-- Erwartung: je 1x lager_display_no_select (RESTRICTIVE, SELECT);
--            KEIN lager_display_read auf arbeitsscheine mehr.
