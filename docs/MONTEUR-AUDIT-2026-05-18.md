# MONTEUR PERMISSION AUDIT — 2026-05-18

**Repo-HEAD:** `1d08865` v3.9.24 PUSHED
**Modus:** Code-Only-Audit (MCP-Blocker: Sebastian-PWs für `barger`/`riedmann` unbekannt; `planung@…/34kolar70` → "Benutzer nicht gefunden [B20-B]", `guenther/34kolar70` → "Benutzername und Passwort eingeben"; Chrome-Instabilität)
**Scope:** Frage 1 (v3.9.23/24-Gates wasserdicht?) · Frage 2 (welche Sites fehlen noch?) · Frage 3 (alle Subpages durchgehen)

---

## Permission-Gates v3.9.23/24 Review

### v3.9.23 (4 Sites)

| Site | Gate | Status |
|---|---|---|
| `HomeView._visibleAS` (L7999) | `_hvIsField ? arbeitsscheine.filter(a.monteur===_hvMid) : arbeitsscheine` | **WASSERDICHT.** Single-Source-of-Truth über `_visibleAS`. `asStats`, `dringendeAS`, `jupLinked` ziehen alle aus `_visibleAS`. Admin/PL/Büro ungebremst. |
| `HomeView` alerts → `dringendeAS` (L8040) | depends auf `_visibleAS` | OK (transitiv). |
| `VMang.ms` (L9661) | `_vmIsField ? _msRaw.filter(worker/zugewiesen/assignee===_vmMid \|\| melder==="Kunde") : _msRaw` | **WASSERDICHT** für Liste. **ABER**: Kundenmeldungen (`melder==="Kunde"`) sind absichtlich sichtbar — Monteur kann via `reviewAccept/reviewReject/reviewProgress/reviewDone` (L9726-9747) Kundenmeldungen ohne isAdmin-Gate bearbeiten. **Siehe Finding M1 unten.** |
| `VPlan.allTickets` (L10278) | `_vpIsField ? _allTicketsRaw.filter(t.assignee===_vpMid) : _allTicketsRaw` | **WASSERDICHT.** Filter scoped auf eigene Tickets. |
| ArbeitsscheinView (Liste, L5676) | `if(isMonteurRole&&!isAdmin&&a.monteur!==curUser.monteurId) return false;` | **WASSERDICHT.** Pre-existing seit früherem Sprint, v3.9.23 hat es nicht gebrochen. Kalender (L6056) ebenfalls gefiltert. |

### v3.9.24 (4 Sites)

| Site | Gate | Status |
|---|---|---|
| `ArbeitsscheinView.saveAs` (L5717) | `if(isMonteurRole&&!isAdmin&&form.monteur!==curUser.monteurId)` early-return + Toast | **WASSERDICHT.** Defense-in-Depth. Form-Select `monteur` ist disabled-forced für Monteure im Render. |
| `VMang.add` (L9716) | `_isMonteurAdd = _vmIsField&&!isAdmin`; force `_effWorker = _vmMid` | **WASSERDICHT.** UI-Select disabled (L9803), JS-Path forced. Bypass-Versuch via DevTools triggert Toast. |
| `VPlan.createTicket` (L10312) | `_isMtTicket ? _vpMid : (newTicket.assignee \|\| "")` early-return wenn mismatch | **WASSERDICHT** für **NEUE** Tickets. **ABER**: `TicketDetail.editing+saveEdit` (L9985, 9977) erlaubt **JEDEM** User (incl. Monteur), `ed.assignee` auf einen **anderen** Worker umzubiegen und `onUpdate` zu speichern. **Bypass-Pfad → Siehe Finding M2.** |
| `VDoku._canEditDoc` (L11093) | `_canEditDoc = !_vdIsField` gated alle 4 Schreib-Pfade (createFolder, deleteFolder, deleteDoc, moveDoc, uploadDoc) | **WASSERDICHT.** Doppel-Layer: Funktions-Gate + UI-Gate (Read-Only-Badge L11334). |

### Bypass-Pfade

| Pfad | Schwere |
|---|---|
| `TicketDetail` Edit-Form `ed.assignee` Reassign auf anderen Worker | **P1 — umgeht v3.9.24-Fix** |
| `TicketDetail` Status-Flow-Button (Storno/Erledigt) für Tickets die assigned-to-self sind = OK | P3 (per design) |
| `VMang.reviewAccept` Monteur weist Kundenmeldungen an dritte Worker zu | **P1** |
| `VMang.updSt` Status-Wechsel auf eigene Mängel | P3 (per design) |
| `VZeit.delEntry` Monteur darf JEDE Zeitbuchung auf einem Projekt löschen (`_canDelZ` inkl. `role==="monteur"` ohne Owner-Check) | **P1** |
| `VZeit.addEntry` Monteur kann Zeit für **anderen** Worker des Projekts buchen (`addModal` allWorkers-Select) | **P2** |

### Admin/PL/Büro-Pfade

Stichprobenartig geprüft — alle v3.9.23/24-Gates folgen `isMonteurRole&&!isAdmin`-Pattern oder `_xxIsField` (excl. `isAdmin`). Admin/PL bleibt ungebremst. Büro hat eigene Gates wo nötig (`canDo("as_create")` etc.). **GREEN.**

---

## NEUE FINDINGS pro View

| View | Issue | Severity | Fix-Sketch |
|---|---|---|---|
| **VZeit** (L9088) | `_canDelZ` lässt Monteur **jeden** Zeit-Entry auf einem Projekt löschen — kein Owner-Check | **P1** | `_canDelZ = isAdmin \|\| (curUser.role==="monteur"&&entry.worker===curUser.monteurId)` — pro-Entry statt global |
| **VZeit** addModal (L9154) | Monteur kann via `allWorkers`-Select Zeit für **anderen** Kollegen buchen wenn beide am Projekt sind | **P2** | `addWorker`-Select disabled für non-admin/PL → forced auf `curUser.monteurId` |
| **VZeit** addEntry (L9115) | Kein Gate, Monteur kann beliebige `addWorker` payload posten | **P2** | Defense-in-Depth: `if(!isAdminPL&&addWorker!==curUser.monteurId) return + Toast` |
| **VBautag** edit-button (L11659) | Edit-Pencil sichtbar für **alle** — Monteur kann Berichte anderer User editieren (delete ist isAdmin-only OK) | **P1** | Edit-Pencil gaten: `(isAdmin\|\|e.erstelltVon===(curUser.name\|\|curUser.username))` |
| **VBautag** saveEntry (L11514) | Update-Pfad keine Server-side-Mt-Check — Monteur kann jeden Eintrag PUT-en | **P2** | Gate analog Edit-Pencil im saveEntry-Body |
| **VCheck** del (L9572) | Monteur kann **jede** Checkliste auf Projekt löschen | **P2** | `del` gated auf `(isAdmin\|\|c.by===curUser.name)` + `setForms`-Map filtern |
| **VCheck** createCustom/createFromTemplate | Open für alle (per design — meist OK) | P3 | Optional Gate; aktuell akzeptabel |
| **VMang** updSt (L9723) | Monteur kann Status seiner sichtbaren Mängel ändern — inkl. Kundenmeldungen via reviewProgress/reviewDone | **P2** | `updSt` für `melder==="Kunde"` nur isAdmin\|\|isPL; eigene mängel OK |
| **VMang** reviewAccept/Reject (L9726, 9732) | Monteur kann Kundenmeldungen **angenommen/abgelehnt** markieren + an dritte Worker zuweisen | **P1** | Beide Funktionen guarden: `if(!isAdmin&&!isPL) return + Toast` |
| **TicketDetail** saveEdit (L9977) | Edit-Form erlaubt Monteur, `assignee` auf anderen Worker umzubiegen → umgeht v3.9.24 createTicket-Fix | **P1** | In `saveEdit`: `if(_vpIsField&&!isAdmin&&ed.assignee!==_vpMid){toast+return;}` ODER assignee-Select disabled für non-admin |
| **TicketDetail** Status-Flow-Button | Monteur kann eigene Tickets storno/erledigt setzen (per design OK), aber kann auch fremde Tickets sehen wenn nicht gefiltert | P3 | Tickets sind via `_allTicketsRaw.filter(assignee===_vpMid)` bereits gefiltert → P3 |
| **ArbeitsscheinView** storno (L5735) | Kein isAdmin-Gate. Monteur sieht nur eigene AS (gefiltert), kann eigene stornieren → semantisch OK (per design erlaubt) | P3 | Optional: `canDo("as_storno", curUser, a.monteur)` |
| **ProjList** | Filter für isFieldOnly auf `monteurProjekte[curUser.monteurId]` aktiv. Create/Edit/Archive/Delete sind isAdmin-only | OK | — |
| **VFotos** delPhoto (L10954) | isAdmin-gated. Upload für alle (per design — Monteur soll Fotos machen). | OK | — |
| **VMaterial** | tab="lager" gated auf isLager. Cart/Verlauf gefiltert (`isLager?orders:orders.filter(created_by===curUser.name)`, L12101). Order-actions (offen/in_bearbeitung) gated auf isLager. | OK | — |
| **VForm** (Regie/SF/DH/AH/Abn) | Erstellung+Edit+Print für alle erlaubt — Formulare sind Monteur-Tagesarbeit (per design) | OK | — |
| **FahrzeugView** | `visibleFz` filtert auf own (`f.fahrer===monteurId`) für non-isVAdmin. Helfer sieht nur eigenes. | OK | — |
| **WerkzeugView** | ROLE-Check: Werkzeug in `monteur.modules` NICHT enthalten, also Tab unsichtbar. Helfer hat `werkzeuge` — separates Audit nötig wenn Helfer-Use-Case live geht | OK für Monteur | — |
| **MitarbeiterView** | `mitarbeiter` nicht in ROLES.monteur.modules — Tab unsichtbar für Monteur. WorkerKompetenzen/Fahrtenbuch nur sichtbar wenn `editable=isAdmin\|\|curUser.monteurId===selM.id`. | OK | — |
| **ZeiterfassungView** | Worker-Selector admin-only (L5986). `_canDelEntry` Pre-Cond: selWorker===curUser.monteurId für Monteur. addEntry default selWorker=eigene monteurId. viewAll-Button isAdmin-only. | OK | — |
| **AbsView** | Names-List `(isAdmin?names:names.filter(n===myMonteurName))` an 3 Stellen (Kontingent compact, Kontingent expanded, Kalender). Tabs antraege/uebersicht/timeline isAdmin-only. Approve/Reject isAdmin-gated. delEntry isAdmin-gated. | OK | — |
| **AuswertungView** | Modul `auswertungen` nicht in monteur.modules — Tab unsichtbar | OK | — |
| **AdminPanel** | Modul `admin` via canDo("admin_panel") — nur admin oder rolle=Lagerleitung. setRole/delUser/setUserPerms/toggleActive/toggleLock alle isAdmin-gated. | OK | — |
| **VerbindungView** | Theme-Toggle, Telefonbuch — keine schreib-kritischen Aktionen für Monteur | OK | — |
| **StundenzettelView** | Modul `stunden` nicht in monteur.modules — Tab unsichtbar | OK | — |
| **WeekPlan** | Modul `wochenplanung` nicht in monteur.modules — Tab unsichtbar | OK | — |
| **VBer** (Project-Wochenbericht) | Read-only-Display alle Workers auf Projekt; Monteur kann sehen wer mitarbeitet | per design OK | — |

### Severity-Breakdown

- **P1: 5** (VZeit.delEntry · VBautag.edit · VMang.reviewAccept/Reject · TicketDetail.saveEdit Reassign · VMang.updSt für Kundenmeldungen)
- **P2: 4** (VZeit.addEntry-für-anderen · VBautag.saveEntry · VCheck.del · VMang.updSt scope)
- **P3: 4** (VCheck.create · TicketDetail Status-Flow · ArbeitsscheinView.storno · VBer Read-only)

**Total NEUE FINDINGS: 13** (5 P1 / 4 P2 / 4 P3)

---

## Sebastian-Actions

Nicht autonom fixbar — entweder weil Verhalten "by-design" ist und Geschäftsentscheidung braucht, oder weil destructive Side-Effects möglich:

1. **Entscheidung TicketDetail Edit-Form Assignee-Reassign:** Soll Monteur ein eigenes Ticket an einen Kollegen weiterreichen können? Wenn JA → kein Fix nötig. Wenn NEIN → Quick-Fix möglich (P1).
2. **Entscheidung VMang.reviewAccept/Reject für Kundenmeldungen:** Aktuell kann jeder Monteur Customer-Reports triagieren. Sebastian: Soll das ein PL/Admin-only-Workflow sein? Wahrscheinlich JA → Quick-Fix möglich (P1).
3. **Entscheidung VZeit.delEntry pro-Owner:** Soll Monteur fremde Zeitbuchungen löschen können? Wahrscheinlich NEIN → Quick-Fix möglich (P1).
4. **Entscheidung VBautag.edit pro-Owner:** Soll Monteur fremde Bautagebuch-Einträge editieren können? Wahrscheinlich NEIN → Quick-Fix möglich (P1).
5. **PW-Reset für `barger` + `riedmann`:** MCP-Test nicht möglich ohne diese PWs. Riedmann ist nicht in INIT_USERS (L2525-2534) — neu anzulegen?
6. **chef-Login PW:** `planung@ep-kolar.at/34kolar70` wird abgelehnt mit "Benutzer nicht gefunden [B20-B]" — entweder Username vs E-Mail-Login-Bug oder PW falsch. `guenther` username existiert (L2526).
7. **DB-Audit (PostgREST/Supabase):** Code-Gates verhindern UI-Bypass, aber jemand mit Service-Role-Key oder direkten REST-Calls könnte SQ.push-Payloads forgen. RLS-Policies sollten Server-side den `worker_id`/`assignee`-Match gegen `auth.uid()` durchsetzen. Nicht in diesem Audit-Scope (Code-Only).
8. **WerkzeugView Helfer-Audit:** Wenn Helfer-Use-Case aktiv wird (aktuell kein User in INIT_USERS hat `role==="helfer"`), eigenes Audit-Pass für `werkzeuge` Modul.

---

## MCP-Test Resume-Procedure (Next Session)

### Benötigt von Sebastian

- [ ] **PW für `barger@ep-kolar.at`** (`role=monteur`, `monteurId=w2`) — Test-User für Monteur-Gates
- [ ] **PW für `riedmann@…`** ← **Hinweis:** User existiert NICHT in INIT_USERS. Bitte klären: Riedmann = neuer User, der noch angelegt werden muss? Oder anderer Username? Falls neu: Username + Rolle + monteurId angeben
- [ ] **chef-Login bestätigen:** `guenther`/`<PW>` (NICHT planung@…). Aktuelle E-Mail-Login-Fehler "Benutzer nicht gefunden [B20-B]" untersuchen (E-Mail-Match-Logic in LoginScreen)
- [ ] **MCP-Chrome stabil:** Letzte Session hat Verbindungsabbrüche gehabt — ggf. `browser_close` + `browser_navigate` fresh start am Session-Beginn

### Test-Tour-Skript (sobald PWs vorhanden)

#### Test 1: Monteur Sicht — Hauptmenu
1. Login als `barger` (Monteur, w2)
2. Tab-Bar prüfen: Erwartet sichtbar = Home, Projekte, Arbeitsscheine, Zeiterfassung, Urlaub, Mängel, Pläne, Bautagebuch, Material. Erwartet UNSICHTBAR = Mitarbeiter, Auswertungen, Einstellungen, Stunden, Fahrzeuge, Werkzeuge, Admin, Büro-Export, Wochenplanung
3. URL-Hack-Versuch: Direkt `#fahrzeuge` → muss redirecten oder leeren Tab zeigen

#### Test 2: HomeView KPIs/Alerts
1. KPI "Offene AS" muss = Anzahl eigener AS (w2 als monteur-id)
2. "Dringende AS" alert nur eigene zählen
3. "Jup-Linked" nur eigene
4. Mein-Tag-Sektion zeigt korrekt myAsToday/myNextAs/myHoursWeek

#### Test 3: ArbeitsscheinView
1. Liste: nur AS mit `monteur=w2` sichtbar
2. AS anlegen: Monteur-Select disabled, forced auf "Barger Ian"
3. DevTools-Bypass-Versuch: `form.monteur=w1` setzen → Save → Toast "Keine Berechtigung"
4. Storno-Button auf eigene AS → erlaubt (per design)
5. Delete-Button auf eigene AS → NICHT sichtbar (isAdmin-only)

#### Test 4: VMang (Mängel auf Projekt)
1. Projekt öffnen mit Mängeln → Mängel-Tab
2. Liste zeigt nur worker=w2 ODER zugewiesen=w2 ODER assignee=w2 ODER melder=Kunde
3. Mangel anlegen: Verantwortlich-Select disabled, forced "Barger Ian"
4. Status-Wechsel auf eigenen Mangel → erlaubt
5. **Kundenmeldung sichtbar** (per design) — "Prüfen & Zuweisen" Button-Test: aktuell **NICHT gated** → Sebastian-Entscheidung **PENDING**
6. Lösch-Button (X) auf Mangel: NICHT sichtbar (isAdmin-only)

#### Test 5: VPlan (Pläne+Tickets)
1. Projekt-Pläne öffnen
2. Tickets-Liste zeigt nur assignee=w2
3. Ticket anlegen: assignee auto-set auf w2
4. **Bypass-Test: Existierendes Ticket öffnen → Edit-Button → assignee dropdown auf anderen Worker → Save** — aktuell **erlaubt** → Sebastian-Entscheidung **PENDING**

#### Test 6: VDoku
1. Projekt-Dokumente öffnen
2. "🔒 Nur Lesezugriff"-Badge sichtbar
3. Upload-Button NICHT sichtbar
4. Ordner-Edit-Pencils NICHT sichtbar
5. View + Download von Dokumenten OK

#### Test 7: VZeit (Zeit auf Projekt)
1. Zeit-Tab im Projekt
2. addModal öffnen via "+ Eintrag" auf Tag → Monteur-Select zeigt **mehrere Worker** (assigned) → **kann fremde Person wählen** → Save → Eintrag wird gepostet → **P2-Bug bestätigt**
3. delEntry auf Eintrag eines anderen Workers (auf gemeinsamem Projekt) → "X"-Button sichtbar → klicken → löschbar → **P1-Bug bestätigt**

#### Test 8: VBautag
1. Bautagebuch-Tab
2. Edit-Pencil auf fremdem Eintrag sichtbar → klicken → Edit-Form öffnen → Speichern OK → **P1-Bug bestätigt**
3. Delete-Button auf fremdem Eintrag NICHT sichtbar (isAdmin-only OK)

#### Test 9: VCheck
1. Checklisten-Tab
2. Lösch-X auf fremder Checkliste sichtbar → löschbar → **P2-Bug bestätigt**

#### Test 10: Zeiterfassung (Top-Level)
1. Tab "Zeiterfassung" öffnen
2. Worker-Select NICHT sichtbar (Span mit Eigenname stattdessen)
3. viewAll-Button NICHT sichtbar
4. Stunden eintragen für eigene Woche OK

#### Test 11: Urlaub
1. Tab "Urlaub" öffnen
2. Mitarbeiter-Liste oben zeigt NUR eigenen Namen
3. Tabs Anträge/Übersicht/Timeline NICHT sichtbar
4. Approve-Buttons NICHT sichtbar

---

## Quick-Fix-Optionen (Sebastian-Entscheidung benötigt)

Wenn Sebastian die folgenden Geschäftsentscheidungen bestätigt, sind die Fixes <30 min jeweils:

- ☐ **Fix-A:** VZeit.delEntry pro-Owner-Gate (P1, 5 LoC) — "Monteur darf nur eigene Zeitbuchungen auf Projekt löschen"
- ☐ **Fix-B:** VBautag edit-pencil pro-Owner-Gate (P1, 3 LoC) — "Monteur darf nur eigene Bautag-Einträge editieren"
- ☐ **Fix-C:** TicketDetail.saveEdit Assignee-Lock für Field-Roles (P1, 5 LoC) — "Monteur darf bestehende Tickets nicht an Kollegen umverteilen"
- ☐ **Fix-D:** VMang.reviewAccept/Reject isAdmin/PL-only (P1, 4 LoC) — "Kundenmeldungen-Triage ist PL-Aufgabe, nicht Monteur"
- ☐ **Fix-E:** VZeit.addModal Worker-Select für Field-Roles disabled (P2, 4 LoC) — "Monteur bucht Zeit nur für sich selbst"

**Bei OK von Sebastian:** Bundle als v3.9.25 → commit → push + tag.

---

**Audit beendet:** 2026-05-18 (Claude Opus 4.7 1M-Kontext)
