# localStorage Audit · 2026-04-24

**Scope:** `index.html` · Baseline: Commit-Range bis `d6ca8c2`.
**Methode:** `grep -nE 'localStorage\.(setItem|getItem|removeItem|clear)' index.html`
**Ergebnis:** 19 distinkte Keys.

## Legende
- 🔴 **Sensibel** — enthält credentials, tokens, PII
- 🟡 **User-scoped Metadata** — wird bei Logout gecleart (Iter-17 Fix)
- 🟢 **Benign** — nur UI-State, Dev-Flags, etc.

## Key-Übersicht

| Key | Kategorie | Inhalt | Logout-Cleanup | Notiz |
|-----|:--------:|--------|:--------------:|-------|
| `epkolar_auth` | 🔴 | `{at, rt, exp}` (access + refresh Token + Ablauf) | ✅ | v3.8.10 Logout-Flow räumt auf |
| `epkolar_token` | 🔴 | JWT (Duplikat zu epkolar_auth.at) | ✅ | Legacy, könnte konsolidiert werden |
| `epkolar_refresh` | 🔴 | refresh_token (Duplikat) | ✅ | Legacy |
| `epkolar_gc` | 🟢 (v3.8.35 eliminiert) | ~~`{e:btoa(email), p:btoa(password)}` — base64 credentials~~ | ✅ (v3.8.34 defensive + v3.8.35 write-source entfernt) | **v3.8.35 CLOSED:** Key wird nicht mehr geschrieben. `_silentReAuth` gestubbed. Siehe `CODE_DEBT.md` L1. |
| `epkolar_auth_backup_preforce` | 🔴 | Token-Backup vor `_forceExpireToken()` | dev-only | Wird durch `_restoreToken()` gecleant |
| `epkolar_user` | 🟡 | Voller User-Objekt (id, role, name, email, monteurId) | ✅ | PII, aber notwendig für Offline |
| `epk_timer` | 🟡 | Laufender Timer `{running, startAt, projectId, task, owner}` | ✅ via Confirm | v3.8.7 Iter-3 warnt vor Logout mit laufendem Timer |
| `epkolar_default_sb` | 🟡 | Standard-Sub-Bereich für AS-List | ✅ | v3.8.16 Iter-17 Cleanup |
| `epkolar_juprowa_wmap` | 🟡 | Dyn. Worksheet-Mapping pro User | ⚠️ | **Nicht in Iter-17 Cleanup-Liste** — könnte Cross-User-Leak sein |
| `epk_autonotif_cd` | 🟡 | Auto-Notification Cooldown-Timer | ✅ | v3.8.16 Iter-17 |
| `epk_dash_vis` | 🟡 | Dashboard-Widget-Sichtbarkeit pro User | ✅ | v3.8.16 Iter-17 |
| `selftest_last_run` | 🟡 | `_selfTest`-Ergebnisse JSON | ✅ | v3.8.16 Iter-17 |
| `s8_last_run` | 🟡 | `_s8Suite`-Ergebnisse JSON | ✅ | v3.8.16 Iter-17 |
| `epk_sw_ver` | 🟢 | SW-Version-String | ❌ (egal) | Nur Boot-Check |
| `log_level` | 🟢 | `_setLogLevel()` Dev-Flag | ❌ (egal) | nur Log-Verbosity |
| `DEBUG` | 🟢 | Dev-Flag `"1"`/`"0"` | ❌ (egal) | Aktiviert dlog-Output |
| `__dev` | 🟢 | Dev-Gate für `_forceExpireToken`/`_thunderTest` | ❌ (egal) | sicherheits-Gate |

## 🔴 Kritischer Fund: `epkolar_gc` NICHT beim Logout gecleart

L1829 (createUser success, B-020 Fallback-Pfad) und L1840 (signup-Success):
```js
localStorage.setItem("epkolar_gc", JSON.stringify({e:btoa(email), p:btoa(p)}));
```

L1160 (login-new-session cleanup):
```js
localStorage.removeItem("epkolar_auth");
localStorage.removeItem("epkolar_gc");         // ← hier JA
localStorage.removeItem("epkolar_token");
localStorage.removeItem("epkolar_refresh");
```

**Aber** das wird nur beim **erneuten Login** ausgeführt (L1148-1160 ist im Login-Pfad).
Beim **Logout** (L4306) fehlt `epkolar_gc` — siehe v3.8.7 Iter-4 Comment:
```
/* v3.8.7 Bug-Hunt Iter-4: Offline-Cache cleanen — base64-Password + lastUser
   bleiben sonst im IDB (M-4 Scenario-Mitigation) */
try{await ODB.del("meta","offlinePwHash");await ODB.del("meta","lastUser");}catch(_){}
```

Der Comment spricht nur von IDB (`ODB.del`). Das **localStorage**-`epkolar_gc` bleibt
beim Logout liegen. Base64(password) ist wie base64(offlinePwHash) **reversibel** =
effektiv Klartext.

### Priorität: P2 Security-Follow-up

**Fix-Vorschlag** (NICHT in dieser Overnight, per R6):
```js
// Im Logout-Handler L4306 nach IDB-Cleanup:
try {
  localStorage.removeItem("epkolar_gc");
  localStorage.removeItem("epkolar_auth_backup_preforce"); // Konsistenz
} catch(_) {}
```

**Härte-Vorschlag** (längerfristig): `epkolar_gc` sollte analog zu `offlinePwHash`
auf PBKDF2 migriert werden (siehe v3.8.33 Iter-19c _OFFPW-Pattern).

## 🟡 `epkolar_juprowa_wmap` Cross-User-Leak?

L2269, L2284, L2296: Setter/Getter für Juprowa-Worksheet-Mapping.

Wird beim **Logout NICHT gecleart** (nicht in `_clearStores`-Liste, nicht separater
`removeItem`-Call). Folge: User B sieht nach Login Juprowa-Mapping-Cache von User A.

**Priorität: P3** — Juprowa-Mapping ist projektorientiert, nicht zwingend PII. Aber
inkonsistent zu anderen user-scoped Caches.

## Sensitive-Data Compliance

Die Kombination `epkolar_gc` (reversible Credentials) + `epkolar_user` (PII mit E-Mail)
sollte im DSGVO-Review explizit behandelt werden:
- **Retention**: Daten bleiben bis zum nächsten Login liegen, auch wenn Gerät gewechselt
  wird (localStorage ist per-Origin, nicht per-User).
- **Device-Sharing**: Wenn Monteur sich auf einem Bürorechner kurz anmeldet und Browser
  nicht aktiv loggt aus, sitzt die nächste Person mit Token + base64-Creds. Mitigation
  ist das Inactivity-Logout (gibt's das?).

## Zusammenfassung

- **19 Keys**, davon **5 sensibel**, **8 user-scoped**, **6 benign**.
- **2 echte Gaps** identifiziert: `epkolar_gc` (P2) + `epkolar_juprowa_wmap` (P3) im
  Logout-Cleanup.
- **Keine automatischen Fixes** (D2-Regel).

## Empfehlungen

1. **P2 (klein, 5 Zeilen):** `epkolar_gc` + `epkolar_auth_backup_preforce` in
   Logout-Handler L4306 ergänzen.
2. **P2 (mittel):** `epkolar_gc` von base64 auf PBKDF2 (analog _OFFPW).
3. **P3:** `epkolar_juprowa_wmap` in Logout-Cleanup aufnehmen.
4. **P4 (Policy):** Inactivity-Logout einführen (zB nach 8 h).
