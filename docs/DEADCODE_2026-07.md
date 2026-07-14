# Dead Code Inventory · 2026-07-14

**Scope:** `index.html` (26.559 Zeilen, Stand `APP_VERSION="3.9.694-supabase"`, Commit `3626dc3`).
**Phase:** NUR INVENTUR. Es wurde keine Zeile in `index.html` geändert. Diese Datei wird
absichtlich nicht committet.

## Ausgangspunkt

Alte Kandidatenlisten geprüft: `sql/DEAD_CODE_CANDIDATES.md` (24.04.), `sql/DEAD_CODE_CANDIDATES_v2.md`
(25.04.), `sql/CODE_DEBT.md` + `_v2.md`. Ergebnis: **alle 4 dort noch offenen Kandidaten
(`ESKALATION_RULES`, `MATERIAL_UNITS`, `SCHEINART_C`, `SCHEINSTATUS_C`) wurden bereits in
v3.8.42 gelöscht** ("Tag-5 Dead-Code-Cleanup", Triple-Grep 0 externe Treffer, siehe Kommentare
L551, L4028, L15142). Die alten Listen sind vollständig abgearbeitet — kein Re-Entdecken nötig,
nur zur Kenntnis genommen.

## Methodik (frischer Scan, 2026-07-14)

1. Alle Top-Level-Deklarationen (`^function NAME`, `^const/let/var NAME =`, Spalte 0 — identisch
   zur April-Methodik) extrahiert: **465** Namen. Davon **1 Singleton** (`count==1` via `\bNAME\b`
   über die ganze Datei): `_safeSessionSet` (L1710) — bereits im Code selbst als
   `/* v3.9.581: NICHT geloescht — 0 App-Aufrufe, aber durch test_sprint77_coverage.py geschuetzt
   (Guard-Test). */` dokumentiert und durch `tests/test_sprint77_coverage.py` (Zeilen 51-75)
   tatsächlich gepinnt. **Kein neuer Fund**, gehört in BEWUSST-TOT.
2. Dieselbe Singleton-Suche auf Einrückungsebene 2/4 (komponenten-lokale `const`/`function`
   innerhalb der Top-Level-Funktionen/Components) ausgeweitet, weil die Datei seit April von
   ~16.000 auf 26.559 Zeilen gewachsen ist und die reine Spalte-0-Heuristik das nicht mehr
   abdeckt: **3.024** Deklarationen, davon **6 Singletons** (`count==1`) → einzeln verifiziert,
   siehe unten.
3. Für jeden Fund: Grep über `index.html` UND `tests/`, `docs/`, `sql/`, `supabase/`,
   `RUNBOOK.md`, `ARCHITECTURE.md` — direkte Aufrufe, String-/`window[...]`-Zugriffe (per
   `['NAME']`/`["NAME"]`-Suche), HTML-Attribute. Keine Dispatch-Tabelle (`ROUTE_MAP`-artig) im
   Codebase gefunden, die dynamisch über diese 6 Namen indiziert.
4. `count==2`-Kandidaten (450 Stück, Deklaration + genau 1 weiterer Treffer) automatisiert nach
   "zweiter Treffer sieht wie Kommentar-Erwähnung aus" gefiltert. Von 2 automatisch markierten
   Fällen war **1 echter Fund**: `TIME_WEEK` (L679) — der zweite Treffer ist der
   Versions-Kommentar "TIME_WEEK bleibt (test-gepinnt)" bei L2819. Verifiziert gegen
   `tests/test_time_constants.py:26` (`assert re.search(r"const TIME_WEEK\s*=\s*7\s*\*\s*TIME_DAY", index_html)`)
   — **exakt die TIME_WEEK-Lektion aus der Aufgabenstellung**. Gehört in BEWUSST-TOT, kein
   SICHER-Kandidat. Der zweite automatische Treffer (`addFz`) war ein Regex-Fehlalarm (Name kam
   zufällig in derselben sehr langen JSX-Zeile wie ein Kommentar vor) — hat echte Callsites, kein
   Kandidat.
5. Für Flotte/GPS-Umfeld-Kandidaten gegen `docs/wip/FLOTTE_GPS_WIP_2026-07.patch` geprüft (0
   Treffer für beide betroffenen Namen — der Patch ist ohnehin nur 10 Zeilen `index.html` +
   4 Zeilen `sw.js`, Basis v3.9.672, und muss beim Wiederaufnehmen laut eigener Doku sowieso
   rebased werden).
6. Bewusst NICHT vollständig geprüft: alle 450 `count==2`-Fälle einzeln von Hand (zu groß für
   Phase-1-Aufwand). Das Sample war ausreichend groß (465 Top-Level + 3.024 Ebene-2/4 = 3.489
   Deklarationen komplett auf Singleton geprüft), um zu zeigen, dass die Datei nach den
   vorangegangenen Cleanup-Runden (v3.8.37, v3.8.42, v3.9.5, v3.9.581 u.a., siehe CSS-Removals
   L111/118/139/149/4928/4938) bereits sehr sauber ist.

---

## 1. SICHER — 0 Referenzen, alle Kanäle geprüft

| # | Symbol | Zeile | Typ | Grep der 0 zeigt | Risikoklasse |
|---|--------|------:|-----|-------------------|--------------|
| 1 | `pendingPushCount` | 8359 | lokale `const` in Arbeitsscheine-Liste-Component | `grep -n "\bpendingPushCount\b" -r .` → nur L8359 selbst (Deklaration). Kein zweiter Treffer in `index.html`, `tests/`, `docs/`, `sql/`, `supabase/`. Kein `window[...]`/String-Zugriff. | **niedrig** — reine Zähl-Berechnung ohne Seiteneffekt (`arbeitsscheine.filter(...).length`), nirgends in JSX gerendert. Kommentar direkt darüber (L8358/8360) dokumentiert, dass `doJuprowaPushAll` (der "Push-All"-Button, zu dem dieser Zähler vermutlich als Badge gehörte) bereits in v3.9.581 als Dead-Code entfernt wurde — `pendingPushCount` ist der übrig gebliebene Rest dieser Aufräumaktion. |
| 2 | `srvBase` | 13026 | lokale `const` in Projekt-Export-Component | `grep -n "\bsrvBase\b" -r .` → nur L13026. Component-Return (L13040-13080) komplett gelesen: der tatsächlich angezeigte Pfad kommt direkt aus `buildExportPath(...)` (L13070) bzw. einem hartkodierten String (L13043/L13048), nicht aus `srvBase`. | **niedrig** — reine String-Berechnung, kein Seiteneffekt, offensichtlich durch die direkte `buildExportPath`-Verwendung ersetzt. |
| 3 | `_tagLabel` | 23484 | lokale Formatter-Funktion in Flotte/Fahrtenbuch-Liste | `grep -n "\b_tagLabel\b" -r .` → nur L23484. Die eigentliche Tages-Kopfzeile im selben Component dupliziert dieselbe Wochentag-Logik inline bei L23705 (`const wd=['So','Mo',...][d.getDay()]`) statt `_tagLabel(key)` aufzurufen. | **niedrig-mittel** (Flotte-Domäne, aktiv in Entwicklung — `docs/wip/FLOTTE_GPS_WIP_2026-07.patch` geprüft, betrifft diese Zeile nicht). Reiner Formatter ohne Seiteneffekt, durch Inline-Duplikat ersetzt. |
| 4 | `_seitFmt` | 24000 | lokale Wrapper-Funktion in Flotte-Fleetview-Component | `grep -n "\b_seitFmt\b" -r .` → nur L24000. Die tatsächliche Anzeige ruft direkt `_fzSeitFmt(_stp.seit, now)` auf (L23946), nicht den Wrapper. | **niedrig-mittel** (Flotte-Domäne). Reiner Formatter-Wrapper ohne Seiteneffekt (`return _fzSeitFmt(ms,_now2)`), durch direkten Aufruf der Basisfunktion ersetzt. `_fzSeitFmt` selbst ist aktiv genutzt und bleibt (auch auf `window` exportiert, L22683). |

**Gesamt SICHER: 4 Kandidaten**, alle < 1 Zeile Ersparnis pro Fund (kleine, lokale
Restposten aus früheren Refactors), kein struktureller Dead-Code mehr auf Modul-/Feature-Ebene
in dieser Datei.

---

## 2. UNSICHER-BEHALTEN — Zweifel dokumentiert

| # | Symbol | Zeile | Zweifel |
|---|--------|------:|---------|
| 1 | `_photoSrc` | 14837 | 0 Referenzen außer Deklaration in `QuickEditPin` (Ticket-Quick-Edit-Popup). ABER: der Doc-Kommentar direkt über der Komponente (L14827-14828, v3.9.138) beschreibt explizit **"+ Foto-Vorschau"** als Teil des beabsichtigten Feature-Umfangs — die JSX-Rückgabe (L14843-14887 komplett gelesen) rendert aber keinerlei `<img>`. Sieht nach unvollständig verdrahtetem Feature aus (gleiches Muster wie das historische `MATERIAL_UNITS` aus der April-Liste), nicht nach reinem Aufräum-Rest. Löschen würde die letzte Spur eines dokumentierten, aber nie fertiggestellten UI-Teils entfernen. |
| 2 | `asNextWeek` | 21006 | 0 Referenzen außer Deklaration im Chef-Dashboard-Component. `useMemo` mit echten Deps (`[arbeitsscheine,_nextMonStart,_nextMonEnd]`), Kommentar direkt darüber (L21004): "C.4 Geplante AS nächste Woche" — liest sich wie eine geplante KPI-Kachel analog zur direkt daneben tatsächlich gerenderten `nextWeekAbs`-Kachel ("Abwesend nächste Woche", L21285). Die Schwester-Metrik wurde gebaut, aber offenbar nie an einen `_metric(...)`-Aufruf angeschlossen. `NACHT_REPORT.md:304` referenziert die Zeile historisch nur als reinen Perf-Fix (useMemo-Wrapping), nicht als vollständige Feature-Doku — die eigentliche Anzeige-Anbindung fehlt nach wie vor. Unklar ob absichtlich pausiert oder schlicht vergessen; nicht ohne Sebastian-Rückfrage löschen. |

**Gesamt UNSICHER: 2 Kandidaten.**

---

## 3. BEWUSST-TOT — dormante Features, bleiben

| Symbol/Feature | Fundstelle(n) | Status |
|---|---|---|
| `_safeSessionSet` | L1710 | 0 echte App-Aufrufe, aber **test-gepinnt** durch `tests/test_sprint77_coverage.py` (L51-75, prüft Signatur + try/catch + Return-Werte). Im Code selbst als "NICHT geloescht" (v3.9.581) markiert. Klassischer Guard-Test-Fall — genau die im Auftrag genannte TIME_WEEK-Lektion, nur ein anderes Symbol. |
| `TIME_WEEK` | L679 | 0 echte Callsites in `index.html` außerhalb der Deklaration. **Test-gepinnt** durch `tests/test_time_constants.py:26`. Versions-Kommentar (L2819) sagt wörtlich "TIME_WEEK bleibt (test-gepinnt)" — das ist die im Auftrag ausdrücklich zitierte TIME_WEEK-Lektion aus v3.9.621. Nicht anfassen. |
| Stempeluhr-Kiosk (`StempelTafel`, Stempeluhr-Fundament) | L2034-2038, L5787ff, L7654 | Als `(DORMANT)` markiert (v3.9.638ff), aber **nicht wirklich tot** — erreichbar über `?screen=stempel` (admin-only), aktiv weiterentwickelt bis mind. v3.9.694 (Teile A/C/F/G laut Versions-Header). Lohnrelevant, laut TABU-Zone der Aufgabenstellung explizit ausgeschlossen. Zur Kenntnis, kein Cleanup-Kandidat. |
| WhatsApp-Integration (Feature 12) | `sql/README.md`, `ARCHITECTURE.md:146`, `docs/SCHNITTSTELLEN-AUDIT-2026-06-03.md` (Zeilen 36-38, 58-59), `docs/handoff/AGENT-REVIEW-FINDINGS-2026-06-05.md` | Live im Code (`whatsapp_config`/`whatsapp_templates`/`whatsapp_messages`-Endpunkte tatsächlich verdrahtet, `_waSendMessage`), aber bewusst im **Mock-Mode** — kein Live-Versand an Kunden ("keine `whatsapp_config`-Zeile → mockMode → kein Live-Send"). Kein Dead Code, sondern bewusst gedrosselte Integration. |
| FinkZeit / `FINKZEIT_ENABLED` | L2822-2826, L6887, L7595, L11187, L11278-11279, L11878, L12035-12039, L12321, L19672-19673, L20958 | **Aktuell NICHT dormant** — `FINKZEIT_ENABLED=true` seit v3.9.204 ("reaktiviert (04.06. geparkt, nicht gelöscht)"). Der Toggle-Mechanismus (Feature-Flag mit sauberem An/Aus-Pfad) bleibt als bewusstes Architektur-Muster bestehen, auch wenn er im Moment "an" ist — kein Cleanup-Kandidat, da jederzeit reversibel gedacht. |
| Flotte/GPS-WIP (Stash) | `docs/wip/FLOTTE_GPS_WIP_2026-07.md` + `.patch` | Referenziert Bestandscode auf Basis v3.9.672 (Null-Island/NaN-Guard, `fz_latest`-Banner). Weder `pop` noch `drop` ohne Sebastians Freigabe. Vor jeder Löschempfehlung im Flotte-Umfeld geprüft (siehe SICHER #3/#4) — betrifft die dortigen Funde nicht, aber die generelle TABU-Zone bleibt bestehen. |

---

## Zusammenfassung

- **SICHER:** 4 Kandidaten (`pendingPushCount` L8359, `srvBase` L13026, `_tagLabel` L23484, `_seitFmt` L24000)
- **UNSICHER-BEHALTEN:** 2 Kandidaten (`_photoSrc` L14837, `asNextWeek` L21006)
- **BEWUSST-TOT:** 6 Einträge (`_safeSessionSet`, `TIME_WEEK`, Stempeluhr-Kiosk, WhatsApp/Feature-12,
  FinkZeit-Toggle, Flotte/GPS-WIP-Stash)
- **Alte Kandidatenliste (April):** alle 4 verbliebenen Einträge bereits in v3.8.42 gelöscht — nichts offen.

### Die 5 lohnendsten SICHER-Treffer (Rangfolge nach Eindeutigkeit/Sicherheit)

1. **`pendingPushCount`** (L8359) — eindeutigster Fund: Kommentarzeilen direkt davor/danach
   dokumentieren selbst, dass die zugehörige Funktion (`doJuprowaPushAll`) bereits entfernt wurde;
   das ist der übersehene Rest genau dieser Aufräumaktion.
2. **`_tagLabel`** (L23484) — Ersatz durch identisches Inline-Duplikat 220 Zeilen weiter unten
   (L23705) ist im Code selbst nachweisbar, kein Interpretationsspielraum.
3. **`_seitFmt`** (L24000) — reiner 1-Zeilen-Wrapper um `_fzSeitFmt`, das tatsächlich genutzt
   (und auf `window` exportiert) bleibt; die Anzeige ruft die Basisfunktion längst direkt auf.
4. **`srvBase`** (L13026) — Pfad-Berechnung ohne jede Ausgabe, kompletter Component-Return
   gegengelesen.
5. *(kein 5. SICHER-Fund — die Datei ist nach den vorangegangenen Cleanup-Runden bereits sehr
   sauber; die beiden UNSICHER-Fälle `_photoSrc`/`asNextWeek` sind interessanter für Sebastian
   als weitere "sichere" Löschungen, weil sie auf unvollständig verdrahtete Mini-Features
   hindeuten statt auf reinen Aufräum-Rest.)*
