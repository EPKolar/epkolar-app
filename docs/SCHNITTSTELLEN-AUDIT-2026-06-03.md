# Schnittstellen-Audit 2026-06-03 - Sprint 75

**Repo:** epkolar-app, HEAD pre-sprint: `62384b2` (v3.9.95).
**Scope:** Supabase REST + Auth-RPC Endpoints (Audit + Tier-1 Fixes).
**Methode:** Statische Code-Analyse via Grep auf `SB_REST` / `SUPABASE_URL+` / `_SB_AUTH` / `SB_STORAGE`.

---

## 1. Endpoint-Inventar

### 1.1 REST-Wrappers (Generic, `index.html:1761-1810`)
Alle Wrappers haben `_authRetry` + Status-Check + Auth-Refresh + Throw.

| Funktion | Method | Auth | Error-Handling |
|----------|--------|------|----------------|
| `_sbGet(table,filter)` | GET | `_sbRH()` | `_authRetry`, throw on non-ok |
| `_sbGetOrder(...)` | GET | `_sbRH()` | wie _sbGet |
| `_sbGetUsersSafe(filter)` | GET | `_sbRH()` | password_hash-Filter |
| `_sbGetAnon(table,filter)` | GET | anon | silent fail -> [] |
| `_sbPost(table,data)` | POST | `_sbWH()` | throw on non-ok |
| `_sbUpsert(table,data)` | POST merge | `_sbWH()` | throw on non-ok |
| `_sbPatch(table,id,data)` | PATCH | `_sbWH()` | throw on non-ok |
| `_sbDelete(table,id)` | DELETE | `_sbH()` | throw on non-ok |
| `_sbUploadFile(path,dataUrl)` | POST Storage | `_sbH()` x-upsert | throw on non-ok |

### 1.2 Direkte fetch()-Calls (Audit)

| Line | Endpoint | Method | Used-By | Error-Handling |
|------|----------|--------|---------|----------------|
| 515 | /users?select=id&limit=1 | GET | Self-test | log only |
| 518 | /storage/.../bucket | HEAD | Self-test | log only |
| 594 | /rest/v1/{t}?{q} | GET | _apiSafe.get | _authRetry OK |
| 601 | /rest/v1/{t} | POST | _apiSafe.post | _authRetry OK |
| 607 | /rest/v1/{t}?id=eq.{id} | PATCH | _apiSafe.patch | _authRetry OK |
| 613 | /rest/v1/{t}?id=eq.{id} | DELETE | _apiSafe.del | _authRetry OK |
| 1315 | /rest/v1/whatsapp_config | GET | wa-load | ensureAuth+ok-only (P3) |
| 1336 | /rest/v1/whatsapp_templates | GET | wa-templates | fallback []  |
| 1350 | /rest/v1/whatsapp_messages | POST | mock-log | fire-forget (mock only) |
| 1552 | /storage/v1/object/... | POST | upload | _authRetry+throw |
| 1911 | /rest/v1/notifications | PATCH | mark-all-read | _authRetry+status check |
| 1914 | /rest/v1/notifications | PATCH | mark-fallback | _authRetry+status |
| 1923 | /rest/v1/notifications | DELETE | clear | _authRetry+status |
| 2051 | /rest/v1/worker_projects | DELETE | assignments | _authRetry+throw |
| 2163 | /rest/v1/rpc/login_lookup | POST | B020-A login | AUDIT-ONLY |
| 2287 | /rest/v1/activity_log | POST | err-telemetry | fire-forget (capped) |
| 2780 | /rest/v1/rpc/juprowa_fetch_worksheets | POST | sync-pull | _authRetry+status+err-ret |
| 3012 | /rest/v1/rpc/juprowa_push_worksheet | POST | sync-push | _authRetry+status+push_error |
| 4430 | /rest/v1/activity_log | POST | boundary-tel | fire-forget |
| 4759 | /rest/v1/bautagebuch | GET | schema-check | _authRetry+throw |
| 4837 | /rest/v1/workers | GET | conn-test | _authRetry+status |
| 7320 | /rest/v1/rpc/admin_reset_password | POST | pw-reset | _authRetry+console.error+toast |
| 7372 | /rest/v1/rpc/juprowa_get_config | POST | admin-cfg | _authRetry+status+toast |
| 7373 | /rest/v1/rpc/juprowa_update_passport | POST | passport-rot | _authRetry+status+toast |
| 7468 | /rest/v1/supplier_articles | POST merge | DATANORM | _authRetry+status+throw |
| **7472** | /rest/v1/supplier_configs?id=eq.{} | PATCH | last_sync-update | _authRetry only, **FEHLT .ok-Check (P2)** |
| 7610 | /rest/v1/rpc/admin_reset_password | POST | inline-pw-reset | _authRetry+status |
| 15106 | /rest/v1/users?select=id&limit=1 | GET | settings-test | ensureAuth+401/403-sep |
| 15217 | /rest/v1/whatsapp_config | GET | admin-load | try/catch+status |
| 15243-45 | /rest/v1/whatsapp_config | POST/PATCH | admin-save | status+errmsg |
| 15335 | /rest/v1/system_config | PATCH | sys-config-edit | ensureAuth+_authRetry+throw |
| 18572 | /rest/v1/activity_log | POST | boundary-bk | fire-forget |

### 1.3 Auth-Endpoints (AUDIT-ONLY, keine Edits)

| Line | Endpoint | Method | Error-Handling |
|------|----------|--------|----------------|
| 1363 | /auth/v1/token?grant_type=password | POST | _safeJsonParse + throw status+msg |
| 1389 | /auth/v1/token?grant_type=refresh_token | POST | singleton-inflight, thundering-herd guard |
| 1431 | /auth/v1/logout | POST | fire-forget try/catch |
| 2163 | /rest/v1/rpc/login_lookup | POST | 15s timeout + JSON-parsed |
| 2190 | /auth/v1/signup | POST | 15s timeout |
| 2239 | /auth/v1/user | PUT | 15s timeout + status |

---

## 2. Findings

### P1 - keine

### P2 - moderat
1. **`supplier_configs` last_sync PATCH ohne .ok-Check** (`index.html:7472`)
   - Risiko: silent RLS-denial -> last_sync veraltet, User sieht falschen Sync-Timestamp.
   - Fix: console.warn observability (non-throwing, da Artikel-Import bereits OK).

### P3 - kosmetisch
1. `_waLoadConfig` (1316) - kein else-handling fuer 4xx/5xx, Mock-Fallback greift.

---

## 3. Tier-1 Fix (Sprint 75.4)
**Fix #1:** `index.html:7472` - last_sync PATCH Status-Check (LoC <20, non-throwing).

## 4. Verify (siehe Commit)
- Brackets pre: () 16 / {} 1 / [] 0
- pytest: passing
- node --check: sw.js passed

## 5. Sebastian-Actions
Keine - Sprint ist code-only.
