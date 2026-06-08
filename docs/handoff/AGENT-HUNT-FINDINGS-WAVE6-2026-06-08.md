# Overnight-Agenten-Bug-Hunt — Welle 6 Funde (2026-06-08, nachts)

2 read-only Audit-Agenten (Export/PDF-Berichte, Mitarbeiter-/Benutzer-Verwaltung). NICHT mehr gefixt (User-Stop
"wenn sauber"); alle als FIX-Kandidaten für die nächste Session dokumentiert. Alle contained + verifiziert am Code.

## Export / PDF-Berichte
- **[HOCH] Export#1 `generateBWB`-Excel ohne UTF-8-BOM → Umlaut-Mojibake** (`index.html:7219`): `new Blob([html],
  {type:"application/vnd.ms-excel"})` — kein `﻿`, kein `;charset=utf-8`. Die Zwillinge `genXls` (3664) +
  `exportBauwochenbericht` (16901) machen es korrekt mit BOM. Live Büro-BWB-Export (Buttons 7264/7271/7380/7398,
  unabhängig FinkZeit) → Müller/Schöller werden beim Kunden/ÖBA als `Ã¼/Ã¶`. **Fix:** `new Blob(["﻿"+html],
  {type:"application/vnd.ms-excel;charset=utf-8"})`. Klarster contained Fix der Welle.
- **[MITTEL] Export#2 `exportAbsCsv` Kontingent/Verbraucht/Rest in JEDER Zeile dupliziert** (`index.html:14360`):
  Bilanzwerte pro MA einmal berechnet (14359), aber in jede Detailzeile geschrieben → Excel-Summe der Spalte überzählt
  (12 Tage → 12× Rest). **Fix:** Bilanz nur in eine Summen-/Kopfzeile pro MA, Detailzeilen leer.
- **[MITTEL/NIEDRIG] Export#3 Datums-Spalten ISO statt de-AT** (`14360` Abwesenheit, `16309` Fahrtenbuch): roh
  `2026-06-07` statt `fdt()` (`DD.MM.YYYY`). Inkonsistent zu allen anderen Exporten. **Fix:** `fdt(dateStr)`.
- Grenzwertig (Info): Dezimalpunkt statt Komma in XLS-Zahlen (`_n` toFixed — bewusste Konvention, genXls-Summe rechnet
  korrekt); `printForm` Signatur-`<img src>` ohne `/^data:image\//`-Check (app-interne Canvas-URIs → low risk).
- Sauber: HTML-Escaping überall (genXls/generateBWB/printForm/exportBauwochenbericht); sumCol-Indizes korrekt
  (Fahrtenbuch sumCol:5=Strecke); KW-Jahr-Label (v3.9.158/169) bereits gefixt.

## Mitarbeiter / Benutzer-Verwaltung
- **[HOCH] MA#1 `monteurId`-Mapping ohne Dedup** (`createUser` 7505/7507, UI 7709): nur username-Dedup, monteurId
  ungeprüft → zwei Accounts können denselben Monteur beanspruchen. monteurId ist Identitäts-Anker (AS-Filter „nur
  eigene" 6112, Fahrtenbuch-Edit 5975, Re-Auth-Rolleninferenz 4773) → beide sehen/bearbeiten dieselben „eigenen"
  Daten = stille Datenisolations-Verletzung. **Fix:** vor Insert `if(nf.monteurId&&users.find(u=>u.monteurId===nf.monteurId)){warn;return;}`.
- **[HOCH] MA#2 `monteurId` nach Anlegen nicht editierbar** (Detail-Panel 7776 read-only, kein Handler): falsch/ohne
  Zuordnung angelegter User sieht dauerhaft keine eigenen Scheine, nur per DB-Direktzugriff behebbar. **Fix:** `<select>`
  + `setMonteurId`-Handler (admin-guard + Dedup aus #1) + `SQ.push PUT /api/users/:id {monteurId}`. (braucht neue UI)
- **[MITTEL] MA#3 Kein E-Mail-Dedup beim Anlegen** (7504/7505): nur username geprüft; E-Mail ist GoTrue-Schlüssel +
  geht an `admin_reset_password(p_email)` (7512) → zwei User gleiche Mail → „PW zurücksetzen" trifft falschen Account.
  **Fix:** case-insensitive E-Mail-Dedup analog username.
- **[NIEDRIG] MA#4 `addMonteur` ohne Dedup/Double-Submit-Ref** (5879, nur `if(!nf.n)`): Doppel-Klick/erneutes Anlegen →
  Monteur-Duplikate mit verschiedenen ids → Auswertung doppelt/halbiert (vgl. AuswertungView-Doppelzählung). **Fix:**
  Namens-Dedup-Warn + `_addingMonteur`-Ref analog createUser.
- Sauber: alle Mutationen admin-guarded + Self-Lock/Delete/Disable doppelt blockiert; togglePermOverride State-konsistent;
  setRole resettet permsOverride; toggleActive konsistent.

> Nächste-Session-Priorität (alle contained): Export#1 (BWB-BOM, kunden-facing) + MA#1/#3 (Dedup, Datenintegrität).
