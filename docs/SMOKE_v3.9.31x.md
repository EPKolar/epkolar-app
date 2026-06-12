# Smoke-Test-Checkliste v3.9.31x

**Stand 2026-06-12, Konsolidierung.** Für Sebastian zum Abklicken. Alles seit v3.9.305 ist hier sichtbar zu prüfen.

## Konsolidierungs-Stand

| Check | Soll | Ist |
|---|---|---|
| `APP_VERSION` / `SW_VER` / sw.js Header / `CACHE_NAME` | synchron | ✅ 3.9.314 |
| Working tree clean (nur Untracked) | clean | ✅ keine modified tracked files |
| `git log origin/main..HEAD` | leer | ✅ 0 ahead |
| OCR Edge-Function letzter Commit | c07e7d7 oder neuer | ✅ c07e7d7 |
| Bracket-Baseline `()` | aktuell dokumentieren | ⚠️ delta -2 (Baseline war -1 → +1 close-paren-Drift, JS bleibt valid, `node_check.py` exit 0) |
| Triade | grün | ✅ pytest 721 passed, node_check exit 0, version-check exit 0 |

## Heutige Aenderungen v3.9.306 → v3.9.314 (auf origin)

| Version | Commit | Inhalt |
|---|---|---|
| v3.9.306 | 352d463 | Tank-Modal editierbar + 0-rows-Safeguard + km-Inputs auf numeric |
| v3.9.307 | 852f56f | Edit-Button ✏️ in ZeiterfassungView (Monteur-Wochenuebersicht) |
| v3.9.308 | e4134f0 | Alle TXT-Exporte aus der App entfernt (nur noch Excel/Drucken) |
| v3.9.309 | 55ef060 | Kachel-Klick scrollt zu Schein-Liste (ArbeitsscheinView) |
| – | c07e7d7 | km-Parser server-seitig zeilenbasiert (STAN/BATCH-Fehlgriff behoben) |
| v3.9.310 | 0582d59 | parseTankBeleg km-Plausi-Guard (OCR-km nur wenn >= aktueller Stand) |
| v3.9.311 | b90c96b | VExport-Vollstaendigkeitspruefung erweitert (ah ergaenzt, sf/dh ok-flags gefixt) — ZUSAETZLICH eingeflossen: MitarbeiterView-Aggregator-Cards (siehe v3.9.312) |
| v3.9.312 | a4b2dbf | Version-Sync (MitarbeiterView-Aggregator-Code war versehentlich in b90c96b mit eingeflossen) |
| v3.9.313 | bf55131 | Tab-Swipe-Fix (touch-action:pan-y + Upper-Bound-Clamp) |
| v3.9.314 | f7e6a8c | Kundenportal-Polishing (Techniker-Name raus, „Anmerkung vom Team", Erklaertexte) |

## Smoke-Tests — bitte abklicken

### (a) Tank-Kontroll-Dialog erscheint vor Speichern + Werte editierbar
**Schritt:** Fahrzeuge → Detail oeffnen → ⛽ Tankung → Liter/Preis/km eingeben → 💾 Speichern.
**Erwartung:** Modal `_tankConfirmModal` poppt vor dem Save mit allen 4 Feldern (Datum/Liter/Preis/km). Werte liessen sich direkt im Modal aendern. Live-Literpreis-Anzeige. Inline-Fehler-Toast bei ungueltigen Werten.
**Pass [ ]**

### (b) km-Sperre blockt kleineren Wert (Monteur)
**Schritt:** Aktueller km-Stand des Fahrzeugs = z.B. 51740. Im Tank-Modal km = 50000 eingeben.
**Erwartung:** Warn-Toast „km-Stand darf nicht kleiner sein als der aktuelle (51.740 km)", Save blockiert. Auch im Quick-Action und Batch-Tank gleiche Sperre.
**Pass [ ]**

### (c) 0-rows-Safeguard: Warnung statt 'gespeichert' wenn Server RLS-ablehnt
**Schritt:** Mit Monteur-Konto fuer ein Fahrzeug einer anderen Monteur-Zuordnung Tankung anlegen (sollte vom RLS abgelehnt werden) — falls nicht reproduzierbar: einfach Sync ablaufen lassen.
**Erwartung:** Statt „⛽ Tankung erfasst" kommt der Error-Toast „⚠️ Fahrzeug-Aenderung NICHT gespeichert — keine Schreibberechtigung fuer dieses Fahrzeug. Bitte Buero/Admin informieren". 9 Sek lang.
**Pass [ ]**

### (d) km-Plausi-Guard: OCR-km < Fahrzeugstand wird verworfen
**Schritt:** Tank-Modal oeffnen (Pre-Befuellung uebernimmt aktuellen km-Stand des Fahrzeugs). Foto-Beleg machen, wo OCR einen niedrigen km-Wert liefert (z.B. STAN/BATCH-Treffer).
**Erwartung:** Toast „⚠️ km vom Beleg unplausibel (<aktueller Stand) — bitte pruefen". `tankKm` bleibt auf der Vorbefuellung (aktueller km-Stand), wird NICHT mit OCR-Wert ueberschrieben. Liter/Preis/Datum aus OCR werden weiterhin uebernommen, wenn plausibel.
**Pass [ ]**

### (e) Edit-Button ✏️ in ZeiterfassungView: 3-fach-Sync
**Schritt:** Als Buero/Admin/PL: Zeiterfassung-Tab → Wochenuebersicht eines Mitarbeiters → bei beliebigem Eintrag das ✏️ klicken → Stunden/Taetigkeit/Bemerkung aendern → 💾 Aenderungen speichern.
**Erwartung:** Toast „✏️ Eintrag aktualisiert". Eintrag in der Wochenuebersicht sofort neu. Wechsel zum Projekt-Tab → VZeit zeigt neuen Wert. Dashboard/KPIs zeigen neuen Wert (Prop-Sync ueber `setEntries`). Eintrag-ID bleibt gleich, kein Duplikat.
**Pass [ ]**

### (f) inputMode: Mobile-Tastatur numerisch bei Liter/Preis/km
**Schritt:** Auf einem Handy (iOS Safari + Android Chrome) Tank-Modal oeffnen + Quick-Action Tank/km + Batch-Tank.
**Erwartung:** Liter/Preis = Dezimal-Tastatur (`inputMode:"decimal"`), km = reines Ziffernpad ohne Komma (`inputMode:"numeric"`). Keine Buchstaben-Tastatur.
**Pass [ ]**

### (g) TXT-Export-Entfernung
**Schritt:** Alle Export-Tabs durchklicken: Bautagebuch, Wochenplanung, Abwesenheit, ZeiterfassungView, Projekt-Export.
**Erwartung:** Nur noch 📊 Excel + 🖨️ Drucken-Buttons. Kein 📄 TXT mehr. Datei-Uploads mit `.txt`-Filter (Lager-Import etc.) bleiben verfuegbar — das ist Absicht.
**Pass [ ]**

### (h) Kachel-Klick scrollt zur Schein-Liste
**Schritt:** ArbeitsscheinView oeffnen, hinunterscrollen damit die Status-Kacheln im Viewport sind. Eine Kachel (z.B. „Offen (alle)") klicken.
**Erwartung:** Filter wird gesetzt, Tab wechselt auf „Liste", Seite scrollt smooth zur Liste (`scrollIntoView`-Animation). Auf Mobile vorher nicht erkennbar dass Liste filtert.
**Pass [ ]**

### (i) v3.9.315 PDF-Pendant — Phase A (3 strategische Stellen)
**Schritt:** In Bautagebuch / Wochenplanung / ZeiterfassungView-Wochenuebersicht je das neue 🖨️ PDF-Button neben Excel klicken.
**Erwartung:** Druck-Dialog des Browsers oeffnet sich, im Print-Preview ist die App-UI ausgeblendet (`.tab-bar`, `.kpi-grid`, `.mob-shell-nav`, Buttons via globalem `@media print`-CSS verborgen). A4-Seite, 12mm Margin, lesbare 10pt-Schrift. „Als PDF speichern" im System-Druckdialog erzeugt sauberes PDF.
**Status:** Phase A — VExport-Tile, Bautagebuch, Wochenplanung, ZeiterfassungView. **Phase B** (Abwesenheit, Fahrtenbuch, Werkzeuge, Auswertungen, MA-Uebersicht KW, OFFA, Projekt-genCsv) bleibt offen.
**Bonus:** `COMPANY_FOOTER`-Konstante (~Z.3962) zentralisiert die Firmen-Footer-Daten — Refactor der hardcoded Strings in genXls/genFormPdf/printPdf folgt schrittweise.
**Pass [ ]**

### (j) MitarbeiterView-Aggregator oeffnet ohne Fehler
**Schritt:** Als Nicht-Admin (Monteur/Techniker/Helfer/Obermonteur) den Tab „Mitarbeiter" oeffnen.
**Erwartung:** Profil zeigt Stammdaten (read-only) + 3 neue Aggregator-Cards:
  - 🌴 Urlaub & Abwesenheit (Jahr): Urlaub/Krank/ZA/Sonstige in Tagen + Nav-Button „→ Urlaub-Tab"
  - ⏱️ Arbeitszeit (Jahr): Gesamt-Stunden, Ø/Woche, Diese/Letzte Woche + „→ Zeiterfassung-Tab"
  - 📋 Meine Arbeitsscheine: Offen/Fertig/Gesamt + „→ Arbeitsscheine-Tab"
Plus die bestehenden FahrbewSection / AnmeldungSection und Passwort-Card.
**Pass [ ]**

### Bonus — Tab-Swipe (v3.9.313)
**Schritt:** Auf Mobile mit dem Finger nach links/rechts ueber den Tab-Content wischen.
**Erwartung:** Wechselt zum naechsten/vorherigen Tab. Bleibt am Anfang/Ende stehen (keine ungueltigen Indizes). Vertikales Scrollen geht weiterhin (touch-action:pan-y).
**Pass [ ]**

### Bonus — Kundenportal (v3.9.314)
**Schritt:** Mit Portal-Code (z.B. GED2024) im Kundenportal einloggen, Maengel-Tab oeffnen.
**Erwartung:** Im Mangel-Detail kein Techniker-Name mehr sichtbar. „Anmerkung vom Team" statt „Rueckmeldung". Info-Box „💡 Was ist ein Mangel?" ueber dem Neuer-Mangel-Formular. Dokumente-Tab erklaert was hier erscheint, wenn leer.
**Pass [ ]**

## Bekannte offene Punkte

- **Rotes „SERVER"-Banner am Handy** — Ursache unklar. Sebastian tippt drauf und meldet den Banner-Text, damit wir die Bedingung finden koennen.
- **Riedmann-Monteur-Tankung als RLS-Beweis** — der historische Fall, bei dem die Tankung still im Sync verloren ging. RLS-Policy `fahrzeuge_update_driver` ist in Prod, und der Client-seitige 0-rows-Safeguard wuerde ein erneutes Auftreten sofort sichtbar machen. **Bitte gezielt re-testen** sobald die Riedmann-Monteur-Zuordnung wieder live ist.
- **km-Parser Riedmann-Beleg** — Original-`rawText` fehlt noch fuer die Regex-Justierung. Wenn der naechste Riedmann-Beleg falsch erkannt wird, bitte `rawText` aus der OCR-Antwort (DevTools Network-Tab → `ocr_tankbeleg`-Response → `rawText`) an mich.
- **Aufraeumen spaeter** (keine Aktion noetig, nur Doku):
  - `ocr-test.html` im Repo-Root — Standalone-Testseite, kann bleiben (nicht Teil des SW-Cache, kein Schaden)
  - Tote Tesseract-Helper in `index.html`: `_loadTesseract` / `_preprocessOcrImage` / `_extractTankFields` — werden seit v3.9.304 nicht mehr aufgerufen (OCR laeuft komplett ueber Google-Vision-Edge-Function). Loeschen oder behalten als Fallback — Entscheidung deferred.

## Geplante naechste Schritte (NICHT in v3.9.31x — abwarten bis Smoke gruen)

- **v3.9.315 Mobile Projekt-Navzeile lesbarer** — User-Report: Tab-Bereiche bei Projekt-Detail schwer erkennbar auf Handy. Recherche laeuft.
- **v3.9.316 PDF-Pendant zu allen Excel-Exporten + CI-Polish** — `COMPANY_FOOTER`-Konstante zentralisieren, Print-CSS perfektionieren, PDF-Buttons an 11 Excel-Stellen.
- **v3.9.317 ProjList Status-Badges** — pro Projekt sofort sichtbar ob Regiebericht/Abnahme fehlt oder Maengel offen sind (Office-UX).

## Validierungs-Triade (vor jedem Commit)
```
python scripts/node_check.py index.html      # exit 0
python -m pytest tests/ -q                    # 721 passed (~110-130 s)
node sql/_check_version.js                    # ✓ versions synced
```
Version-Bump 4 Stellen: `SW_VER` (index.html ~Z.15), `APP_VERSION` (~Z.2360), sw.js Header-Kommentar (Z.1), sw.js `CACHE_NAME` (Z.2).
