# Portal SECURITY DEFINER RPC — Design + Feld-Inventur (v3.9.156)

**Ziel:** Kunden-Portal von anon-Tabellen-Direktzugriff (projects/project_documents/defects) auf EINE
`SECURITY DEFINER`-RPC `portal_fetch(p_code)` umstellen. Endzustand: anon braucht KEIN SELECT mehr auf
diese 3 Tabellen. Reversibel, getestet, in dieser Reihenfolge: RPC → Frontend live → DANN Policies droppen.

**Out of Scope:** plans + checklists (Portal liest sie weiter direkt via anon — eigener Folge-Task),
activity_log, ~29 authenticated-Tabellen, _juprowaPush.

## PHASE 1 — INVENTUR (read-only verifiziert aus index.html)

### Portal-Reads heute (KundenPortal Z.4143–4188 + PortalEntry Z.4112–4141)
| Read | Zeile | Filter |
|---|---|---|
| `projects` | 4121 | `portal_code=not.is.null&portal_code=neq.` (Client-Match Z.4122 case-insensitiv) |
| `defects` | 4159 | `project_id=eq.<id>&melder=eq.Kunde` |
| `project_documents` | 4163 | `project_id=eq.<id>&kunde_freigabe=eq.1` |
| `plans` | 4170 | `project_id=eq.<id>` (+ client `kunde_freigabe`) — **OUT OF SCOPE** |
| `checklists` | 4178 | `project_id=eq.<id>` — **OUT OF SCOPE** |

### Gerenderte Felder (regex über KundenPortal-Bereich) → das DARF die RPC zurückgeben
- **Mangel (m.*):** id, pid, name(=title), beschreibung(=description), date(=created_at), melder, kundeStatus(=kunde_status), ort, photos(=images), pct, **reviewNote**, **zugewiesen**
- **Projekt (p.*):** id, name, nr, kunde, ansprechpartner, strasse, plz, ort, telefon, emailKunde(=email_kunde), status, fortschritt, start, ende, gewerk
- **Doc (d.*):** id, project_id/pid, name, file_name, category, created_at, file_data, file_path

### DB-Spalten aus den Writern (defects-POST Z.4213/10290): canonical
`id, project_id, title, description, status, prio, created_by, images, melder, kunde_status, ort, zugewiesen, frist, ebene, gewerk`
→ Reader-Mapper `_mapDefect` (Z.1754) liest `title||name`, `description||beschreibung`, `images||fotos`, `zugewiesen||worker`, `frist||deadline`. **Kanonisch = title/description/images/zugewiesen/frist.**

### 🔒 AUSSCHLUSSLISTE — interne Felder, die NICHT zum Kunden dürfen (RPC gibt sie NICHT zurück)
- **defects:** `zugewiesen` (Techniker), `frist`/`deadline`, `review_note`, `status` (interner Status — Kunde sieht nur `kunde_status`), `prio`, `ebene`, `gewerk`, `created_by`.
  - ⚠️ HINWEIS: `reviewNote` + `zugewiesen` werden HEUTE im Render angezeigt (Z.~4361 — der dokumentierte P3-Leak). Nach RPC werden sie leer → **gewollte Verbesserung** (interne Infos nicht mehr an Kunden). Render muss deren Abwesenheit graceful tolerieren (Phase 3 prüfen: conditional `m.reviewNote && ...`).
- **projects:** `betrag`/Vertragsbetrag, `kunden_nr`, `created_by`, interne Notizen, `tags`, sonstige nicht oben gelistete Spalten. (Portal rendert KEIN betrag — bestätigt.)

### RPC-Whitelist (explizit, kein SELECT *) — ⚠️ Spaltennamen aus Writer/Mapper INFERRED, nicht gegen Live-Schema verifizierbar (CC hat keinen DB-Zugriff). Der Applier (Chat-Claude) MUSS Block 0 (information_schema) laufen lassen und ggf. anpassen (z.B. start vs start_date, ende vs end_date, nr-Spaltenname).
- **project:** `id, name, nr, kunde, ansprechpartner, strasse, plz, ort, telefon, email_kunde, status, fortschritt, start, ende, gewerk, portal_code`
- **documents:** `id, project_id, name, file_name, category, created_at, file_data, file_path`  (WHERE kunde_freigabe = 1)
- **defects:** `id, project_id, title, description, melder, kunde_status, ort, images, created_at`  (WHERE melder = 'Kunde')

## PHASE 2 — RPC (Datei sql/portal_rpc_v3.9.156.sql, NICHT appliziert)
`portal_fetch(p_code text) RETURNS json`, `SECURITY DEFINER`, `SET search_path=public,pg_temp`.
Input-Härtung: trim + leere/zu-kurze Codes → leeres json (kein Fehler, keine Enumeration). Gibt
`{project, documents, defects}` mit obiger Whitelist; Code-Match `portal_code = p_code AND portal_code <> ''`.
`REVOKE ALL FROM public; GRANT EXECUTE TO anon, authenticated`. Rollback = DROP FUNCTION.

## PHASE 3 — Frontend (index.html, v3.9.156)
- Helper `_portalRpc(code)` → POST `/rest/v1/rpc/portal_fetch` `{p_code}` (anon-Key).
- **tryPortal:** RPC zuerst; liefert sie ein Projekt → onPortal(project, +_portalDocs/_portalDefects/_viaRpc).
  **FALLBACK** (RPC noch nicht appliziert / Fehler): exakt der alte `_sbGet("projects",...)`+Match-Pfad → **Zero-Downtime**, da GitHub Pages bei Push sofort live geht, die RPC aber erst später appliziert wird.
- **KundenPortal-Load:** wenn `p._viaRpc` → `p._portalDefects.map(_mapDefect)` + Doc-Map aus `p._portalDocs`; sonst alte Direktreads. plans/checklists IMMER direkt (out of scope, p.id kommt aus RPC).
- Mapper-getrieben (keine neuen Spalten-Annahmen im Frontend) → robust gegen exakte RPC-Shape.
- Triade (node --check, Bracket-Baseline, pytest) + Version-Bump v3.9.156 + sw.js.

## PHASE 4 — Apply-Reihenfolge (docs/handoff/CHAT-CLAUDE-PORTAL-RPC-APPLY.md)
**KRITISCH:** (1) RPC-Migration applizieren, (2) Frontend live + Portal über RPC testen, (3) ERST dann
`DROP POLICY projects_anon_select`, `DROP POLICY project_documents_anon_select` (+ defects-anon prüfen).
Vorher droppen = Portal kaputt (bis RPC+Frontend live). Fallback im Frontend deckt das Fenster ab.
