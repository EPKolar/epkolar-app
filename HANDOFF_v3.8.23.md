# HANDOFF · v3.8.23 Instant-Push + Button-Cleanup · 2026-04-23 spät

**Start-HEAD**: `41e50ae` (v3.8.22)
**End-HEAD**: `6e56f88` (v3.8.23 full bump)
**Tag**: `v3.8.23` (lokal, push zusammen mit Handoff-Commit)
**Modus**: vollautonom via CC-Command Instant-Push + Button-Cleanup.

---

## Block-Status-Tabelle

| Block | Thema | Status | Commit | Notiz |
|---|---|---|---|---|
| 0 | Pre-Flight | ✅ DONE | — | HEAD clean, syntax/brackets grün |
| 1 | Instant-Push nach AS-Save | ✅ DONE | `936bdad` | Injection L5049 nach `_juprowaMarkEdited`, vor `_epkVibrate` |
| 2 | AS-Tab Juprowa-Sync + Push Buttons entfernt | ✅ DONE | `a9360a9` | L5370 Chain, 2 Buttons raus, Status-Span bleibt |
| 3 | Letzter-Sync-Indikator im App-Header | ⚠️ SKIPPED | — | Deferred v3.8.24 — siehe unten |
| 4 | v3.8.23 Version-Bump + Tag | ✅ DONE | `6e56f88` | APP_VERSION + CACHE_NAME sync (via `_check_version.js` verifiziert) |
| 5 | Handoff + Push | 🔵 IN PROGRESS | — | Dieser Commit + `git push origin main --tags` |

---

## Abweichungen / Beobachtungen

### Funktionsname: `saveAs` (nicht `saveAS`)

Command-File referenziert `saveAS` (L5034). Im Code heißt die Funktion `saveAs` (camelCase — L5034). Funktional ohne Auswirkung, Injection-Point war eindeutig.

### Startzustand-Diff

Command-File sagt Start-HEAD `41e50ae`. Tatsächlicher Start war `485bcc3` — dazwischen lagen Aufräumen-Commits (`7034ecf`, `e776e76`, `f4f688b`) + Deploy-SQL-Review (`485bcc3`). Keine Berührung von `index.html`/`sw.js`, daher Line-Numbers aus Command-File gültig.

### Block 3 SKIP-Begründung

`lastSync` state ist lokal im AS-Tab-Komponent (L4886), `_juprowaSyncing` ist module-scope global (L2228). App-Header-Anzeige bräuchte:
1. State-Lifting in App-Root ODER `window._onSyncComplete`-Callback-Registry
2. Callback-Trigger in `_juprowaSync` success-Path (L2390-Bereich)
3. Trigger in `_juprowaPushAll` success-Path (L2517–2530)
4. Header-Render-Location + 30s Auto-Tick useEffect

Das sind 4–5 Edit-Points im gleichen Scope wo die **OFFA-Sync-Parallel-Session** arbeitet. Konflikt-Risiko + Nice-to-have-Charakter → SKIP gemäß Command-Regel "LIEBER SKIPPEN als kaputte Hooks".

Der **existierende** `lastSync`-Indikator im AS-Tab-Header (Status-Span) bleibt sichtbar; User die auf anderen Tabs sind sehen den nicht, aber das war auch vorher schon so.

### Block 2 Button-Text Korrektur

Command-File sagte `⊕ Push (N)`. Tatsächlicher Button-Text war `☁️↑ Push (N)`. Beide entfernt.

---

## Offen — Sebastian

- [ ] **Push** noch offen (dieser Commit + Tag)
- [ ] **PAT rotieren** (remote-URL hat alten Token)
- [ ] **B-020 Login-Smoke** für 5 User (paschinger, barger, cracana, pinger, schmid)
- [ ] **Orphan-UPDATE-SQL** (11 Rows, siehe `sql/B_12_ORPHANS_ANALYSIS.md`)
- [ ] **Index-Deploy** (siehe `sql/INDEX_AUDIT_v3.7.sql` + Review-Hinweis zu CONCURRENTLY)
- [ ] **Photos-RLS Audit + Fix** (siehe `sql/PHOTOS_RLS_AUDIT.sql` → Entscheidungsmatrix)
- [ ] **BASELINE_FIX** nicht deployen — Repo-File hat buggy CHECK-Constraints, siehe `sql/DEPLOY_SQL_REVIEW_2026-04-23.md`. Separate Task für v3.8.24.
- [ ] **Smoke-Test** nach Deploy: Neuen AS anlegen / bearbeiten → Juprowa-Sync sollte innerhalb 10s passieren (nicht erst nach 5 Min)

## Offen — CC v3.8.24-Kandidaten

- **BASELINE_FIX_v3.8.sql CHECK-Constraints fixen** (scheinstatus/prioritaet/role Werte-Listen — siehe `sql/DEPLOY_SQL_REVIEW_2026-04-23.md`). Postmortem-Kontext: CHECKs wurden heute Abend live in DB gedroppt; Repo-File ist aber weiterhin buggy.
- **Block 3 nachholen**: Letzter-Sync-Indikator App-Header via Callback-Registry
- **`_juprowaSyncing`-Flag in try/finally wrappen** (Leak-Risiko wenn Sync hängt — eigener Task laut Command-File)
- **Feature 12 WhatsApp UI** (braucht Schema+Seeds-Deploy)

---

## Metrics

- Commits: **3 Code-Commits + 1 Handoff** = 4
- 3 von 4 Blocks durch (75%), 1 bewusst geskipped
- Syntax-Check + Bracket-Check + Version-Sync nach jedem Commit grün
- `index.html` Delta: 2 Insertions, 2 Deletions (Instant-Push-Snippet ersetzt kurz; Button-Entfernung netto 0)

---

## Post-Merge Smoke-Test (Sebastian)

1. App laden, harter Reload (Cache-Bust via neuer `CACHE_NAME`)
2. AS öffnen, irgendwas editieren, Speichern → Console-Tab: kein "doJuprowaPushAll"-Call, aber `_juprowaPushAll`-Activity direkt
3. 5 Sekunden warten, Supabase-Arbeitsscheine-Row-Check: `push_pending=false`, `juprowa_id` gesetzt (falls Juprowa-AS)
4. AS-Tab-Header visuell: keine "🔄 Juprowa Sync"/"☁️↑ Push"-Buttons mehr
5. Status-Span mit `⏱ lastSync` rechts sollte weiter tickern nach Sync
