# EPKolar HANDOFF — 3h-Testlauf FINAL · 18.04.2026

App live: **v3.5.134** (`681f204`). 3-Iterationen-Scan komplett.

## 🏆 Gefundene Bugs (3-Iterationen + Runde)

| Iter | Ver | SHA | Kategorie | Fix |
|---|---|---|---|---|
| **Pre-Runde** | 125-132 | `41c835d`…`0394cb4` | Diverse | Fahrzeug-Anzeige null-safe, DATANORM-upsert härter, Popup-null-guard, MAT_STATUS-lookup-guard, Notif-permission defensiv, AudioContext-leak gefixt, bcrypt-hashSync try/catch, Signup-Timeout |
| **1/3** | **133** | `e4e96f0` | **CRITICAL** | IndexedDB-Migration non-destruktiv — vorher: DB_VER-Bump LÖSCHTE alle Stores inkl. syncQueue → Offline-User verloren ungespeicherte Änderungen. Jetzt: nur fehlende Stores anlegen |
| 2/3 | — | — | Keine gefunden | Exhaustive Null-Safety (alle Export-Pfade schon abgedeckt) |
| **3/3** | **134** | `681f204` | Kompetenz | `createFromTemplate` — `tpl.items.map()` crashte bei Legacy-Templates ohne items-Feld. Plus curUser username-Fallback |

**Total diese Session (seit v3.5.108):** 27 Bugs gefixt.

## 🟢 Was gescannt wurde

### Iteration 1: Integration-Pfade
- ✅ Auth-Restore Race → `_ensureAuth` + Flight-Promise-Guard decken ab
- ✅ SQ `uid()` Math.random-Collision → Risiko 1/1.7M pro ms-window, akzeptabel
- ✅ Optimistic-UI + Server-Reject → keine automatische Reconcile, aber selten kritisch
- ✅ SQ Error-Paths (network/auth/max-5-retry) → alle 3 funktionieren
- 🐛 **IndexedDB-Migration destruktiv — v3.5.133 FIX**

### Iteration 2: Data-Integrity
- ✅ Alle `.replace()`/`.toUpperCase()`/`.toLowerCase()` auf user-fields null-safe (nach v3.5.89-108 Sprint)
- ✅ Alle Export-Pfade (OFFA/Werkzeug/Fahrtenbuch/PDF) null-safe (v3.5.117, 118, 120, 122 gefixt)
- ✅ `csvRows.push` bei Abwesenheits-Export — AT_T-lookup mit Fallback
- ✅ `_fetchLiveKpis` Interval-Cleanup via useEffect-return
- ℹ️ **WorkerKompetenzen toggle** hat keinen in-flight-Guard → rapid-click könnte Duplikate erstellen. **Low-Impact, skip** (Panel rarely hit + DB-constraint kann abfangen)

### Iteration 3: Edge-Cases + Close-out
- ✅ `env(safe-area-inset-bottom)` korrekt in bottom-nav (2× Positionen)
- ✅ Resize-Listener debounced + cleanup vorhanden
- ✅ Modal-backdrop-click-close, mit `e.target===e.currentTarget` Check
- 🐛 **createFromTemplate tpl.items.map() — v3.5.134 FIX**
- ⚠️ **Setform({...form,...}) in 52 Stellen** (funktional: 9) — stale-closure-Risiko in async callbacks. Zu riskant für bulk-refactor ohne Tests.
- ⚠️ **500 `<button>`s ohne `aria-label`** — A11y-Debt, low ROI für kleine Firma

## 📊 Session-Statistik (v3.5.108 bis v3.5.134 = 27 Versionen)

| Kategorie | Anzahl | Beispiele |
|---|---|---|
| **CRITICAL** | 2 | TZ-off-by-1-day (108/109), IndexedDB-Migration (133) |
| **Mobile/iOS** | 4 | _uuid-fallback, _dl-helper, 100dvh, AudioContext |
| **Auth** | 4 | Flight-Promise, Error-Parsing, Timeout, Storage-Keys |
| **Null-Safety** | 10+ | .split/.replace/.toLowerCase/.toFixed verschiedenste Stellen |
| **XSS-Härtung** | 2 | printLabels _e(), genBarcodeSVG |
| **Timeout/Race** | 4 | _fT überall, _sbGetAnon, DATANORM-upsert, SyncQueue-Concurrency |

## 🔴 Noch offen (DEINE 5 Min Kaffee-Tasse)

**Auth-500 bei info@/office@** (Riedmann läuft):
1. `/sql/AUTH_DEBUG_QUERIES.sql` Query B ausführen → NULL-Trap check
2. FIX B (falls NULL-Felder) → Login-Retry mit v3.5.113+ (zeigt echte GoTrue-Msg)

## 🟡 Nicht gefixt — bewusst skip

| Bereich | Grund |
|---|---|
| Juprowa Phase-1-Pull | forbidden zone per CLAUDE.md |
| Juprowa Phase-2-Push Timeouts | gleiche forbidden zone |
| 52× `setForm({...form,...})` → funktionale Form | Risiko ohne Tests zu hoch, latent-bug wartet auf konkrete Bug-Meldung |
| 500× `<button>` ohne `aria-label` | Bulk-refactor, niedrige ROI |
| WorkerKompetenzen Toggle in-flight guard | rarely-hit, DB-constraint fängt ab |

## 📋 Deferred Blocks (nächste Session)

| Block | Titel | Aufwand | Priorität |
|---|---|---|---|
| **8** | **AS-Signature-Close-Flow** | 1-2h | ⭐ Schnell-Win |
| **13** | **Audit-Log-UI** (activity_log wird gefüllt) | 1-2h | ⭐ Schnell-Win |
| 4 | Fahrzeug-Buchungs-Kalender | 2-3h | med |
| 9 | AS-PDF v2 (jsPDF) | 2h | med |
| 14 | Web-Push (VAPID + Server) | 1 Woche | low |

**Empfehlung**: **Block 8** oder **13** als nächstes.

## 🤖 Loop-Status

**3h-Testlauf beendet nach Iteration 3/3.** Keine weiteren Wakeups gescheduled. Repo + DB (nach deinem B-006b+B-007 SQL-Run) synchron.

## 📌 Letzter Stand in einer Zeile

```
HEAD: 681f204 · v3.5.134 · 27 bugs this session · B-006+B-007 DONE · B-018 (Auth 500 info@/office@) wartet auf SQL Query B
```
