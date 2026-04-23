# _authRetry Coverage Audit · 2026-04-24

**Scope:** Alle `fetch(SB_REST+...)` und `fetch(_SB_AUTH+...)` Calls in `index.html`.
**Baseline:** Stand Commit `85b6ab0` (v3.8.33 + _n-sweep).
**Methode:** `grep -nE 'fetch\([^)]*(SB_REST|_SB_AUTH)' index.html`.
**Ergebnis:** 21 SB_REST + 6 _SB_AUTH = 27 Sites. 13 `_authRetry`-wrapped, 14 nicht.

## Legende
- ✅ **wrapped** — via `_authRetry(()=>fetch(...))`
- 🟡 **intentional** — Bewusst ohne Retry (pre-auth, Auth-Endpoint, Debug)
- 🔴 **gap** — Legitim, aber fehlt; Action erwogen

## SB_REST Sites (21)

| Line | Status | Endpoint | Kommentar |
|-----:|:------:|----------|-----------|
|  372 | 🟡 | `GET /users?limit=1` | Boot-Debug-Log, einmaliger Smoke bei Init |
| 1434 | ✅ | `POST /<table>` | `_sbPost` generic write |
| 1439 | ✅ | `POST /<table>` merge-dup | `_sbPostUpsert` |
| 1444 | ✅ | `PATCH /<table>?id=` | `_sbPatch` |
| 1449 | ✅ | `DELETE /<table>?id=` | `_sbDel` |
| 1564 | ✅ | `PATCH /notifications` | mark single read |
| 1567 | ✅ | `PATCH /notifications` | mark all read |
| 1574 | ✅ | `DELETE /notifications` | bulk delete |
| 1701 | ✅ | `DELETE /worker_projects` | user-delete cleanup |
| 1812 | 🟡 | `POST /rpc/login_lookup` | pre-auth (kein Token vorhanden) |
| 2355 | ✅ | `POST /rpc/juprowa_fetch_worksheets` | |
| 2528 | ✅ | `POST /rpc/juprowa_push_worksheet` | |
| 3954 | 🔴 | `GET /bautagebuch?limit=1` | Admin-Schema-Check on mount; silent fail möglich. **P3** |
| 4031 | 🔴 | `GET /workers?limit=1` | Sync-Probe vor Full-Sync; AbortSignal 5s; silent bei 401. **P3** |
| 6319 | ✅ | `POST /rpc/admin_reset_password` | createUser-Pfad |
| 6365 | 🔴 | `POST /rpc/juprowa_get_config` | Admin-UI Config-Load; bei 401 Endlos-Loading schon via Toast gefixt (v3.8.20), aber Auto-Retry wäre sauberer. **P2** |
| 6366 | 🔴 | `POST /rpc/juprowa_update_passport` | **Admin-Write**, unretried; 401 → Toast "Fehler: 401" ohne Retry. **P2** |
| 6450 | ✅ | `POST /supplier_articles` | Bulk-Upload (60s timeout) |
| 6454 | ✅ | `PATCH /supplier_configs` | last_sync Update |
| 6588 | ✅ | `POST /rpc/admin_reset_password` | Reset-Button in Admin-UI |
|13183 | 🟡 | `GET /users?limit=1` | UI-Button "doTest" — intentional simple probe |

## _SB_AUTH Sites (6)

| Line | Status | Endpoint | Kommentar |
|-----:|:------:|----------|-----------|
| 1119 | 🟡 | `POST /token grant_type=password` | Login — ist selbst Auth, kein Retry-Kandidat |
| 1139 | 🟡 | `POST /token grant_type=refresh_token` | Refresh-Mechanismus (= das, was `_authRetry` intern aufruft) |
| 1151 | 🟡 | `POST /token grant_type=password` | Silent Re-Auth (B-021) — auth selbst |
| 1157 | 🟡 | `POST /logout` | Logout — 401 egal |
| 1839 | 🟡 | `POST /signup` | User-Create — pre-auth für neuen User |
| 1885 | 🟡 | `PUT /user password` | changePassword GoTrue-Sync — Token frisch nötig, `_authRetry` hätte race mit PW-Wechsel; beobachtbar via v3.8.17 Iter-18 Logging |

## Zusammenfassung

- **Wrapped:** 13/21 SB_REST (62 %). Wesentliche Write-Pfade (`_sbPost/_sbPatch/_sbDel/_sbPostUpsert/Notifications/worker_projects`) sind alle wrapped.
- **Intentional:** 8 (pre-auth, Debug, Auth-Endpoints).
- **Gaps:** 4 — alle **Priorität P2/P3**, keine Silent-Leaks, sondern Graceful-Degradation-Lücken.

## Aktion-Kandidaten (NICHT automatisch gefixt per R6/A2-Regel)

1. **L6366 juprowa_update_passport** (P2) — Admin-Write-Retry ergänzen wie L6588-Pattern.
2. **L6365 juprowa_get_config** (P2) — selbes Pattern.
3. **L3954 bautagebuch-schema-check** (P3) — admin-only, seltener Fall, Toast statt silent.
4. **L4031 workers-sync-probe** (P3) — Wrap oder akzeptieren als "best effort".

Sebastian entscheidet Priorisierung.
