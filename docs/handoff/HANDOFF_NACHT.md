# HANDOFF NACHT — EPKolar-App Session 2026-06-08

**Session:** 2026-06-08, sehr lange Session (Contextlimit erreicht bei 98%). **Version-Range: v3.9.156 → v3.9.182.**
**main HEAD `eb74968` = v3.9.182 live**, 726 pytest grün, Working-Tree clean, Bracket `() -1` (Baseline).
Repo: `T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app`. Supabase `jiggujpruejkaomgxarp`.

## ORG-GUARD / Final-Verify (read-only, 2026-06-08, alle PASS)
| Check | Soll | Ist |
|---|---|---|
| `portal_fetch` prosecdef | true | **true** ✓ |
| anon-Policies `projects` | 0 | **0** ✓ |
| anon-Policies `project_documents` | 0 | **0** ✓ |
| anon-Policies `storage.objects` | 0 | **0** ✓ |
| comments-Spalte tickets | 1 | **1** ✓ (heute angelegt) |
| vignette-Spalten fahrzeuge | 2 | **2** ✓ (heute angelegt) |
| Bracket index.html | () -1 | **() -1** ✓ |
| APP_VERSION | — | **3.9.182** |

## AUSGEFÜHRTE LIVE-SQL (Supabase MCP, Sebastian-freigegeben)
- **apply_migration `tickets_add_comments_column`**: `ALTER TABLE tickets ADD COLUMN IF NOT EXISTS comments text` (für Ticket-Journal/Kommentare, AskUserQuestion-Freigabe).
- **apply_migration `fahrzeuge_add_vignette`**: `vignette_typ text` + `vignette_bis text` (für Vignette-Feature, AskUserQuestion-Freigabe).
- **DB-Cleanup (DELETE per exakter ID)**: 4 Test/Orphan-Tickets + 4 Test/Orphan-Defects + 3 Orphan-Checklisten + 1 Orphan-Plan + 1 Orphan-Doc gelöscht. DB sauber: 1 Ticket (Aufzugsanschluss), 0 Defects, echte Projekte intakt.
- (Hinweis: breites `DELETE ... ILIKE '%test%'` wurde vom Auto-Mode-Klassifizierer geblockt → exakte IDs genutzt.)

## FRONTEND-COMMITS (alle pytest-grün-gegated + gepusht)
| Version | Hash | Inhalt |
|---|---|---|
| 3.9.182 | `eb74968` | Bug-Hunt Projekte+Pläne: Ticket↔Defect-Mirror-Sync (update/delete), PNG-Export-Pin-Nr, Projekt-Edit-Merge, ProjectShell-key, x/y im Ticket-PUT |
| 3.9.181 | `095337d` | **KRITISCH** plans-PUT-Fix (updated_at-Injection→PGRST204 → Geschoss/Freigabe/page_count persistierten nie) + Fotos im Pin-Popup |
| 3.9.180 | `03e1e05` | **KRITISCH** comments in die DB (Spalte + photos/comments-Parse-Fix) + QuickEditPin-Journal + Status-Auto-Log |
| 3.9.179 | `4e900d3` | Fotos im Create-Formular |
| 3.9.178 | `2c1bcd6` | Pin-Nummer Liste = Pin (kanonisch) |
| 3.9.177 | `8feb6a5` | Plan-Geschosse/Ebenen (frei + Presets + Sortierung, plans.category) |
| 3.9.175-176 | `604a414`/`5ceae93` | Back-Navigation-Fix (useBackLayer, in-Tab-Details) |
| 3.9.173 | `ee74290` | **KRITISCH** Tickets "verschwanden" (Lade-Mapping planId) + Viewer-Layout |
| 3.9.170-172 | `82d3afb`/`2ec888e`/`5bbbcb0` | Viewer-Design-Upgrade (EP-grüne Pins, Toolbar, CTA) |
| 3.9.162-168 | `09f8f1c`…`76a17a5` | PlanRadar-Viewer (Banner, immersiv, Direkt-Flow, Mobile-Sheet) |
| 3.9.158-161 | `327b336`…`19a0394` | Overnight Welle 1-2 (KW-Key, 403-Wedge, PhotoQ, OFFA-Dedupe) |

## OFFEN — Empfehlung nächste Session (User: "fix alle Bugs + Vignette")
**File-only-Doku:** `docs/handoff/HANDOFF-2026-06-08-NEW-CC.md` (detaillierte TODOs + Code-Stellen) + Findings-Docs WAVE4/5/6 + SECURITY-ADVISOR-BACKLOG.
1. **VIGNETTE-Frontend** (DB-Spalten schon da): FahrzeugView-Form (Typ-Select + gültig-bis) + Detail-Anzeige + Ablauf-Warnung + PUT/POST/Load. Stellen: ~17498 (nf), 17884/18046 (Form), `_mapFahrzeug`.
2. **Restliche Bug-Hunt-Funde (contained):** Projekte#2 deleteP-Lösch-Kaskade (9222), Projekte#3 Portal-Code-Uniqueness (9274), Projekte#4 Double-Submit-Guard, Pläne#6 page-Clamp (10900).
3. **Pläne#4 (größer):** Layer-Definitionen nicht persistiert → DB-Design-Entscheidung mit Sebastian.
4. **Pin-Drag** halb fertig (x/y im PUT da, Drag-Handler fehlt).
5. **Sebastian-Backlog (RLS/sensibel, NICHT blind):** is_staff-Rollen + notifications-RLS-Denials, Login Cold-Boot/Cross-User-syncQueue, 86 Advisor-Lints, `authenticated_write_projects:ALL` (30 always-true-Policies).

## GOTCHAS
- DB-DDL/DELETE = AskUserQuestion-Freigabe + exakte IDs (kein breites Pattern). plans hat KEINE updated_at (Blacklist 2158). Playwright React-onBlur = `focusout`-Event. MCP-Browser vor langen Flows killen. UNC-pytest zäh (~3-5 min) + git-index.lock-Hänger.
