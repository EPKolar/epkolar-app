-- ═══════════════════════════════════════════════════════════
-- RLS anon-Scope v3.9.155 — Kunden-Portal anon-SELECT eingrenzen (ALTER, nicht DROP)
-- Erstellt: 2026-06-07 (CC, Sebastian-Spec). Supabase: jiggujpruejkaomgxarp, public.
-- ═══════════════════════════════════════════════════════════
--
-- WARUM: Das Kunden-Portal liest ohne Login als anon (anon-Key = SUPABASE_KEY, index.html Z.471).
--   Die anon-SELECT-Policies haben qual=(auth.role()='anon') OHNE Zeilenfilter → anon kann den
--   Client-Filter weglassen und ALLE Zeilen lesen (Leak).
--
-- BELEG (anon-curl mit öffentlichem Key, read-only, 2026-06-07):
--   GET /project_documents?select=id              → content-range .../1   (1 Dokument lesbar)
--   GET /project_documents?select=id&kunde_freigabe=eq.1 → .../0          (0 freigegeben!)
--   → anon liest aktuell 1 NICHT-freigegebenes Dokument (kunde_freigabe=0). Leak demonstriert.
--   GET /projects?select=id                       → content-range .../2   (alle 2 Projekte)
--   GET /projects?select=id&portal_code=not.is.null → .../2               (beide haben portal_code)
--   → projects: aktuell senkt portal_code-Filter die Menge NICHT (beide Projekte sind Portal-Projekte),
--     ist aber korrekte Härtung für künftige interne Projekte ohne portal_code.
--   Spaltentyp verifiziert: project_documents.kunde_freigabe = INTEGER (Wert 0) → Prädikat "= 1".
--
-- ANSATZ: ALTER POLICY (nicht DROP — DROP würde das Portal lahmlegen). Behält die anon-Rolle,
--   ergänzt nur den Zeilenfilter. Reversibel über RLS_anon_scope_v3.9.155_ROLLBACK.sql.
--
-- POLICY-NAMEN belegt durch: Task-Kontext (Chat-Claude frontend-verifiziert) + bestehender Draft
--   sql/migrate_anon_portal_lockdown_v3103.sql. NICHT unabhängig gegen pg_policies verifiziert,
--   weil der CC-Supabase-MCP-Connector KEINEN Zugriff auf jiggujpruejkaomgxarp hat (andere Org).
--   → DESHALB ZWINGEND: Block 1 (Verify) VOR den ALTERs ausführen und prüfen, dass die Policies
--     mit diesen Namen + qual=(auth.role()='anon') existieren. Sonst STOP.
--
-- SCOPE: NUR projects + project_documents (Task-Scope). plans_anon_select hat dasselbe Leck
--   (anon liest alle Pläne) — bewusst NICHT hier (Task-Scope), siehe v3103-Draft + PORTAL-RLS-AUDIT.
--
-- ═══════════════════════════════════════════════════════════
-- BLOCK 1 — VERIFY (read-only, PFLICHT vor den ALTERs)
-- ═══════════════════════════════════════════════════════════
SELECT policyname, cmd, roles, qual, with_check
FROM pg_policies
WHERE schemaname='public'
  AND policyname IN ('projects_anon_select','project_documents_anon_select');
-- Erwartet: 2 Zeilen, cmd=SELECT, roles={anon}, qual=(auth.role() = 'anon'::text), with_check=NULL.
-- Wenn nicht so: STOP, nicht weiter.

-- Spalten/Typen bestätigen:
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema='public'
  AND ((table_name='projects' AND column_name='portal_code')
    OR (table_name='project_documents' AND column_name='kunde_freigabe'));
-- Erwartet: projects.portal_code existiert; project_documents.kunde_freigabe = integer.
-- Falls kunde_freigabe boolean ist (data_type='boolean'): unten "= 1" durch "= true" ersetzen!

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2 — FIX (ALTER, nicht DROP)
-- ═══════════════════════════════════════════════════════════
ALTER POLICY projects_anon_select ON public.projects
  USING (auth.role()='anon' AND portal_code IS NOT NULL AND portal_code <> '');
  -- v3.9.155b (anon-curl-Befund 2026-06-07): Projekt pmof9xiwk hat portal_code='' (leer, nicht NULL).
  -- Der Client schließt leere Codes aus (Z.4121 portal_code=neq.''). Nur "IS NOT NULL" würde das
  -- Leer-Code-Projekt anon-lesbar LASSEN → "<> ''" ergänzt, um exakt die Client-Portal-Eligibility zu treffen.
  -- Wirkung: anon-lesbare projects 2 → 1 (nur echte Portal-Projekte).

ALTER POLICY project_documents_anon_select ON public.project_documents
  USING (auth.role()='anon' AND kunde_freigabe = 1);   -- kunde_freigabe ist INTEGER (verifiziert)

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3 — SMOKE-VERIFY (nach Apply; zusätzlich anon-curl, siehe Bericht/PORTAL-RLS-AUDIT)
-- ═══════════════════════════════════════════════════════════
-- Neue Policy-Defs anzeigen:
SELECT policyname, qual FROM pg_policies
WHERE schemaname='public'
  AND policyname IN ('projects_anon_select','project_documents_anon_select');
-- Erwartet jetzt:
--   projects_anon_select:          (auth.role() = 'anon'::text) AND (portal_code IS NOT NULL) AND (portal_code <> ''::text)
--   project_documents_anon_select: (auth.role() = 'anon'::text) AND (kunde_freigabe = 1)
-- anon-curl danach: GET /projects?select=id (kein Filter) → muss .../1 sein (vorher .../2; das Leer-Code-Projekt fällt raus).
--
-- ANSCHLIESSEND anon-curl (Bericht Phase 3):
--   1) /project_documents?select=id OHNE Filter → muss jetzt NUR kunde_freigabe=1-Zeilen liefern (hier: 0).
--   2) Portal lebt: gültigen portal_code holen, GET /projects?portal_code=eq.<code> → 1 Zeile.
--   3) Intern unberührt: eingeloggter authenticated-User lädt projects/project_documents weiter voll
--      (ALTER betrifft NUR die _anon_select-Policies; authenticated-Policies sind separat).
--
-- AUTO-ROLLBACK: Wenn Portal-Login (2) NICHT die Zeile liefert → sofort RLS_anon_scope_v3.9.155_ROLLBACK.sql.
--   Lieber Leak offen als Portal kaputt.
