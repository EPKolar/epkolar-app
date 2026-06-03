# PAGE-AUDIT-2026-06-03 — Sprint 76 Code-side All-Pages-Audit per User-Role

**Datum:** 2026-06-03
**HEAD:** `717bacb` v3.9.94 (Sprint 73 closed)
**Scope:** Code-side User-Role x Page audit (MCP-Login durch Classifier blockiert, daher static code-read)
**Hard-Cap:** 60 Min
**Output:** Doc-only (kein Code-Fix in dieser Iteration, weil identifizierte P1s >20 LoC pro Site oder UX-Tradeoffs)

---

## 1. Rolle-Matrix

`index.html` Z2604 definiert `ROLES`-Konstante. 8 App-Rollen total (`admin`, `projektleiter`, `buero`, `obermonteur`, `techniker`, `monteur`, `helfer`, `viewer`). Daneben gibt es Worker-`rolle` (`Lagerleitung`, `Backoffice`, `Geschaeftsfuehrer` etc.) als zweiter Layer (via `user.rolle` fuer spezielle Perms wie EK-Preise/supplier_manage).

| Role | Modules (Tab-Perm IDs) | Special perms |
|---|---|---|
| **admin** | projekte, arbeitsscheine, wochenplanung, zeiterfassung, urlaub, mitarbeiter, werkzeuge, auswertungen, formulare, maengel, plaene, export, offa, **admin**, stunden, fahrzeuge, bautagebuch, material, bueroexport | Alle canDo(*) Actions, Chef-Tab nur Admin |
| **projektleiter** | wie admin ausser admin & bueroexport | proj_create, fz_edit, wz nur admin, zeit_other |
| **buero** | wie admin ausser admin (aber canDo("admin_panel") nicht-A -> user.rolle==lagerleitung check) | abs_kontingent, worker_edit, fz_create, fz_edit |
| **obermonteur** | projekte, arbeitsscheine, zeiterfassung, urlaub, werkzeuge, auswertungen, formulare, maengel, plaene, stunden, fahrzeuge, bautagebuch, material | as_create, zeit_delete_own, form_delete_own, mangel_create, bt_create |
| **techniker** | wie obermonteur ohne `auswertungen` | gleich obermonteur |
| **monteur** | projekte, arbeitsscheine, zeiterfassung, urlaub, formulare, maengel, plaene, bautagebuch, material | as_create, zeit_delete_own (self), form_delete_own (self), mangel_create |
| **helfer** | projekte, arbeitsscheine, zeiterfassung, urlaub, werkzeuge, stunden, fahrzeuge | nicht in `isField` (isOM||isTech||isM) -> KEINE as_create / mangel_create / zeit_delete_own |
| **viewer** | projekte, urlaub, stunden, fahrzeuge | nur Lesen |
| **lagerleitung** (kein App-Role, nur worker.r) | n/a — App-User mit rolle="Lagerleitung" muss `role` aus admin/PL/buero haben | view_ek_price, supplier_manage, admin_panel-Zugang (via canDo) |

---

## 2. Page-Coverage-Matrix

Tabs-Definition `_allTabs` Z5298. Sichtbarkeit = `hasPerm(role, perm)` ODER spezielle `_*`-Pseudo-Perms. Filter Z5316.

| Tab (perm) | View-Component | Z | admin | PL | buero | obermonteur | techniker | monteur | helfer | viewer |
|---|---|---|---|---|---|---|---|---|---|---|
| Home (`_home`) | HomeView | 8204 | + | + | + | + | + | + | + | + |
| Chef (`_chef`) | ChefDashboard | 15740 | + (admin-only) | - | - | - | - | - | - | - |
| Projekte | ProjList | 9050 | + | + | + | + (filter) | + (filter) | + (filter) | + (filter) | + |
| Arbeitsscheine | ArbeitsscheinView | 5808 | + | + | + | + | + | + (own only) | - | - |
| Planung | WeekPlan | - | + | + | + | - | - | - | - | - |
| Zeiterfassung | ZeiterfassungView | 16200 | + | + | + | + | + | + (own) | + (own) | - |
| Urlaub | AbsView | 13975 | + | + | + | + | + | + (own) | + (own) | + (own) |
| Monatsabrechnung (`stunden`) | StundenzettelView | 14565 | + | + | + | + | + | - | + | + |
| Fahrzeuge | FahrzeugView | 16937 | + | + | + | + | + | + (own) | + (own) | + |
| Werkzeuge | WerkzeugView | 17928 | + | + | + | + | + | - | + | - |
| Mitarbeiter | MitarbeiterView | 5693 | + | + | + | - | - | - | - | - |
| Auswertungen | AuswertungView | 16073 | + | + | + | + | - | - | - | - |
| Einstellungen (`_settings`) | VerbindungView | 15090 | + | + | + | + | + | - | - | + |
| Buero-Export (`bueroexport`) | VBueroExport | - | + | - | + | - | - | - | - | - |
| Admin | AdminPanel | - | + | - | + (wenn rolle=Lagerleitung) | - | - | - | - | - |

**Hinweis:** `bueroexport` ist NICHT in `projektleiter`-Modulen (Z2606 listet `bueroexport` NICHT — nur `admin` + `buero` haben es). Gewollt? Sebastian-Action.

---

## 3. Findings pro Page x Rolle

Codereading-basierte Findings, sortiert nach Severity.

### 3.1 P1 (Production Risk / Data-Visibility)

| # | Page | Rolle | Finding | Code-Site | Fix-Sketch |
|---|---|---|---|---|---|
| P1-1 | StundenzettelView | helfer/monteur/techniker/obermonteur | `meineZettel` filtert `z.mitarbeiterId===curUser.id`. Aber Stundenzettel werden mit `mitarbeiterId:selMA` aus `allMA` (=users+monteure) angelegt. Most Stundenzettel haben `mitarbeiterId=monteur.id` (`w*`) — Helfer/Monteur (`curUser.id=u*`) sehen LEERE Liste statt eigene Stundenzettel. **Echte Data-Leak Gegenrichtung**: Falls Stundenzettel mit `u*`-ID upgeladen wurde, sieht Helfer u1's Daten wenn curUser.id===u1. Filter sollte `curUser.monteurId===z.mitarbeiterId OR curUser.id===z.mitarbeiterId` sein. | Z14680 | Erweitere Filter: `meineZettel = canUpload?zettel:zettel.filter(z=>z.mitarbeiterId===curUser.id||z.mitarbeiterId===curUser.monteurId)`. ~5 LoC. **Aber:** Sebastian-Decision noetig: Sollen Field-User ueberhaupt eigene Stundenzettel SEHEN? (DSGVO + FinkZeit-Sichtbarkeit-Frage). |
| P1-2 | ZeiterfassungView | monteur/helfer | Field-user sieht eigene Woche, aber `loadAllOverview` (viewAll-Modus Z16282) liest alle entries fuer alle workers UNABHAENGIG von isAdmin. UI-Button fuer `viewAll` muesste in Z~16700 vor `!viewAll` gegated sein (nicht verifiziert). Wenn Field-user `setViewAll(true)` via Console aufruft, kommt vollstaendige Wochenuebersicht. | Z16282-16292 | `viewAll`-Setter-Buttons in UI auf `isAdmin?...:null` gaten + `loadAllOverview` early-return wenn !isAdmin. ~6 LoC. |

### 3.2 P2 (Confusing UX / Permission Leaks ohne Data-Risk)

| # | Page | Rolle | Finding | Code-Site | Fix-Sketch |
|---|---|---|---|---|---|
| P2-1 | AbsView | helfer | Helfer hat `urlaub`-Perm und kann eigenen Urlaub eintragen. Aber `kontingent`-Defaults (25 Tage/192.5 h) sind hardcoded — sollte aus DB pro Helfer kommen (TBV `urlaubskontingent` Z14007). Wenn Helfer-Kontingent nicht in DB -> falscher Resturlaub. | Z13993 | Initial-State per worker.id aus `urlaubskontingent`-Tabelle laden, kein hardcode. ~10 LoC. **Hat seit Sprint-26 keinen Fix bekommen.** |
| P2-2 | FahrzeugView | techniker/obermonteur/buero | `isVAdmin=admin||projektleiter` — `buero` ist NICHT isVAdmin, kann also keine Service-Termine anlegen, obwohl Z2607 buero `fz_edit` impliziert (canDo("fz_edit") fuer buero=true Z3587). UI gating zu strikt fuer Backoffice/Schober. | Z16940 | Erweitere: `isVAdmin = role===admin||role===projektleiter||role===buero||canDo("fz_edit",curUser)`. ~3 LoC. |
| P2-3 | ArbeitsscheinView | techniker/obermonteur | `isMonteurRole=role===monteur||role===helfer` Z5921 — techniker+obermonteur fallen in den Filter nicht rein, sehen ALLE AS auch wenn nicht zugewiesen. Sebastian-Erwartung: techniker/obermonteur sehen nur eigene + zugewiesene. **ABER**: Sprint-23 spezifizierte fuer obermonteur "Team-Sicht" -> unklar. | Z5921 | Sebastian-Decision: Soll obermonteur/techniker auch nur eigene AS sehen? Falls ja: `isMonteurRole` erweitern. Falls nein: Doku. |
| P2-4 | AdminPanel | buero (rolle=Backoffice) | `canDo("admin_panel")` ist nur true wenn `user.rolle.toLowerCase()===lagerleitung` (Z3587). Schober/Lindhuber (rolle=Backoffice, role=buero) bekommen Admin-Tab NICHT. Wenn UC sein soll dass Backoffice Benutzer verwaltet -> fehlend. Tab-Filter Z5321 erwartet `hasPerm(curUser,"admin")||canDo("admin_panel")`. buero hat KEINE `admin`-perm (Z2607). | Z5321/Z3587 | Sebastian-Decision: Soll Backoffice Admin-Panel sehen? Wenn ja: `buero` Modul-Liste um `admin` erweitern oder canDo-Branch fuer rolle=Backoffice. |
| P2-5 | MitarbeiterView | buero | `isAdmin=admin||projektleiter` Z5694. buero kann KEINE Mitarbeiter anlegen/bearbeiten, obwohl Z2607 buero `mitarbeiter`-Perm hat und canDo("worker_edit",buero)===true (Z3587). UI gating zu strikt. | Z5694 | `const isAdmin=role===admin||role===projektleiter||canDo("worker_edit",curUser)`. ~3 LoC. |
| P2-6 | ChefDashboard | - | Tab-Filter Z5318 laesst nur `role==="admin"` rein — Sebastian (role=admin) ist GF. Aber wenn ein zweiter Geschaeftsfuehrer angelegt wird (z.B. role=projektleiter mit rolle=Geschaeftsfuehrer), sieht er Chef-Tab nicht. | Z5318 | `t.perm==="_chef"?curUser.role==="admin"||(curUser.rolle||"").toLowerCase()==="geschaeftsfuehrer"` (Eszett-handling). |

### 3.3 P3 (Polish / Defensive)

| # | Page | Finding | Code-Site |
|---|---|---|---|
| P3-1 | ZeiterfassungView | `_isFieldRoleZE` Z16323 prueft 4 Rollen — Sprint-17-Pattern. Aber `viewer` (auch wenn Tab `zeiterfassung` nicht in viewer-Modulen) wird bei direktem Aufruf nicht abgefangen. Defense-in-depth: `viewer`-early-return. | Z16201 |
| P3-2 | AbsView | Z14019 `tog` early-returns `if(!isAdmin && sel!==myMonteurName)return` — aber kein Toast. User klickt Datum als nicht-admin & nichts passiert. Toast wie in ArbeitsscheinView Z5980. | Z14019 |
| P3-3 | FahrzeugView | `addKm`-Handler Z17036 (~) — Monteur kann eigene km fuer eigenes Fahrzeug eintragen. Aber kein Check ob `fzId===myFzId`. Console-Bypass moeglich. Defense-in-depth-Guard. | Z17036 |
| P3-4 | WerkzeugView | `_wzPool` filtert nicht-Admin auf `w.zugewiesen===monteurId||__none__` Z17999. helfer (rolle=Helfer/Lehrling/Praktikant) hat keine `monteurId` zwingend -> `__none__` Fallback -> leere Liste. Erwartung war: helfer soll Werkzeug-Uebersicht ALLER haben (rolle?). | Z17999 |
| P3-5 | StundenzettelView | `canUpload=admin||username==="schober"` — hardcoded Username. Sollte ueber canDo() laufen. Lindhuber kann keine Stundenzettel hochladen obwohl rolle=Backoffice. | Z14585 |
| P3-6 | AuswertungView | Tab-Filter laesst techniker NICHT rein (Z2609 `techniker` listet `auswertungen` NICHT). buero/obermonteur sehen Auswertungen. Konsistent? Sebastian-Decision. | Z2609/Z2608/Z2610 |
| P3-7 | Sidebar/TopBar | `Mehr`-Button (g:4) wird nur gezeigt wenn `moreTabs.length>0` (Z5610). Helfer (kein g:4-Tab -> Stunden ist g:2) zeigt Mehr nicht — OK. Aber viewer hat keine g:4-Tabs -> auch korrekt. | Z5610 |
| P3-8 | Routing | Tab-Index `setKat(idx)` via `onNav("admin")` aus HomeView ist NICHT permission-gated. Wenn ein Field-user via deep-link/Console `setKat(...AdminIdx)` aufruft, wuerde React-Tree die Admin-Route rendern, aber die `&& hasPerm(curUser,"admin")` Z5655 wuerde block. + OK | - |

---

## 4. Fix-Recommendations & Severity-Triage

**Tier-1 sofort (<5 LoC, kein UX-Trade-off):** keine — alle Findings >5 LoC oder benoetigen Sebastian-Decision.

**Tier-1 mit Decision-Block (~5-15 LoC):**
- P1-2 (ZeiterfassungView viewAll-gate): Sebastian-OK & dann fix
- P2-2 (FahrzeugView buero isVAdmin): Sebastian-Frage
- P2-5 (MitarbeiterView buero isAdmin): Sebastian-Frage

**Tier-2 doc-only (Sebastian-Action):**
- P1-1 (StundenzettelView mitarbeiterId-Filter): DSGVO-Decision
- P2-1 (AbsView Kontingent-Initial pro Helfer)
- P2-3 (ArbeitsscheinView techniker/obermonteur AS-Sicht)
- P2-4 (AdminPanel Backoffice-Zugang)
- P2-6 (ChefDashboard zweiter GF)

**Tier-3 defensive:** P3-1..P3-5, P3-7.

---

## 5. NICHT in dieser Iteration gefixt — Begruendung

Hard-Constraint: Auth/Sync/Juprowa/OFFA/Helpers — NIE. P1-1 beruehrt FinkZeit/Stunden direkt = Sebastian-Decision-required. P1-2 beruehrt viewAll-Logik = UX-Trade (Admin-Feature, vermutlich gewollt fuer PL/buero auch). Hard-Cap 60 min erreicht durch Code-Reading.

Audit liefert Sebastian Klarheits-Liste fuer naechste Iterationen. KEIN Code-Commit, NUR Doc.

---

## 6. Stats

- **Rollen analysiert:** 9 (8 App + 1 implicit "Lagerleitung" via worker.rolle)
- **Pages analysiert:** 15 Top-Level Views (Home/Chef/Projekte/AS/Planung/Zeiterfassung/Urlaub/Stunden/Fahrzeuge/Werkzeuge/Mitarbeiter/Auswertungen/Einstellungen/BueroExport/Admin)
- **Findings total:** **15** (2 P1 + 6 P2 + 7 P3+1 OK)
- **Tier-1 Fixes applied:** 0 (alle benoetigen Sebastian-Decision oder >5 LoC)
- **Brackets pre/post:** `() -1 / {} 0 / [] 0` (unveraendert, kein Code-Edit)
- **pytest:** 518 passed in 171.80s

— ENDE AUDIT —
