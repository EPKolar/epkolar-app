# Upgrade Notes · v3.8.20 → v3.8.39

Für Sebastian. Was hat sich in dieser "Overnight-Cluster"-Phase geändert und was muss er tun?

---

## Executive Summary

- **12 Releases** (v3.8.20 … v3.8.39) über zwei Overnight-Runs.
- **Keine Breaking Changes**, die DB-Migrations erzwingen.
- **2 Security-Hardenings**: `_OFFPW` PBKDF2 + `epkolar_gc` Elimination. User muss evtl. 1× neu einloggen.
- **Alle Tests grün**: 74/74 pytest + bracket-/version-Check.

---

## Release-Timeline

| Version | Datum | Summary |
|---|---|---|
| v3.8.20-31 | 23.04 Nacht | Bug-Hunt-Loop + Polish + Monteur-UX (siehe HANDOFF_SESSION_2026-04-23.md) |
| v3.8.32 | 23.04 Nacht | Session-Final + Silent-Catch-Observability |
| v3.8.33 | 23.04 spät | changePassword + Offline-PW PBKDF2 + SMOKE_TESTS |
| v3.8.34 | 25.04 | Logout-Cleanup (epkolar_gc + juprowa_wmap) |
| v3.8.35 | 25.04 | Silent-Re-Auth via Password eliminiert |
| v3.8.36 | 25.04 | 4 _authRetry-Gaps gewrappt |
| v3.8.37 | 25.04 | XSS-Härtung + _mapBody-Doku + Dead-Code |
| v3.8.38 | 25.04 | Juprowa-Push Response-Parse Observability |
| v3.8.39 | 25.04 | a11y alt-Attribute |

---

## DB-Schema-Änderungen

| Topic | Status |
|---|---|
| `whatsapp_templates` / `whatsapp_log` | 🟡 Schema + Seeds ready, Deploy pending |
| `photos` RLS | 🟡 Archiv, Status-Quo OK |
| bestehende Tabellen | ✅ unverändert |

**Nichts erforderlich** für v3.8.20-v3.8.39 Upgrade. Feature 12 WA ist separat.

---

## Silent-Re-Auth (WICHTIG für inaktive User)

Vorher (≤v3.8.34):
- Browser blieb via `epkolar_gc` (base64 creds) automatisch eingeloggt, auch wenn refresh_token starb.

Jetzt (≥v3.8.35):
- `epkolar_gc` wird nicht mehr gecached. Wenn refresh_token stirbt (default 7 Tage Supabase), muss User neu einloggen.

**Wen betrifft das?**
- Daily-User (Login mind. 1× pro Woche): **keine Änderung bemerkbar**.
- Kiosk-Tablets / wochenlang ungetoucht: **müssen neu einloggen**.
- Normaler Arbeitsalltag: transparent.

**Was tun?**
- **Nichts**, wenn UX-Friction akzeptabel ist.
- Alternativ: Refresh-Token-TTL in Supabase Dashboard von 7 auf 30 Tage erhöhen. **Keine Code-Änderung nötig**.

Details: `SILENT_REAUTH_STATUS.md`.

---

## User-Password-Änderungen

- `changePassword` API: jetzt mit klarer Message bei GoTrue-only Accounts (`"Dieser Account hat keinen lokalen Passwort-Hash — bitte Admin um Passwort-Reset bitten"`). Vorher silent fail als "Falsches Passwort".
- Offline-PW-Hash: PBKDF2-SHA256 statt base64. Alte User werden automatisch beim nächsten Online-Login migriert (kein Handlungsbedarf).

---

## Deploy-Sequenz

```
1. git pull   # holt v3.8.39 falls noch nicht local
2. GitHub Pages served automatisch nach Push
3. User öffnet App → Service Worker detected CACHE_NAME-Wechsel → Reload
4. User sieht "Neue Version verfügbar" Prompt → bestätigen
5. Fertig
```

Falls Service Worker hängt: DevTools → Application → Service Workers → "Update on reload" + "Unregister" + F5.

Details: `RUNBOOK.md` Abschnitt 2.

---

## Smoke-Tests nach Upgrade

Führe Checkliste in `sql/SMOKE_TESTS_v3.8.33.md` durch. Dort 17 Prüfungen für v3.8.33-Iter-19-Fixes, alle bleiben gültig für v3.8.39.

**Minimal-Smoke (5 min):**
1. Login als Admin → Dashboard lädt
2. `window.APP_VERSION` in Console = `"3.8.39-supabase"`
3. `window._selfTest({mode:"quick"})` grün (inkl. `epkolar_gc NICHT vorhanden` Regression-Check)
4. AS öffnen + speichern → Toast erscheint
5. Logout + Re-Login → keine fremden Daten in Cache

---

## Offene Sebastian-Tasks

### PAT-Rotation
Seit 2026-04-18 blockiert. Needs Sebastian aktiv im GitHub-UI.

### B-020 5-User-Smoke
`paschinger`, `barger`, `cracana`, `pinger`, `schmid` manuell einmal einloggen um B-020-Final-Closeout zu bestätigen.

### WhatsApp Schema-Deploy
Ready seit v3.8.32-Audit. `sql/WHATSAPP_SCHEMA_v3.8.sql` + `sql/WHATSAPP_SEEDS_v3.8.sql` im Supabase-SQL-Editor ausführen. Danach Feature-12-UI-Integration freischalten.

### Entscheidungen aus CODE_DEBT v2

- **QW6 COLORS-Namespace** (P3, 1-2 h) — wenn EP-Grün je feinjustiert werden soll.
- **L6 TABLES-Namespace** (P3, 2 h) — Typo-Prävention für 50+ Table-Namen.
- **G0 htmlFor/id Binding** (P2, 6-8 h) — a11y-Major-Verbesserung, 154 Labels.

---

## Was NICHT in diesen Upgrades enthalten ist

- Feature 12 WhatsApp-UI in index.html (Preview in `preview/whatsapp_ui_v0.html` ansehen, später mergen)
- Meta-API-Integration (Phase 2)
- sync_supplier Source ins Repo (bleibt im Supabase-Dashboard)
- Orphan-AS Migrations-Entscheidung

---

## Rollback

Falls etwas kritisch bricht:

```bash
git checkout v3.8.33
# oder
git revert v3.8.39
```

v3.8.33 ist der letzte Stand VOR allen Overnight-Cluster-Änderungen und stabil verifiziert. Details: `RUNBOOK.md` Abschnitt 9 "Rollback".
