# OVERNIGHT STATUS · Block C · SQL-Housekeeping + Doku

**Baseline:** `0a3c8d4` (Ende Block B)
**End-State:** `1d1df4a`

## Commits (4)

| SHA | Subject |
|---|---|
| 6c6cba3 | docs: archive SQL readme + sql active readme expansion |
| f773883 | docs: ARCHITECTURE.md |
| 7327d2b | docs: RUNBOOK.md |
| 1d1df4a | docs: ROADMAP updated |

## C1 + C2 · READMEs (1 Commit)

Beide READMEs existierten bereits. Aktualisiert statt neu geschrieben:

- `_archiv/sql/README.md` +10 Zeilen: "Nicht löschen"-Warnung prominent, Wiederherstellungs-Kommando dokumentiert.
- `sql/README.md` +28 Zeilen: neue Audit-Docs verlinkt (CANDO_MATRIX, _authretry_gaps, SMOKE_TESTS_v3.8.33), Deploy-Reihenfolge Full-Rebuild (5 Stufen), Abhängigkeiten (SEEDS→SCHEMA, Policies→Helpers), Idempotenz-Hinweise pro File.

## C3 · ARCHITECTURE.md

Neu am Repo-Root. 155 Zeilen. Sektionen:
- Stack (Single-File, React 18 CDN, Sucrase, sw.js, Supabase Pro, IDB v7)
- Datenfluss (fetch-Paths, ODB, SW)
- Auth-Schicht (_authToken, _authRetry, Silent Re-Auth, bcrypt, _OFFPW)
- Offline-Strategie (13 user-data-Stores + meta-Store, SQ+PhotoQ)
- Externe Integrationen (Juprowa, FinkZeit, OFFA, DATANORM, sync_supplier)
- Rollen & Permissions (Verweis auf CANDO_MATRIX)
- Datei-Layout (kompletter Tree mit Zweck pro File)
- 11 window._*-Code-Helper (mit dev-gate-Notizen)
- TODOs (sync_supplier-src, _mapBody-Whitelist-Frage, Orphans)
- bewusst out of scope (Meta-API, DR-Plan, Conflict-Resolution)

Alles aus Code verifizierbar (grep-/read-backed). Keine Spekulation. Bei Unklarheit TODO markiert.

## C4 · RUNBOOK.md

Neu am Repo-Root. 229 Zeilen. 10 Runbooks:
1. Version-Bump (exakt 2 Stellen, node-check-Triade)
2. Deploy (GH Pages auto, Cache-Bust via CACHE_NAME)
3. Häufige Fehler & Fixes (6 Szenarien mit Repro+Fix)
4. SQL-Deploy (IF NOT EXISTS + IF EXISTS Guards)
5. Edge-Function-Deploy (sync_supplier Kurzform)
6. Chrome-MCP-Fallback (wenn CC nicht verfügbar)
7. Smoke-Tests nach Deploy (5-Punkt-Minimal-Smoke)
8. Disaster-Recovery (Supabase Backups, git reset --hard)
9. Rollback (revert vs reset, Version-Bump auch bei Rollback!)
10. Secrets-Handling (4 Klassen: anon/DB_URL/Edge-ENV/PAT)

## C5 · ROADMAP.md

Neu am Repo-Root. 125 Zeilen.
- ✅ DONE: 11 Features + 5 Bug-Closeouts + Bug-Hunt-Loop + Silent-Catch + PBKDF2
- 🟡 PENDING: Feature 12 Sub-Schritte, PHOTOS_RLS, RLS-Reconcile, Index-Deploy,
  sync_supplier-src, B-020 5-User-Smoke, PAT-Rotation
- 🔵 BACKLOG: P1 Security (2 Auth-Retry-Gaps, Opt-out, Retention), P2 UX (5 Items),
  P3 Code-Quality (4 Items), P4 Architecture (4 long-term)
- 🔴 OPEN INCIDENTS: sync_supplier-src, PAT-Blocker, _mapBody-Whitelist, ARCHITECTURE-Duplikat
- Version-Chronik letzte 10 Tags
- 5 konkrete Entscheidungs-Punkte für Sebastian

## Checks

- Keine index.html-Änderung → R3 OK, kein Version-Bump.
- Alle Docs sind pure Markdown, kein Risiko für Bracket-Drift.
- Test-Suite weiterhin grün (33/33 — Docs-Tests aktualisieren sich durch Dir-Struktur).

## Skipped
- Keine. C1-C5 komplett.

## Tangential discovered (nicht gefixt)

- Der alte `sql/ARCHITECTURE.md` existiert (sh. sql/README.md erwähnung). Der neue
  Repo-Root `ARCHITECTURE.md` überlappt ggf. — TODO in ROADMAP gelistet: alte Version
  prüfen/löschen in separater Session. R6 verbietet spekulative Merges in dieser
  Overnight-Session.
