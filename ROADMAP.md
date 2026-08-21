# EPKolar · ROADMAP

Status der Features und Backlog. Keine Release-Dates — nur Prio + Zustand.

---

## 🎯 STRATEGISCHE RICHTUNG · Mehr PlanRadar (sauber & einfach)

**Leitprinzip (Sebastian, 21.08.2026): PlanRadar-Funktionalität soll schrittweise
immer stärker in die App — aber sauber und für den User einfach.** Nicht Feature-Fülle,
sondern jeder Schritt so, dass ein Monteur/Bauleiter ihn **ohne Schulung** bedient
(Mangel-Pin setzen → zuweisen → Foto dran → fertig = **ein Fluss**, keine Formularwüste).
Jeder neue Schritt: rein additiv, bestehende Bedienung nicht verändern.

**Ist-Stand — die PlanRadar-Kernschleife existiert bereits (kein Greenfield):**
Plan → Pin → Ticket/Mangel → Status/Foto/Frist → PDF. Belegt im Code:
- Plan-Viewer mit Pan/Zoom/Pinch/Multi-Page-PDF (`PlanViewerCanvas` ~16460, pdf.js-Cache ~4030).
- **Pins an Plan-Koordinate** (x/y in %), Tap platziert, Drag verschiebt (`handleCanvasClick` ~16622, `PlanCanvasPinMarker` ~16398), stabile Pin-Nr (`_ticketNr` ~17017).
- **Mängel als eigene draggbare Pins** am Plan (`_defectPins` ~17016, in `tickets` gemerged ~17111).
- Ticket-Objekt: Status-Workflow, Prio, Frist, Fortschritt, **Kommentar-Journal** (`TicketDetail` ~16295), Status-Historie (jsonb, v3.9.463).
- **Polymorphe Foto-Queue** an Entität gebunden, GPS+Kompression+Offline (`captureAndQueue` ~3259).
- **Einzel-Ticket-PDF** mit Plan-Ausschnitt + eingezeichnetem Pin (`_genTicketPdf` ~16256), Mängel-Snag-Liste (`genMangelPdf` ~15820).
- Bulk-Status/-Zuweisung (v3.9.464), reifer Offline-Sync (`SQ`/`doSync` ~8180).
- Vorgeschichte/Details: `docs/handoff/STAND-2026-06-18-PLANRADAR.md` (Block A/B/C).

**Nächste Schritte (priorisiert nach Hebel/Aufwand — alle bauen auf Vorhandenem auf):**

| # | Schritt | Warum / Hebel | Aufbauen auf | Größe |
|---|---|---|---|---|
| **①** | ~~**Plan-Gesamtreport-PDF**~~ ✅ **GELIEFERT v3.9.828** — Button „📄 Plan-Report" im Plan-Viewer (admin/PL/buero): Gesamtplan je Seite + alle nummerierten Pins (Farbe=Status) + Legendentabelle. Funktion `_genPlanReportPdf`. | *Bester Hebel — erledigt.* | (gebaut auf `_tkRenderPdfPage`/`_tkLoadImg`/`_pdfStr`/`TICKET_STATUS`) | ✅ |
| **②** | ~~**Defect-Pins am Plan editierbar**~~ ✅ **GELIEFERT v3.9.829** — Klick auf Mängel-Pin öffnet QuickEditPin (Status/Zuständig/Frist/Prio), schreibt kanonische `defects`-Felder, Status→MANGEL_ST rückgemappt. | *UX-Naht geschlossen.* | `QuickEditPin` +`statusOptions`/`hideJournal`, `_mapDefect` | ✅ |
| **③** | **Formular-/Checklisten-Builder** mit typisierten Feldern (Zahl/Messwert/Dropdown/Datum/Unterschrift) + serverseitige Vorlagen | Heute nur Text+Checkbox aus **hartcodierten** `CL_TEMPLATES` (~15610). | `VCheck` (~15618) + `checklists`-Tabelle; Item-Schema um `type`/`options`, Vorlagen in eigene Tabelle | mittel–groß |
| **④** | **Externe Zuweisung an Subunternehmer** (eigener Zugang + Benachrichtigung) | Assignee heute nur interne `monteure` (~16332). | Kunden-Portal + `kundeStatus`-Spiegel (~15884) als Vorbild; Notifications (~8035) vorhanden, E-Mail an Externe fehlt | groß (Entität/Auth/RLS/Portal) |

**① + ② sind geliefert (v3.9.828 / v3.9.829).** **Nächster Schritt: ③** — Formular-/Checklisten-Builder
mit typisierten Feldern + serverseitigen Vorlagen. **Achtung: braucht eine Design-Entscheidung**
(welche Feldtypen, Vorlagen-Schema `checklist_templates` = **DDL → Human-Run-Gate/Sebastian**) und ist
mittel–groß — kein reiner Additiv-Schritt wie ①/②. Restlücken laut 18.06.-Doku: Plan-Versionierung +
Pin-Migration (größter Aufwand), Fälligkeits-/Eskalations-Automatik, Mengen/Aufmaß auf Plan.

*(Zeilennummern sind Näherungswerte Stand v3.9.826 — vor dem Bau die Funktion per Name greppen.)*

---

## ✅ DONE

| # | Feature | Verfügbar ab | Notiz |
|---|---|---|---|
| 1 | **Arbeitsscheine (AS)** | v2.x | CRUD, Status-Workflow, OFFA-Export, FinkZeit-Print |
| 2 | **Projekte** | v2.x | Projekt-Ampel, Material-Warenkorb |
| 3 | **Zeiterfassung** | v3.x | Eintrag + Timer + Monats-Report, 40h→38,5h in v3.6.1 |
| 4 | **Fahrzeuge + Fahrtenbuch** | v3.x | KM-Log + Kraftstoff, mobile-first |
| 5 | **Werkzeuge + Wartung** | v3.5 | Inventar, Termine |
| 6 | **Dokumente + Pläne** | v3.x | Upload-Queue, Folder-Struktur |
| 7 | **Mängel + Bautagebuch** | v3.5 | Foto-Capture, Position-Tagging |
| 8 | **Abwesenheit/Urlaub** | v3.6 | Kontingent, Approvals |
| 9 | **Material-Bestellung** | v3.6 | Katalog-Import (DATANORM), Gewerk-Filter (v3.8.26) |
| 10 | **Juprowa-Sync** | v3.7 | RPC fetch/push, Passport-Rotation |
| 11 | **Audit-Log UI** | v3.8.22 | 17 Action-Filter, Entity-Filter |
| — | **B-020 Login-Reliability** | v3.8.3 | ✅ CLOSED (9× verifiziert), monteur_id Konsistenz, RPC login_lookup |
| — | **B-006 + B-007 RLS** | v3.5.94 | ✅ CLOSED, 4 Helpers + 22 Policies live-verified |
| — | **B-017/B-021/B-022** | v3.5/3.8 | ✅ CLOSED, Window-Exposures / Silent-ReAuth / Stale-Closures |
| — | **Overnight-Bug-Hunt-Loop** | v3.8.1-3.8.18 | 18 Iter, 2 User-Stops, alle gefixt |
| — | **Silent-Catch-Observability** | v3.8.28-3.8.31 | 13 kritische Stellen → Console-Breadcrumbs |
| — | **Offline-PW-Hash PBKDF2** | v3.8.33 | M-4 Security-P2 closed, Legacy-Grace-Migration |

---

## 🟡 PENDING (Schema/Code ready, Deploy oder Integration ausstehend)

### Feature 12 · WhatsApp-Benachrichtigungen

- ✅ Schema `sql/WHATSAPP_SCHEMA_v3.8.sql` (inkl. 24.04-Audit-Fix: UNIQUE(name), PL-Read-Policy, P3-Diagnose)
- ✅ Seeds `sql/WHATSAPP_SEEDS_v3.8.sql` (4 Default-Templates)
- ✅ UI-Preview `preview/whatsapp_ui_v0.html` (Overnight Block B, 2026-04-24)
- ⏳ Deploy Schema + Seeds (Sebastian manuell im Supabase-SQL-Editor)
- ⏳ UI-Integration in `index.html` (nach Deploy, 2-3h eigene Session)
- ⏳ Meta-API-Phase-2 (Edge Function + Webhook + pg_cron) — separate Session

### Schema + SQL Ops

- ⏳ **PHOTOS_RLS deployen** (2 Files in `_archiv/sql/PHOTOS_RLS_*.sql`: AUDIT + FIX, Status-Quo seit 19.04 bestätigt laut `_archiv/sql/README.md` "B-021 Status Quo") — oder Migration-Variante aktivieren
- ⏳ **RLS-Reconcile v3.8** (`sql/RLS_RECONCILE_v3.8.md` + `sql/RLS_SNAPSHOT_v3.8.sql`) — Soll/Ist-Vergleich laufen lassen
- ⏳ **Index-Deploy** falls Perf-Bedarf (aktuell <130 ms → konservativ skippen)
- ⏳ **sync_supplier Edge-Function-Source** ins Repo (aktuell nur im Dashboard)

### B-020 Final-Closeout

- ⏳ **5-User-Smoke** (paschinger, barger, cracana, pinger, schmid) — Browser-Test-Run
- ⏳ PAT-Rotation (2× Platzhalter geschickt, echter Token fehlt)

---

## 🔵 BACKLOG (Priorisiert, kein Commit)

### P1 · Security / Reliability

- **M-4 Offline-PW bcrypt-Migration** — ✅ DONE v3.8.33 (PBKDF2)
- **L6366 juprowa_update_passport Auth-Retry** (P2, `sql/_authretry_gaps.md`)
- **L6365 juprowa_get_config Auth-Retry** (P2)
- **Opt-out für WhatsApp-Log** — wenn Phase 2 kommt
- **Log-Retention-Policy** (6 Monate DSGVO) — Daily-Delete-Job

### P2 · UX / Features

- **I1 canDo admin_panel vs isLager** (`sql/CANDO_MATRIX.md`) — klären ob PL Admin-Panel sehen soll
- **I5 isOwn-Mehrdeutig** (monteurId|name|id → UUID-only?)
- **Mobile-UX-Hit-List** aus `window._mobileCheck()` iPhone-Output
- **Auto-Save in AS-Editor** (aktuell manuell, Monteur-Frustration)
- **Kalender-View für AS** (Zeitleiste statt nur Liste)

### P3 · Code-Quality

- **I3 canDo isField entflechten** (OM/Tech/Mont ungranular)
- **L3954 bautagebuch-schema-check Auth-Retry** (P3)
- **L4031 workers-sync-probe Auth-Retry** (P3)
- **Bulk-supplier-articles changePassword-Fallback** für GoTrue-only Users (Teil-fixed v3.8.33a — Error-Message verbessert, volle GoTrue-Reauth ausstehend)
- **Dead-Code-Review** (Block D generiert `sql/DEAD_CODE_CANDIDATES.md`)

### P4 · Architecture / Long-term

- **Bundle-Step erwägen** — derzeit Single-File 16k Zeilen, Refactor in Modul-Struktur wäre Release v4.0
- **Offline-Conflict-Resolution** — was bei 2 User schreiben dasselbe AS offline?
- **Disaster-Recovery-Plan** dokumentieren
- **Test-Suite auf Live-Integration erweitern** (Playwright? tavern? — Architektur-Entscheidung)

---

## 🔴 OPEN INCIDENTS / Bekannte Lücken (kein offener Ticket, nur Merkposten)

- `sync_supplier/`-Source fehlt im Repo (nur Doku)
- PAT-Blocker seit 2026-04-18 (GitHub-Push via CC geht nicht ohne Token-Rotation; Sebastian pushed manuell)
- `_mapBody TEXT_JSON_FIELDS` Whitelist (L1312) ohne erklärte Herkunft
- ARCHITECTURE.md in Repo-Root vs `sql/ARCHITECTURE.md` — die alte Version im sql/ löschen oder refactoren (siehe ARCHITECTURE.md Notiz)

---

## Version-Chronik (letzte 10 Tags)

| Tag | Datum | Highlight |
|---|---|---|
| v3.8.33 | 2026-04-23 spät | changePassword + PBKDF2 + SMOKE_TESTS |
| v3.8.32 | 2026-04-23 Nacht | Session-Final Breadcrumbs + HANDOFF |
| v3.8.31 | 2026-04-23 Nacht | Kpi-Stagger Final-Sweep |
| v3.8.30 | 2026-04-23 Nacht | Silent-Catch Teil 2 + Kpi-Stagger |
| v3.8.29 | 2026-04-23 Nacht | App-Header Last-Sync-Indikator |
| v3.8.28 | 2026-04-23 Nacht | Motto + Kpi-Stagger-Infra + EP-Spinner |
| v3.8.27 | 2026-04-23 Nacht | Empty-State-Polish |
| v3.8.26 | 2026-04-23 Nacht | Gewerk-Profil + Material-Filter |
| v3.8.25 | 2026-04-23 Nacht | _juprowaSyncing try/finally + Emoji-Rotation |
| v3.8.24 | 2026-04-23 Nacht | sql-Archive-Pass (16 Files) |

Vor-v3.8.20 siehe Git-Log + `_archiv/sql/HANDOFF_*`.

---

## Entscheidungen die Sebastian treffen muss

1. **Feature-12 Go/No-Go**: Preview ansehen, UI-Integration beauftragen oder pausen.
2. **CODE_DEBT Priorisierung**: Nach Block-D-Lauf (`sql/CODE_DEBT.md`).
3. **I1 Admin-Panel-Zugang** für Projektleiter.
4. **PHOTOS_RLS**: Status-Quo bestätigen oder Migrations-Variante.
5. **PAT-Rotation**: irgendwann diese Woche bitte.
