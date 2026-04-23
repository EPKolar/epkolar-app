# EPKolar · Security Notes · Stand v3.8.39 (2026-04-25)

Aktuelle Security-Baseline nach Overnight #1 + #2. Zielgruppe: Sebastian + Support-Contractor.

---

## Auth-Flow (aktuell)

```
┌─────────────┐  password   ┌─────────────┐
│ Client      │ ──────────► │ GoTrue /token│
│ LoginScreen │             │ grant=pw     │
└─────────────┘ ◄────────── └─────────────┘
       │       access + refresh token
       │
       ▼
┌─────────────┐   Bearer    ┌─────────────┐
│ _sbH/_sbWH  │ ──────────► │ PostgREST    │
│ _authRetry  │ ◄─401       │ /rest/v1/*   │
└─────────────┘             └─────────────┘
       │ 401 detected
       ▼
┌─────────────┐  refresh_token  ┌─────────────┐
│ _sbAuthRefr │ ──────────────► │ GoTrue /token│
└─────────────┘                 │ grant=refresh│
       │       new access      └─────────────┘
       │ refresh fails
       ▼
┌─────────────┐
│ _silentReAuth (stub seit v3.8.35)│
│ → returns null                   │
│ → User muss neu einloggen        │
└──────────────────────────────────┘
```

**Details:** `SILENT_REAUTH_STATUS.md`.

## Token-Lebenszyklus

| Token | Lifetime | Storage | Verwendung |
|---|---|---|---|
| `access_token` | ~1 h (Supabase-Default) | `_authToken` in-memory + `localStorage.epkolar_auth.at` | `Authorization: Bearer` Header |
| `refresh_token` | 7 d (Supabase-Default) | `_authRefreshToken` in-memory + `localStorage.epkolar_auth.rt` | Refresh bei 401 |
| bcrypt `password_hash` | Permanent in `public.users.password_hash` | DB only | Login-Fallback wenn GoTrue schlaegt fehl |
| `_OFFPW` PBKDF2 | Pro Session (bis IDB cleared) | IndexedDB `meta/offlinePwHash` | Offline-Login-Verifikation |

Alte Token-Systeme, die **entfernt** wurden:
- `epkolar_gc` (base64 credentials) — v3.8.35 eliminiert
- `offlinePwHash` als `btoa("user:pw")` — v3.8.33 durch PBKDF2 ersetzt

## RLS-Strategie

- **B-006 + B-007** ✅ CLOSED (v3.5.94) mit 4 Helpers + 22 Policies
- Siehe `sql/CANDO_MATRIX.md` (44 Actions × 7 Rollen — UI-Gating)
- Helper-Funktionen: `current_monteur_id()`, `current_user_role()`, `current_user_pk()`, `is_staff()`
- Schema-Konventionen: `arbeitsscheine.monteur`, `time_entries.worker_id`, `fahrtenbuch.worker_id`, `notifications.user_id`, `as_checklist.as_id`, `as_kommentare.as_id+autor_id`, `worker_kompetenzen.worker_id`, `users.monteur_id`

## localStorage — was liegt da drin?

Siehe `sql/LOCALSTORAGE_AUDIT.md`. Kurz:

🔴 **Sensibel**:
- `epkolar_auth` — `{at, rt, exp}` Tokens (beim Logout gecleart)
- `epkolar_token` / `epkolar_refresh` — Duplikat von epkolar_auth.at/rt (Legacy)

🟡 **Moderate**:
- `epkolar_user` — PII (User-Objekt incl. Email)
- `epk_timer` — laufender Timer (mit Projekt-ID)

🟢 **Benign**:
- `epk_sw_ver`, `log_level`, `DEBUG`, `__dev`

## Was ist NICHT in localStorage?

- Refresh-Cookie (Supabase ist pure REST, kein HttpOnly-Cookie)
- Edge-Function Meta-API-Token (bleibt server-side)
- DB-Passwörter (kommen aus SUPABASE_DB_URL only lokal beim Deploy)

## Was ist im Client-Code hartcodiert?

- `SUPABASE_URL` (L331) — public, OK
- `SUPABASE_KEY` (L334) — **anon-JWT**, public OK (RLS schützt)
- `MONT`-Tabelle — Monteur-Stammdaten (intern, aber kein PII-Risk solange Namen allein)
- Admin-Email-Patterns, Phone +43-Nummer (EPKolar-Büro) — intern

## Was wäre besser in Env (nicht jetzt)?

Technisch ginge alles via `localStorage.SUPABASE_URL = ...` + Bootstrap-Script. Aber: single-file deployment ist der ganze Punkt der Architektur. Kein Value, Risiko hoch.

## PII-Check (nach L4-Cleanup)

- **INIT_AS** mit echten Kundendaten: ✅ GELÖSCHT v3.8.37 (Git-History nicht umgeschrieben per R2)
- **INIT_WZ** mit Werkzeug-Seriennummern: ✅ GELÖSCHT v3.8.37
- **MONT** Monteur-Stammdaten: KEPT (wird aktiv genutzt)
- **Kundendaten-Seeds allgemein**: KEEP `INIT_PROJECTS` (nur Dummy-Namen)

## XSS-Oberflaeche

Siehe `sql/XSS_AUDIT.md`. Kurz:
- `innerHTML=` Nutzungen: 5 Stellen, alle entweder static oder mit `_xe`/`_xe1`-Escape seit v3.8.37
- `dangerouslySetInnerHTML`: nur 1 Stelle (`genBarcodeSVG`), escaped
- `document.write`: nur in `window.open()`-Print-Popups, escape via `_e` seit v3.8.20/21
- `eval` / `new Function`: **0 Vorkommen** (pytest-Guard)

## Offline-Security

- Offline-PW-Hash: **PBKDF2-SHA256, 100 000 Iter, 16-Byte Salt** (seit v3.8.33)
- Legacy base64 wird beim Offline-Verify noch akzeptiert (Grace-Migration) → automatisches Re-Hash beim nächsten Online-Login

## Logout-Sauberkeit

Seit v3.8.34 (QW1+QW2) werden **alle user-scoped localStorage-Keys** beim Logout gecleart:
- `epkolar_auth`, `epkolar_token`, `epkolar_refresh` (Legacy-Cleanup)
- `epkolar_user`
- `epkolar_default_sb`, `epk_autonotif_cd`, `epk_dash_vis`, `selftest_last_run`, `s8_last_run`
- `epkolar_gc`, `epkolar_juprowa_wmap`, `epkolar_auth_backup_preforce` (v3.8.34)

Plus IDB: `offlinePwHash`, `lastUser`, 13 user-scoped Data-Stores (`entries`, `forms`, etc.)

Plus window-globals: `_sbH`, `_sbAuthLogin`, `_sbAuthRefresh`, `_silentReAuth`.

## Pytest-Regression-Guards

- `test_no_eval_calls` — verhindert eval()-Reintroduction
- `test_no_function_constructor` — verhindert new Function(...)
- `test_no_toplevel_document_write` — erlaubt `<win>.document.write` in Print-Popups, blocked top-level
- `test_offline_pw_is_not_plain_base64_write` — verhindert Regression zu btoa() für `offlinePwHash`
- `test_no_epkolar_gc_setitem` — verhindert Reintroduction des Plaintext-PW-Cache

## Offene Items (Sebastian-Entscheidung)

1. **Inactivity-Logout** (`CODE_DEBT_v2.md` A1) — P3
2. **Refresh-Token-TTL verlängern** in Supabase Dashboard? 7d → 30d? Reduziert Re-Login-UX-Friction für inaktive User (siehe `SILENT_REAUTH_STATUS.md`). Trade-off: längeres Exposure bei Session-Hijacking.
3. **MFA / WebAuthn** für Admin? — sehr P4, Aufwand vs. Threat-Model.
4. **Git-History PII-Rewrite** (`filter-repo`) für die gelöschten INIT_AS-Kundendaten. Destruktiv, alle Clones müssten re-pullen.
