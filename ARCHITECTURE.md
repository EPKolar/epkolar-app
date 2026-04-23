# EP Kolar — Baumanagement & Zeiterfassung · ARCHITECTURE

**App:** `epkolar-app`
**Live-Version:** v3.8.33 (2026-04-23 spät)
**Repo:** `EPKolar/epkolar-app`
**Deploy:** GitHub Pages

---

## Stack

- **Single-File App** — `index.html` (~16 280 Zeilen) enthält UI + Logik + CSS
- **React 18** via unpkg.com CDN (`react.production.min.js`, `react-dom.production.min.js`)
- **JSX-transpile** via Sucrase pre-baked: `var _jsxFileName=""; function _optionalChain(ops){...}` im ersten inline-`<script>`
- **Service Worker** (`sw.js`) — Cache-First, `epkolar-v<version>` Cache-Name synced mit `APP_VERSION`
- **Supabase** (`https://jiggujpruejkaomgxarp.supabase.co`) — Pro-Tier (eigener Project-Ref)
- **IndexedDB** (`epkolar_offline`, DB_VER=7) — Offline-Cache + SyncQueue + PhotoQueue

Keine Build-Pipeline. Kein npm. Einziger Build-Artefakt ist `index.html` selbst.

## Datenfluss

```
  Browser (index.html)
     │
     ├── fetch(SB_REST+"/...")         →  Supabase PostgREST (authed, RLS-gated)
     ├── fetch(_SB_AUTH+"/...")        →  Supabase GoTrue (login/refresh/signup)
     ├── fetch(SB_REST+"/rpc/...")     →  Postgres Stored Procedures
     ├── ODB.* (IndexedDB)             →  Offline-Cache (13 Stores)
     └── SW fetch-handler              →  Cache-First, Network-Fallback
```

Alle Writes gehen durch `_authRetry(()=>fetch(...))` (siehe `sql/_authretry_gaps.md`).
Alle Reads durch `_sbGet`/`_sbGetOrder`/`_sbGetUsersSafe` Wrapper.

## Auth-Schicht

- **Token-Quelle:** `_authToken` global, via Login `grant_type=password` bekommen
- **Refresh:** `_authRetry` fängt 401 → `grant_type=refresh_token` → retry
- **Silent Re-Auth** (B-021): `_silentReAuth(user,pw)` versucht im Hintergrund neu einzuloggen
- **Helpers:**
  - `_sbH()` → `{apikey, Authorization: Bearer ...}`
  - `_sbWH("Prefer:...")` → write-Header mit Content-Type+Prefer
  - `_sbRH()` → read-Header, stricter
- **bcrypt:** zusätzlicher lokaler Hash in `public.users.password_hash` (dcodeIO/bcrypt.js). Login versucht zuerst GoTrue, fällt auf bcrypt zurück.
- **Offline-PW:** `_OFFPW` (PBKDF2-SHA256, 100 000 Iter, 16-Byte Salt) in IDB — v3.8.33 Iter-19c ersetzt das alte `btoa(user:pw)`.

## Offline-Strategie

- **ODB** (IndexedDB-Wrapper) kapselt `get/set/del/getAll/clear/save/load`
- **13 User-Data-Stores** (`entries`, `forms`, `abs`, `absApprovals`, `files`, `planData`, `arbeitsscheine`, `werkzeuge`, `monteure`, `projects`, `monteurProjekte`, `fahrzeuge`, `notifications`, `stundenzettel`, `syncQueueFailed`) — beim Logout alle gecleart (Iter-11/17 Fix)
- **meta**-Store für `lastUser`, `offlinePwHash`, `lastSync`, uid-scoped `notifPrefs`
- **SyncQueue `SQ`** — alle Writes offline → queued → flushed bei Verbindung, mit Batching (1.5 s Debounce)
- **PhotoQueue `PhotoQ`** — Storage-Uploads separat queued, mit `_authRetry`-Wrap seit v3.8.15

## Externe Integrationen

| System | Zweck | Code-Einstieg |
|---|---|---|
| **Juprowa** | Arbeitsschein-Sync externe DB | RPC `juprowa_fetch_worksheets`, `juprowa_push_worksheet`, `juprowa_get_config`, `juprowa_update_passport` |
| **FinkZeit** | Stundenabrechnung-Druck | client-side PDF-Gen in `printFinkZeit()` |
| **OFFA** | XLSX-Export/Import | `exportOffa()` + `importOffa()` (PDF-Parser) |
| **DATANORM** | Artikel-Katalog-Import | `dnUploadSupp` Admin-Flow |
| **sync_supplier** | Edge-Function-Supplier-Sync | `sql/DEPLOY_sync_supplier_v3.md` (Source nicht im Repo) |

## Rollen & Permissions

Siehe `sql/CANDO_MATRIX.md` (44 Actions × 7 Rollen).

Kurz: `admin` kann alles, `projektleiter` kann viel, `buero` kann alles außer Field-Actions, `obermonteur`/`techniker`/`monteur` sind via `isField` über AS/Form/Zeit/Material berechtigt. `lagerleitung` (Alt-Feld `user.rolle`) ist eine Lager-Teilrolle mit EK-Preis + supplier_manage.

RLS: DB-seitig via `current_monteur_id()`, `current_user_role()`, `current_user_pk()`, `is_staff()` Helpers (siehe `_archiv/sql/B006b_HEILUNGS_SQL.sql`).

## Datei-Layout im Repo

```
epkolar-app/
├── index.html                    # App (React + CSS + Logik)
├── sw.js                         # Service Worker
├── README.md                     # Repo-Einstieg
├── ARCHITECTURE.md               # dieses File
├── RUNBOOK.md                    # Ops-Runbook
├── HANDOFF_SESSION_2026-04-23.md # Session-Log
├── HANDOFF_v3.8.20.md            # ältere Session-Logs
├── HANDOFF_v3.8.23.md
├── HANDOFF_v3.8.24.md
├── OVERNIGHT_STATUS_A/B/C/D.md   # Block-Status (Overnight 24.04)
├── preview/
│   ├── whatsapp_ui_v0.html       # WA UI Mock (nicht in App verlinkt)
│   └── WHATSAPP_UI_README.md
├── sql/
│   ├── README.md                 # Inhalts- + Deploy-Index
│   ├── ARCHITECTURE.md           # TODO: dieses File löst ggf. ab
│   ├── CANDO_MATRIX.md           # Permission-Matrix
│   ├── _authretry_gaps.md        # Fetch-Wrap-Audit
│   ├── SMOKE_TESTS_v3.8.33.md    # 17 Prüfungen
│   ├── WHATSAPP_SCHEMA_v3.8.sql  # Feature-12 Schema
│   ├── WHATSAPP_SEEDS_v3.8.sql   # Feature-12 Seeds
│   ├── WHATSAPP_P3_TYPECHECK.sql # FK-Type-Verify
│   ├── RLS_SNAPSHOT_v3.8.sql
│   ├── RLS_RECONCILE_v3.8.md
│   ├── DEPLOY_sync_supplier_v3.md
│   ├── DEPLOY_SQL_REVIEW_2026-04-23.md
│   ├── Testkonzept_EPKolar_v5_0.md
│   ├── SELFTEST_USAGE.md
│   ├── WHATSAPP_INTEGRATION_PLAN.md
│   ├── _check_brackets.js        # Node: Bracket-Balance-Check
│   ├── _check_syntax.js          # Node: <script>-Body syntax
│   ├── _check_version.js         # Node: APP_VERSION↔CACHE_NAME↔sw.js
│   └── sql-runner.mjs            # Node pg direct runner
├── tests/                        # Python static invariants (33 Tests)
│   ├── conftest.py
│   ├── requirements.txt
│   ├── README.md
│   └── test_*.py
├── _archiv/
│   ├── README.md
│   └── sql/
│       ├── README.md
│       └── <historical SQL + Docs>
└── .gitignore
```

## Code-Helper (Dev-Console)

Globale window-Helpers für Debugging, alle seit v3.7/v3.8 live:

- `window._selfTest({mode:'full'|'quick'|'security'})` — umfassender Smoke-Check
- `window._curUser()` — aktueller User-Objekt (v3.8.13)
- `window._b017check` — Admin-Exposure-Scanner
- `window._s8Suite` — Block-8 Signatur-Integration-Suite
- `window._rlsAudit` — RLS-Policy-Verifier
- `window._perfBench` — Performance-Benchmark-Set
- `window._mobileCheck` — iPhone-Simulation-Report
- `window._a11yCheck` — Accessibility-Scan
- `window._syncDiag` — Sync-Queue-Diagnose
- `window._thunderTest` (dev-gated) — Load-Test
- `window._forceExpireToken`/`_restoreToken` (dev-gated) — Auth-Simulation

Dokumentiert in `sql/SELFTEST_USAGE.md`.

## TODOs / Unklarheiten

- **sync_supplier Edge-Function-Source** ist nicht im Repo, nur der Deploy-Runbook. Siehe `sql/DEPLOY_sync_supplier_v3.md`. Source liegt laut HANDOFF im Supabase-Dashboard.
- **B_12_ORPHANS Ghost-Rows** gefixt (23.04 Migration). Follow-up-Regression-Check siehe `sql/B_12_ORPHANS_ANALYSIS.md`.
- **Feature-12 WhatsApp**: Schema + Seeds ready, UI-Preview in `preview/`, Integration in index.html pending (2-3h eigene Session).
- **_mapBody TEXT_JSON_FIELDS-Whitelist** ist L1312 — warum diese 6 Felder (`perms_override`, `tank_log`, `km_log`, `tags`, `config`, `order_items`) und nicht andere? TODO klären.

## Nicht abgedeckt

Dieses File dokumentiert nur verifizierbare Struktur. Folgendes bleibt offen:
- Meta-API-Integration (WhatsApp Phase 2)
- PAT-Rotation-Policy
- Offline-Conflict-Resolution-Strategy (was bei concurrent write?)
- Disaster-Recovery-Plan (Supabase-Backups?)
