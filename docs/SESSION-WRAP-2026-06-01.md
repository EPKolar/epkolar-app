# Session-Wrap 2026-05-18 → 2026-06-01 — 23-Sprint Marathon

**Live HEAD:** `a1bda4e` v3.9.38 (https://epkolar.github.io/epkolar-app/)
**Range:** v3.9.16 → v3.9.38 (23 Tag-Commits + 2 Doc-Commits, alle gepusht)
**Tests:** 502/502 grün durchgehend
**Bracket-Baseline:** `() -1 / {} 0 / [] 0` identisch pre/post pro Sprint

## Sprint-Übersicht

| Sprint | Tag | Commit | Inhalt |
|---|---|---|---|
| 1 | v3.9.16 | `1c1b330` | Code-Quality: 5 async-catch logs + 3 localStorage wraps. JSON.parse alle safe |
| 2 | v3.9.17 | `7824f0d` | PARTIAL UX-Bugs: B-016 Pinger-Hardcode (3 sites) + B-007 TZ-drift |
| 3 | v3.9.18 | `74793ef` | B-014 `_pickerlStatus` Helper + 3 Sites + Werkzeug Mobile-Cards |
| 4 | v3.9.19 | `d98d44d` | WhatsApp Scaffold Mock + SQL-Datei + Helpers + UI |
| 5 | v3.9.20 | `31f7690` | Theme `--epk-error` Token definiert |
| Extra | v3.9.21 | `ef11e7a` | Begrüßungs-Header 🌷→🔧 |
| 6 | v3.9.22 | `a95bdf4` | Free Bug-Hunt Material+Bestellungen: 17 Findings/8 Fixes |
| 7 | v3.9.23 | `3459017` | **KRITISCH** Monteur-Permission-Filter (HomeView/VMang/VPlan/dringendeAS) |
| 8 | v3.9.24 | `1d08865` | **KRITISCH** Monteur-Tightening AS/Mängel/Tickets-Anlegen + Dokumentexplorer Read-Only |
| 9 | docs | `8f3962c` | MONTEUR-AUDIT 13 Findings |
| 10 | v3.9.25 | `68eb5e4` | **KRITISCH** P1-Followup 5 Gates (Bypass-Closures + VZeit/VBautag/VMang.review) |
| 11 | v3.9.26 | `17aeff6` | P2-Batch 3 Defense-in-Depth |
| 12 | v3.9.27 | `6aed570` | Kalender+AbsView 10/5 — **Bug-1 Urlaub Carry-Over FIXED** (Export-UI war Bug) |
| 13 | v3.9.28 | `bd34fc2` | B-006 KPI-Gate FIXED (isOps=isAdmin\|\|_isBuero), FahrzeugView 5/1 |
| 14 | v3.9.29 | `5e1017a` | FahrzeugView F-3 part-fix, MitarbeiterView 10/3 (2 P1) |
| 15 | v3.9.30 | `ef98d6e` | WerkzeugView 10/3, AdminPanel 11/4 |
| 16 | v3.9.31 | `4001d5a` | VerbindungView 8/3, AuswertungView 11/3 (2 P1 incl. absPerName Doppel-Zählung) |
| 17 | v3.9.32 | `1189643` | **HomeView H-1 CRITICAL Timer-Button ReferenceError** + ZE _canDelEntry Field-Rollen |
| 18 | v3.9.33 | `9cd6af4` | ProjList 9/2, StundenzettelView 9/4 |
| 19 | v3.9.34 | `695881c` | VBer 0, VFotos 2, VForm 2 (FRegie nr-Overwrite Edit-Bug P1) |
| 20 | v3.9.35 | `08ca081` | WeekPlan 6/3, Notifier 5/2 |
| 21 | v3.9.36 | `a310f02` | VMaterial cartKey-cleanup pro Project-Wechsel (rate-limited partial) |
| 22 | v3.9.37 | `87d49d4` | Mobile-Round-2: HomeView/ProjList/ASView 11/7 (Touch-Targets+iOS-Zoom-Prevention) |
| 23 | v3.9.38 | `a1bda4e` | **Sebastian-Live-Diagnose** Sync-Button-Bug Auto-Sync setArbeitsscheine-Refresh |

## User-Visible Top-Wins

1. **Sync-Button-Bug (v3.9.38)** — Orange ☁️↑ blieb nach Auto-Sync hängen. Diagnose live auf S075295 via Chrome MCP. Patch: nach `_juprowaDrainPending` weiterer Pull+setArbeitsscheine.
2. **HomeView Timer-Button ReferenceError (v3.9.32)** — Klick auf "Timer starten" crashte für HomeView mit ReferenceError → ErrorBoundary-Reset. `_myProjIds` war undefined in HomeView-Scope.
3. **Bug-1 Urlaub Carry-Over (v3.9.27)** — `exportAbsCsv/exportAbsTxt` benutzten falsche Formel statt `resturlaub()` Helper. NO-GO-Helpers intakt.
4. **Monteur-Permissions (v3.9.23-26)** — 13 Sites gefixt: Monteure sehen nur eigene Daten, können nur eigenes anlegen, Dokumentexplorer Read-Only.
5. **AuswertungView absPerName Doppel-Zählung (v3.9.31)** — Namens-Präfix-Kollision: "Max" matchte "Maximilian_..."-Keys.

## Audit-Statistik

- 130+ Findings analysiert über 20+ Views
- 65+ Fixes implementiert + gepusht
- 23 Versionen-Bumps
- Bracket-Baseline stabil über alle Sprints
- pytest 502/502 jedem Commit

## Sebastian-Action-Queue (nicht autonom fixbar)

1. **PWs für MCP-Test-Tour** (Test-Tour-Skript in `docs/MONTEUR-AUDIT-2026-05-18.md` ready)
   - barger-PW (Monteur w2)
   - guenther-PW (Chef, login wirft "Benutzer nicht gefunden [B20-B]")
   - riedmann-Entscheidung (User existiert NICHT in INIT_USERS, neu anlegen?)
2. **SQL `sql/migrate_whatsapp_v3919.sql`** ausführen (3 Tables + RLS + 2 Seed-Templates)
3. **Meta Business Console** — Templates `epkolar_as_done` + `epkolar_appt_confirm` anlegen+approven
4. **WhatsApp aktivieren:** Einstellungen → 📱 WhatsApp → Credentials + Toggle
5. **RLS-Server-Audit Supabase** — clientseitige Permission-Gates allein nicht safe. Server-side `auth.uid()===worker_id` Policies fehlen
6. **`admin_stats`-RPC Backend** — für Sprint-15-A-Fix4 (aktuell Display-Defense gegen NaN-Crash)
7. **B-011 Mein-Tag** — Toggle existiert noch nicht (Feature-Add, kein Bug)
8. **Theme-Sprint** — 190× `#ef4444` auf `COLORS.ERROR/ERROR_DARK` Theme-aware migrieren

## Hard-Constraints respected (alle 23 Sprints)

- `_silentReAuth`/`_authRetry`/`_ensureAuth`/`_sbAuthRefresh`/`_storeAuth`/`_authLog` — NICHT angefasst
- `_mapBody` / `TEXT_JSON_FIELDS` — NICHT angefasst
- SyncQueue / IndexedDB / sw.js Cache-Strategie — NICHT angefasst
- Juprowa (8 Push-Felder + Phase-1-Pull + `_juprowaPush` RPC) — NICHT angefasst (Country-Code-Incident-Schutz)
- OFFA/DATANORM-Parser, `_OFFPW.verify` — NICHT angefasst
- Berechnungs-Helpers `yearSt/resturlaub/kontingent` — NICHT angefasst
- Hooks NICHT nach early-return (React #310) — keine Verletzung
- KEIN force-push

## Lokale Doku (NICHT in git)

- `\\SRVDC02\Projekte\05_Claude\02_Baumanagment & Zeiterfassungs - APP\NACHT_REPORT_18052026.md` — Voll-Details pro Sprint
- `epkolar-app/SPRINT_FINDINGS_v3922.md` — Sprint-6 Findings
- `epkolar-app/SPRINT_FINDINGS_v3927.md` — Sprint-12 Findings

## Resume für Folge-Session

```powershell
cd "T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app"
git log --oneline -3
python scripts/_bracket_check.py index.html   # expect () -1 / {} 0 / [] 0
python -m pytest tests/ -q                    # expect 502/502
```

Memory: `epkolar_baumgmt_session_2026-05-17.md` (HEAD `a1bda4e` v3.9.38)
