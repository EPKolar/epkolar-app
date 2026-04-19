# HANDOFF NACHT v3.8.19 — 10h-Plan-Abarbeitung

**Start**: 2026-04-19 (Abend)
**Start-HEAD**: `e6c9498` (v3.8.18)
**Plan-Quelle**: `CC_COMMAND_10h_v3.8.19_PARTIAL.md` (Paste-Chunks, Code-Blocks
durch Paste-Mechanismus truncated — CC arbeitet prose-basiert + Baseline-Kontext)
**Philosophie**: "Nicht übertreiben und ehrlich bleiben."
**Budget**: 8-10h autonom

---

## Block-Status

| Block | Status | Commit | Notiz |
|---|---|---|---|
| 0 Pre-Flight | ✅ | v3.8.19-wip pre-flight | Baseline clean, Plan gespeichert, HANDOFF init |
| A Baseline-Fixes | ✅ | v3.8.19-wip BASELINE_FIX_v3.8 | 4 Fixes: users.email UNIQUE, arbeitsscheine.juprowa_id UNIQUE, 3 CHECK-Constraints (scheinstatus/prioritaet/role), 3 NOT NULL (photos.project_id, time_entries.worker_id, time_entries.project_id). **Sebastian muss BASELINE_FIX_v3.8.sql manuell im Supabase SQL-Editor ausführen**, danach VERIFY-Query (8 TRUE erwartet). |
| B 12 Orphan-AS | ✅ | v3.8.19-wip 12-orphan-arbeitsscheine analysis | sql/B_12_ORPHANS_ANALYSIS.md mit Details-Query + Kategorisierungs-Matrix (4 Kategorien: EMPTY_STRING / WORKER_ID_PATTERN / JUPROWA_CODE / UNKNOWN) + 4 Staging-SQLs. **Sebastian führt Query aus, entscheidet Aktion per Row**, resolved-SQL dann in eigenem Commit. |
| C Chef-Seite v2 | ✅ | v3.8.19-wip feat(chef): v2 | **C.2 Sorgenkind-Widget** (5 Indikatoren: AS ohne Monteur / AS ohne Termin / Juprowa Push-Stau / Projekte ohne Aktivität 14d / Monatsabrechnung offen) eingefügt zwischen Projekt-Ampeln und Überfällig-Liste. **C.3 Trend-Pfeile** (↑/↓ + Delta vs Vorwoche) an 3 KPIs: Offene AS / Heutige AS / Überfällig — Offene+Überfällig invertiert (↑=rot). Aktive Projekte + Monteure heute ohne Trend. **C.4 Nächste-Woche-Preview** am Ende: Geplante AS / Abwesend (Namen) / Fahrzeuge fällig 14d. Async: finkzeit + absences via useEffect. `abs` prop zu ChefDashboard-Aufrufer hinzugefügt. |
| D RLS-Reconcile | ✅ | v3.8.19-wip Block10 RLS-reconcile | sql/RLS_RECONCILE_v3.8.md (bestehendes Template überschrieben). 45-Tabellen-Matrix mit Role-Pattern + Verdict. 44× ✅OK, 1× ⚠️SPECIAL (photos, B-021 Business-Entscheidung), 0× 🔴REVIEW. Matrix-Query für Sebastian dokumentiert (optional, 0 Gaps erwartet). |
| E Mobile-UX | ✅ | v3.8.19-wip Block13 mobile touch-targets | Global CSS `@media (pointer: coarse), (max-width: 768px)` in index.html `<style>` appended: 44px min-height/min-width auf button/role=button/clickable/a.btn/input[submit|button|checkbox|radio]. Icon-only-Heuristik via `[style*="fontSize:10/11/12"]` + `padding:10px`. Label-Wrapping für checkbox/radio mit `min-height:44px`. Top-5-Fixes durch pointer:coarse abgedeckt (keine gezielten Einzeledits nötig). **Sebastian**: iPhone-12-Viewport in DevTools → `window._selfTest()` — tooSmallTouch sollte <5. Screenshots before/after bei Bedarf in docs/. |
| F | ⏳ | | Plan-Chunk ausstehend |
| G | ⏳ | | Plan-Chunk ausstehend |
| H | ⏳ | | Plan-Chunk ausstehend |
| I | ⏳ | | Plan-Chunk ausstehend |
| Final v3.8.19-Bump | ⏳ | | |

---

## Pre-Flight-Baseline (Block 0)

- `git status`: clean
- HEAD: `e6c9498` v3.8.18
- `node --check index.html`: green
- `node --check sw.js`: green
- Brackets: `() -2 {} 0 [] 0` (baseline unverändert)
- APP_VERSION: `3.8.18-supabase`
- CACHE_NAME: `epkolar-v3.8.18`
- DB_VER: `7`

---

## Paste-Chunks-Protokoll

Der Plan `CC_COMMAND_10h_v3.8.19_COMPLETE.md` wurde via Prompt-Paste übergeben,
Claude-Code-Paste-Mechanismus hat aber alle Triple-Backtick-Code-Blocks
truncated. Bisher erhalten:

1. Chunk 1: Header + Philosophie + DB-Baseline-Befunde + Priorisierung + Kernregeln + Block 0 (powershell truncated)
2. Chunk 2: HANDOFF-Init + Block A-Struktur (2× sql truncated)
3. Chunk 3: Block A.3 Aktion + Block B.1 Details-Query (sql truncated)
4. Chunk 4: Block B.2, B.3 + Block C Header + C.2 Sorgenkind
5. Chunk 5: Block C.3 Trend-Pfeile Detail + sql-Beispiel truncated
6. Chunk 6: Block C.4 Nächste-Woche-Preview

CC-Strategie:
- SQL aus Baseline-Kontext + Prose-Anweisungen rekonstruieren
- In Commit + HANDOFF explizit als "CC-reconstructed" markieren
- Sebastian-Review vor DB-Execute (Block A, B) kritisch — kein Auto-Execute

---

## Ehrlichkeits-Bilanz (wird am Ende gefüllt)

### Wirklich gemacht

### NICHT gemacht (weil nicht plan-konform rekonstruierbar / Zeit ausgelaufen / unsicher)

### Zeit Ist vs Plan

### Follow-Ups für Sebastian

### Follow-Ups für CC v3.8.20
