# HANDOFF · v3.8.47 Auth-Hardening · ABORT (Phase 0) · 2026-04-24

**Baseline:** `73b0c86` (v3.8.46) · **End-State:** unverändert (nur Docs)
**Tag:** keiner (kein Code-Change → kein Rollback-Punkt nötig)

## TL;DR

Session nach Phase 0 Inventory **abgebrochen per H8 / ABBRUCH-BEDINGUNG**: Die Auth-Architektur ist fundamental anders als im Session-Plan angenommen. Der Großteil dessen was die Session implementieren sollte existiert bereits seit v3.5.x. Code-Änderung vermieden; Inventar-Doku + Handoff committed damit Sebastian informierte Entscheidung treffen kann.

## Was der Plan annahm vs. Realität

| Plan-Annahme | Realität |
|---|---|
| `_refreshToken`-Helper FEHLT | `_sbAuthRefresh` L1145, Singleton via `_authRefreshInflight` |
| `_tokenWatchdog` FEHLT | `_authRefreshTimer` one-shot 60s-vor-exp existiert (kein Interval, aber zweckgleich) |
| `_getTokenExpiry` FEHLT | `_ensureAuth` L1088 + inline JWT-parsing an mehreren Stellen |
| `epkolar_refresh` NIE VERWENDET | **Wird verwendet** indirekt via `epkolar_auth.rt` beim Bootstrap-Restore (L1190 → `_authRefreshToken` → `_sbAuthRefresh`) |
| visibility-Handler FEHLT | L1197 existiert, 120s-Threshold |
| `_silentReAuth` halb-fertig | **Absichtlich Stub seit v3.8.35** — base64-PW-Cache wurde aus Sicherheitsgründen entfernt |

Vollständiges Inventar: `sql/AUTH_INVENTORY_20260424.md`.

## Phase-Progression

- **Phase 0** (Inventory) · ✅ durchgeführt, keine Code-Änderung
- **Phase 1** (Safety-Tag) · übersprungen (kein Rollback-Ziel nötig ohne Code-Change)
- **Phase 2-8** · ❌ nicht ausgeführt

## Was wirklich "fehlt" (additive, nicht kritisch)

1. **`online`-Event-Auth-Refresh** — L4350 triggert aktuell nur Sync-Flush, nicht `_sbAuthRefresh`. 1-Zeilen-Ergänzung.
2. **Backup-Watchdog als setInterval(60s)** — falls der one-shot `_authRefreshTimer` durch Browser-Tab-Throttling silent dies. Defense-in-Depth.
3. **`__authLog`-Ring-Buffer** für Debug-Telemetrie (keine Token-Werte).
4. **Preflight in `_sbGet/Patch/Post/Delete`** — dupliziert großteils `_authRetry`-Verhalten, fraglicher Mehrwert.

Keiner dieser Punkte ist kritisch für "Token immer gültig" — das leistet die bestehende Architektur bereits:
- **Tab-Sleep 12h:** Visibility-Handler (L1197) fängt beim Wiederkommen + exp<120s → refresh ✅
- **8h Offline:** Fehlt aktuell (online-Handler refresh-t nicht) ❌
- **Password-Wechsel:** `_authRetry` fängt 401, rufft refresh, retry — User sieht kurze Verzögerung ✅

## H-Rules-Bilanz

- **H0 Pfad-Lock:** ✅ `T:\05_Claude\...\epkolar-app`
- **H1 Kritische Zonen:** ✅ vollständig unberührt (auch Auth-Zone nicht touched)
- **H2 Safety-Tag:** n/a (kein Code-Change)
- **H3 Refactor-Verbot:** ✅ nichts angefasst
- **H4 UI-Blocker:** n/a
- **H5-H10:** n/a (keine Code-Änderung)
- **H8 Abweichung → STOPP:** ✅ Phase 0 Inventar zeigte fundamentale Abweichung → STOPP

## Remaining (für Sebastian-Entscheidung)

**Option A · "Mini-Additiv" (Empfehlung, <30min)**
- 1 Commit: `online`-Handler ergänzt `_sbAuthRefresh()`-Call
- 1 Commit: Backup-`setInterval(60s)`-Watchdog mit 10-min-Threshold
- 1 Commit: Tests
- 1 Commit: Version-Bump v3.8.47

**Option B · "Full-Plan durchziehen"**
- Die im Plan beschriebenen Funktionen _zusätzlich_ zu den bestehenden einbauen
- Risiko: Doppel-Refresh-Races, Widerspruch zwischen `_ensureFreshToken(120s)` und `_ensureAuth(300s)`, `__authLog` ist guter Add-On aber rest duplizert bestehendes
- Aufwand: 4h, revertbar via Tag

**Option C · "Nichts tun"**
- Existing-Architektur ist für 95% der Fälle ausreichend
- 5%-Lücke (8h-Offline-Wiederkommen ohne Tab-Visibility-Change): würde sowieso via 401-Retry gefangen werden, nur mit 1× UX-Hickser

**CC-Empfehlung:** Option A nach Sebastian-Rückkehr aus Urlaub. Bis dahin bleibt v3.8.46 LIVE + stabil.

## Nicht-getane Aktionen (transparent)

- Kein git-tag gesetzt (war für Phase 1 geplant, nicht nötig ohne Code-Change)
- Keine pytest-Tests geschrieben
- Keine Version-Bump
- Kein `_refreshTokenOnce`/`_tokenWatchdog`/`_ensureFreshToken`-Code geschrieben
- Kein `__authLog` implementiert

## Dateien in diesem Commit

- `sql/AUTH_INVENTORY_20260424.md` (neu, ~220 Zeilen) — vollständiges Auth-Code-Inventar
- `HANDOFF_v3847_ABORT.md` (diese Datei) — Abort-Begründung + Empfehlung
- `sql/URLAUB_STATUS.md` (Update) — Abort-Eintrag

## Sebastian-Action-Required

Wenn Sebastian zurück ist:
1. `sql/AUTH_INVENTORY_20260424.md` lesen (3-5 min)
2. Entscheidung treffen zwischen Option A / B / C (oben)
3. Bei Option A: CC kann in einer kurzen Session (<30min) durchziehen
4. Bei Option B: CC braucht aktualisierten Plan-Prompt mit korrekten Baseline-Annahmen
5. Bei Option C: schließt den Eintrag in `sql/URLAUB_STATUS.md` als "resolved as no-op"
