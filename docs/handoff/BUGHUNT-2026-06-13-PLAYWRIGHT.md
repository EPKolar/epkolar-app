# Bug-Hunt 2026-06-13 — Playwright, read-only, Live-Prod v3.9.352

**Methode:** Read-only Playwright-Durchlauf auf `https://epkolar.github.io/epkolar-app` als Monteur **barger** (`worker_id=w2`, `user_id=u2`). Kein Save/Senden/Löschen geklickt. Keine DB-Writes durch CC. Console- + Network-Timing mitgeloggt.

**Console über die ganze Session:** genau **1 harter Error** (#1 `activity_log` 403) + 1 transiente Warning (#9 PlanViewer). Sonst 0 Errors. App insgesamt sehr stabil.

---

## RLS-Status (DB — NICHT von CC angefasst; via Chat-Claude/Human-Run-Gate)

Der Client lädt zahlreiche Tabellen **ungefiltert** (`select=*&limit=5000`); das Scoping passierte bisher **nur clientseitig** → Daten-Leak über DevTools/Network.

| Tabelle | Befund | Status |
|---|---|---|
| **`absences`** | #11 — Monteur sah ALLE Krankenstände/Arztbesuche/Trauerfälle aller MA (DSGVO Art.9) | ✅ **RESOLVED (DB-RLS)** — `absences_select` neu zeilenweise: `is_staff() OR worker_id = (eigenes monteur_id)` via `auth.uid()→users.auth_user_id→users.monteur_id→absences.worker_id`. Nur SELECT. Verifiziert (ROLLBACK-Sim): Barger 0 Zeilen, Schober/Büro 50. 0 orphan worker_ids, kein Datenverlust. |
| **`time_entries`** | #12 — `select=*` liefert 52 Einträge aller MA (w1/w2/w3/w5/w9) = Arbeitszeiten/Lohndaten des Teams | ⏳ **NÄCHST-DRINGEND** (gleiche `using=true`-Lücke; DB-Fix folgt) |
| `projects, fahrzeuge, werkzeuge, arbeitsscheine, defects, forms, plans, tickets, checklists, weekplans, worker_projects` | vermutlich gleiches Muster (Geschäftsdaten-Leak, nicht Art.9) | ⏳ offen (RLS-Welle 1) |
| `material_orders` | **projekt-gescoped** (`project_id=eq…`) — kein Cross-Projekt-Leak | ✅ ok |
| `finkzeit` (Lohn) | Response `[]` für Monteur | ✅ ok |
| `users` | nur eigener Datensatz (`id=eq.u2`) | ✅ ok |

**UI-Impact der `absences`-RLS (geprüft, kein Code-Fix nötig):** `AbsView` ist bereits rollen-gegated — Monteure erreichen nur den Kalender-Sub-Tab (antraege/uebersicht/timeline = admin/`urlaub_edit`-only, v3.9.107); Kontingent-Listen `names.filter(n=>n===myMonteurName)`; `setSel(Kollege)` ist `if(isAdmin)`-gated. Einzige sichtbare Änderung: die 4 Statuskacheln (Ausstehend/Genehmigt) zeigen für Monteure jetzt **eigene** statt firmenweite Zahlen — **gewollt**, kein Fake-Bug.

> **Lesson:** „RLS Welle 1" war fälschlich als niedrig-Risiko eingestuft. `absences`+`time_entries` sind Personendaten-Leaks.

---

## Master-Liste der Befunde (12)

| # | Befund | Schwere | Typ | Status |
|---|--------|---------|-----|--------|
| 1 | `activity_log` 403 RLS bei jedem Monteur-Login (42501) → Console-Error + stiller Audit-/Forensik-Verlust (= Diagnose #3, leeres activity_log) | **hoch** | DB-RLS | offen — DB (Insert-Policy für Monteure) |
| 2 | Dashboard zeigt nach Cold-Cache-Erstlogin stale/ungescopte Daten (Projekte 5/8 + fremde Projektliste, Fahrzeuge/Werkzeug=0), korrigiert nach Tab-Wechsel. Ursache: `projects` (Req13) lädt vor `worker_projects` (Req21) | **hoch→mittel** | CC-Code | offen — Loading-Gate bis `worker_projects` da ist |
| 3 | Glocke regeneriert gelöschte Auto-Notifs (admin/PL): deterministische ID + Dedup nur gegen vorhandene; 4h-Cooldown beim Logout gelöscht; kein Dismissed-Gedächtnis (Z.5524–5566) | mittel | CC-Code | offen |
| 4 | Werkzeug-Liste: WERT-Spalte je Zeile „0", Summe €16.490/298 Geräte | mittel | CC-Code | offen |
| 5 | Arbeitsscheine: Sentinel `0001-01-01` in Spalte Vorgeschl./Bestätigt statt leer/„—" (S075342/324/323/315/279/278/275 …) | mittel | **CC-Code** | offen (vom Chef bestätigt CC-Task) |
| 6 | Wochenplanung: Monteur-Edit lokal möglich + „automatisch gespeichert", aber `saveWeek`/Flush `isAdmin`-gegated (Z.14928/14938) → Phantom-Save, persistiert nie. Edit-Handler (toggleMA Z.14861) nicht gegated | mittel | CC-Code | offen — Controls für nicht-Admins disablen + Read-only-Hinweis |
| 7 | Urlaub: Resturlaub 193h vs 192.5h Rundungs-Inkonsistenz; KPI-Zeile mischte global/persönlich (durch #11-Fix für Monteure nun eigen) | kosmetisch | CC-Code | offen |
| 8 | Projekt-Detail-Header: leere „()" (leere Projektnr.) + hängender Trenner „… Kirchberg ·" | kosmetisch | CC-Code | offen |
| 9 | `[PlanViewer] Render: PDF not loaded` Console-Warning (Z.11592) obwohl Plan korrekt rendert = transientes Render-vor-Load-Rauschen | kosmetisch | **CC-Code** | offen (vom Chef bestätigt CC-Task) |
| 10 | Wochenspann inkonsistent: Wochenbericht Mo–So (7 T) vs Planung/Zeiterfassung Mo–Sa (6 T) | kosmetisch | CC-Code | offen |
| 11 | `absences` RLS-Leak (Gesundheitsdaten) | **hoch (DSGVO)** | DB-RLS | ✅ **RESOLVED** |
| 12 | `time_entries` RLS-Leak (Arbeitszeiten aller MA) | **hoch** | DB-RLS | ⏳ nächst-dringend (DB) |

**Sauber geprüft (kein Befund):** Gefahrenstoffe, Mitarbeiter/Mein-Profil (korrekt gescoped + konsistent mit Modulen), Zeiterfassung, Monatsabrechnung (leer), Fahrzeug-Detail, Projekt-Dashboard, Pläne-Viewer, Berichte/Wochenbericht, Material-Warenkorb.

---

## Offene CC-Code-Tasks (kein DB-Bezug, read-only-Hunt-Ergebnisse)

Priorisiert (vom Chef bestätigt: #5 + #9 sind CC-Tasks):
- **#5** Sentinel `0001-01-01` → bei leerem Datum „—"/leer rendern (Arbeitsscheine-Tabelle Vorgeschl./Bestätigt).
- **#9** `[PlanViewer] PDF not loaded`-Warning unterdrücken/erst nach Load loggen.
- #2 Dashboard Loading-Gate, #6 Wochenplanung Read-only-UI für Nicht-Admins, #3 Glocke Dismissed-Gedächtnis, #4 Werkzeug-Wert-Spalte, #8 Projekt-Header-„()", #10 Wochenspann, #7 Urlaub-Rundung.

## Noch nicht gehuntet (Bridge-Crash unterbrach)
Arbeitsschein Such-/Filter + Detail-Ansicht; Projekt-Sub-Tabs Mängel/Bautagebuch.

## Schutz/DB-Direktive
`jiggujpruejkaomgxarp` — CC fasst die DB NIE an. Alle RLS-Fixes via Chat-Claude/Human-Run-Gate. Tank-Flow/Juprowa unberührt.
