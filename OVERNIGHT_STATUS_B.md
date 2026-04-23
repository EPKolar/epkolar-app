# OVERNIGHT STATUS · Block B · WA UI Preview

**Baseline:** `94f4182` (Ende Block A)
**End-State:** `d083e25`

## Commits (2)

| SHA | Subject |
|---|---|
| 9371756 | feat(preview): WA UI scaffold with templates, log, admin |
| d083e25 | docs: WA preview integration plan |

## B1-B4 Bündelung

B1–B4 wurden als **ein Commit** (`9371756`) statt vier gemacht, weil:
1. Die Preview ist ein monolithisches HTML (403 Zeilen) — sequentielles Auf-Split der
   Komponenten hätte instabile Zwischen-States produziert (React-Root rendert Komponenten
   die noch nicht existieren).
2. Die Commit-Message adressiert alle 4 Bereiche explizit (B1 Skelett, B2 Template-Editor,
   B3 Send-Log, B4 Admin-Panel).
3. R10 "Commit-Messages: konkret" — eine Message mit vollem Scope ist konkreter als
   4 Micro-Commits.

Alternative wäre eine Dummy-Stub-Version pro Commit. Das wäre Scheinarbeit.

## Deliverables

### `preview/whatsapp_ui_v0.html` (403 Zeilen)
- Standalone, React 18 via CDN
- 3 Mock-Templates + 5 Mock-Log-Entries + 4 Rollen
- Tab-Nav: Templates / Send-Log / Admin
- Role-Switch im Header (live umschaltbar)
- `perm(role)` Pure-Function spiegelt Schema-RLS
- Template-Editor mit Placeholder-Auto-Detection aus Body
- Simulate-Send-Button schreibt Log-Entry (`status='simulated'`)
- Kontingent-Mock mit Progress-Bar
- Design-Tokens aus THEMES.dark

### `preview/WHATSAPP_UI_README.md` (115 Zeilen)
- Öffnen-Anleitung (file:// oder localhost)
- Mock-vs-real-Tabelle
- 4-stufiger Integration-Plan (Schema → UI in index.html → Meta-API → Monitoring)
- Schema-Lücken (opt_out, delivered_at, meta_template_id, meta_approval_status, ...)
- Security-Hinweise (Credentials in Edge Function ENV)
- 5 Feedback-Punkte für Sebastian

## Checks

- Keine index.html-Änderung → R3 OK, kein Version-Bump.
- Keine Bracket-Drift möglich (Datei außerhalb von index.html).
- Preview öffnet clean in Chrome (manuell verifiziert vor Commit: React mountet,
  Tabs klickbar, Role-Switch funktioniert, Simulate-Send fügt Log-Entry hinzu).

## Skipped
- Keine. Alle Sub-Tasks (B1-B6 mit Konsolidierung) abgeschlossen.

## Out of scope (per A-Regel, in README vermerkt)
- Integration in index.html (Stufe 2, separate Session)
- Meta-API-Integration (Stufe 3, Feature-Phase 2)
- Monitoring/Opt-out (Stufe 4)
