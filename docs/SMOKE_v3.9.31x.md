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

### (w) v3.9.329 Tank-km Admin-Override
**Schritt:** Drei Tests mit verschiedenen Rollen + km < aktueller Stand.
  1. **Monteur** → Fahrzeug → ⛽ Tankung → km eingeben < aktueller Fahrzeug-km → 💾 Speichern. **Erwartung:** Modal blockt mit rotem Hinweis „km-Stand darf nicht kleiner sein als der aktuelle (X km)". Hart-Sperre wie bisher.
  2. **Projektleiter / Büro** → gleicher Test. **Erwartung:** Modal blockt identisch. Kein Admin-Override für PL/Büro.
  3. **Admin** → gleicher Test. **Erwartung:** Modal akzeptiert. Nach Modal-Confirm öffnet sich ein zweites `_confirmModal` mit danger-Variant: „⚠️ km Y ist KLEINER als aktueller Stand (X km). Trotzdem speichern? Das korrigiert den Fahrzeug-km nach unten." Buttons „✓ Korrigieren" / „Zurück". Nach Bestätigung: Tankung wird gespeichert UND `fahrzeuge.kmStand` wird auf Y (den niedrigeren Wert) gesetzt. Toast „⛽ Tankung erfasst · km nach unten korrigiert".
**Hintergrund:** Wenn an der Zapfsäule jemand einen zu HOHEN km-Stand eintippt und das in die DB läuft, konnte ihn vorher niemand nach unten korrigieren. Admin kann jetzt mit zwei Bestätigungen den Stand auf den realen Wert zurücksetzen.
**Pass [ ]**

### (v) v3.9.328 Material canDo-Defense-in-Depth (deleteSuppOrd + deleteCatalog)
**Schritt:** Material-Tab als Monteur einloggen (nicht Admin/PL/Büro).
  1. Eine Händler-Bestellung öffnen → erwartet: kein 🗑-Button mehr (war vorher sichtbar mit "Permission-Toast on click").
  2. DATANORM-Kataloge-Liste → erwartet: kein 🗑-Button neben Katalogen.
  3. Als Admin → Buttons da, Klick öffnet `_confirmModal`, Bestätigung löscht.
**Pass [ ]**

### (u) v3.9.327 Notifs Modal-Guard für delete + Alle-löschen
**Schritt:** Notif-Bell → Liste öffnen → einzelne Benachrichtigung mit ✕ löschen + „🗑️"-Button (Alle löschen) klicken.
**Erwartung:** Vor jeder Aktion `_confirmModal` mit Bestätigungs-Text + Count im Alle-löschen-Dialog. Bei Abbruch keine Änderung.
**Pass [ ]**

### (t) v3.9.326 Urlaubsplanung Modal-Guard für approve/reject
**Schritt:** Urlaub-Tab → einen offenen Antrag genehmigen (✅) und einen anderen ablehnen (❌).
**Erwartung:** Jeweils erscheint ein `_confirmModal` mit Mitarbeitername + Datum: „Urlaub für X am Y wirklich GENEHMIGEN/ABLEHNEN?". Erst nach Bestätigung wird `status` gesetzt + Push-Notification an Mitarbeiter raus. Bei Abbruch keine Änderung.
**Pass [ ]**

### (s) v3.9.325 Wochenplanung Modal-Guard
**Schritt:** Wochenplanung-Tab → bei einer befüllten Zeile a) das „leeren"-Icon klicken und b) das „löschen"-Icon klicken.
**Erwartung:** Vor jeder Aktion erscheint ein `_confirmModal` mit der Rückfrage. Erst nach Bestätigung wird die Zeile geleert / gelöscht. Bei Abbruch bleibt alles unverändert.
**Pass [ ]**

### (r) Nach RLS Welle 1 Phase 1 (Block 0.5+1.1+1.2 live)
**Schritt:** Drei Schnell-Tests mit verschiedenen Rollen:
  1. **Monteur** (z.B. paschinger w1) → Zeiterfassung-Tab → eigene Zeit für heute buchen (Stunden eintragen, speichern). **Erwartung:** Eintrag erscheint sofort, Toast „✅ XXh gespeichert" (oder analog).
  2. **Büro / Projektleiter** (z.B. schober w7 buero oder admin) → Zeiterfassung-Tab → Wochenübersicht eines Monteurs → ✏️-Button auf einem fremden Eintrag → Werte ändern → 💾. **Erwartung:** Toast „✏️ Eintrag aktualisiert" (canDo('zeit_other') + RLS-PUT lässt durch).
  3. **Monteur** (eigenes Fahrzeug) → ⛽ Tankung speichern. **Erwartung:** Toast „⛽ Tankung erfasst" (RLS-Policy `fahrzeuge_update_office_or_driver` + bestehende `fahrzeuge_update_driver` lassen es durch).
**Wenn 1+2+3 grün:** Welle 1 Phase 1 stabil → Sebastian gibt Phase 2 (Blöcke 1.3-1.8) frei.
**Pass [ ]**

### (q) v3.9.323 RLS-Welle-1 Defense-in-Depth (Client)
**Vorbereitung:** Sebastian hat `sql/RLS_WELLE_1_READY_v3.sql` blockweise im Supabase-SQL-Editor ausgeführt. **v1 + v2 sind DEPRECATED** (v1: TEXT-vs-UUID-Lockout; v2: `polname`-statt-`policyname`-Crash + fehlende INSERT-Loop-Branch + nicht vorhandene `is_hr()`).

**Live-Stand 12.06.2026 abends:** Block 0.5 (is_hr bootstrap) ✅, Block 1.1 (fahrzeuge, Snapshot 5 Zeilen, fahrzeuge_update_driver erhalten) ✅, Block 1.2 (time_entries, additiv auf te_read/te_write) ✅. Blöcke 1.3-1.8 stehen aus.
**Schritt:** Als Monteur (z.B. w7) in der App einloggen.
  1. **Eigenes Fahrzeug** öffnen → ⛽ Tankung → Werte eingeben → Speichern. **Erwartung:** Toast „⛽ Tankung erfasst" + Eintrag in der Liste.
  2. **Fremdes Fahrzeug** öffnen → ⛽ Tankung → Werte eingeben → Speichern. **Erwartung:** Toast „⚠️ Fahrzeug-Änderung NICHT gespeichert — keine Schreibberechtigung. Bitte Büro/Admin informieren (Eingabe ging nicht in die Datenbank)." (rot, 9 s).
  3. **Eigenen Zeiteintrag** in der Wochenübersicht bearbeiten → Stunden ändern → Speichern. **Erwartung:** Toast „✏️ Eintrag aktualisiert".
  4. **Fremden Zeiteintrag** versuchen zu bearbeiten (z.B. via direkter SQ.push aus DevTools-Console). **Erwartung:** Toast „⚠️ Zeiteintrag NICHT gespeichert — keine Schreibberechtigung…".
**Hintergrund:** `_RLS_SILENT_DENIAL_LABELS`-Map in `_translateAndExec` triggert den Toast für `fahrzeuge`, `time_entries`, `forms`, `bautagebuch`, `fz_schaeden` sobald die Server-Policies scharf sind.
**Pass [ ]**

### (o) v3.9.319 PDF-Pendant Phase C — Stichprobe 2 Exporte
**Schritt:** (1) Urlaub-Tab → "Edit-Mode" als Admin → "📊 Excel" Button daneben "🖨️ PDF". (2) Werkzeuge-Tab → "🖨️ PDF" neben "📊 Excel".
**Erwartung beide:** Druck-Dialog des Browsers öffnet, UI-Chrome ausgeblendet (`.tab-bar`/`.kpi-grid`/`.no-print`/`.mob-shell-nav`), A4-Seitenformat mit 12mm Rand, Schrift 10pt, EP-Kolar-Footer (Andreas Kolar … FN 042490k … UID ATU20296908) sichtbar. „Als PDF speichern" erzeugt sauberes Dokument.
**Pass [ ]**

### (p) v3.9.321 Tank-Scan nach Tesseract-Removal
**Schritt:** Fahrzeug → ⛽ Tankung → 📷 Foto vom Beleg machen (mit Vision-Server-Pfad, online).
**Erwartung:** OCR liefert Datum/Liter/Preis/km in den Formularfeldern (wenn lesbar). Kein CDN-Lazy-Load mehr (Tesseract weg seit v3.9.321), keine Console-Errors. Offline: graceful Fallback "📷 Beleg gespeichert — Werte manuell eingeben (OCR offline)".
**Hintergrund:** v3.9.321 hat `_loadTesseract`, `_preprocessOcrImage`, `_extractTankFields` (Dead-Code seit v3.9.304) entfernt. parseTankBeleg läuft ausschließlich über Google-Vision-Edge-Function ocr_tankbeleg.
**Pass [ ]**

### (n) v3.9.322 addTank Doppelklick-Guard
**Schritt:** Fahrzeug → ⛽ Tankung → Liter/Preis/km eingeben → 💾 Speichern SEHR SCHNELL doppelt tippen.
**Erwartung:** Es öffnet sich **GENAU EIN** Kontroll-Modal. Nach Confirm landet **GENAU EINE** Tankung in der Liste + DB (kein Duplikat). Der zweite Tap ist no-op (war vorher Race auf 2× upd).
**Hintergrund:** `__addTankInFlight`-Guard analog zu `__addKmInFlight` (v3.9.39), gesetzt direkt beim Eintritt, im finally zurückgesetzt.
**Pass [ ]**

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
**Status:** Phase A (v3.9.315) + Phase B (v3.9.318) + Phase C (v3.9.319: Urlaubskontingent-Edit, Fahrtenbuch, Auswertungen, Bauwochenbericht, Fuhrpark-Uebersicht). **Skipped:** OFFA Excel (dropdown picker — kein 1:1 PDF-Pendant moeglich), Plaene/Tickets-Export (niche).
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

### (k) v3.9.316 Mobile Projekt-Navzeile lesbarer
**Schritt:** Projekt oeffnen auf Handy/iPhone-Safari. Tab-Bar oben (Dashboard / Zeit / Berichte / Plaene / Formulare / Maengel / Checklisten / Bautagebuch / Fotos / Material / Dokumente / OFFA / Export) anschauen + durch die Tabs tippen.
**Erwartung:** Jeder Tab zeigt **Icon UND Label** (vorher nur Icon auf Mobile). Aktiver Tab erkennbar durch dickeren 3px-Underline + farbigen Hintergrund + Bold-Text. Icons groesser (16px statt 12px). Bereich-Wechsel sofort sichtbar. Touch-Target mindestens 44px hoch.
**Pass [ ]**

### (m) v3.9.320 COMPANY_FOOTER-Refactor (Print/PDF/Excel-Footer)
**Schritt:** Beliebigen Excel-Export oder PDF-Print auslösen (z.B. Bautagebuch Excel, Mängel-Report PDF via Print, Bauwochenbericht, Material-Warenkorb-Print).
**Erwartung:** Firmen-Footer (Andreas Kolar & Sohn GesmbH · Marktplatz 17, 3470 Kirchberg am Wagram · Tel +43 2279 2361 · office@ep-kolar.at · FN 042490k, LG St. Pölten · UID: ATU20296908) sieht in JEDEM Output identisch aus. Vorher waren ~13 Stellen hardcoded mit kleinen Abweichungen — jetzt eine `COMPANY_FOOTER`-Konstante (Z.~3964) + Helfer `CF_HTML_LINE1` / `CF_HTML_LINE2` / `CF_HTML_NAME` / `CF_HTML_AGB`.
**Spot-Check:** Wenn künftig die Telefonnummer oder UID wechselt, reicht eine Änderung in der Konstante — die 13 Stellen ziehen automatisch nach.
**Pass [ ]**

### (l) v3.9.317 ProjList Status-Badges (Office-UX)
**Schritt:** Als Admin / Projektleiter / Buero den Projekte-Tab oeffnen → Projekt-Liste.
**Erwartung:** Unter den bekannten KPI-Werten (⏱️h / 💰 / ⚡Gewerk / 📊%) eine zweite Reihe Status-Badges:
  - ⚠️ N (gelb hervorgehoben, nur wenn Maengel offen) — zeigt Anzahl offener Maengel.
  - 📋 N oder „📋 –" (gruen wenn Regiebericht vorhanden, grau wenn keiner).
  - 🤝 ✓ oder „🤝 –" (gruen wenn Abnahmeprotokoll, grau wenn keines).

Hover/Tap zeigt Tooltip mit Klartext.
**Sichtbar:** Nur fuer isAdmin || curUser.role==='buero'. Monteur/Helfer/Techniker sehen die Badges NICHT (kein Office-Use-Case + reduziert Lärm).
**Performance:** Aggregator als useMemo gegen forms/projects — 1 Durchlauf pro Render statt N×M Filter.
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
