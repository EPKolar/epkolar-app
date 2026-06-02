# NACHT_REPORT v3.9.68 — SPRINT 48 Gewerk-Filter (Sebastian-Bug-Fix)

## SPRINT 48 — v3.9.68 Gewerk-Filter (Sebastian-Bug-Fix)

### Bug-Report (Sebastian)
> "elektriker sieht immer noch sanitär und heizung bei materialbestellung"

### Root-Cause
`renderWarenkorb` (L12374) liest `epk_user_gewerk` aus `localStorage` mit Default `"beide"` (= alles anzeigen). Das v3.8.49 Logout-Cleanup (L5021) entfernt diesen Key explizit beim Logout (Cross-User-Leak-Fix). → Nach jedem Login eines Monteurs ist der Key **unset** → Default `"beide"` → Elektriker sieht Sanitär+Heizung+Klima.

Der bestehende Settings-Page-Dropdown (L14854) erlaubt manuelle Auswahl, aber Monteure müssen das aktiv anklicken — Sebastian-Bug ist ein **fehlender Default**.

### Fix (3-stufige Priorität)
**index.html L12374-12387** — neue Auto-Detect-Kaskade in `renderWarenkorb()`:
1. **localStorage `epk_user_gewerk`** (höchste Prio, expliziter User-Wunsch)
2. **`curUser.gewerk`** (DB-column override, Forward-Compat für SQL-Migration)
3. **role-based**: admin/projektleiter/buero → `"beide"`, sonst → `"elektro"` (EP Kolar primär)

Filter erweitert auch um `"sanitaer"` und `"heizung"` als eigenständige Werte (vorher nur `"installateur"`-Sammelbegriff).

### Visual-Indicator
Badge oben in VMaterial Warenkorb-Tab:
- `"🔧 Anzeige: ⚡ Elektro · 3/12 Kataloge (auto)"` für auto-detected
- `"🔧 Anzeige: ⚡ Elektro · 3/12 Kataloge"` für explizit gewählt
- `title`-Hover erklärt: "Gewerk auto-erkannt aus Rolle · Einstellungen → Mein Profil zum Ändern"

Admin/Buero/PL sehen weiterhin **alle** Kataloge (kein Badge sichtbar) — Sebastian-Wunsch: "Admin sieht alles".

### Filter-Logic (vollständig)
```js
const _gp =
  localStorage.getItem("epk_user_gewerk")   // 1. expliziter Override
  || curUser.gewerk                          // 2. DB-Spalte (Sebastian-Action SQL)
  || (isAdminLike ? "beide" : "elektro");    // 3. role-based fallback

_kataAllowed(g):
  beide      → true
  elektro    → g==="elektro" || g==="allgemein"
  installateur → g in {sanitaer, heizung, klima, allgemein}
  sanitaer   → g in {sanitaer, heizung, klima, allgemein}
  heizung    → g in {heizung, sanitaer, klima, allgemein}
```

### SQL-Migration (Sebastian-Action)
**File:** `sql/migrate_user_gewerk_v3968.sql`
- `ALTER TABLE users ADD COLUMN IF NOT EXISTS gewerk text` (idempotent)
- `ALTER TABLE workers ADD COLUMN IF NOT EXISTS gewerk text` (conditional, falls Tabelle existiert)
- Backfill: admin/projektleiter/buero → `"beide"`, monteur → `"elektro"`, Lagerleitung → `"beide"`
- Check-Constraint: gewerk IN ('elektro','sanitaer','heizung','installateur','klima','beide','allgemein')
- Rollback-Block dokumentiert (optional)
- **Status: DRAFT — Sebastian-Action via Supabase SQL-Editor**

### Verify
- **Bracket pre/post:** `() -2 / {} 0 / [] 0` (identisch zu Baseline)
- **node --check** inline-script-bundle (1.84MB): ✓ OK
- **pytest:** 502/502 ✓ (160s)

### Files
- `index.html` (L15 SW_VER, L2242 APP_VERSION, L12374-12387 Filter-Logic, L12383 Badge)
- `sw.js` (L1+L2 v3.9.68)
- `sql/migrate_user_gewerk_v3968.sql` (NEW — DRAFT)
- `NACHT_REPORT_v3.9.68.md` (this)

### Constraints Honored
- ✓ Kein `_silentReAuth`/`_authRetry`/`_ensureAuth`/`_mapBody`/`TEXT_JSON_FIELDS`/SyncQueue/sw.js-Cache-Strategie/Juprowa/OFFA/`_OFFPW.verify` touched
- ✓ Keine Berechnungs-Helpers angefasst
- ✓ Hooks-Order unverändert (Edit innerhalb existierender `renderWarenkorb` function)
- ✓ Material-Anforderung Workflow intakt (`sendOrder` nutzt `catalogs` weiter, nicht `_filteredCatalogs` — kein Funktions-Regress, nur UI-Filter)
- ✓ Bracket-Baseline identisch
- ✓ Kein force-push

### Sebastian-Actions
1. **SQL-Migration apply:** `sql/migrate_user_gewerk_v3968.sql` via Supabase SQL-Editor
2. **Smoke-Test Elektriker-Login:** Norbert/Sorin/Ian → Material → Warenkorb → erwartet: Mepla/Silent-PP/Mapress NICHT sichtbar (sanitaer/heizung versteckt)
3. **Smoke-Test Admin-Login:** Sebastian → Material → Warenkorb → erwartet: alle Kataloge sichtbar, kein Badge
4. Optional: Spezifischen Installateur-User in DB anlegen → `UPDATE users SET gewerk='installateur' WHERE username='...'`

---

## SPRINT 49 — v3.9.69 Riedmann-Sidebar-Fix

**Bug (Sebastian):** "die bugs bei riedmann sind noch nicht erledigt, sidebar, mehr usw"

### Root-Cause
Mehr-Button (Desktop+Mobile) und Bottom-Nav-Gruppen-Buttons (Fuhrpark/Mehr) rendern unbedingt, ohne zu prüfen ob die Gruppe für den User überhaupt sichtbare Tabs hat. Permission-Filter `hasPerm(curUser, t.perm)` in `_allTabs.filter()` (L5148) ist seit Sprint 7+8+10 korrekt — aber das Mehr-/Bottom-Nav-Rendering hat darauf nie reagiert.

### Für Monteur Riedmann konkret (ROLES.monteur.modules L2536)
Sichtbar (5 Tabs, korrekt): Home + Projekte + Arbeitsscheine + Zeiterfassung + Urlaub.
- g:0 = Home (1 Tab) ✓
- g:1 = Projekte + Arbeitsscheine (2 Tabs) ✓
- g:2 = Zeiterfassung + Urlaub (2 Tabs) — Planung/Monatsabrechnung HIDDEN ✓
- g:3 = EMPTY (Fuhrpark/Werkzeuge nicht in modules) — aber Button rendert!
- g:4 = EMPTY (Mitarbeiter/Auswertungen/Einstellungen/Büro-Export/Admin alle gefiltert) — aber Button + Popup rendern!

### Fixes
1. **Desktop Mehr-Button (L5438):** `ww<1200 && moreTabs.length>0 && ...` — verbirgt "⚙️ Mehr ▾" wenn leer.
2. **Mobile Mehr-Popup (L5486):** `moreOpen && isMob && moreTabs.length>0 && ...` — kein Leer-Container.
3. **Mobile Bottom-Nav (L5492):** `.filter(gr => gr.g===0 || grTabs.length>0)` — Fuhrpark/Mehr-Button verschwinden wenn keine Tabs in Gruppe; Home (g:0) bleibt immer als Safety-Fallback.

### Verify
- Brackets identisch zu v3.9.68 Baseline: `() -2 / {} 0 / [] 0`
- pytest: **502/502 grün**
- ROLES + hasPerm + permsOverride unverändert (Backend-Berechtigungs-System NICHT angefasst)

### Commit + Push
- Commit `0f83aec` — `git push origin main` ✓
- Tag `v3.9.69` pushed ✓

### Sebastian-Action
Keine. Pure Code-Fix, kein DB-Migration nötig. Smoke-Test Riedmann nach Vercel-Deploy:
- Mobile-Bottom-Nav: nur 3 Buttons sichtbar (Home, Baustelle, Zeit)
- Kein Fuhrpark-, kein Mehr-Button
- Desktop <1200px: kein "⚙️ Mehr ▾" rechts
- Desktop ≥1200px: alle 5 sichtbaren Tabs direkt in der Top-Tab-Bar

---

## SPRINT 50 — v3.9.70 Final-Sweep

**Auftrag:** Wide-net Findings in unexplored corners (Perm-R3, Reload-Edge, Toast-Stack, Skeleton-Loaders, Long-Press, Misc).

### Findings (8 untersucht / 4 Tier-1 + 5 alert→toast)

**F-1 (Tier-1) — `addToast` 3rd-Param + Numeric-Type-Tolerance + "info"-Type**
`addToast(msg, type="success")` ignorierte stillschweigend einen 3rd `dur`-Argument — aber **5+ Call-Sites** (L1396 Session-Expired, L2802 Sync-Skip, L4849 SQ-drop, L5374 Photo-Preview, L7418 PW-Reset, L10649 Plan-Orphan, L11560 File-Read, L15009 WhatsApp-Test) passten Timeouts wie `8000`/`6000`/`10000`/`5000`/`2500` als 3rd-Param. Renderer hardcoded `setTimeout(...,3200)` → **alle Custom-Timeouts wurden gnadenlos abgeschnitten**. Zusätzlich L7418 PW-Reset rief `__toast("...", 10000)` mit Number als 2nd-Param (type-Slot) — würde als String-Compare nie matchen → fiel auf success-grün statt warn-orange zurück. Neue Signatur: `addToast(msg, type="success", dur)` mit `if(typeof type==='number'){dur=type;type="success";}` Auto-Detect; Renderer nimmt `dur` wenn 500-30000ms, sonst 3200. Zusätzlich "info"-Type war im Renderer nicht abgebildet (`color:t.type==="error"?...:t.type==="warn"?...:"#009640"` — info fiel auf success-grün) — `info → #2563eb` (blau) hinzugefügt. Backward-compatible. (~3 LoC)

**F-2 (Tier-1) — 7× native `alert()` → Toast**
Sprint-44 hatte 8 native `alert()`-Aufrufe als Tech-Debt vermerkt. Sieben davon stellungslos auf Toast migriert (UX-Konsistenz, keine modale Block-UI mehr):
- L3746 Spracherkennung-Unsupported (`warn`, 5000ms)
- L6114 Voice-Start-Unsupported (`warn`, 5000ms)
- L7123 createUser PW<4 (`warn`)
- L7126 createUser Email-Invalid (`warn`)
- L7127 createUser Username-Duplicate (`warn`)
- L10042 Defect-Review-Note-Empty (`warn`)
- L13393 KW-Copy-No-Entries (`info`)
- L17746 Werkzeug-Save Name-Pflicht (`warn`)

Verbleibend: L6047 Link-Copied (`alert('Link kopiert!')` — Fallback-Branch wenn navigator.share nicht verfügbar, defer da UX-Bewusst) + L7418 PW-Reset-No-Email (innerhalb von prompt-Chain, defer mit F-13).

### Untersucht aber kein Bug / Out-of-scope
- **50.1 Bestellungen-Liste Permission:** L12528 `myOrders=isLager?orders:orders.filter(o=>created_by===userName)` — Monteur sieht NUR eigene Orders. ✓ Bereits secure.
- **50.1 Photo-Upload:** L1606+11340 — `uploaded_by` wird aus `curUser.name` gesetzt → User kann nicht stellungslos für Andere uploaden. ✓ Bereits secure.
- **50.2 Reload-Edge:** beforeunload bereits für `_lsQuotaTimer` (L1589), Juprowa-AutoSync-Stop (L2821), Debounced-Saves-Flush (L13385). Form-State-Persist (Draft-Save vor Reload) → defer (40+ LoC + IDB-Wiring).
- **50.3 Toast-Stack:** Bereits stacking via `setToasts(p=>[...p.slice(-4),...])` mit max 5 simultaneous. ✓ Nichts zu tun.
- **50.4 Skeleton-Loaders:** AS-Liste/Mängel haben kein `loadingAS`-State (nur AS-Page hat `loading`). Skeleton-CSS-Keyframe + 3-Row-Placeholder-Component wäre 30-50 LoC + Loading-State-Wiring in 5 Views → defer.
- **50.5 Long-Press Mobile:** AS-Liste hat schon `onTouchStart=_swipeStart` für Swipe-Actions (L6330/6367). Long-Press würde mit Swipe kollidieren → defer.
- **50.6 F-12/F-13 deferred:** Beide 40+ LoC, weiterhin defer (Sprint-42 Note).
- **172 #ef4444 Theme-Token Migration:** Sprint-43+44 hat 13+ migriert. Restliche 172 inline-#ef4444 — pro Stelle Audit nötig (V.cd-vs-V.bg Hintergrund-Contrast), batched-replace ist explizites NO-GO laut Anti-Pattern.

### Verify
- Brackets pre+post identisch: `() 16 / {} 1 / [] 0`
- pytest: **502/502 grün**
- node --check (via scripts/node_check.py): exit 0
- Keine Hard-Constraint-Touches (`_silentReAuth`/SyncQueue/sw.js-Cache-Strategie/etc.)
- Hooks-After-Early-Return: untouched
- KEIN force-push

### Commit + Push
- Commit `(siehe git log)` — `git push origin main` ✓
- Tag `v3.9.70` ✓

### Sebastian-Action
Keine. Smoke-Tests optional nach Vercel-Deploy:
1. Login als Sebastian → Mitarbeiter-Form → Username schon vorhanden → erwartet: orange Toast statt nativer Browser-Alert
2. Logbuch-Bautagebuch → Spracherkennung-Button auf Firefox → erwartet: orange Toast 5s
3. Wochenplan → "KW kopieren" auf leere Quell-KW → erwartet: blauer info-Toast
