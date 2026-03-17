# HANDOFF v3.3.3 — EPKolar Dynamic Monteure & DB Fixes

## Aktueller Stand (17.03.2026)

**App:** EPKolar v3.3.3-supabase — Baustellenmanagement PWA  
**Live:** https://epkolar.github.io/epkolar-app/  
**Repo:** https://github.com/EPKolar/epkolar-app  
**Supabase:** jiggujpruejkaomgxarp.supabase.co (eu-west-2, MICRO) — **PRO-Version**  
**Entwickler:** Sebastian Günther (Admin-User: admin, Worker-ID: w6)

---

## v3.3.3 Änderungen

### Fix 1: `moveDoc` — POST→PUT (Zeile 5947)
**Problem:** Beim Verschieben eines Dokuments in einen anderen Ordner wurde `POST` (INSERT) statt `PUT` (UPDATE) gesendet → Duplicate-Key-Error in Supabase, Dokument wurde nicht verschoben.  
**Fix:** `method:"PUT"`, Body nur `{folder_id: folderId}` statt vollem Objekt.

### Fix 2: MONT hardcoded → dynamische `monteure` Prop (26+ Stellen)
**Problem:** In vielen Projekt-Subviews und Hauptviews wurde der hartcodierte `MONT`-Array (Initialdaten) statt der dynamischen `monteure`-State verwendet. Wenn ein Monteur hinzugefügt/geändert/gelöscht wurde, zeigten diese Views die alten Daten.

**Betroffene Komponenten (alle gefixt):**

| Komponente | Fix | Stellen |
|------------|-----|---------|
| **VDash** | Signature + MONT.find → (monteure\|\|MONT).find | 1 |
| **VExport** | Signature + 3x MONT.find → (monteure\|\|MONT).find | 3 |
| **VMang** | Signature + MONT.find/map in Dropdowns, Lookups, Review | 4 |
| **VOffa** | Signature + ASC Export Worker-Lookup | 1 |
| **VPlan** | Signature + Ticket-Zuordnung, Tabelle, Export, Dropdowns | 6 |
| **TicketDetail** | Signature + Assignee-Lookup, Dropdown | 3 |
| **AdminPanel** | Signature + Monteur-Zuordnung Dropdown | 1 |
| **FahrzeugView** | Fahrer-Dropdown, Fahrer-Lookup, XLS Export, QR Scan | 5 |
| **HomeView** | Arbeitsschein-Kalender + Karte Worker-Lookup | 2 |
| **ProjectShell** | Monteur-Dropdown | 1 |
| **Kundenportal** | Techniker-Anzeige bei Mängeln | 2 |

**Alle `MONT.find` und `MONT.map` sind eliminiert** — durchgängig `(monteure||MONT).find/map` mit Fallback auf Initialdaten für Offline-Szenarien.

**Prop-Threading:**
```
App → ProjectShell (monteure ✅ existierte)
    → VDash       (monteure ✅ NEU)
    → VExport     (monteure ✅ NEU)
    → VMang       (monteure ✅ NEU)
    → VOffa       (monteure ✅ NEU)
    → VPlan       (monteure ✅ NEU)
        → TicketDetail (monteure ✅ NEU)
App → AdminPanel  (monteure ✅ NEU)
App → FahrzeugView (monteure ✅ existierte, Refs gefixt)
```

### Fix 3: Delta-PUT statt Voll-Objekt (3 Stellen)
**Problem:** `archiveP` und Fortschritt-Slider sendeten `{...p, status:"archiv"}` bzw. `{...p, fortschritt:v}` — das gesamte Projekt-Objekt inklusive Frontend-Feldern, geparster Arrays etc.  
**Fix:**
- `archiveP`: Body nur `{status:"archiv"}`
- Fortschritt-Slider (onMouseUp + onTouchEnd): Body nur `{fortschritt:v}`

---

## Vollständiger Test-Report (17.03.2026)

### Verifikation
- ✅ Bracket-Balance: `() delta=-2` (Baseline unverändert)
- ✅ MONT.find: 0 verbleibend (war 20+)
- ✅ MONT.map: 0 verbleibend (war 5+)
- ✅ Alle 7 Komponenten-Signaturen mit `monteure`
- ✅ moveDoc: PUT mit Delta-Body
- ✅ archiveP: Delta-Body
- ✅ Fortschritt-Slider: Delta-Body
- ✅ SW_VER: `epkolar-v3.3.3`

### DB — Supabase (unverändert)
| Tabelle | Rows | Status |
|---------|------|--------|
| projects | 8 | ✅ |
| workers | 7 | ✅ |
| users | 7 | ✅ |
| fahrzeuge | 20 | ✅ |
| werkzeuge | 298 | ✅ |
| arbeitsscheine | 10 | ✅ |
| notifications | 304+ | ✅ |
| checklists | 3 | ✅ |
| project_documents | 1 | ✅ |
| time_entries | 1 | ✅ |
| weekplans | 1 | ✅ |
| project_folders | 1 | ✅ |
| absences/defects/photos/plans/forms/tickets | 0 | ✅ (leer) |

---

## Basis-Features (unverändert aus v3.3.2)

### Permissions & Rollen (aus v3.3.2)
- Hauptnavigation per `hasPerm()` gefiltert
- ProjectShell-Sidebar per `hasPerm()` gefiltert
- Login liefert `permsOverride`
- Auto-Refresh synct `permsOverride`
- Rollenwechsel resettet `permsOverride`
- Spotlight berechtigungsbasiert

### Self-Heal + Boot-Indicator (aus v3.3.1-fix1)
- SW_VER Check → auto Cache-Clear + Reload
- Boot-Indicator + CDN-Check + 12s Watchdog

### Auto-Save (aus v3.3.1)
- Wochenplanung + Stundenzettel automatisch

### Browser-Zurück (aus v3.3.1)
- History API: pushState / popstate

### Tätigkeit durchgängig (aus v3.3.1)
- In allen 4 Exporten + Stundenzettel-Karten

---

## Technische Details

- **Version:** `3.3.3-supabase`
- **Bracket-Baseline:** `() delta=-2` (unverändert seit v3.3.0)
- **Zeilenzahl:** ~9535
- **SW Cache:** `epkolar-v3.3.3`
- **Self-Heal:** `localStorage.epk_sw_ver = 'epkolar-v3.3.3'`

## Architektur
- **Frontend:** Single HTML (~9535 Zeilen), React 18 createElement, keine Build-Tools
- **Backend:** Supabase (jiggujpruejkaomgxarp.supabase.co), PostgREST API
- **Hosting:** GitHub Pages (epkolar.github.io/epkolar-app)
- **Offline:** IndexedDB (SyncQueue → _translateAndExec → Supabase REST)
- **Storage:** Supabase Storage Bucket 'epkolar-files'
- **PWA:** Inline manifest, Service Worker, iOS meta tags

## ROUTE_MAP (26 Tabellen)
projects, workers, time_entries, arbeitsscheine, fahrzeuge, werkzeuge, defects, forms, checklists, absences, absence_files, plans, tickets, weekplans, finkzeit, project_documents, project_folders, notifications, users, urlaubskontingent, bescheinigungen, photos, fz_termine, fz_schaeden, wz_service, worker_projects

## Offene Punkte
- (A) Pläne + Tickets E2E testen (tables existieren, noch keine Daten)
- (B) Foto-Upload Storage testen
- (C) Kundendaten befüllen (strasse/ansprechpartner/telefon/email_kunde für 8 Projekte leer)
- (D) Duplikat-Projekt löschen
- (E) FinkZeit Standby
