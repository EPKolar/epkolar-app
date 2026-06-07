# Für Chat-Claude — RLS anon-Scope v3.9.155 applizieren

**Supabase:** `jiggujpruejkaomgxarp`, Schema `public`. **Du hast DB-Zugriff, CC nicht** (CC-MCP = andere Org).
**Ziel:** anon-SELECT-Policies einschränken — **ALTER, NICHT DROP** (DROP würde das Portal lahmlegen).
**Grundsatz:** lieber Leak offen als Portal kaputt → bei gebrochenem Portal sofort Rollback.

Dateien im Repo: `sql/RLS_anon_scope_v3.9.155.sql` + `sql/RLS_anon_scope_v3.9.155_ROLLBACK.sql`.

## Vorab-Beleg (CC read-only per anon-curl, 2026-06-07)
- `GET /project_documents?select=id` (kein Filter) → `content-range .../1` ; mit `&kunde_freigabe=eq.1` → `.../0`
  → anon liest **1 NICHT-freigegebenes Dokument** (kunde_freigabe=0) = **Leak**. ALTER schließt das (1→0).
- `GET /projects?select=id` → `.../2` ; `&portal_code=not.is.null` → `.../2` → beide Projekte haben portal_code
  (ALTER senkt die Menge aktuell nicht, ist aber korrekte Härtung).
- `project_documents.kunde_freigabe` = **INTEGER** (Wert `0`) → Prädikat **`= 1`**.

---

## Schritt 1 — VERIFY (Pflicht vor jedem Write)
```sql
SELECT policyname, cmd, roles, qual, with_check FROM pg_policies
WHERE schemaname='public' AND policyname IN ('projects_anon_select','project_documents_anon_select');
-- Erwartet: 2 Zeilen, cmd=SELECT, roles={anon}, qual=(auth.role() = 'anon'::text), with_check=NULL.
-- Wenn Namen/qual NICHT so: STOP, melden, nicht raten.

SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema='public'
  AND ((table_name='projects' AND column_name='portal_code')
    OR (table_name='project_documents' AND column_name='kunde_freigabe'));
-- Erwartet: projects.portal_code existiert; project_documents.kunde_freigabe = integer.
-- Falls kunde_freigabe = boolean: unten "= 1" durch "= true" ersetzen.
```

## Schritt 2 — APPLY (ALTER)
```sql
ALTER POLICY projects_anon_select ON public.projects
  USING (auth.role()='anon' AND portal_code IS NOT NULL AND portal_code <> '');

ALTER POLICY project_documents_anon_select ON public.project_documents
  USING (auth.role()='anon' AND kunde_freigabe = 1);   -- kunde_freigabe ist INTEGER (verifiziert)
```
> ⚠️ `portal_code <> ''` ist Absicht: Projekt `pmof9xiwk` hat `portal_code=''` (leer). Der Client schließt
> leere Codes aus (Z.4121 `neq.''`); ohne `<> ''` bliebe dieses Nicht-Portal-Projekt anon-lesbar.

## Schritt 3 — SMOKE (anon real per curl)
anon-Key = `SUPABASE_KEY` aus `index.html` Z.471. Basis-URL: `https://jiggujpruejkaomgxarp.supabase.co/rest/v1`.
Header je Request: `apikey: <KEY>`, `Authorization: Bearer <KEY>`, `Prefer: count=exact`, `Range: 0-0`.
Den `content-range`-Response-Header lesen (Format `bereich/TOTAL`). Mit `curl.exe` (nicht PowerShell Invoke-WebRequest — der lehnt `Range: 0-0` ab).

1. **Leak weg:** `GET /project_documents?select=id` (kein Filter) → muss jetzt `.../0` sein (vorher `.../1`).
   `GET /projects?select=id` (kein Filter) → muss jetzt `.../1` sein (vorher `.../2`; Leer-Code-Projekt fällt raus).
2. **Portal lebt (KRITISCH):**
   ```sql
   SELECT portal_code FROM projects WHERE portal_code IS NOT NULL LIMIT 1;
   ```
   dann `GET /projects?portal_code=eq.<code>` mit anon-Key → **muss genau 1 Zeile** liefern (`.../1`).
   Ebenso `GET /project_documents?project_id=eq.<projektId>&kunde_freigabe=eq.1` → freigegebene Docs des Projekts.
3. **Intern unberührt:** mit einem authenticated-JWT (eingeloggter User) `GET /projects` + `/project_documents`
   → laden weiter VOLL (ALTER betrifft nur die `_anon_select`-Policies; authenticated-Policies sind separat).

## Schritt 4 — AUTO-ROLLBACK (NUR falls Schritt 3.2 KEINE Zeile liefert = Portal kaputt)
```sql
ALTER POLICY projects_anon_select ON public.projects USING (auth.role()='anon');
ALTER POLICY project_documents_anon_select ON public.project_documents USING (auth.role()='anon');
SELECT policyname, qual FROM pg_policies WHERE schemaname='public'
  AND policyname IN ('projects_anon_select','project_documents_anon_select');
```
→ und KLAR melden, dass zurückgerollt wurde + warum.

---

## Bericht zurück an Sebastian/CC
1. Schritt-1-Defs (policyname/qual + kunde_freigabe-Typ).
2. Smoke 1/2/3 grün? (mit den content-range-Zahlen).
3. Rollback nötig gewesen? ja/nein.

## NICHT in diesem Task (separate Folge-Tasks, dokumentiert in PORTAL-RLS-AUDIT-2026-06-06.md)
- `plans_anon_select` hat dasselbe Leck (anon liest alle Pläne) — gleiche ALTER-Logik nötig (`plans` von Portal-Projekten + kunde_freigabe).
- `defects` anon INSERT/UPDATE: client-gesetztes project_id/melder/kunde_status → Schreib-Scope serverseitig fehlt.
- Robuster Endzustand: `SECURITY DEFINER`-RPC `portal_load(code)` → danach anon-SELECT entbehrlich.
