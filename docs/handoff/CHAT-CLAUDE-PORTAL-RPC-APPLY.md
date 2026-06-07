# Für Chat-Claude — Portal-RPC v3.9.156 applizieren (Supabase `jiggujpruejkaomgxarp`, public)

> ## ✅ ERLEDIGT 2026-06-07 (CC via Supabase-Plugin-MCP nach OAuth)
> Alle Schritte ausgeführt + verifiziert: Block-0-Spalten-Verify (start_date/end_date, uploaded_at/file_url
> korrigiert) → `portal_fetch` CREATE (SECURITY DEFINER, search_path, anon-EXECUTE) → Funktions- +
> Frontend-Integrations-Test (anon-RPC 200, `_mapProject` ok, KEIN betrag/kunden_nr/review_note/zugewiesen,
> Härtung `{}`) → **DROP** `projects_anon_select` + `project_documents_anon_select` → Smoke: anon-Direktread
> projects/project_documents/defects = **0 rows**, RPC weiter **200**. **Kein Rollback nötig.** defects hatte
> keine anon-SELECT-Policy. Die untenstehende Anleitung ist nur noch Referenz/Rollback-Quelle.

**Du hast DB-Zugriff, CC nicht.** Ziel: Portal von anon-Direktreads auf `portal_fetch`-RPC umstellen,
danach anon-SELECT auf projects/project_documents/defects droppen.

## 🔴 REIHENFOLGE IST KRITISCH — erst RPC, dann Frontend live, DANN Policies droppen
Frontend (v3.9.156, schon gepusht) hat einen **Fallback** auf die alten Direktreads → solange die
RPC fehlt ODER die Policies noch da sind, läuft das Portal weiter. **Niemals Policies VOR RPC+Frontend droppen.**

### Schritt 1 — RPC-Migration applizieren
- **Erst Block 0** von `sql/portal_rpc_v3.9.156.sql` (information_schema) laufen lassen und die
  **Whitelist-Spaltennamen gegen das echte Schema prüfen** (CC hat sie aus index.html-Writern inferred):
  - projects: heißt es `start`/`ende` oder `start_date`/`end_date`? Existieren `nr, fortschritt, email_kunde, ansprechpartner, gewerk`?
  - defects: `title, description, kunde_status, melder, ort, images` vorhanden?
  - Bei Abweichung: json_build_object-Keys in Block 1 anpassen, BEVOR du CREATE ausführst.
- Dann Block 1+2 (CREATE FUNCTION + REVOKE/GRANT) ausführen.
- Block 3 Smoke (im SQL-Editor):
  ```sql
  SELECT portal_code FROM projects WHERE portal_code IS NOT NULL AND portal_code <> '' LIMIT 1;  -- erwartet GED2024
  SELECT public.portal_fetch('GED2024');   -- {project, documents, defects} mit NUR whitelisteten Feldern
  SELECT public.portal_fetch('xx');         -- '{}' (zu kurz)
  SELECT public.portal_fetch('NICHTDA99');  -- '{}' (unbekannt)
  ```
  **Prüfen:** project enthält KEIN `betrag`/`kunden_nr`; defects enthält KEIN `review_note`/`zugewiesen`/`frist`/`status`/`prio`.

### Schritt 2 — Frontend über RPC verifizieren (CC macht das read-only)
- Sag CC „RPC ist live" → CC fährt: `POST /rest/v1/rpc/portal_fetch {"p_code":"GED2024"}` (anon-Key) →
  muss das Projekt + Docs + Mängel liefern. Und prüft im Live-Portal, dass `_viaRpc`-Pfad Daten zeigt.
- **Erst wenn das grün ist → Schritt 3.**

### Schritt 3 — anon-Policies droppen (NUR nach grünem Schritt 2)
Zuerst prüfen, ob eine defects-anon-Policy existiert:
```sql
SELECT policyname, cmd, qual FROM pg_policies
WHERE schemaname='public' AND tablename IN ('projects','project_documents','defects') AND 'anon'=ANY(roles);
```
Dann droppen (nur die anon-SELECT-Policies dieser Tabellen):
```sql
DROP POLICY IF EXISTS projects_anon_select ON public.projects;
DROP POLICY IF EXISTS project_documents_anon_select ON public.project_documents;
-- defects: NUR wenn oben eine anon-SELECT-Policy gelistet ist (Name aus der Abfrage einsetzen):
-- DROP POLICY IF EXISTS defects_anon_select ON public.defects;
```
> Hinweis: Die v3.9.155-ALTER (anon-Scope) sind dann obsolet — der DROP ist der Endzustand. Wer v3.9.155 schon
> appliziert hat: der DROP ersetzt es sauber. Wer nicht: direkt hierher.

### Schritt 4 — CC verifiziert read-only (anon-Direktread jetzt zu)
- `GET /projects?select=id`, `GET /project_documents?select=id`, `GET /defects?select=id` mit anon-Key
  → muss jetzt **0 Zeilen / 401 / 403** liefern (Direktread tot).
- `POST /rpc/portal_fetch {GED2024}` → liefert weiter Daten (Portal lebt über RPC).
- authenticated (eingeloggt) → projects/defects/documents laden unverändert voll.

### ROLLBACK
- RPC-Probleme vor Policy-Drop: `sql/portal_rpc_v3.9.156_ROLLBACK.sql` (DROP FUNCTION) + Frontend-Fallback trägt.
- Policies versehentlich zu früh gedroppt + Portal kaputt: anon-SELECT-Policies neu anlegen
  (`CREATE POLICY ..._anon_select ON ... FOR SELECT TO anon USING (...)` mit dem v3.9.155-Scope-Prädikat),
  bis RPC+Frontend grün sind.

## Was schon erledigt ist (CC)
- `sql/portal_rpc_v3.9.156.sql` + `_ROLLBACK.sql` geschrieben (Datei, nicht appliziert).
- Frontend v3.9.156 (RPC-first + Fallback) gepusht — node-check 0, Bracket `() -1` stabil, pytest grün.
- Design + Feld-Inventur: `docs/handoff/PORTAL-RPC-DESIGN.md`.
- OUT OF SCOPE bleibt: plans/checklists (Portal liest weiter direkt), activity_log, ~29 auth-Tabellen, _juprowaPush.
