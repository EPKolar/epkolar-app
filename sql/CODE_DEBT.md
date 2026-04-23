# Code Debt Inventory · 2026-04-24

**Scope:** `index.html`.
**Methoden:**
- `grep -nE '(TODO|FIXME|HACK|XXX)' index.html`
- Manual analysis (bemerkte Muster beim Block-A-D-Lauf)

## Harter TODO/FIXME/HACK-Grep

```
TODO   → 0 Treffer
FIXME  → 0 Treffer
HACK   → 0 Treffer (ausser "XXX" Literale in IBAN-BIC und mock-JWT-Strings)
```

Der Code ist erstaunlich frei von Inline-Markern. Das bedeutet nicht, dass es keine
Schulden gibt — sie sind nur nicht als TODO markiert. Die folgenden Items wurden
durch Block-A-D-Audits + Session-Reviews entdeckt.

## Quick Wins (< 30 min Fix)

### QW1 · `epkolar_gc` nicht im Logout-Cleanup
- **Wo:** `index.html` L4306 (logout-Handler)
- **Problem:** base64(email)+base64(password) bleibt im localStorage nach Logout
- **Fix:** 2 `localStorage.removeItem()`-Calls in bestehenden try-Block einfügen
- **Prio:** P2 (siehe LOCALSTORAGE_AUDIT.md)

### QW2 · `epkolar_juprowa_wmap` user-Cleanup
- **Wo:** `index.html` L4306
- **Problem:** Juprowa-Mapping vorigen Users sichtbar bei nächstem Login
- **Fix:** `localStorage.removeItem('epkolar_juprowa_wmap')` in Cleanup-Liste
- **Prio:** P3

### QW3 · Error-Overlay textContent statt innerHTML
- **Wo:** L307, L1941
- **Problem:** `innerHTML = static + String(msg)` rendert HTML wenn msg manipulierbar
- **Fix:** Message-Teil via `createElement('div')` + `.textContent`
- **Prio:** P3 (siehe XSS_AUDIT.md)

### QW4 · Doppelte Token-Keys konsolidieren
- **Wo:** `epkolar_auth`, `epkolar_token`, `epkolar_refresh`
- **Problem:** `{at,rt,exp}` liegt in 1 Key; `at` und `rt` zusätzlich in separaten Keys dupliziert (Legacy)
- **Fix:** Leser umstellen auf `epkolar_auth` only, dann `epkolar_token` + `epkolar_refresh` in Write-Pfad entfernen
- **Prio:** P4 (kein Bug, nur Entropie)

### QW5 · `_n()` Sweep Nachziehen
- **Wo:** `fahrten`-Liste L14031 (guarded by >0) + GeoAPI L7237 (safe)
- **Problem:** Konsistenz (optional)
- **Prio:** P4

## Larger (1-2 h)

### L1 · `epkolar_gc` PBKDF2-Migration
- **Motivation:** base64 ist reversibel = Klartext
- **Plan:** Analog `_OFFPW` (v3.8.33 Iter-19c) mit Salt + 100k Iter PBKDF2
- **Aufwand:** Migration + Grace-Period (Legacy-Verify beim nächsten Login)
- **Prio:** P2

### L2 · 4 `_authRetry`-Gaps (siehe `_authretry_gaps.md`)
- L6366 juprowa_update_passport (P2 Admin-Write)
- L6365 juprowa_get_config (P2 UX)
- L3954 bautagebuch-schema-check (P3)
- L4031 workers-sync-probe (P3)
- **Aufwand:** 15 min pro Site + Testing

### L3 · `_mapBody TEXT_JSON_FIELDS` dokumentieren
- **Wo:** L1312
- **Problem:** Whitelist `['perms_override','tank_log','km_log','tags','config','order_items']` ohne Erklärung
- **Fix:** Inline-Comment mit Herkunft + Regel "wann ist ein Feld TEXT_JSON vs. echtes JSONB"
- **Prio:** P3

### L4 · 7 Dead-Code-Kandidaten aufräumen (siehe `DEAD_CODE_CANDIDATES.md`)
- ESKALATION_RULES, INIT_AS, INIT_WZ, LazyImg, MATERIAL_UNITS, SCHEINART_C, SCHEINSTATUS_C
- **Aufwand:** jeweils kurz verifizieren (manuell), dann löschen oder mit Kommentar markieren
- **Prio:** P3

### L5 · canDo `isField`-Granularität
- **Wo:** L3009-3010
- **Problem:** OM/Tech/Mont bundled via `isField`, keine Rechte-Differenzierung
- **Fix-Aufwand:** Wenn Business-Case besteht (z. B. "nur OM darf AS eröffnen"), dann eigene Flags
- **Prio:** P3 (warten auf Business-Anforderung)

## Architecture-Level (Diskussion nötig)

### A1 · Inactivity-Logout
- **Problem:** Token bleibt aktiv, wenn User das Fenster offen lässt
- **Vorschlag:** nach 8 h Inactivity: Logout-Prompt
- **Komplexität:** Session-Store + Visibility-API-Integration + User-Flow

### A2 · Offline-Conflict-Resolution
- **Problem:** Wenn 2 User denselben AS offline editieren → Sync-Queue
  nimmt First-Writer-Wins
- **Vorschlag:** Last-Writer-Wins mit Merge-Notification, ODER PessimisticLock via `locked_by`/`locked_until`
- **Komplexität:** Schema-Migration + UI-Conflict-Modal + Merge-Algorithmus

### A3 · Bundle-Schritt einführen
- **Problem:** Single-File 16 k Zeilen macht Edits riskanter (jeder Edit kann die ganze App zerstören)
- **Vorschlag:** Rollup/esbuild mit Module-Struktur → `index.html` bleibt als Shell
- **Komplexität:** Groß (Refactor-Phase, eigene Release v4.0)

### A4 · Test-Suite auf Live-Integration erweitern
- **Aktueller Stand:** Python static (33 Tests)
- **Vorschlag:** Playwright für User-Flow-Smoke (Login → AS-Create → Logout)
- **Komplexität:** Neue Dev-Dependency, Headless Chrome, neue CI

### A5 · `SCHEINART_C` / `SCHEINSTATUS_C` Migrations-Check
- **Problem:** Konstanten definiert, aber Code nutzt raw-Strings (`'aufgenommen'`)
- **Vorschlag A:** Code auf Konstanten umstellen → Type-Safety via Tooling
- **Vorschlag B:** Konstanten löschen (ehrlich zur aktuellen Realität)
- **Komplexität:** A ist groß (hunderte Callsites), B klein

## Priorisierungs-Empfehlung

**Diese Woche (wenn Zeit):**
- QW1 + QW2 (15 min, schließt zwei Leaks)

**Nächste Session (2-3 h):**
- L1 (epkolar_gc PBKDF2) + L2 (4 Auth-Retry-Gaps)

**Mittel-Term (Projekt-Tag):**
- L4 Dead-Code + L3 Doku + A1 Inactivity-Logout

**Release v4.0:**
- A3 Bundle-Schritt + A5 Konstanten-Konsolidierung
