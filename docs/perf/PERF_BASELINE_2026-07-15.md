# Performance-Baseline · 2026-07-15

**Quelle:** Live-Messung (Chat-Claude, ~18:40) am Live-Stand v3.9.707/708. Diese Zahlen sind die
Referenz für die Vorher/Nachher-Belege der Perf-Fixes. Nicht wiederholt gemessen außer wo ein Fix
eine gezielte Nachmessung braucht.

## Startup / Netz
| Kennzahl | Baseline |
|---|---|
| Boot `domInteractive` | **245 ms** |
| Daten komplett (alle Bootstrap-Fetches fertig) | **5.616 ms** |
| `fahrzeuge`-Fetch (einzeln) | **2.370 ms** |

## RAM / IndexedDB
| Kennzahl | Baseline |
|---|---|
| JS-Heap nach Boot (Admin) | **89 MB** |
| IDB `fahrzeuge`-Store | **15.405 KB** mit **24 Base64-Fotos** |
| Größter Einzel-Fresser | `TU-266BP` allein **~3 MB** Base64 |

→ Der `fahrzeuge`-Store dominiert Heap **und** `fahrzeuge`-Fetch-Zeit, weil `tank_log`
(Base64-Tankbelegfotos) im Boot mitkommt. **Fix 1 = größter Hebel.**

## Poll-Last (Kiosk-Tab ~10 min, ?screen=planung)
| Collection | Requests / 10 min |
|---|---|
| workers | 11× |
| defects | 9× |
| absences | 7× |
| material_orders | 4× |

→ Die Tafel braucht davon nur workers (1× beim Mount) — `defects`/`material_orders`/`absences`-roh
gehören nicht in den Kiosk-Zyklus. **Fix 2 = Kiosk-Poll-Diät.**

## Haupt-App Doppel-Fetches
workers 10×, defects 8× über eine Session — Verdacht auf mehrfach fetchende Views/Effects derselben
Collection. **Fix 3 = nur ECHTE Doppler dedupen** (gleicher Endpoint+Query kurz hintereinander),
konservativ.

## Fix-Plan (je eigene Version/Commit, Verhalten aus User-Sicht identisch außer schneller)
- **Fix 1 (P1):** `tank_log`-Base64 raus — (a) Zulauf stoppen (addTank/qDoTank/batchSave →
  `_sbUploadFile`→Storage-URL, Muster v552), (b) Migration `_migrateTankFotos` (admin-gated,
  Sebastian löst aus), (c) Bootstrap-Diät: `fahrzeuge`-Boot-Fetch ohne `tank_log`-Spalte, on-demand
  nachladen. Ziel: Daten-komplett <3 s, `fahrzeuge`-Fetch <300 ms.
- **Fix 2 (P2):** Kiosk-Poll auf Tafel-Bedarf reduzieren.
- **Fix 3 (P3):** belegte Doppel-Fetches dedupen.

**Verbote:** keine Sync-Queue-Semantik, kein Juprowa-Push, keine Auth/RLS/DDL (Index-Vorschläge
höchstens als gestagete `sql/PERF_INDEX_v1.sql` mit Human-Run-Gate). Migration-`{go:true}` nur nach
explizitem Sebastian-OK oder Admin-Button durch ihn selbst.
