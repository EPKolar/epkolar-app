# EPKolar Eternal Bug Hunt Report

Branch: `cc-bug-hunt-eternal/2026-04-26`
Started: 2026-04-26 (Setup)
Repo-State at start: `8c11b41` (v3.8.64)
Mode: Append-only single-document. Alle Sub-Sprints hängen Sektionen unten an.

## Severity-Skala
- **P1** = Crash / Datenverlust / Auth-Bruch
- **P2** = funktional kaputt aber recoverable
- **P3** = Code-Quality / Tech-Debt / Performance
- **P4** = Cosmetic / UX-Optimierung

## Confidence-Skala
- **HIGH** = Audit + Verifier vollständig in Übereinstimmung
- **MEDIUM** = Verifier neutral, Audit plausibel
- **LOW + DISPUTED** = Verifier widerspricht Audit
- **NOISE** = False-Positive, aus Master-Index ausgeschlossen

---

## Sprint 1 — Home/Dashboard (Wetter, KPIs, Live-Updates, Baustellen-Cards)
Date: 2026-04-28 (CC-Run, manuell ins Repo eingetragen weil Permissions-Block)
Round: R1 (Sprint 1 von 15)
Repo-State: `87bcb41` (cc-bug-hunt-eternal/2026-04-26)

### Sprint-Master-Index (Quick-Reference)

| ID | Title | Confidence | Severity | Sebastian-Disposition |
|---|---|---|---|---|
| B-001 | setNow 60s-Tick re-rendert Heavy-Subtrees ohne Memo | HIGH | P3 | OPEN |
| B-002 | Wetter "Heute" via i===0 statt Datums-Compare | MEDIUM | P3 | OPEN |
| B-003 | Stunden-Lookup `wid===_myMid2` schlägt bei Name-keyed Legacy fehl | MEDIUM | P2 | OPEN |
| B-004 | `startsWith(name+date)` Namen-Kollision in abs-Lookup | HIGH | P3 | OPEN |
| B-005 | `dringendeAS`/MyAs-Aggregates ohne useMemo | HIGH | P3 | OPEN |
| B-006 | `_fetchLiveKpis` läuft auch für Monteur ohne KPI-Render | HIGH | P3 | OPEN |
| B-007 | activity_log TZ-Drift in Team-aktiv-Count | MEDIUM | P3 | OPEN |
| B-008 | weatherErr-Fallback Daten irreführend (statisch) | HIGH | P4 | OPEN |
| ~~B-009~~ | ~~setNow Mount-Ref-Schutz fehlt (NOISE)~~ | LOW + DISPUTED | P4 | NOISE |
| B-010 | alertsExpanded index-basiert → Re-Order zeigt falsche Details | HIGH | P3 | OPEN |
| B-011 | "Mein Tag" nicht in DASH_SECS / dv()-togglebar | HIGH | P4 | OPEN |
| B-012 | "Material anfordern" hardkodiert topProjects[0] | HIGH | P3 | OPEN |
| B-013 | Wetter-Cache nicht koordinaten-key'd | HIGH | P3 | OPEN |
| B-014 | Pickerl/Service "abgelaufen" via Datetime-Compare | MEDIUM | P4 | OPEN |
| B-015 | Klickbare KPI/Alert-Tiles ohne role=button + Keyboard | HIGH | P3 | OPEN |
| B-016 | `_isFleetAdmin` hardcoded `username==="pinger"` | HIGH | P3 | OPEN |
| B-017 | `myProjects.slice(0,8)` ohne Truncation-Hinweis | HIGH | P4 | OPEN |
| B-018 | Geolocation-Permission Prompt jedes Mount | MEDIUM | P3 | OPEN |
| B-019 | Open-Meteo-Fetch ohne AbortController-Cleanup | HIGH | P4 | OPEN |
| ~~B-020~~ | ~~weather.daily.time slice(0,7) Längen-Schutz (NOISE)~~ | LOW + DISPUTED | P4 | NOISE |
| B-021 | firstName-Heuristik fragil bei "Nachname Vorname" | MEDIUM | P4 | OPEN |
| B-022 | `monteurProjekte` Lookup mit Name-Fallback | MEDIUM | P3 | OPEN |
| B-023 | Charts ohne useMemo (verschachtelte forEach/reduce/Tick) | HIGH | P3 | OPEN |
| B-024 | `dv('charts')` Default-true belastet Mobile/Monteur | MEDIUM | P3 | OPEN |
| B-025 | `material_orders.status`-Liste hartcoded vs Schema-Drift | MEDIUM | P3 | OPEN |

**Summary**: 25 Findings — 13 HIGH · 9 MEDIUM · 2 NOISE. Severity: 1×P2, 17×P3, 7×P4.

### AUDIT-Details (kompakt)

#### B-001 — setNow 60s-Tick re-rendert Heavy-Subtrees ohne Memo · HIGH · P3
Location: index.html:7584 (Trigger) + 8183-8304 (Charts), 7689-7711 (Alerts)
Tick aktualisiert nur Greeting/Time-String, aber alle Sektionen (Charts ×4, Alerts-Reduce, KPIs) re-rendern. Bei 5000 entries / 50 Projekten >50ms/Tick.
Fix: Greeting/Time in React.memo extrahieren; Charts/Alerts/KPIs in useMemo mit korrekten Deps.

#### B-002 — Wetter "Heute" via i===0 ist falsch nach Mitternacht-Cache · MEDIUM · P3
Location: index.html:7767
Cache wurde 23:50 geschrieben, daily.time[0]="gestern" — Render markiert i===0 trotzdem als "Heute".
Fix: `const today=td2(); const isToday=d===today;` statt `i===0`.

#### B-003 — Stunden-Lookup schlägt bei Name-keyed Legacy-Entries fehl · MEDIUM · P2
Location: index.html:7732-7736 (Mein Tag), 7682 (Wochen-Summe), 14470 (Chef)
Falls historische time_entries.worker Namen statt IDs enthalten ("Paschinger" statt "w1"): Stunden unsichtbar → "0h" obwohl gebucht.
Fix: Lookup tolerant — `if(wid!==_myMid2 && wid!==myName) return;`

#### B-004 — startsWith(name+date) Namen-Kollision in abs-Lookup · HIGH · P3
Location: index.html:8169 (Team-Card)
"Schmid" und "Schmidberger" → startsWith("Schmid_2026-04-28") matcht beide → falsche Abwesenheit-Anzeige.
Fix: ID-basierter Lookup statt name-startsWith.

#### B-005 — dringendeAS/MyAs-Aggregates ohne useMemo · HIGH · P3
Location: index.html:7675, 7723-7729
5 inline arbeitsscheine.filter(...) im Render-Body, jeden 60s-Tick neu (B-001).
Fix: Top-of-Component useMemo-Block für alle AS-Aggregates.

#### B-006 — _fetchLiveKpis läuft auch für Monteur ohne KPI-Render · HIGH · P3
Location: index.html:7559-7577 (Definition + Interval) vs Render 8048-8062 (admin-gated)
Alle 120s 5 parallele Supabase-Requests, deren Resultate nie gerendert werden. Verschwendet Token-Pool.
Fix: useEffect mit `if(!isAdmin) return;` Gate.

#### B-007 — activity_log UTC vs td2() lokal · MEDIUM · P3
Location: index.html:7569
PostgREST parst `created_at=gte.2026-04-28T00:00:00` ohne TZ als UTC. Vienna-Frühbucher 00:00-02:00 fallen aus.
Fix: `created_at=gte.${td2()}T00:00:00%2B02:00` oder Server-Side-View mit korrekter TZ.

#### B-008 — weatherErr-Fallback statisch (Winter-Werte im Sommer) · HIGH · P4
Location: index.html:7777-7787
wFallback ist `[{c:2,h:4,l:-1},...]` hartcodiert. Comment "from date seed" ist falsch.
Fix: Saison-Lookup `[winter,spring,summer,autumn][month/3|0]` oder Sektion ausblenden.

#### B-009 — NOISE: setNow Mount-Ref-Schutz · LOW + DISPUTED · P4
JS-Single-Thread + clearInterval macht Race praktisch unmöglich. Aus Master-Index ausgeschlossen.

#### B-010 — alertsExpanded index-basiert → Re-Order zeigt falsche Details · HIGH · P3
Location: index.html:7552, 7794-7805
User klickt Alert #2, async finkStats-Update reordert Array → Detail-Block zeigt falschen Alert.
Fix: Identifier-basiert (`alertsExpandedKey` statt Index).

#### B-011 — "Mein Tag" nicht in DASH_SECS / dv()-togglebar · HIGH · P4
Location: index.html:7808-7872 (kein dv-Wrapper), DASH_SECS 7579 (kein meinTag)
Inkonsistenz mit anderen Sektionen.
Fix: meinTag-Eintrag in DASH_SECS + dv('meinTag')&&-Wrapper.

#### B-012 — "Material anfordern" hardkodiert topProjects[0] · HIGH · P3
Location: index.html:7867
Bei mehreren zugewiesenen Projekten falsches Projekt. Timer-Action 14 Zeilen darüber zeigt korrektes Pattern.
Fix: Picker-Prompt analog Timer-Action.

#### B-013 — Wetter-Cache nicht koordinaten-key'd · HIGH · P3
Location: index.html:7634
User reist Wien → Salzburg, Cache-Key konstant "epk_weather", 15min TTL → falsches Wetter.
Fix: `cKey="epk_weather_"+lat+"_"+lon`.

#### B-014 — Pickerl "abgelaufen" via Datetime-Compare · MEDIUM · P4
Location: index.html:7695, 7699
`new Date("2026-04-28") < new Date()` → Pickerl ab 00:01 desselben Tages als "abgelaufen" markiert, obwohl bis Tagesende gültig.
Fix: Date-only-Vergleich via _ymd().

#### B-015 — Klickbare Tiles ohne role=button + Keyboard · HIGH · P3
Location: 14 Stellen (8006-8053, 7796-7943, 8093)
Tab-Navigation überspringt KPI-Kacheln, Screen-Reader liest "div", Enter/Space lösen onClick nicht aus.
Fix: ClickableTile-Helper oder `role="button" tabIndex="0" onKeyDown`.

#### B-016 — _isFleetAdmin hardcoded username==="pinger" · HIGH · P3
Location: index.html:7690
Würde Pinger umbenannt → verliert Fleet-Sicht trotz isVAdmin-Flag. Neuer User mit username="pinger" bekäme ungewollt Fleet-Sicht.
Fix: `_isFleetAdmin = isAdmin || curUser.isVAdmin === true || hasPerm(curUser,"fz_admin")`.

#### B-017 — myProjects.slice(0,8) ohne Truncation-Hinweis · HIGH · P4
Location: index.html:7937
Monteur mit 12 Projekten sieht stille Truncation auf 8.
Fix: Footer-Link "→ {N-8} weitere ansehen".

#### B-018 — Geolocation-Prompt bei jedem Mount · MEDIUM · P3
Location: index.html:7641-7647
Tab-Wechsel zurück zu Home → erneuter getCurrentPosition-Aufruf, bei "denied" sichtbarer Prompt (iOS Safari) oder Logspam.
Fix: navigator.permissions.query cachen.

#### B-019 — Open-Meteo-Fetch ohne AbortController-Cleanup · HIGH · P4
Location: index.html:7635
Tab-Wechsel vor Wetter-Response → Fetch läuft weiter, _weatherMountedRef verhindert setState (gut), aber Network/CPU verschwendet.
Fix: AbortController explizit halten + abort() im Cleanup.

#### B-020 — NOISE: weather.daily.time slice(0,7) · LOW + DISPUTED · P4
Open-Meteo garantiert forecast_days=7. NaN-Schutz greift via ||0. Aus Master-Index ausgeschlossen.

#### B-021 — firstName fragil bei "Nachname Vorname" · MEDIUM · P4
Location: index.html:7662
User "Riedmann Christoph" → firstName="Riedmann" → "Guten Morgen, Riedmann".
Fix: Konsequente vorname-Spalte in users-DB ODER Heuristik.

#### B-022 — monteurProjekte Lookup mit Name-Fallback · MEDIUM · P3
Location: index.html:7927-7928
Fallback `monteure.find(m=>m.n===curUser.name)?.id` bei prefix-gleichen Namen wackelig.
Fix: Single source of truth — curUser.monteurId, Fallback weglassen.

#### B-023 — Charts ohne useMemo · HIGH · P3
Location: index.html:8186-8215
Verschachtelte fahrzeuge.forEach(f=>f.tankLog.forEach(...)) in IIFE pro Render. 12×200×6 = 14400 Iterationen/Tick.
Fix: chartsData=useMemo([entries,fahrzeuge]).

#### B-024 — dv('charts') Default-true belastet Mobile · MEDIUM · P3
Location: index.html:8183 (in Verbindung mit B-023)
Mobile-Monteur hat Charts standardmäßig aktiv → mit B-001/B-023 ist App träge.
Fix: Default-Map pro Rolle: `monteur:{charts:false,kpis:false}`.

#### B-025 — material_orders.status-Liste hartcoded · MEDIUM · P3
Location: index.html:7565
Status-Liste "(angefordert,in_bearbeitung,offen)" hartcoded; Schema-Drift möglich.
Fix: Konstante MATERIAL_OPEN_STATES shared mit Material-Order-View.

---

### Sebastian-TODO post-Urlaub (Priorisiert)

**Tier 1 — Sofort fixen (nächster v3.8.65 Run):**
- **B-016** (5min, HIGH) — _isFleetAdmin via isVAdmin statt username==="pinger"
- **B-001+B-005+B-023+B-024** zusammenfassen als "Performance-Audit Phase 5.1+5.2 done" — der Hunt validiert genau das Memory #28 SKIP-Risk
- **B-007** (10min, MEDIUM) — TZ-Suffix in activity_log-Filter

**Tier 2 — Nice-to-have (v3.8.66):**
- B-012 Material-Picker analog Timer
- B-013 Wetter-Cache koordinaten-keyen
- B-010 alertsExpanded auf identifier-basiert
- B-011 meinTag in DASH_SECS

**Tier 3 — Backlog:**
- B-015 a11y-Sweep ClickableTile-Helper (eigener Mini-Run)
- B-008 Wetter-Fallback saisonal
- B-002 Wetter "Heute"-Marker
- Rest

**Tier 4 — Won't-Fix Kandidaten:**
- B-009, B-020 (NOISE, schon ausgeschlossen)
- B-021 (DSGVO-Heuristik, abhängig von name-Pflege)
