# B-017 Window-Exposures Inventur · 19.04.2026

## Gesamt-Befund

30 `window.X =` Zuweisungen in index.html. Davon:
- **3 CRITICAL** → müssen raus (Credentials)
- **2 SENSIBLE** → admin-guard
- **25 HARMLOS** → bleiben (Utility, Formatter, Events, Testing)

## Tabelle

| Variable | Line | Warum exposed | Entscheidung |
|---|---|---|---|
| `window.SUPABASE_URL` | 294 | Debugging (v3.5.115) | **ENTFERNEN** — bleibt in Closure |
| `window.SB_REST` | 294 | Debugging (v3.5.115) | **ENTFERNEN** — bleibt in Closure |
| `window.SUPABASE_KEY` | 296 | Debugging (v3.5.115) | **ENTFERNEN** — Anon-Key aber Exposure-Fläche |
| `window._sbH` | 296 | Debugging + Smoke-Test TC-S | **ADMIN-GUARD** (oder beibehalten falls TC-S abhängig) |
| `window._sbAuthLogin` | 296 | Debugging | **ADMIN-GUARD** |
| `window._authToken` | — | wird NIE gesetzt | ✅ kein Handlungsbedarf (dead-read an Line 529 bleibt harmlos) |
| `window._sbGet/_sbPost/_sbPatch/_sbDelete/_sbUpsert` | — | wird NIE gesetzt | ✅ kein Handlungsbedarf |
| `window._sbAuthRefresh`, `_silentReAuth`, `_forceLogout` | — | wird NIE gesetzt | ✅ kein Handlungsbedarf |
| `window._epkVibrate`, `_haptic`, `_epkTimer` | 304, 315, 324 | UI-Utility | ✅ bleibt |
| `window._runSmokeTests`, `_runAllTests`, `_checkIntegrity`, `_measurePerf` | 330, 339, 460, 513 | Test-Harness | ✅ bleibt (Sebastian ruft manuell) |
| `window.APP_LIMITS`, `ROLLE` | 360 | Constants für Child-Comp | ✅ bleibt |
| `window._showToast` | 366 | UI-Util von überall | ✅ bleibt |
| `window._api` | 413 | Legacy-Bridge | ✅ bleibt |
| `window._fmtDate`, `_fmtDatetime`, `_fmtRelative`, `_fmtEur`, `_fmtH` | 418-422 | Formatter | ✅ bleibt |
| `window._maskPhone`, `_maskSVNR` | 427, 428 | PII-Masking | ✅ bleibt |
| `window._rateLimit`, `_dedupeGet` | 434, 446 | Util | ✅ bleibt |
| `window._ensureAuth` | 528 | Auth-Check vor Writes | ✅ bleibt (ist nur check, kein secret) |
| `window.API` | 1184 | Legacy UI-Layer | ✅ bleibt |
| `window._forceCacheClear` | 1333 | SW-Admin-Util | ✅ bleibt |
| `window._allUsers` | 2988 | Component-Bus | ✅ bleibt |
| `window._epkAudioCtx` | 3338 | Audio | ✅ bleibt |
| `window._epkSyncInflight` | 3412, 3465 | Sync-Flight-Flag | ✅ bleibt (nur flag, kein secret) |
| `window._vorlagenBus` | 12534 | PubSub | ✅ bleibt |

## Aktion

1. **Line 294-296 umbauen**: SUPABASE_URL/SB_REST/SUPABASE_KEY raus. `_sbH` und `_sbAuthLogin` in admin-guard (user.role==='admin' check NACH Login).
2. **TC-S test anpassen** (Line 501-502): statt `window.SB_REST===SUPABASE_URL+'/rest/v1'` → Test deaktivieren oder via interne API verifizieren.
