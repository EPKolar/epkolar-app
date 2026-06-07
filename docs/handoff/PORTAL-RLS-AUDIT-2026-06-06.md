# 🔴 Kundenportal Security-Audit (Agententeam Welle 6, 2026-06-06)

> ## ✅ GESAMTSTAND 2026-06-07 (CC via Supabase-Plugin-MCP, alles live appliziert + read-only verifiziert)
> Der hier beschriebene anon-Leak ist **serverseitig geschlossen**:
> - **projects / project_documents:** anon-Direktread-Policies **GEDROPPT** → anon kann diese Tabellen NICHT mehr
>   direkt lesen (verifiziert: anon-curl `GET /projects`/`/project_documents` = **0 rows**). Portal-Zugriff läuft
>   nur noch über die SECURITY-DEFINER-RPC **`portal_fetch`** (whitelisted, kein betrag/kunden_nr/review_note/
>   zugewiesen, serverseitige Code-Validierung). Migrationen: `sql/portal_rpc_v3.9.156.sql`,
>   `sql/portal_anon_policy_drop_v3.9.156.sql` (+ Rollbacks).
> - **defects:** hatte nie eine anon-SELECT-Policy. Portal-LESEN via RPC; Portal-SCHREIBEN (Mangel melden / Abnahme)
>   jetzt über `portal_submit_defect` / `portal_confirm_abnahme` (SECURITY DEFINER, code-validiert, scoped) —
>   vorher 403/kaputt. `sql/portal_write_rpcs_v3.9.157.sql`.
> - **storage.objects:** anon-**Listing/Enumeration GEDROPPT** (`Allow anon reads` + `Public read epkolar-files`) →
>   anon kann den Bucket nicht mehr enumerieren (verifiziert: `/object/list` 200/4 → 200/0). App nutzt nur
>   `/object/public/` + listet nie → verifiziert non-breaking (public-Download HEAD 200 unverändert).
>   `sql/storage_anon_listing_drop_v3.9.156.sql` (+ Rollback).
>
> ### ⚠️ RESTRISIKO (NICHT in dieser Arbeit gefixt — separater Pre-Live-Task)
> - **Bucket `epkolar-files` bleibt PUBLIC**: Wer einen exakten Datei-Pfad kennt oder errät
>   (`plans/<projectid>/<ts>_<name>.pdf`), kann die Datei weiterhin **ohne Login** per public-URL laden. Das Drop
>   schließt nur die Enumeration, nicht den Direkt-URL-Zugriff. **Echte Dokumentensicherheit = privater Bucket +
>   signierte URLs** (Frontend müsste überall `createSignedUrl` statt `/object/public/` nutzen). Aufwand: Frontend +
>   Storage-Policy-Umbau. Als eigener Pre-Live-Task vormerken.
> - **`activity_log_anon_insert`** weiterhin offen (anon darf ins Audit-Log schreiben) — separater Task, nicht Teil
>   dieser Portal-Arbeit.


**KRITISCH für Sebastian — server-seitig, NICHT im Client fixbar.** Das Kundenportal läuft **unauthentifiziert**: Portal-Nutzer sind nie eingeloggt → `_authToken=null` → **jede Portal-Anfrage geht mit dem hartkodierten anon-`SUPABASE_KEY`** (im ausgelieferten JS sichtbar). Der „Zugangscode" wird **nur client-seitig** verglichen (`tryPortal` L4122 `portalCode===code`). **Der gesamte Access-Boundary ist damit anon-RLS.** Wenn die anon-Policies permissiv sind, ist das Portal ein voller Kunden-Daten-Leak + Cross-Project-Write — **unabhängig vom Code**.

## ✅ Client-seitig gehärtet (v3.9.154)
- **Portal-Token-Entropie**: Generator nutzte `Math.random()` 4-stellig + 3-Zeichen-Präfix aus der öffentlichen Projektnummer (~13 bit, trivial brute-forcebar, nicht crypto). → jetzt `crypto.getRandomValues` 6 Zeichen aus 31er-Alphabet ohne 0/O/1/I/L (~30 bit). **Notwendig, aber NICHT hinreichend** — der Code-Match bleibt client-only, RLS muss zeilenscopen.

## 🔴 SEBASTIAN-SERVER-AUDIT — anon-RLS-Policies prüfen (load-bearing)
Für die **anon**-Rolle in Supabase, pro Tabelle:

1. **`projects`** — anon SELECT MUSS verweigert oder spalten-/zeilenrestriktiv sein. Aktuell liest der Client die **ganze Tabelle inkl. ALLER `portal_code`** (`_sbGet("projects","portal_code=not.is.null...")` L4121). Ist anon-SELECT offen → `fetch(REST+"/projects",{headers:{apikey:SUPABASE_KEY}})` dumpt **alle Kunden, Adressen, Emails, Vertragsbeträge (`betrag`) + alle Portal-Codes** in einem Request. **Wichtigster Punkt.**
2. **`defects`** — anon SELECT/INSERT/UPDATE MUSS zeilen-scoped auf den server-validierten Portal-Kontext sein, NICHT auf client-geliefertes `project_id=eq.`. Sonst:
   - SELECT: jedes Projekt-`project_id` einsetzbar (ids `p1`,`p4` trivial enumerierbar) → fremde Kunden-Mängel + Fotos leaken. Der `&melder=eq.Kunde`-Filter (L4159) ist client-only Defense-in-Depth, server-seitig wirkungslos.
   - INSERT (Mangel melden, L4213): `project_id`/`melder`/`kunde_status` sind client-gesetzt → Portal-Nutzer kann Defect in **jedes** Projekt posten + `melder` fälschen.
   - UPDATE (Abnahme, L4230): `PUT /defects/{id}` mit `{status:"behoben",kunde_status:"abgenommen"}` auf **jede** Defect-id → Status-Eskalation/Fälschung fremder/interner Defects. Spalten-Whitelist nötig (`_mapBody` reicht beliebige Felder durch).
3. **`project_documents`, `plans`, `checklists`** — anon SELECT scoped auf freigegebene Zeilen des richtigen Projekts. Insbesondere **`plans`** wird OHNE `kunde_freigabe`-Filter geholt (L4170, nur client-seitig gefiltert L4173) → server-seitig müssen nicht-freigegebene Pläne geblockt sein.

## ⏳ Weitere Funde (niedriger / Client)
- **P2 `_portalSync` Cross-Context** (L4185): Portal flusht die **globale** syncQueue (nicht nach Session/Rolle getrennt). Auf geteiltem Gerät: Staff loggt aus → Kunde nutzt Portal → `window.__doSync=_portalSync` versucht Staff-Items unter anon-Key zu flushen (meist RLS-fail, aber Loop `break`t → Queue stockt; was anon-RLS erlaubt, läuft im falschen Kontext). project_id ist im Body eingebacken → **kein** Re-Routing, aber Cross-Context-Execution. Fix: Items nach Session/Rolle taggen, Portal flusht nur portal-origin-Items. (Auch: `_portalSync` ohne Retry-Cap, siehe AGENT-REVIEW-FINDINGS Welle 2.)
- **P3 reviewNote-Disclosure**: interner `reviewNote`/zugewiesener Techniker wird dem Kunden für seine eigenen Mängel gezeigt (L4361-4362). Prüfen ob review notes kundentauglich sind.
- **P3 XSS aktuell verteidigt**: Kunden-Text (name/beschreibung) ist NICHT sanitisiert, aber überall via React (auto-escape) ODER `esc()` in Exporten gerendert → kein aktiver Stored-XSS. **Aber**: AS/Formular-Reports nutzen `document.write(el.innerHTML)` (L9914/L7081) — wenn je ein Defect-Feld in einen `document.write`-Export kommt, MUSS `esc()`. Guard/Kommentar empfohlen.

## ✅ Korrekt verteidigt
Kein service-role-Key im Client; users-Tabelle hinter `login_lookup`-RPC + Spalten-Allowlist; Mangel-Text längenlimitiert + Doppel-Submit-Guard; bestehende Report-Exporte escapen via `esc()`/`_e()`; `_openFileUrl` via Blob + noopener; Portal zeigt nur das eine gematchte Projekt (keine Enumeration in der UI).

---

## Update 2026-06-07 — anon-Scope-ALTER vorbereitet (v3.9.155), NICHT appliziert

**⚠️ CC konnte die ALTER NICHT selbst applizieren:** Der claude.ai-Supabase-MCP-Connector ist
für eine andere Org autorisiert (MOBOLog/SRC Seefunk/Hausverwaltung) — `list_projects` enthält
`jiggujpruejkaomgxarp` NICHT → `execute_sql`/`apply_migration` → "You do not have permission".
Konsistent mit der langjährigen Realität „SQL macht Chat-Claude/Sebastian". **Phase 2 (Apply) +
Phase 3 (post-Apply-Smoke) + Auto-Rollback müssen von jemandem mit DB-Zugriff ausgeführt werden.**

**Read-only-Beleg (anon-curl, öffentlicher anon-Key, 2026-06-07):**
| Query | content-range (.../TOTAL) | Deutung |
|---|---|---|
| `/project_documents?select=id` (kein Filter) | `.../1` | anon liest **1 Dokument** |
| `/project_documents?...&kunde_freigabe=eq.1` | `.../0` | davon **0 freigegeben** → **das 1 ist NICHT-freigegeben** = Leak |
| `/projects?select=id` (kein Filter) | `.../2` | anon liest alle 2 Projekte |
| `/projects?...&portal_code=not.is.null` | `.../2` | beide haben portal_code |
| `kunde_freigabe`-Wert | `0` | Spaltentyp **INTEGER** (Prädikat `= 1`) |

**Bewertung (ehrlich):**
- **project_documents**: ALTER schließt einen **demonstrierten** Leak (1 nicht-freigegebenes Dok wird anon-unlesbar → 0).
- **projects**: ALTER ist korrekte Härtung, senkt aber die aktuell lesbare Menge NICHT (beide Projekte sind Portal-Projekte). Das eigentliche projects-Leck (anon liest **alle Spalten aller Portal-Projekte** inkl. Beträge/Email, ohne den Code zu kennen) bleibt offen — das schließt erst die RPC unten.
- **plans_anon_select**: NICHT im v3.9.155-Scope (Task-Scope = 2 Tabellen), hat aber dasselbe Leck (anon liest alle Pläne) → eigener Folge-Task (auch im v3103-Draft enthalten).

**Bereitgestellt (committet):** `sql/RLS_anon_scope_v3.9.155.sql` (Verify-Block + 2 ALTER + Smoke-Block)
+ `sql/RLS_anon_scope_v3.9.155_ROLLBACK.sql`. Hinweis: Es existiert bereits `sql/migrate_anon_portal_lockdown_v3103.sql`
(deckt zusätzlich plans, aber Snapshot+Recreate-Ansatz) — ebenfalls **nicht appliziert**. v3.9.155 ist die
schlankere ALTER-statt-DROP-Variante.

## PHASE 4 — Follow-up (NICHT jetzt bauen, separater Task)
Die ALTER sind nur **Zwischen-Härtung**: anon kann weiterhin **alle Portal-Projekte enumerieren** und
deren volle Zeilen lesen (Code-Match ist client-only). **Robuster Endzustand:** eine
`SECURITY DEFINER`-RPC `portal_load(p_code text)`, die serverseitig den Code validiert und NUR das eine
passende Projekt + dessen freigegebene Docs/Pläne/Defects zurückgibt (whitelisted Spalten, kein betrag/intern).
Danach ist anon-SELECT auf projects/project_documents/plans **ganz entbehrlich** (Policies können zu
`USING(false)` für anon werden). Frontend ruft dann `rpc/portal_load` statt der Tabellen-GETs.
→ Als separaten Task vorschlagen; benötigt Frontend-Änderung (KundenPortal) + RPC-Definition.

### Nachtrag 2026-06-07 (2. Apply-Versuch): immer noch nicht appliziert + Prädikat-Korrektur
- CC-MCP-Zugriff erneut geprüft: weiterhin "You do not have permission" → Apply weiterhin nur durch Chat-Claude/Editor.
- Read-only-Smoke (anon-curl) bestätigt: **Migration NICHT appliziert** (anon liest weiter 1 nicht-freigegebenes Dok).
- **Neuer Befund:** Projekt `pmof9xiwk` hat `portal_code=''` (leer, nicht NULL). Aufschlüsselung: `IS NOT NULL`=2,
  `IS NOT NULL & <> ''`=1 (nur `p4`/GED2024), `= ''`=1. Der Client schließt leere Codes aus (Z.4121 `neq.''`).
  → Migrations-Prädikat von `portal_code IS NOT NULL` auf **`portal_code IS NOT NULL AND portal_code <> ''`**
  korrigiert (Datei v3.9.155). Sonst bliebe das Nicht-Portal-Projekt `pmof9xiwk` anon-lesbar. Erwartete Wirkung:
  anon-lesbare projects 2 → 1.
