# Testkonzept EPKolar — v4.0
**Stand:** 18.04.2026 · **App-Version:** v3.5.91 (Live auf github.io/epkolar-app)
**Vorgänger:** Testkonzept_EPKolar_v3_5_65.docx (v3.0, Update Juli)

---

## 1. Scope

Testkonzept für **EPKolar Baustellen- & Zeiterfassungs-PWA** nach Abschluss des
Bug-Fix-Sprints (v3.5.82→91), Feature-Erweiterungen (v3.5.73→81) und
RLS-Security-Fix (B-006 teils + B-007 voll).

**Neu gegenüber v3.0:**
- RLS-verifikationsteil (B-006, B-007)
- Monteur-Isolation-Tests (Schober-Smoke)
- OfflineBanner + SyncQueue-Tests
- ChefDashboard-KPI-Verifikation
- Urlaubsantrag-Workflow (Antrag → Genehmigung → Notif)
- Fahrtenbuch (CRUD + XLS-Export)
- Excel-Export-Test (AuswertungView komplett)
- Timer-Schutz (negative Stunden, Systemuhr-Rücksprung)
- Null-Safety-Regression-Pack (Search, Projekte, AS)

---

## 2. Testumgebungen

| Umgebung | URL | User |
|----------|-----|------|
| Live (GitHub Pages) | https://epkolar.github.io/epkolar-app/ | verifiziert |
| Supabase DB | jiggujpruejkaomgxarp.supabase.co | Service-Role via Dashboard |
| Chrome-DevTools | F12 | Network-Offline-Sim |
| Mobile Safari iOS 18 | home-screen installed | Echtgerät |

---

## 3. Test-Datensätze (verifiziert)

| Role | Username | Password | Worker-ID |
|------|----------|----------|-----------|
| admin | sebastian | (bekannt) | (kein Worker-Link) |
| projektleiter | (PL-Account) | — | — |
| monteur | schober | test1234 | w? |
| monteur | riedmann | (bekannt) | w9 |
| portal | (Projekt-Code) | n/a | n/a |

DB-Stand (bei v3.5.81 verifiziert):
- 54 arbeitsscheine
- 36 time_entries (Summen-Sample)
- 649 notifications (vor B-007 lesbar; nach B-007 pro User ~20-50)
- 25121 supplier_articles (vor B-006: anon lesbar; nach B-006: anon=0)
- 3 projects, 9 users

---

## 4. Testfälle (Pflicht-Pack)

### 4.1 Authentication (TC-A)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-A-01 | Login mit `schober/test1234` | Weiterleitung zum HomeView, `curUser` gesetzt, `window._ensureAuth()` verfügbar |
| TC-A-02 | JWT-Refresh nach 55 Min Idle | `_api.get` funktioniert weiterhin, kein 401-Crash |
| TC-A-03 | Falsches Passwort | Fehler-Meldung, kein Session-Leak |
| TC-A-04 | Offline-Login (Network→Offline + bekannter User) | aus IndexedDB-Cache (lastUser), Auth-Hash-Match |
| TC-A-05 | Logout | `_authToken=null`, Redirect zu Login, IndexedDB sessionData cleared |

### 4.2 RLS B-006 Anon-Block (TC-R6) — ✅ PASS (17.04.2026 ~21:50)

JS im Incognito-Tab **ohne Login**:
```js
const U="https://jiggujpruejkaomgxarp.supabase.co";
const K="<anon-apikey>";
const H={"apikey":K,"Authorization":"Bearer "+K};
const tests=[];
for(const t of ["users","projects","supplier_articles","supplier_configs",
                "material_items","material_orders","bautagebuch","project_documents"]){
  const r=await fetch(`${U}/rest/v1/${t}?select=id&limit=1`,{headers:{...H,Prefer:"count=exact"}});
  const cr=r.headers.get("content-range")||"";
  tests.push({t, anon_count:cr.split("/")[1]||"?"});
}
console.table(tests);
```
**Pass-Kriterium**: Alle anon_count=`0`. Wenn `users`, `projects`, `project_documents` noch >0
→ **FAIL** (B-006-Rest-Fix aus HANDOFF_v3591.md §3 ausführen).

### 4.3 RLS B-007 Monteur-Isolation (TC-R7) — ✅ PASS (17.04.2026 ~21:50)

**DB-Verifikation live-bestätigt:** helpers=4, b007_total=22, rls_zero_left=0, per_table={AS:2, TE:2, notif:4, urlaub:4, fb:2, chk:2, komm:4, komp:2}

JS eingeloggt als **schober**:
```js
const tests=[];
for(const [n,path,max] of [
  ["AS",             "arbeitsscheine?select=id",   54],
  ["ZE",             "time_entries?select=id",     36],
  ["Notif",          "notifications?select=id",   649],
  ["Fahrtenbuch",    "fahrtenbuch?select=id",      -1],
  ["Urlaubsantrag",  "urlaubsantraege?select=id",  -1],
  ["Komp (alle)",    "worker_kompetenzen?select=id", -1],
]){
  const r=await fetch(window.SUPABASE_URL+"/rest/v1/"+path,{headers:window._sbH()});
  const d=await r.json();
  tests.push({n, count:d.length, below_max: max<0 ? "n/a" : d.length<max});
}
console.table(tests);
```
**Pass-Kriterium:**
- AS-Count ≤ anzahl schober-eigene AS (nicht 54)
- ZE-Count = schober-eigene ZE
- Notif-Count < 649 (nur eigene user_id)
- Worker-Kompetenzen-Count = alle (komp_read_all USING true)

Gleiches als **admin** eingeloggt:
- AS=54, ZE alle, Notif = nur admin's eigene
- Kein "0"-Effekt auf AS (Regression-Check der neu eingeführten Policies)

### 4.4 Home / Timer (TC-H)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-H-01 | Timer starten via Projekt-Prompt | Toast "Timer gestartet", Banner oben sichtbar |
| TC-H-02 | Timer stoppen | `time_entry` wird gespeichert, `hours ≥ 0` (Regression v3.5.89) |
| TC-H-03 | Systemuhr-Rücksprung simulieren (DevTools) | `Math.max(0,...)` greift, keine negativen Stunden |
| TC-H-04 | HomeView Today-Hours | KW-Summe stimmt mit DB überein |
| TC-H-05 | "Mein Tag" Section | Eigene AS des Tages nach Termin-Zeit sortiert |

### 4.5 Arbeitsscheine (TC-AS)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-AS-01 | Liste öffnen als admin | 54 Rows |
| TC-AS-02 | Liste öffnen als schober | nur eigene (nach B-007) |
| TC-AS-03 | Schnell-Filter "aktiv" | `scheinstatus=in_bearbeitung` |
| TC-AS-04 | AS editieren, speichern | `bearbeitetVon = <username>` (null-safe split, v3.5.89) |
| TC-AS-05 | Duplikat-Check beim Speichern | `form.kundName` null-safe (v3.5.90) |
| TC-AS-06 | Kommentar mit @mention | Notif an gementionten User |
| TC-AS-07 | Checkliste markieren | `as_checklist.status` → "ok", via RLS erlaubt |
| TC-AS-08 | AS mit `arbeitsanweisungen=null` anzeigen | Kein Crash (v3.5.86 fix) |

### 4.6 Projekte (TC-P)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-P-01 | Projekt-Suche "bäck" | null-safe Filter (v3.5.90), kein Crash bei Projekt ohne name |
| TC-P-02 | Projekt öffnen → Dokumente | PDF-Liste |
| TC-P-03 | Projekt → Fortschritt ändern | Speichert, ChefDashboard-Ampel updatet |

### 4.7 Suche (Spotlight, TC-S)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-S-01 | Cmd+K, "bäck" | Projekte+Scheine+Kunden Treffer (null-safe v3.5.90) |
| TC-S-02 | Kategorie "Mitarbeiter" | Monteure gelistet (null-safe `m.n`) |
| TC-S-03 | Kategorie "Fahrzeuge" | null-safe `f.kennzeichen` |

### 4.8 Urlaubsantrag (TC-U)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-U-01 | Als schober Antrag stellen | Row in `urlaubsantraege` mit `status=beantragt` |
| TC-U-02 | Admin sieht Antrag | via `is_staff()` RLS |
| TC-U-03 | Admin genehmigt | Notif an Antragsteller, `status=genehmigt` |
| TC-U-04 | Schober versucht Antrag zu ändern nach Genehmigung | **RLS blockt** (urlaub_update mit `status='beantragt'`) |
| TC-U-05 | Doppel-Submit (Button während Save drücken) | Guard blockt (v3.5.87) |

### 4.9 Fahrtenbuch (TC-F)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-F-01 | Mitarbeiter-Detail → Fahrtenbuch | nur eigene (Monteur) oder alle (Admin) |
| TC-F-02 | Neue Fahrt anlegen | `worker_id = current_monteur_id()` |
| TC-F-03 | Monats-Filter 04/2026 | `ft_datum LIKE '2026-04-%'` |
| TC-F-04 | XLS-Export "Fahrtenbuch KW15" | Datei mit Spalten Datum/KFZ/Zweck/KM |
| TC-F-05 | Doppel-Submit-Guard | `saving`-State blockt (v3.5.87) |

### 4.10 Offline / SyncQueue (TC-O)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-O-01 | Network → Offline | OfflineBanner sichtbar (nicht weggeflickert bei `pendingCount=0` — v3.5.82) |
| TC-O-02 | Offline: Foto aufnehmen | `PhotoQ.add()`, Banner zeigt Pending-Count |
| TC-O-03 | Network → Online | Auto-Sync läuft, Banner verschwindet erst wenn `pendingCount=0 && !syncing` |
| TC-O-04 | Sync 5× Retry exhausted | Toast-Warning "Sync fehlgeschlagen nach 5 Versuchen" |

### 4.11 ChefDashboard (TC-CD, admin only)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-CD-01 | ChefDashboard-Tab öffnen | 5 KPI-Tiles (keine NaN, `filter(Boolean).size` v3.5.82) |
| TC-CD-02 | Projekt-Fortschritt-Balken | null-safe Projekt-Namen (v3.5.91) |
| TC-CD-03 | Top-8 überfällige AS | sortiert nach `terminBestaetigt < today` |

### 4.12 Excel-Exports (TC-X)

| ID | Schritt | Erwartung |
|----|---------|-----------|
| TC-X-01 | AuswertungView → "📥 Alle als Excel" | XLS mit allen Charts als Sheets |
| TC-X-02 | Bautagebuch-Export | korrekte Spaltenreihenfolge (v3.5.84 Fix) |
| TC-X-03 | Mitarbeiter-Bericht KW-Filter | Summenblatt + KW-Sheets |

### 4.13 Null-Safety-Regression-Pack (TC-N)

Pflicht nach jedem Release:
1. DB hat mindestens 1 Row mit `name=NULL` in `projects` → App crasht nicht
2. DB hat mindestens 1 AS mit `arbeitsanweisungen=NULL` → AS-Liste rendert (v3.5.86)
3. DB hat mindestens 1 User ohne `.name` (nur `.username`) → Header rendert (v3.5.89)
4. DB hat mindestens 1 Material-Order mit `project.name=NULL` → OrderList rendert (v3.5.91)

---

## 5. Smoke-Test-Checkliste (nach jedem Deploy)

- [ ] `curl -sI https://epkolar.github.io/epkolar-app/index.html | grep 200`
- [ ] DevTools-Console: `APP_VERSION` = erwartete Version
- [ ] DevTools-Console: `SW_VER` = erwartete Version
- [ ] Login als admin + schober funktioniert
- [ ] AS-Liste lädt (Admin=54, Schober<54)
- [ ] OfflineBanner: Network→Offline→sichtbar→Online→weg
- [ ] Timer Start/Stop speichert time_entry mit `hours≥0`
- [ ] Cmd+K / Search → liefert Treffer ohne Crash
- [ ] Service-Worker aktiv: `navigator.serviceWorker.controller` != null
- [ ] `window._runAllTests()` — 15 Tests grün

---

## 6. Automatisierungsgrad

| Test-Kategorie | Automatisiert | Manuell |
|----------------|---------------|---------|
| RLS-Verifikation | ✅ JS-Block (TC-R6, TC-R7) | — |
| Auth-Flow | Teil (JWT-Check) | Login-UI |
| UI-Interactions | Nein | 100% |
| Offline-Sim | Nein | DevTools |
| Mobile iOS | Nein | 100% Echtgerät |

**Nächste Iteration** (v4.1): Playwright E2E-Tests für TC-A, TC-H, TC-AS Golden-Paths.

---

## 7. Abnahme-Kriterien v3.5.91

- [x] `node --check` OK
- [x] Bracket-Baseline `() -2, {} 0, [] 0`
- [x] SW_VER + APP_VERSION synchron
- [x] B-006: anon-count=0 auf allen Tabellen (verified 17.04.2026)
- [x] B-007: helpers=4, policies=22, rls_zero_left=0 (DB-verified)
- [ ] Schober-Isolation via JS-Block (pending)
- [ ] Admin sieht nach B-007 weiterhin AS=54 (pending)
- [ ] Manuelle Smoke-Liste aus §5 grün

---

## 8. Historie

| Version | Datum | Umfang |
|---------|-------|--------|
| v1.0 | 2025-04 | Erste Fassung (Login, AS, ZE) |
| v2.0 | 2025-09 | + Offline, Sync, Photos |
| v3.0 | 2026-02 | + Bautagebuch, Material, Scheine-Upload |
| v3.5.65 | 2026-03 | + Rolle-Modell, Portal, Juprowa-Sync |
| **v4.0** | **2026-04-18** | **+ RLS B-006/B-007, ChefDashboard, Urlaub, Fahrtenbuch, Null-Safety-Pack** |
