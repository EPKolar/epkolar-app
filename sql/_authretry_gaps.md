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
| 3954 | ✅ *(v3.8.36)* | `GET /bautagebuch?limit=1` | Admin-Schema-Check on mount, wrapped (L2-P3 CLOSED) |
| 4031 | ✅ *(v3.8.36)* | `GET /workers?limit=1` | Heartbeat-Probe AbortSignal 5s, wrapped (L2-P3 CLOSED) |
| 6319 | ✅ | `POST /rpc/admin_reset_password` | createUser-Pfad |
| ~~6365~~ | ~~🔴~~ → ✅ | `POST /rpc/juprowa_get_config` | **v3.8.36 wrapped** (L2-P2 CLOSED) |
| ~~6366~~ | ~~🔴~~ → ✅ | `POST /rpc/juprowa_update_passport` | **v3.8.36 wrapped** (L2-P2 CLOSED, Admin-Write Passport-Rotation) |
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

- **Wrapped (v3.8.36):** 17/21 SB_REST (81 %). Alle 4 echten Gaps gefixt.
- **Intentional:** 4 (pre-auth login_lookup, Debug, User-probe-Button).
- **Gaps:** 0 (alle L2-Items in v3.8.36 closed).

## L2 CLOSED (v3.8.36)

Alle 4 ursprünglichen Kandidaten gefixt mit einfachem `_authRetry(()=>fetch(...))` Wrap:

- L3954 `bautagebuch-schema-check` → wrapped
- L4031 `workers-heartbeat-probe` → wrapped
- L6365 `juprowa_get_config` → wrapped
- L6366 `juprowa_update_passport` → wrapped (Admin-Write)

Kein funktionaler Regress: `_authRetry` ruft `fn()` auf, bei 401 einmal Refresh + Retry,
bei Erfolg gleich durch. Keine neue Logik, nur der Token-Refresh-Pfad wird aktiv.
