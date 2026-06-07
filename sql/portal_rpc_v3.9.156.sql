-- ═══════════════════════════════════════════════════════════
-- portal_fetch RPC v3.9.156 — SECURITY DEFINER, ersetzt anon-Direktreads im Kunden-Portal
-- Erstellt: 2026-06-07 (CC, Sebastian-Spec). Supabase: jiggujpruejkaomgxarp, public.
-- ═══════════════════════════════════════════════════════════
-- ZWECK: Kunde gibt portal_code ein → RPC validiert serverseitig + gibt NUR das eine Projekt +
--   dessen freigegebene Dokumente (kunde_freigabe=1) + dessen Kunden-Mängel (melder='Kunde') zurück,
--   NUR mit whitelisteten, kundentauglichen Spalten (kein SELECT *, keine internen Felder).
--   Danach braucht anon KEIN SELECT mehr auf projects/project_documents/defects (Phase 4 = Policy-Drop).
--
-- ✅ APPLIZIERT 2026-06-07 (CC via Supabase-Plugin-MCP nach OAuth). Block 0 lief, Spalten gegen echtes
--   Schema VERIFIZIERT + korrigiert: projects start_date/end_date (NICHT start/ende), project_documents
--   uploaded_at + file_url (es gibt KEIN created_at/file_path auf der Tabelle). JSON-Keys (start/ende/
--   created_at/file_path) bewusst unverändert → Frontend-Mapper. defects-Whitelist unverändert.
--   Smoke grün: portal_fetch('GED2024')=Projekt ohne betrag/kunden_nr/review_note/zugewiesen; 'xx'/'NICHTDA99'='{}';
--   anon-EXECUTE=true; prosecdef=true. Danach DROP der 2 anon-SELECT-Policies (s.u.) → anon-Direktread
--   projects/project_documents = 0 rows, RPC weiter 200. Kein Rollback nötig.
--   Ausschlussliste (NICHT in der RPC): defects.zugewiesen/frist/review_note/status/prio/ebene/gewerk/created_by;
--   projects.betrag/kunden_nr/matchcode/land/type/beschreibung/notizen/tags/created_by. (Siehe PORTAL-RPC-DESIGN.md.)
--
-- ═══════════════════════════════════════════════════════════
-- BLOCK 0 — VERIFY Spalten (read-only, PFLICHT vor CREATE; Whitelist ggf. anpassen)
-- ═══════════════════════════════════════════════════════════
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema='public' AND table_name IN ('projects','project_documents','defects')
ORDER BY table_name, ordinal_position;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1 — Funktion
-- ═══════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.portal_fetch(p_code text)
RETURNS json
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  WITH proj AS (
    SELECT *
    FROM public.projects
    WHERE portal_code = btrim(coalesce(p_code,''))
      AND portal_code <> ''
      AND length(btrim(coalesce(p_code,''))) >= 3   -- Input-Härtung: zu kurz/leer → kein Treffer
    LIMIT 1
  )
  SELECT CASE
    WHEN NOT EXISTS (SELECT 1 FROM proj) THEN '{}'::json   -- kein Treffer → leeres Objekt, kein Fehler, keine Enumeration
    ELSE json_build_object(
      'project', (SELECT json_build_object(
          'id', p.id, 'name', p.name, 'nr', p.nr, 'kunde', p.kunde,
          'ansprechpartner', p.ansprechpartner, 'strasse', p.strasse, 'plz', p.plz, 'ort', p.ort,
          'telefon', p.telefon, 'email_kunde', p.email_kunde, 'status', p.status,
          'fortschritt', p.fortschritt, 'start', p.start_date, 'ende', p.end_date, 'gewerk', p.gewerk,
          'portal_code', p.portal_code
        ) FROM proj p),
      'documents', COALESCE((SELECT json_agg(json_build_object(
          'id', d.id, 'project_id', d.project_id, 'name', d.name, 'file_name', d.file_name,
          'category', d.category, 'created_at', d.uploaded_at, 'file_data', d.file_data, 'file_path', d.file_url
        )) FROM public.project_documents d JOIN proj ON d.project_id = proj.id
           WHERE d.kunde_freigabe = 1), '[]'::json),
      'defects', COALESCE((SELECT json_agg(json_build_object(
          'id', x.id, 'project_id', x.project_id, 'title', x.title, 'description', x.description,
          'melder', x.melder, 'kunde_status', x.kunde_status, 'ort', x.ort, 'images', x.images,
          'created_at', x.created_at
        )) FROM public.defects x JOIN proj ON x.project_id = proj.id
           WHERE x.melder = 'Kunde'), '[]'::json)
    )
  END;
$$;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2 — Rechte: nur EXECUTE für anon + authenticated (kein direkter Tabellenzugriff nötig)
-- ═══════════════════════════════════════════════════════════
REVOKE ALL ON FUNCTION public.portal_fetch(text) FROM public;
GRANT EXECUTE ON FUNCTION public.portal_fetch(text) TO anon, authenticated;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3 — Smoke (nach CREATE)
-- ═══════════════════════════════════════════════════════════
-- a) Treffer: gültigen Code holen + RPC testen
--    SELECT portal_code FROM projects WHERE portal_code IS NOT NULL AND portal_code <> '' LIMIT 1;
--    SELECT public.portal_fetch('<code>');   -- muss {project,documents,defects} mit den whitelisteten Feldern liefern
-- b) Kein Treffer / Härtung:
--    SELECT public.portal_fetch('xx');        -- zu kurz → '{}'
--    SELECT public.portal_fetch('NICHTDA99'); -- unbekannt → '{}'
-- c) anon real (curl, anon-Key): POST /rest/v1/rpc/portal_fetch  Body {"p_code":"<code>"} → JSON.
--    Prüfen: KEIN betrag/kunden_nr im project; KEIN review_note/zugewiesen/frist im defects.
--
-- ROLLBACK: sql/portal_rpc_v3.9.156_ROLLBACK.sql (DROP FUNCTION).
