# Bug-Hunt Abschluss — 2026-06-04 (Live v3.9.112)

Koordiniertes Agententeam (2 Wellen, 9 Finder über alle Domänen) + adversarielle Verifikation + MCP-Live-Smoke.

## ✅ MCP-Playwright-Test (Admin-Session, v3.9.112)
**Alle 15 Tabs** (Home/Chef/Projekte/Arbeitsscheine/Planung/Zeiterfassung/Urlaub/Monatsabrechnung/Fahrzeuge/
Werkzeuge/Mitarbeiter/Auswertungen/Einstellungen/Büro-Export/Admin) rendern **sauber**: 0 Console-Errors,
0 Warnings, 0 Error-Boundaries, 0 Render-Crashes. Urlaub-TDZ-Fix + die 3 früheren Crash-Fixes live bestätigt.

## ✅ Gefixt + gepusht (v3.9.107 – v3.9.112)
| Fix | Version |
|---|---|
| 9 Welle-1-Bugs (JUPROWA-String, Übersicht-Leak, Labels-Leak, Kontingent-Save, Deadline-TZ, authRetry-offline, reauth-reset, tog-Orphan) | v3.9.107 |
| **Urlaub-Tab TDZ-Crash-Hotfix** | v3.9.109 |
| JUPROWA-Prio (dringend→0), exportXls-Summenspalte, Bescheinigung-Escaping | v3.9.110 |
| OFFA-Re-Import-Datenverlust, Server-Approval-Bridge | v3.9.111 |
| Logout-Token-Fenster, Übernacht-von/bis (_wrapHrs) | v3.9.112 |

## 🟡 FLAGGED — braucht Sebastian-Entscheidung / höheres Risiko (NICHT autonom gefixt)
| # | Fund | Ort | Warum aufgeschoben | Vorschlag |
|---|---|---|---|---|
| F1 | **DATANORM schreibt Listenpreis in `ek_preis` UND `listenpreis`** → Cross-Supplier-EK-Vergleich ist listenpreis-basiert (Rabattgruppe nie aufgelöst) | `index.html:7517` | Business: braucht Rabattgruppe→Rabattsatz-Tabelle pro Händler | Beim Import EK = Listenpreis × (1−Rabatt) speichern, ODER ek_preis NULL lassen |
| F2 | **Jahreswechsel-KW**: `yr=getFullYear()` mit ISO-`isoW()` → Dez/Jan liest/schreibt Zeiterfassung/WeekPlan ins falsche Jahr | `16173/13451/9515` | Risiko: ISO-Wochenjahr-Logik in 3 Views; nur ~2 Wochen/Jahr (jetzt Juni) | Jahr aus ISO-Wochen-Montag ableiten, nicht aus getFullYear() |
| F3 | **effEk falsy-0**: legit 0-Preis-Zeile wird als "kein Preis" verworfen + aus Bestellung gedroppt | `12320/12378` | Geldlogik — ändert Lieferanten-Ranking; selten | `ek==null/NaN`-Check statt `!ek`; `eff>=0` |
| F4 | **Fuzzy-Name-Match** ordnet fremden Artikel-Preis zu + Order paart Original-artNr mit anderem Preis/Shop-Link | `12338/13039` | Business-Logik, Risiko bei Matching-Änderung | Dimension/Einheit-Gleichheit vor Name-Match; `art_nr: sp.artNr||it.artNr` |
| F5 | **parseVoice scheinart `"wartung"`/`"regie"`** nicht in AS_ART → "?"-Rendering, fehlt in Statistik/OFFA | `6309-6310` | Braucht Mapping-Entscheidung (wartung→? / eigener Key?) | wartung→reparatur (o. neuer AS_ART-Key); regie-Zweig raus (ist Scheintyp) |
| F6 | **Cross-User-ODB-Leak**: globale `"data"`-Stores werden nur beim Logout-Button gecleart, nicht bei _silentReAuth/Reload → nächster User sieht offline kurz Vor-User-Daten | `2435/5246/1448` | Größerer Umbau (uid-Scoping aller ODB-Keys o. Purge-on-Login bei uid-Wechsel) | ODB-`"data"`-Key per uid scopen ODER bei Login purgen wenn uid≠lastUser |
| F7 | qty `parseInt` schneidet Nachkomma bei m/kg/l-Mengen ab | `12963/12502` | UI-Verhalten | `parseFloat(...replace(',','.'))`, `>0`-Guard |

## Hinweise
- `||stdVonTag(d)`-Fallback in yearSt NICHT geändert (schützt unmigrierte Legacy-0-Rows; erst nach C1 anfassen).
- React-Hunter: die 3 Crashes (StundenzettelView/ChartBox/WerkzeugView) waren der komplette TDZ/Scope-Satz; die AbsView-TDZ (v3.9.109) war von der Bug-Hunt-Welle selbst eingeschleppt und ist gefixt + per Test geguardet.
- Offene Sebastian-Items unverändert: P0-2 supplier_configs (Edge-Deploy supplier-sync + REVOKE), admin-create-user-Deploy.
