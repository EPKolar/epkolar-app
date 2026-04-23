# EPKolar · RUNBOOK

Operational Recipes. Was Sebastian (oder Claude Code / Chrome-MCP) wann ausführt.

---

## 1 · Version-Bump

**Wann:** Nach jeder Code-Änderung in `index.html` oder `sw.js`, die deployed werden soll.
**Warum:** Ohne Bump invalidiert der Service Worker den Cache nicht → User bleibt auf alter Version.

```bash
# 1. Entscheidung: Patch / Minor / Major
#    Beispiel: v3.8.33 -> v3.8.34 (Patch)

# 2. Exakt 2 Stellen ändern:
#    - index.html L~1916:  const APP_VERSION="<NEW>-supabase"
#    - sw.js L1:           // EP Kolar Service Worker v<NEW>
#    - sw.js L2:           const CACHE_NAME = "epkolar-v<NEW>"

# 3. Verify
node sql/_check_version.js
# Erwartet: ✓ versions synced: <NEW>

# 4. Bracket-Check (falls index.html geändert)
node sql/_check_brackets.js
# Erwartet: () -2 {} 0 [] 0

# 5. Syntax-Check (falls index.html geändert)
node sql/_check_syntax.js
# Erwartet: syntax OK

# 6. Commit + Tag
git add index.html sw.js
git commit -m "v<NEW> <Beschreibung>"
git tag v<NEW>
git push origin main --tags
```

---

## 2 · Deploy (GitHub Pages)

Automatisch beim Push auf `main`. Pages baut nichts — es serviert `index.html` direkt aus dem Repo-Root.

**Cache-Busting:**
- Hauptmechanismus ist der Service Worker mit `CACHE_NAME`-Wechsel.
- Beim nächsten Load fetcht der SW die neue `CACHE_NAME`, löscht die alte, holt `index.html` + `sw.js` neu.
- Erzwingen (falls SW hängt): DevTools → Application → Service Workers → "Update on reload" + "Unregister" → F5.

**Sanity-Check nach Deploy:**
```
DevTools → Console:
  window.APP_VERSION          // sollte NEW sein
  navigator.serviceWorker.getRegistrations().then(r => console.log(r[0].active.scriptURL))
```

---

## 3 · Häufige Fehler & Fixes

### 3.1 · Auth 401 Spam in Console

**Symptom:** `[auth] 401` oder "Silent Re-Auth failed".
**Ursachen:**
- `_authToken` abgelaufen ODER Refresh-Token ungültig
- GoTrue und `public.users.password_hash` auseinander (B-020-ähnlich)

**Fix:**
1. User-side: Logout + Login → neuer Token, neuer Refresh
2. Console: `window._forceExpireToken()` + `window._silentReAuth(user, pw)` simulieren → reproduzieren
3. Admin: `_a11yCheck`/`_selfTest({mode:"security"})` zeigt Current-Role/Token-State

### 3.2 · Syntax-Error "Unexpected token" in Chrome

**Symptom:** App startet nicht, weißer Screen, Console-Fehler bei bestimmter Zeile.
**Ursache:** Zuletzt gespeicherter `index.html`-Edit hat unbalancierte Klammern oder Tippfehler.

**Fix:**
```bash
node sql/_check_brackets.js           # sollte () -2 {} 0 [] 0
node sql/_check_syntax.js             # sollte "syntax OK"
git diff HEAD~1 -- index.html         # letzten Edit inspizieren
git revert <bad-commit>               # im Zweifel zurück
```

### 3.3 · Bracket-Baseline drift (`() -2 {} 0 [] 0`)

**Warum -2?** Historisch: 2 JSX-ähnliche Template-Strings enthalten unbalancierte `(`.
Das ist der Baseline-Wert, NICHT Null.

**Wenn abweichend:**
- **`()` ≠ -2**: Entweder Klammer fehlt oder hinzugefügt wurde. Suche via Diff.
- **`{}` ≠ 0 oder `[]` ≠ 0**: echter Bug.

**Fix:** Last commit reverten, Edit neu machen, re-checken.

### 3.4 · IndexedDB-Migration stuck

**Symptom:** "DB blocked by other tab", Toast "App in anderem Tab offen".
**Ursache:** Anderes Tab hat noch die alte `DB_VER` offen.

**Fix:**
1. Andere Tabs der App schließen
2. F5 (reload) im aktuellen Tab
3. Falls stubborn: DevTools → Application → IndexedDB → `epkolar_offline` → Delete DB → F5

### 3.5 · SyncQueue wächst ohne Flush

**Symptom:** `window.SQ.count()` >>0, trotz Online.
**Ursache:** `_authToken` fehlt oder fetch-Target timeouts.

**Fix:**
```
Console:
  window._syncDiag()          // Queue-Inhalt + Last-Error
  await window.__doSync()     // manueller Trigger
```

Wenn Queue weiterhin wächst: siehe 3.1 (Auth) und `sql/_authretry_gaps.md` (4 bekannte Graceful-Degradation-Lücken).

### 3.6 · Photos-Upload bleibt queued

**Symptom:** `window.PhotoQ.count()` >>0, Sync läuft aber Fotos bleiben.
**Ursache (historisch, gefixt in v3.8.15):** `_sbUploadFile` war nicht `_authRetry`-gewrappt.

**Verify:** `grep -n "_sbUploadFile" index.html` → sollte innerhalb `_authRetry(...)` sein.

---

## 4 · SQL-Deploy Workflow

```
1. SQL-File in sql/ anlegen oder editieren (IF NOT EXISTS + DROP/CREATE POLICY).
2. Review: sql/DEPLOY_SQL_REVIEW_2026-04-23.md konsultieren falls ähnliches Thema.
3. Supabase Dashboard → SQL Editor → File-Inhalt einfügen → RUN.
4. Verify-Query am Ende des Files (meistens SELECT count, rowsecurity etc.).
5. Falls idempotent: nochmal laufen lassen ändert nichts, safe.
6. Commit SQL-File mit klarem Namen (zB "WHATSAPP_P3_TYPECHECK.sql").
```

**Alternativ über Node-Runner** (wenn DB_URL gesetzt):
```
export SUPABASE_DB_URL="postgres://postgres.<ref>:<pw>@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
node sql/sql-runner.mjs
```

**NIEMALS:**
- `DROP TABLE` ohne Backup
- RLS `DISABLE` auf Live-Table (höchstens lokal testen)
- Policies ohne `IF EXISTS`-Guard droppen (bricht Re-Runs)

---

## 5 · Edge-Function-Deploy (sync_supplier)

Siehe `sql/DEPLOY_sync_supplier_v3.md`. Kurzform:

```
supabase login            # CLI-Auth (einmalig)
supabase functions deploy sync_supplier --project-ref jiggujpruejkaomgxarp
```

**Source ist NICHT im Repo** — liegt im Supabase-Dashboard. TODO: in Repo migrieren.

---

## 6 · Chrome-MCP-Fallback (wenn CC fehlt)

Wenn Claude Code nicht erreichbar und Sebastian einen Bug fixen muss:

1. Chrome-MCP-Skripte in `_archiv/sql/` (alle archivierten Browser-Automationen) anschauen — Pattern für DOM-Interaktion.
2. `window._selfTest({mode:"full"})` im Browser → JSON-Output für Diagnose.
3. Quick-Fixes direkt in `index.html` editieren (VSCode/Notepad++) → Bracket-Check + Syntax-Check manuell laufen lassen.
4. Push von lokal ohne CC: `git add/commit/push` standard.

**Bei mehreren Files zeitgleich bearbeiten:** Immer `node sql/_check_syntax.js` nach JEDER Änderung.

---

## 7 · Smoke-Tests nach Deploy

Aktuelle Checkliste: `sql/SMOKE_TESTS_v3.8.33.md` — 17 Prüfungen für v3.8.33 Iter-19-Fixes. Pro Release aktualisieren.

Minimal-Smoke (immer):
1. Login als Admin → Dashboard lädt
2. Version-Check: `window.APP_VERSION` matcht Tag
3. `window._selfTest({mode:"quick"})` grün
4. AS-Liste lädt, 1 AS öffnen + wieder schließen
5. Logout + Re-Login → keine fremden Daten

---

## 8 · Disaster-Recovery

**Supabase-Backup:** Pro-Plan macht automatische Daily-Backups (7 Tage Retention). Restore via Dashboard → Database → Backups.

**Git-Backup:** Repo ist auf GitHub — Clone-lokale-Kopie auf Sebastian's NAS empfohlen (ist das der Fall? TODO prüfen).

**App-Repo-Korrupt:** `git reset --hard origin/main` — letzter stabiler Push ist immer die "gute" Baseline.

**Index.html komplett kaputt:** `git revert HEAD` → push. Dann diagnostizieren.

---

## 9 · Rollback eines Deploys

```
# Last-known-good Tag identifizieren
git tag -l | tail -5

# Rollback
git revert <bad-sha>..HEAD          # erzeugt Revert-Commits (safer als reset)
# ODER hart (nur wenn niemand gepulled):
git reset --hard <good-tag>
git push --force-with-lease         # NUR wenn wirklich nötig, R2 warnt davor

# Version-Bump: Revert braucht eigenen Version (z.B. v3.8.34 -> v3.8.34-hotfix)
# damit SW-Cache den Rollback sieht.
```

---

## 10 · Secrets-Handling

- **SUPABASE_KEY** (anon key, in `index.html` L334): public JWT, okay im Client, da Row-Level-Security schützt.
- **SUPABASE_DB_URL** (Pooler-Connect-String mit Passwort): NUR in `.env` lokal, nie committen (`.gitignore` blocked).
- **Meta API Access Token** (für Feature-12 Phase 2): NUR in Edge-Function ENV, niemals im Client.
- **PAT für GitHub-Pushes:** User-spezifisch, rotierbar. Siehe HANDOFF_SESSION_2026-04-23.md — rotation pending per 24.04.
