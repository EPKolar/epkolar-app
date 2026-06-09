-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ═══════════════════════════════════════════════════════════════════════════
-- AUFGABE #3 — material_catalogs anon-Lockdown (v3.9.213)
-- Supabase: jiggujpruejkaomgxarp, schema public.
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ZIEL: anon darf KEIN DML/TRUNCATE auf public.material_catalogs mehr ausführen.
--   DML bleibt ausschließlich `authenticated` vorbehalten. Das SELECT-Verhalten
--   (Katalog-READ) bleibt UNVERÄNDERT — weder Grants noch SELECT-Policies werden
--   angefasst.
--
-- ── CODE-PFAD-EVIDENZ (index.html @ v3.9.213, Commit fa9d37a) ────────────────
--   READ (muss weiter funktionieren):
--     Z12939  const cats=await _sbGet("material_catalogs","order=system.asc");
--             → _sbGet → fetch(... headers:_sbRH()) → _sbH() sendet
--               "Authorization: Bearer "+_authToken (AUTHENTICATED, da der Material-
--               Katalog-Editor NUR in der eingeloggten App erreichbar ist, NICHT im
--               anon Kunden-Portal). Anon-Read wird hier nicht benötigt.
--
--   WRITE (alle via SyncQueue SQ.push → _translateAndExec → Generic CRUD):
--     ROUTE_MAP Z1887  "material-catalogs":["material-catalogs","material_catalogs"]
--     Z13791  PUT  /api/material-catalogs/:id   (update cats)
--     Z13800  POST /api/material-catalogs       (neuer Katalog)
--     Z13812  DELETE /api/material-catalogs/:id  (löschen)
--     Z13878  PUT  /api/material-catalogs/:id   (gewerk-update)
--     Z13885  POST /api/material-catalogs       (neuer Katalog)
--     → _translateAndExec Generic-CRUD (Z2161-2181): POST=_sbPost, PUT/PATCH=_sbPatch,
--       DELETE=_sbDelete — ALLE nutzen _sbWH()/_sbH() → "Authorization: Bearer "+_authToken
--       (AUTHENTICATED JWT). KEIN anon-Schreibpfad existiert im Frontend.
--
--   → FRONTEND-IMPACT: KEINER. Kein anon-Write gefunden; READ bleibt authenticated
--     und durch diese Migration unberührt (nur DML/TRUNCATE-Grants/Policies anon
--     werden entzogen).
--
-- ── ANNAHME / VERIFY-PFLICHT (Operator vor Apply) ───────────────────────────
--   Die exakten Namen evtl. vorhandener anon-DML-Policies auf material_catalogs
--   sind im Repo NICHT belegt (kein pg_policies-Dump für jiggujpruejkaomgxarp im
--   CC-Zugriff — andere Org). Daher:
--     * Block 0 (Snapshot) listet/sichert ALLE bestehenden material_catalogs-
--       Policies + Grants VOR der Änderung (re-runnable, idempotent).
--     * Block 2 REVOKE entzieht anon table-level DML/TRUNCATE deterministisch
--       (wirkt unabhängig von Policy-Namen).
--     * Block 3 droppt anon-DML-Policies NUR über bekannte/erwartete Namen
--       (DROP POLICY IF EXISTS = No-Op falls nicht vorhanden). Findet der Snapshot
--       in Block 0 weitere anon-INSERT/UPDATE/DELETE-Policies mit ABWEICHENDEM
--       Namen → Operator ergänzt analoge DROP-Zeilen (siehe Hinweis in Block 3).
--   SELECT-Policies/Grants werden bewusst NICHT angefasst.
--
-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK 0 — SNAPSHOT (read+persist, PFLICHT vor den Änderungen, idempotent)
-- ═══════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS public._rls_snapshot_matcat_v39213 (
  ts          timestamptz DEFAULT now(),
  kind        text,          -- 'policy' | 'grant'
  schemaname  text,
  tablename   text,
  polname     text,
  roles       text[],
  cmd         text,
  qual        text,
  with_check  text,
  grantee     text,
  privilege   text
);

-- Bestehende Policies sichern:
INSERT INTO public._rls_snapshot_matcat_v39213
  (kind, schemaname, tablename, polname, roles, cmd, qual, with_check)
SELECT 'policy', schemaname, tablename, polname, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname='public' AND tablename='material_catalogs';

-- Bestehende Table-Grants sichern:
INSERT INTO public._rls_snapshot_matcat_v39213
  (kind, schemaname, tablename, grantee, privilege)
SELECT 'grant', table_schema, table_name, grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema='public' AND table_name='material_catalogs';

-- Manuelle Sichtprüfung (Operator): zeigt, WAS anon aktuell darf —
--   erwartet wird HÖCHSTENS SELECT; INSERT/UPDATE/DELETE/TRUNCATE = Leak-Fläche.
--   SELECT grantee, privilege_type FROM information_schema.role_table_grants
--   WHERE table_schema='public' AND table_name='material_catalogs' AND grantee='anon'
--   ORDER BY privilege_type;

-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK 1 — RLS aktiv sicherstellen (idempotent; ändert SELECT-Verhalten nicht)
-- ═══════════════════════════════════════════════════════════════════════════
ALTER TABLE public.material_catalogs ENABLE ROW LEVEL SECURITY;

-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK 2 — anon table-level DML/TRUNCATE entziehen (deterministisch)
--   SELECT wird NICHT entzogen → Katalog-READ bleibt unverändert.
-- ═══════════════════════════════════════════════════════════════════════════
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.material_catalogs FROM anon;

-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK 3 — etwaige anon-DML-Policies droppen (idempotent, No-Op wenn fehlend)
--   HINWEIS: Falls Block-0-Snapshot weitere anon-Policies mit cmd
--   IN ('INSERT','UPDATE','DELETE','ALL') und ABWEICHENDEM Namen zeigt,
--   hier analoge DROP-Zeilen ergänzen. SELECT-Policies NICHT droppen.
-- ═══════════════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS material_catalogs_anon_insert ON public.material_catalogs;
DROP POLICY IF EXISTS material_catalogs_anon_update ON public.material_catalogs;
DROP POLICY IF EXISTS material_catalogs_anon_delete ON public.material_catalogs;
DROP POLICY IF EXISTS material_catalogs_anon_all    ON public.material_catalogs;
DROP POLICY IF EXISTS material_catalogs_anon_write   ON public.material_catalogs;

-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK 4 — Defense-in-Depth: authenticated-DML-Policies sicherstellen
--   "CREATE POLICY IF NOT EXISTS" ist KEIN gültiges PostgreSQL (Lesson v3.9.105)
--   → DROP IF EXISTS + CREATE = idempotent & re-runnable.
--   So bleibt der authenticated Schreibpfad (Generic CRUD) garantiert offen.
--   ANNAHME: material_catalogs ist eine globale Stammdaten-Tabelle ohne
--   user_id/boat_id-Scoping → WITH CHECK (true)/USING (true) für authenticated.
--   Falls in der Live-DB bereits feiner granulierte authenticated-DML-Policies
--   existieren (Block-0-Snapshot prüfen), diese BEVORZUGEN und Block 4 weglassen.
-- ═══════════════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS material_catalogs_auth_insert ON public.material_catalogs;
CREATE POLICY material_catalogs_auth_insert
  ON public.material_catalogs FOR INSERT TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS material_catalogs_auth_update ON public.material_catalogs;
CREATE POLICY material_catalogs_auth_update
  ON public.material_catalogs FOR UPDATE TO authenticated
  USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS material_catalogs_auth_delete ON public.material_catalogs;
CREATE POLICY material_catalogs_auth_delete
  ON public.material_catalogs FOR DELETE TO authenticated
  USING (true);

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFY (manuell nach Apply ausführen):
-- ═══════════════════════════════════════════════════════════════════════════
-- a) anon hat KEIN DML/TRUNCATE mehr (nur noch ggf. SELECT):
--      SELECT grantee, privilege_type FROM information_schema.role_table_grants
--      WHERE table_schema='public' AND table_name='material_catalogs' AND grantee='anon'
--      ORDER BY privilege_type;
--    Erwartung: KEINE Zeile mit INSERT/UPDATE/DELETE/TRUNCATE (höchstens SELECT).
--
-- b) Keine anon-DML-Policy mehr vorhanden:
--      SELECT polname, roles, cmd FROM pg_policies
--      WHERE schemaname='public' AND tablename='material_catalogs'
--      ORDER BY cmd, polname;
--    Erwartung: KEINE Policy mit roles enthält 'anon' und cmd IN (INSERT/UPDATE/DELETE/ALL).
--
-- c) anon WRITE → 403 (anon-Key als apikey + Authorization):
--      curl -s -o /dev/null -w "POST %{http_code}\n" -X POST \
--        "https://jiggujpruejkaomgxarp.supabase.co/rest/v1/material_catalogs" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY" \
--        -H "Content-Type: application/json" \
--        -d '{"id":"verify_anon_matcat","system":"ZZ","gewerk":"ZZ","cats":"[]"}'
--      curl -s -o /dev/null -w "PATCH %{http_code}\n" -X PATCH \
--        "https://jiggujpruejkaomgxarp.supabase.co/rest/v1/material_catalogs?id=eq.any" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY" \
--        -H "Content-Type: application/json" -d '{"gewerk":"ZZ"}'
--      curl -s -o /dev/null -w "DELETE %{http_code}\n" -X DELETE \
--        "https://jiggujpruejkaomgxarp.supabase.co/rest/v1/material_catalogs?id=eq.any" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY"
--      Erwartung: jeweils 401/403/42501 — KEIN 2xx.
--
-- d) authenticated WRITE → unverändert (gültiger User-JWT, z.B. admin/buero):
--      curl -s -o /dev/null -w "POST %{http_code}\n" -X POST \
--        "https://jiggujpruejkaomgxarp.supabase.co/rest/v1/material_catalogs" \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $USER_JWT" \
--        -H "Content-Type: application/json" -H "Prefer: return=representation" \
--        -d '{"id":"verify_auth_matcat","system":"ZZ","gewerk":"ZZ","cats":"[]"}'
--      Erwartung: 201. (Test-Zeile danach wieder löschen.)
--
-- e) Katalog-READ → unverändert 200 (in-App, eingeloggt):
--      Material-Katalog-Tab öffnen → Liste lädt (entspricht
--      _sbGet("material_catalogs","order=system.asc") → REST 200 mit Zeilen).
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK: siehe fix_material_catalogs_anon_v3.9.213_ROLLBACK.sql
-- ═══════════════════════════════════════════════════════════════════════════
