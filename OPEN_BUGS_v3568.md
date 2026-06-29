# OPEN BUGS — Stand v3.9.569 (2026-06-29)

Konsolidierte Liste der **echten** offenen Bugs nach dem Hunt-Pass auf v3.9.568/569.
Vollständige Befundliste (inkl. Defense-in-depth + Dead-Code): `FINDINGS_v3568.md`.
Der alte `docs/handoff/BUGHUNT-2026-06-17-OFFEN.md` ist ~75% stale (siehe Kopf-Notiz dort).

---

## 🔴 EINZIGER echter offener Bug mit Handlungsbedarf

### A-2 · Juprowa Status-Roundtrip 4→1 / 15→11
- **Was:** `JUPROWA_STATUS_MAP` (`index.html:3017`) ist nicht-injektiv (4 und 15 kollabieren auf
  `freigegeben`/`bar_bezahlt` wie 1/11). Der Push-Builder `_juprowaReversMap` (`:3307`) schreibt
  ohne Dirty-Check den kanonischen Reverse → ein gepullter OFFA-Status **4 wird als 1**, **15 als 11**
  zurückgepusht, auch ohne echte Status-Änderung. Stille, OFFA-seitig irreversible Korruption.
- **Schwere:** MEDIUM (Korrektheit, externe Buchhaltung).
- **Fix:** STAGED auf lokalem Branch `a2-juprowa-roundtrip` (Commit `b72742d`, v3.9.570) — Dirty-Check
  gegen `juprowa_raw.AK_AUFSTATUS`. Builder-only, `_juprowaPush` unberührt. **NICHT gepusht.**
- **Dry-Run:** `scripts/a2_dryrun.mjs` → alle 10 OFFA-Codes roundtrip-stabil (4→4, 15→15) verifiziert.
- **⚠️ FREIGABE-BEDARF (Sebastian):**
  1. Tabu-Auslegung bestätigen (`_juprowaReversMap`-Edit ändert Push-Verhalten, auch wenn `_juprowaPush`
     selbst nicht editiert ist).
  2. Erst NACH Sicht des Dry-Runs den Live-Deploy (= ermöglicht echten OFFA-Push) freigeben.
- **Details:** `HANDOFF_A2_juprowa_status_roundtrip.md`.

---

## ✅ Bereits geschlossen diese Session (kein offener Bug mehr)
- **HIGH A-1 · Kiosk-PII-Leck:** lager_display las workers/arbeitsscheine/projects direkt (SVNR/Reisepass/
  Stundensatz/Kunden-Tel/Adresse). GESCHLOSSEN: RPCs `kiosk_field_workers`/`kiosk_week_arbeitsscheine`
  (minimal, kein PII) + Client v3.9.569 (`d065111`, live) + RLS `lager_display_no_select` RESTRICTIVE
  auf workers/projects/arbeitsscheine. Live-verifiziert (lager_display direct=0, RPC liefert 11/55).
- **A1/B5/B6/B034/A3** aus dem 17.06.-Backlog = stale/bereits gefixt/tot (siehe Backlog-Kopfnotiz).
- **supplier-sync set-credentials** (Validierung) = gefixt+committet (`ac44304`).
- **2b GoTrue-Logins** lindhuber/schober = angelegt (MCP).

---

## 🟡 Niedrigprio / Defense-in-depth (kein akuter Handlungsbedarf — Detail in FINDINGS_v3568.md)
- weekplan Dirty/Deleted-Set-Leak im Drop-Pfad (`:6405` vs `:6424`) — Korrektheit, selten.
- weekplan reload-Guard global statt KW-gefiltert (`:16204`).
- `notif_insert` `with_check=true` → lager_display könnte notifications INSERTen (DB-Policy, DiD).
- worker_projects/ROUTE_MAP generischer GET ohne Client-Scope (`:2096/2106`).
- Juprowa Doppel-Push-Race (`:3343` push_pending = Marker, kein Lock) — Verdacht.
- Juprowa optimistische Erfolgs-Zählung bei verschluckten Writes (`:3155/3160`) — selbstheilend via Pull.
