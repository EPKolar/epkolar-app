# EPKolar · ROADMAP

Status der Features und Backlog. Keine Release-Dates — nur Prio + Zustand.

---

## ✅ DONE

| # | Feature | Verfügbar ab | Notiz |
|---|---|---|---|
| 1 | **Arbeitsscheine (AS)** | v2.x | CRUD, Status-Workflow, OFFA-Export, FinkZeit-Print |
| 2 | **Projekte** | v2.x | Projekt-Ampel, Material-Warenkorb |
| 3 | **Zeiterfassung** | v3.x | Eintrag + Timer + Monats-Report, 40h→38,5h in v3.6.1 |
| 4 | **Fahrzeuge + Fahrtenbuch** | v3.x | KM-Log + Kraftstoff, mobile-first |
| 5 | **Werkzeuge + Wartung** | v3.5 | Inventar, Termine |
| 6 | **Dokumente + Pläne** | v3.x | Upload-Queue, Folder-Struktur |
| 7 | **Mängel + Bautagebuch** | v3.5 | Foto-Capture, Position-Tagging |
| 8 | **Abwesenheit/Urlaub** | v3.6 | Kontingent, Approvals |
| 9 | **Material-Bestellung** | v3.6 | Katalog-Import (DATANORM), Gewerk-Filter (v3.8.26) |
| 10 | **Juprowa-Sync** | v3.7 | RPC fetch/push, Passport-Rotation |
| 11 | **Audit-Log UI** | v3.8.22 | 17 Action-Filter, Entity-Filter |
| — | **B-020 Login-Reliability** | v3.8.3 | ✅ CLOSED (9× verifiziert), monteur_id Konsistenz, RPC login_lookup |
| — | **B-006 + B-007 RLS** | v3.5.94 | ✅ CLOSED, 4 Helpers + 22 Policies live-verified |
| — | **B-017/B-021/B-022** | v3.5/3.8 | ✅ CLOSED, Window-Exposures / Silent-ReAuth / Stale-Closures |
| — | **Overnight-Bug-Hunt-Loop** | v3.8.1-3.8.18 | 18 Iter, 2 User-Stops, alle gefixt |
| — | **Silent-Catch-Observability** | v3.8.28-3.8.31 | 13 kritische Stellen → Console-Breadcrumbs |
| — | **Offline-PW-Hash PBKDF2** | v3.8.33 | M-4 Security-P2 closed, Legacy-Grace-Migration |

---

## 🟡 PENDING (Schema/Code ready, Deploy oder Integration ausstehend)

### Feature 12 · WhatsApp-Benachrichtigungen

- ✅ Schema `sql/WHATSAPP_SCHEMA_v3.8.sql` (inkl. 24.04-Audit-Fix: UNIQUE(name), PL-Read-Policy, P3-Diagnose)
- ✅ Seeds `sql/WHATSAPP_SEEDS_v3.8.sql` (4 Default-Templates)
- ✅ UI-Preview `preview/whatsapp_ui_v0.html` (Overnight Block B, 2026-04-24)
- ⏳ Deploy Schema + Seeds (Sebastian manuell im Supabase-SQL-Editor)
- ⏳ UI-Integration in `index.html` (nach Deploy, 2-3h eigene Session)
- ⏳ Meta-API-Phase-2 (Edge Function + Webhook + pg_cron) — separate Session

### Schema + SQL Ops

- ⏳ **PHOTOS_RLS deployen** (2 Files in `_archiv/sql/PHOTOS_RLS_*.sql`: AUDIT + FIX, Status-Quo seit 19.04 bestätigt laut `_archiv/sql/README.md` "B-021 Status Quo") — oder Migration-Variante aktivieren
- ⏳ **RLS-Reconcile v3.8** (`sql/RLS_RECONCILE_v3.8.md` + `sql/RLS_SNAPSHOT_v3.8.sql`) — Soll/Ist-Vergleich laufen lassen
- ⏳ **Index-Deploy** falls Perf-Bedarf (aktuell <130 ms → konservativ skippen)
- ⏳ **sync_supplier Edge-Function-Source** ins Repo (aktuell nur im Dashboard)

### B-020 Final-Closeout

- ⏳ **5-User-Smoke** (paschinger, barger, cracana, pinger, schmid) — Browser-Test-Run
- ⏳ PAT-Rotation (2× Platzhalter geschickt, echter Token fehlt)

---

## 🔵 BACKLOG (Priorisiert, kein Commit)

### P1 · Security / Reliability

- **M-4 Offline-PW bcrypt-Migration** — ✅ DONE v3.8.33 (PBKDF2)
- **L6366 juprowa_update_passport Auth-Retry** (P2, `sql/_authretry_gaps.md`)
- **L6365 juprowa_get_config Auth-Retry** (P2)
- **Opt-out für WhatsApp-Log** — wenn Phase 2 kommt
- **Log-Retention-Policy** (6 Monate DSGVO) — Daily-Delete-Job

### P2 · UX / Features

- **I1 canDo admin_panel vs isLager** (`sql/CANDO_MATRIX.md`) — klären ob PL Admin-Panel sehen soll
- **I5 isOwn-Mehrdeutig** (monteurId|name|id → UUID-only?)
- **Mobile-UX-Hit-List** aus `window._mobileCheck()` iPhone-Output
- **Auto-Save in AS-Editor** (aktuell manuell, Monteur-Frustration)
- **Kalender-View für AS** (Zeitleiste statt nur Liste)

### P3 · Code-Quality

- **I3 canDo isField entflechten** (OM/Tech/Mont ungranular)
- **L3954 bautagebuch-schema-check Auth-Retry** (P3)
- **L4031 workers-sync-probe Auth-Retry** (P3)
- **Bulk-supplier-articles changePassword-Fallback** für GoTrue-only Users (Teil-fixed v3.8.33a — Error-Message verbessert, volle GoTrue-Reauth ausstehend)
- **Dead-Code-Review** (Block D generiert `sql/DEAD_CODE_CANDIDATES.md`)

### P4 · Architecture / Long-term

- **Bundle-Step erwägen** — derzeit Single-File 16k Zeilen, Refactor in Modul-Struktur wäre Release v4.0
- **Offline-Conflict-Resolution** — was bei 2 User schreiben dasselbe AS offline?
- **Disaster-Recovery-Plan** dokumentieren
- **Test-Suite auf Live-Integration erweitern** (Playwright? tavern? — Architektur-Entscheidung)

---

## 🔴 OPEN INCIDENTS / Bekannte Lücken (kein offener Ticket, nur Merkposten)

- `sync_supplier/`-Source fehlt im Repo (nur Doku)
- PAT-Blocker seit 2026-04-18 (GitHub-Push via CC geht nicht ohne Token-Rotation; Sebastian pushed manuell)
- `_mapBody TEXT_JSON_FIELDS` Whitelist (L1312) ohne erklärte Herkunft
- ARCHITECTURE.md in Repo-Root vs `sql/ARCHITECTURE.md` — die alte Version im sql/ löschen oder refactoren (siehe ARCHITECTURE.md Notiz)

---

## Version-Chronik (letzte 10 Tags)

| Tag | Datum | Highlight |
|---|---|---|
| v3.8.33 | 2026-04-23 spät | changePassword + PBKDF2 + SMOKE_TESTS |
| v3.8.32 | 2026-04-23 Nacht | Session-Final Breadcrumbs + HANDOFF |
| v3.8.31 | 2026-04-23 Nacht | Kpi-Stagger Final-Sweep |
| v3.8.30 | 2026-04-23 Nacht | Silent-Catch Teil 2 + Kpi-Stagger |
| v3.8.29 | 2026-04-23 Nacht | App-Header Last-Sync-Indikator |
| v3.8.28 | 2026-04-23 Nacht | Motto + Kpi-Stagger-Infra + EP-Spinner |
| v3.8.27 | 2026-04-23 Nacht | Empty-State-Polish |
| v3.8.26 | 2026-04-23 Nacht | Gewerk-Profil + Material-Filter |
| v3.8.25 | 2026-04-23 Nacht | _juprowaSyncing try/finally + Emoji-Rotation |
| v3.8.24 | 2026-04-23 Nacht | sql-Archive-Pass (16 Files) |

Vor-v3.8.20 siehe Git-Log + `_archiv/sql/HANDOFF_*`.

---

## Entscheidungen die Sebastian treffen muss

1. **Feature-12 Go/No-Go**: Preview ansehen, UI-Integration beauftragen oder pausen.
2. **CODE_DEBT Priorisierung**: Nach Block-D-Lauf (`sql/CODE_DEBT.md`).
3. **I1 Admin-Panel-Zugang** für Projektleiter.
4. **PHOTOS_RLS**: Status-Quo bestätigen oder Migrations-Variante.
5. **PAT-Rotation**: irgendwann diese Woche bitte.
