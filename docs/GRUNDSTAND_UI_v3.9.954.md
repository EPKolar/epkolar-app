# Grundstand nach dem Umbau - v3.9.954

Erhoben am 26.09.2026 mit `scripts/grundstand_erheben.py`, **gemessen an der
gerenderten Seite**, nicht aus dem Quelltext gelesen.

**Zweck.** Nach jedem Umbau wird dieselbe Aufnahme wiederholt. Was hier
steht, muss danach noch da sein. Ein verschwundener Knopf, ein
verschwundenes Feld, eine verschwundene Auswahloption ist ein
Regressionsfehler - auch dann, wenn alles huebscher aussieht und alle
Pruefungen gruen sind.

**Nicht enthalten und bewusst so:** Aussehen, Reihenfolge, Gruppierung,
Beschriftungstexte. Die duerfen sich aendern - darum geht es ja.
Geprueft wird, dass die *Handlung* und die *Zahl* erhalten bleiben.

## 🔴 Was diese Aufnahme NICHT abdeckt

Ein „nicht gemessen" ist **kein** bestandener Fall.

* **Unterzustaende.** Je Ansicht ist der EINE Zustand aufgenommen, in
  den die Navigation fuehrt. Chef hat fuenf, Admin sechs, das
  Buero-Portal fuenf.
* **Alle Rollen ausser `admin`.**
* **Serverleere Ansichten** (Flotte, Gefahrenstoffe, Bauprovisorien und
  mehrere Unterreiter): ihre Zahlen sind die eines leeren Blatts.
* **Alles hinter einem Klick**: Dialoge, Menues, Aufklapper.
* Die Saaten der drei Sondengruppen sind **nicht gleich** (12-15 fuehrt
  fuenf Monteure, davon zwei ausgetretene; 4-7 drei). Zahlen aus
  verschiedenen Gruppen sind deshalb nicht direkt vergleichbar - die
  Gruppe steht bei jeder Ansicht dabei.

---

## Mengengeruest

| Ansicht | Gruppe | Breite | Knoepfe | Felder | Auswahl | Optionen |
|---|---|---|---|---|---|---|
| Werkzeuge | 4-7 | 390 | 18 | 2 | 3 | 22 |
| Werkzeuge | 4-7 | 1440 | 23 | 9 | 2 | 17 |
| Planung / Wochenplanung | 4-7 | 390 | 31 | 0 | 0 | 0 |
| Planung / Wochenplanung | 4-7 | 1440 | 29 | 0 | 0 | 0 |
| Home / Startseite | 4-7 | 390 | 27 | 0 | 0 | 0 |
| Home / Startseite | 4-7 | 1440 | 27 | 0 | 0 | 0 |
| Arbeitsschein bearbeiten | 4-7 | 390 | 34 | 22 | 4 | 21 |
| Arbeitsschein bearbeiten | 4-7 | 1440 | 34 | 22 | 4 | 21 |
| Projektakte / Berichte (Wochenbericht) | 8-11 | 390 | 24 | 0 | 1 | 3 |
| Projektakte / Berichte (Wochenbericht) | 8-11 | 1440 | 30 | 0 | 1 | 3 |
| Projektakte / Bautagebuch | 8-11 | 390 | 24 | 0 | 1 | 3 |
| Projektakte / Bautagebuch | 8-11 | 1440 | 30 | 0 | 1 | 3 |
| Projektakte / Material | 8-11 | 390 | 30 | 1 | 1 | 3 |
| Projektakte / Material | 8-11 | 1440 | 36 | 1 | 1 | 3 |
| Projektakte / Pläne | 8-11 | 390 | 52 | 1 | 1 | 3 |
| Projektakte / Pläne | 8-11 | 1440 | 57 | 1 | 1 | 3 |
| Arbeitsscheine / LISTE | 8-11 | 390 | 56 | 1 | 1 | 7 |
| Arbeitsscheine / LISTE | 8-11 | 1440 | 48 | 13 | 28 | 172 |
| Chef-Dashboard | 12-15 | 390 | 15 | 0 | 0 | 0 |
| Chef-Dashboard | 12-15 | 1440 | 15 | 0 | 0 | 0 |
| Zeiterfassung | 12-15 | 390 | 29 | 5 | 2 | 7 |
| Zeiterfassung | 12-15 | 1440 | 29 | 5 | 2 | 7 |
| Abwesenheiten | 12-15 | 390 | 25 | 0 | 0 | 0 |
| Abwesenheiten | 12-15 | 1440 | 25 | 0 | 0 | 0 |
| Monatsabrechnung | 12-15 | 390 | 3 | 0 | 6 | 63 |
| Monatsabrechnung | 12-15 | 1440 | 3 | 0 | 6 | 63 |
| Fahrzeuge | 12-15 | 390 | 10 | 0 | 0 | 0 |
| Fahrzeuge | 12-15 | 1440 | 10 | 0 | 0 | 0 |
| Flotte / Fuhrpark-GPS | 12-15 | 390 | 12 | 2 | 1 | 1 |
| Flotte / Fuhrpark-GPS | 12-15 | 1440 | 12 | 3 | 1 | 1 |
| Mitarbeiter | 12-15 | 390 | 5 | 0 | 0 | 0 |
| Mitarbeiter | 12-15 | 1440 | 5 | 0 | 0 | 0 |
| Auswertungen | 12-15 | 390 | 101 | 0 | 0 | 0 |
| Auswertungen | 12-15 | 1440 | 101 | 0 | 0 | 0 |
| Büro-Portal | 12-15 | 390 | 10 | 0 | 0 | 0 |
| Büro-Portal | 12-15 | 1440 | 10 | 0 | 0 | 0 |
| Admin | 12-15 | 390 | 19 | 1 | 1 | 3 |
| Admin | 12-15 | 1440 | 19 | 1 | 1 | 3 |
| Einstellungen | 12-15 | 390 | 12 | 4 | 1 | 3 |
| Einstellungen | 12-15 | 1440 | 12 | 4 | 1 | 3 |
| Gefahrenstoffe | 12-15 | 390 | 2 | 1 | 0 | 0 |
| Gefahrenstoffe | 12-15 | 1440 | 2 | 1 | 0 | 0 |
| Bauprovisorien | 12-15 | 390 | 3 | 0 | 0 | 0 |
| Bauprovisorien | 12-15 | 1440 | 3 | 0 | 0 | 0 |

---

## Was an diesen Zahlen wackelt - und was hart ist

**Die rohen Knopf- und Feldzahlen sind nur eingeschraenkt vergleichbar.**
Drei Gruende, alle in dieser Aufnahme sichtbar:

1. **Der Datenbestand.** Die Saat fuehrt sechs Werkzeuge, nicht 296; zwei
   Projekte, nicht drei. Jede Zeile bringt Knoepfe mit. Der alte Grundstand
   nannte fuer Werkzeuge 25 Knoepfe, diese Aufnahme 18 bei 390 px - das ist
   kein verschwundener Knopf, sondern ein anderer Bestand.
2. **Die Breite aendert die Form, nicht nur das Aussehen.** Die
   Arbeitsschein-Liste zeigt bei 390 px Karten und bei 1440 px eine Tabelle
   mit einem Monteur-Auswahlfeld JE ZEILE - daher 28 Auswahlfelder mit 172
   Optionen bei 1440 gegen eines mit 7 bei 390. Beides ist richtig.
3. **Die drei Sondengruppen saeen verschieden.** 12-15 fuehrt fuenf Monteure
   (zwei davon ausgetreten), 4-7 drei. Eine Zahl aus Gruppe 4-7 gegen eine aus
   12-15 zu stellen ist ein Vergleich zweier Welten.

**Hart und vergleichbar sind die BENANNTEN STUECKE**: die Auswahloptionen, die
Feldbeschriftungen, die Statuskacheln, die Unterreiter, die Sortierkriterien.
Genau die prueft `scripts/bestand.py` - 118 Begriffe in 17 Gruppen, und die
Pruefung wird rot, wenn einer fehlt.

---

## Je Ansicht

### Werkzeuge  *(Gruppe 4-7)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 🔧 Werkzeuge & Geräte

2 Felder, Platzhalter: 🔍 Name, Seriennr, Inventar...

Auswahlfeld (7 Optionen): Alle Status · ✅ Verfügbar · 📤 Ausgegeben · 🔧 In Reparatur · 📏 Kalibrierung fällig · ❌ Verloren/Defekt · ⏸️ Stillgelegt

Auswahlfeld (10 Optionen): Alle Kategorien · ⚡ Elektrowerkzeug · 📏 Messgeräte · 🔨 Handwerkzeug · ⚙️ Maschinen · 🦺 Sicherheit/PSA · 📦 Verbrauchsmaterial · 🔌 Kabelwerkzeug · 🪜 Leiter/Gerüst · 📎 Sonstiges

Auswahlfeld (5 Optionen): Inventar · Bezeichnung · Standort · Status · Letzte Wartung

18 Knoepfe: + Neues Gerät · 🏷️ Labels · 📊 Excel · 🖨️ PDF · 📷 · 📋 · 📤 · 🔧 · ✏️ · Alle (6) · ✅ Verfügbar (2) · 📤 Ausgegeben (1) · ⚠️ Kalibrierung fällig (1) · ❌ Defekt (1) · ▲ · 📦 Ausleihen · ✅ Zurückgeben · 📦 Ausleihen

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 🔧 Werkzeuge & Geräte

Tabellenkoepfe:  · Inventar ▲ · Gerät/Werkzeug ↕ · Kategorie ↕ · Status ↕ · Zugewiesen ↕ · Standort ↕ · Wert € ↕ · Zustand ↕ · 

9 Felder, Platzhalter: 🔍 Name, Seriennr, Inventar...

Auswahlfeld (7 Optionen): Alle Status · ✅ Verfügbar · 📤 Ausgegeben · 🔧 In Reparatur · 📏 Kalibrierung fällig · ❌ Verloren/Defekt · ⏸️ Stillgelegt

Auswahlfeld (10 Optionen): Alle Kategorien · ⚡ Elektrowerkzeug · 📏 Messgeräte · 🔨 Handwerkzeug · ⚙️ Maschinen · 🦺 Sicherheit/PSA · 📦 Verbrauchsmaterial · 🔌 Kabelwerkzeug · 🪜 Leiter/Gerüst · 📎 Sonstiges

23 Knoepfe: + Neues Gerät · 🏷️ Labels · 📊 Excel · 🖨️ PDF · 📷 QR Scan · 📋 Liste · 📤 Check-In/Out · 🔧 Service · ✏️ Neu · Alle (6) · ✅ Verfügbar (2) · 📤 Ausgegeben (1) · ⚠️ Kalibrierung fällig (1) · ❌ Defekt (1) · ✏️ · 📦 Ausleihen · ✏️ · ✅ Zurückgeben · ✏️ · ✏️ · 📦 Ausleihen · ✏️ · ✏️

### Planung / Wochenplanung  *(Gruppe 4-7)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: **keine** (kein h1/h2/h3)

31 Knoepfe: ◀ · ▶ · 📅 Nächste Woche ▶ · + Zeile · 📋 Vorwoche · 📅 Planung · 👷 MA-Übersicht · Mo3 MA · Di2 MA · Mi4 MA · Do4 MA · Fr4 MA · Sa— · ▲ · ▼ · ✕ · ▲ · ▼ · ✕ · ▲ · ▼ · ✕ · ▲ · ▼ · ✕ · ▲ · ▼ · ✕ · + Zeile hinzufügen · 📊 Excel · 🖨️ PDF

**1440 px** — Weg: `geklickt/1`

Ueberschriften: **keine** (kein h1/h2/h3)

Tabellenkoepfe: Nr · BVH / Baustelle · Mo📋21.09. · Di📋22.09. · Mi📋23.09. · Do📋24.09. · Fr📋25.09. · Sa📋26.09. · Bem. · 

29 Knoepfe: ◀ · ▶ · 📅 Nächste Woche ▶ · + Zeile · 📋 Vorwoche · 📅 Planung · 👷 MA-Übersicht · ▲ · ▼ · 🗑 · ✕ · ▲ · ▼ · 🗑 · ✕ · ▲ · ▼ · 🗑 · ✕ · ▲ · ▼ · 🗑 · ✕ · ▲ · ▼ · 🗑 · ✕ · 📊 Excel · 🖨️ PDF

### Home / Startseite  *(Gruppe 4-7)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: **keine** (kein h1/h2/h3)

27 Knoepfe: 🔄 · ⚙️ · 🏗️ Neues Projekt · 📋 Arbeitsscheine · 📅 Wochenplanung · 🏖️ Urlaub beantragen · 🚐 Fahrzeuge · 📊 Auswertungen · ⛽ Tanken · 📐 0 · ⚠️ 0 · 📄 Docs · 📐 0 · ⚠️ 0 · 📄 Docs · Projekte aktiv22 gesamt · Scheine offen66 dringend · Fahrzeuge0Alle OK · Werkzeugwert€4 9856 Geräte · Abwesenheiten0Alle bearbeitet · Monatsabrechnung…nicht gemessen · 📦 Material…nicht gemessen · 📝 Bautagebuch…nicht gemessen · Alle → · 23DR.-GSCHMEIDLERSTRASSE 10PA24192 · 67BVH Sparkasse RavelsbachPA242467 · Alle →

**1440 px** — Weg: `geklickt/1`

Ueberschriften: **keine** (kein h1/h2/h3)

27 Knoepfe: 🔄 · ⚙️ · 🏗️ Neues Projekt · 📋 Arbeitsscheine · 📅 Wochenplanung · 🏖️ Urlaub beantragen · 🚐 Fahrzeuge · 📊 Auswertungen · ⛽ Tanken · 📐 0 · ⚠️ 0 · 📄 Docs · 📐 0 · ⚠️ 0 · 📄 Docs · Projekte aktiv22 gesamt · Scheine offen66 dringend · Fahrzeuge0Alle OK · Werkzeugwert€4 9856 Geräte · Abwesenheiten0Alle bearbeitet · Monatsabrechnung…nicht gemessen · 📦 Material…nicht gemessen · 📝 Bautagebuch…nicht gemessen · Alle → · 23DR.-GSCHMEIDLERSTRASSE 10PA24192 · 67BVH Sparkasse RavelsbachPA242467 · Alle →

### Arbeitsschein bearbeiten  *(Gruppe 4-7)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 📋 Arbeitsscheine / Störungen

22 Felder, Platzhalter: Uhrzeit · z.B. 03:00 · z.B. 01:30 · z.B. 01:30 · Was wurde erledigt? · Interne Notizen, Anmerkungen... · Neuer Punkt… (Enter) · Kommentar… (@Name = Mention, Ctrl+Enter = Senden)

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (6 Optionen): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (8 Optionen): aufgenommen · freigegeben · in Bearbeitung · aufgeschoben · erledigt · abgerechnet · bar bezahlt · storniert

Auswahlfeld (4 Optionen): — · verrechenbar · nicht verrechenbar · Garantiefall

34 Knoepfe: 📊 OFFA Excel · Gesamt6Arbeitsscheine · Offen (alle)6zu erledigen · 📋 aufgenommen1offen · ✅ freigegeben2offen · 🔧 in Bearbeitung2offen · ⏸️ aufgeschoben1offen · 🔵 erledigt0fertig · 💰 abgerechnet0fertig · 💵 bar bezahlt0fertig · ❌ storniert0storniert · Fertig (alle)0erledigt+abgerechnet · 📋Liste · 📷QR Scan · 📅Kalender · 🗓Dispo · ✕ Abbrechen · Verschieben · − · + · − · + · 🎤 · 🎤 · + Material · 🎤 · 💾 Aktualisieren · 📄 PDF · ⊘ Storno · 🗑️ · ✅ Speichern & PDF erstellen · 📄 Vorschau · + · Senden

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 📋 Arbeitsscheine / Störungen

22 Felder, Platzhalter: Uhrzeit · z.B. 03:00 · z.B. 01:30 · z.B. 01:30 · Was wurde erledigt? · Interne Notizen, Anmerkungen... · Neuer Punkt… (Enter) · Kommentar… (@Name = Mention, Ctrl+Enter = Senden)

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (6 Optionen): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (8 Optionen): aufgenommen · freigegeben · in Bearbeitung · aufgeschoben · erledigt · abgerechnet · bar bezahlt · storniert

Auswahlfeld (4 Optionen): — · verrechenbar · nicht verrechenbar · Garantiefall

34 Knoepfe: 📊 OFFA Excel · Gesamt6Arbeitsscheine · Offen (alle)6zu erledigen · 📋 aufgenommen1offen · ✅ freigegeben2offen · 🔧 in Bearbeitung2offen · ⏸️ aufgeschoben1offen · 🔵 erledigt0fertig · 💰 abgerechnet0fertig · 💵 bar bezahlt0fertig · ❌ storniert0storniert · Fertig (alle)0erledigt+abgerechnet · 📋Liste · 📷QR Scan · 📅Kalender · 🗓Dispo · ✕ Abbrechen · Verschieben · − · + · − · + · 🎤 · 🎤 · + Material · 🎤 · 💾 Aktualisieren · 📄 PDF · ⊘ Storno · 🗑️ · ✅ Speichern & PDF erstellen · 📄 Vorschau · + · Senden

### Projektakte / Berichte (Wochenbericht)  *(Gruppe 8-11)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste) / Berichte`

Ueberschriften: 📄 Wochenbericht

Tabellenkoepfe: Gewerk · Mo21.09. · Di22.09. · Mi23.09. · Do24.09. · Fr25.09. · Sa26.09. · So27.09. · Σ

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

24 Knoepfe: 🔄 Jetzt sync · ☰ · ◀ · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · Uebersicht · Pläne · Mängel1 · Fotos · Zeiten · Mehr · ◀ · ▶

**1440 px** — Weg: `geklickt/1 / Berichte`

Ueberschriften: 📄 Wochenbericht

Tabellenkoepfe: Gewerk · Mo21.09. · Di22.09. · Mi23.09. · Do24.09. · Fr25.09. · Sa26.09. · So27.09. · Σ

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

30 Knoepfe: 🔄 Jetzt sync · ◀ Alle Projekte · 📊Dashboard · 🗺️Pläne · ⚠️Mängel · 📷Fotos · ⏱️Zeiterfassung · 📄Berichte · 📝Formulare · ✅Checklisten · 📋Bautagebuch · 🔩Material · 📁Dokumente · 🔗OFFA · 📦Export · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · ◀ · ▶

### Projektakte / Bautagebuch  *(Gruppe 8-11)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste) / Bautagebuch`

Ueberschriften: 📋 Bautagebuch

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

24 Knoepfe: 🔄 Jetzt sync · ☰ · ◀ · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · Uebersicht · Pläne · Mängel1 · Fotos · Zeiten · Mehr · ➕ Neuer Eintrag · ➕ Neuer Eintrag

**1440 px** — Weg: `geklickt/1 / Bautagebuch`

Ueberschriften: 📋 Bautagebuch

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

30 Knoepfe: 🔄 Jetzt sync · ◀ Alle Projekte · 📊Dashboard · 🗺️Pläne · ⚠️Mängel · 📷Fotos · ⏱️Zeiterfassung · 📄Berichte · 📝Formulare · ✅Checklisten · 📋Bautagebuch · 🔩Material · 📁Dokumente · 🔗OFFA · 📦Export · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · ➕ Neuer Eintrag · ➕ Neuer Eintrag

### Projektakte / Material  *(Gruppe 8-11)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste) / Material`

Ueberschriften: 🔩 Material-Anforderung0 Anforderungen

1 Felder, Platzhalter: 🔍 Bestellungen suchen (z.B. "hansgrohe 32")

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

30 Knoepfe: 🔄 Jetzt sync · ☰ · ◀ · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · Uebersicht · Pläne · Mängel1 · Fotos · Zeiten · Mehr · 🛒 Warenkorb · 📋 Verlauf · 📦 Lager · 🏪 Bestellungen · ⚙ Katalog · Offen0 · Erledigt · Alle

**1440 px** — Weg: `geklickt/1 / Material`

Ueberschriften: 🔩 Material-Anforderung0 Anforderungen

1 Felder, Platzhalter: 🔍 Bestellungen suchen (z.B. "hansgrohe 32")

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

36 Knoepfe: 🔄 Jetzt sync · ◀ Alle Projekte · 📊Dashboard · 🗺️Pläne · ⚠️Mängel · 📷Fotos · ⏱️Zeiterfassung · 📄Berichte · 📝Formulare · ✅Checklisten · 📋Bautagebuch · 🔩Material · 📁Dokumente · 🔗OFFA · 📦Export · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · 🛒 Warenkorb · 📋 Verlauf · 📦 Lager · 🏪 Bestellungen · ⚙ Katalog · Offen0 · Erledigt · Alle

### Projektakte / Pläne  *(Gruppe 8-11)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste) / Pläne`

Ueberschriften: 🗺️ Pläne & Tickets

1 Felder, Platzhalter: 🔍 Pin-Nr oder Titel suchen…

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

52 Knoepfe: 🔄 Jetzt sync · ☰ · ◀ · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · Uebersicht · Pläne · Mängel1 · Fotos · Zeiten · Mehr · 📤 Plan hochladen · 📥 Export · 🗺️ · 🎫3 · 📐7 · 📁2 · 🏢ErdgeschossErdgeschoss Elektro Re · 🏢1. Obergeschoss1. Obergeschoss Da · ⚡ Elektro👁️ · 🔥 Heizung👁️ · 🚿 Sanitär👁️ · ❄️ Klima/Lüftung👁️ · 🔧 Allgemein👁️ · 🧯 Brandschutz👁️ · 🧱 Baumeister👁️ · 📌 Ticket platzieren · 🎫 Ticket-Liste · 📄 Plan-Report · Alle2 · 🟢 Offen1 · 🟢 Erledigt1 · − · + · ⊡ · ↔ · ⬚ · ⛶ · 📥 · 📍 · 📌

**1440 px** — Weg: `geklickt/1 / Pläne`

Ueberschriften: 🗺️ Pläne & Tickets

1 Felder, Platzhalter: 🔍 Pin-Nr oder Titel suchen…

Auswahlfeld (3 Optionen): Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

57 Knoepfe: 🔄 Jetzt sync · ◀ Alle Projekte · 📊Dashboard · 🗺️Pläne · ⚠️Mängel · 📷Fotos · ⏱️Zeiterfassung · 📄Berichte · 📝Formulare · ✅Checklisten · 📋Bautagebuch · 🔩Material · 📁Dokumente · 🔗OFFA · 📦Export · 🏠Home · 👑Chef · 🏗️Projekte · 📋Arbeitsscheine · 📅Planung · ⏱️Zeiterfassung · 🏖️Abwesenheiten · 📄Monatsabrechnung · 🚐Fahrzeuge · 🛰️Flotte · 🔧Werkzeuge · 🚧Bauprovisorien · ☣️Gefahrenstoffe · 📤 Plan hochladen · 📥 Export · 🗺️Plan-Viewer · 🎫Alle Tickets3 · 📐Ebenen7 · 📁Planverwaltung2 · 🏢ErdgeschossErdgeschoss Elektro Re · 🏢1. Obergeschoss1. Obergeschoss Da · ⚡ Elektro👁️ · 🔥 Heizung👁️ · 🚿 Sanitär👁️ · ❄️ Klima/Lüftung👁️ · 🔧 Allgemein👁️ · 🧯 Brandschutz👁️ · 🧱 Baumeister👁️ · 📌 Ticket platzieren · 🎫 Ticket-Liste · 📄 Plan-Report · Alle2 · 🟢 Offen1 · 🟢 Erledigt1 · − · + · ⊡ · ↔ · ⬚ · ⛶ · 📥 · 📍

### Arbeitsscheine / LISTE  *(Gruppe 8-11)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 📋 Arbeitsscheine / Störungen

1 Felder, Platzhalter: 🔍 Suche Nr, Kunde, Arbeit...

Auswahlfeld (7 Optionen): Nummer · Erf.-Datum · Termin (best.) · Termin (vorg.) · Status · Kunde · Monteur

56 Knoepfe: 📊 OFFA Excel · Gesamt6Arbeitsscheine · Offen (alle)6zu erledigen · 📋 aufgenommen1offen · ✅ freigegeben2offen · 🔧 in Bearbeitung2offen · ⏸️ aufgeschoben1offen · 🔵 erledigt0fertig · 💰 abgerechnet0fertig · 💵 bar bezahlt0fertig · ❌ storniert0storniert · Fertig (alle)0erledigt+abgerechnet · 📋Liste · 📷QR Scan · 📅Kalender · 🗓Dispo · Alle · 🟡 Offen · 🔧 In Arbeit · ✅ Erledigt · 👤 Meine · 📅 Heute · 🔴 Überfällig · ⚠️ Kein Monteur · ▸ Filter · ▼ · AS-2406🔧 in BearbeitungPfarre Sank · ✏️ · 📄 · ⬜ · ⊘ · AS-2405⏸️ aufgeschobenSparkasse Ra · ✏️ · 📄 · ⬜ · ⊘ · AS-2404✅ freigegebenWeingut Gerald · ✏️ · 📄 · ⬜ · ⊘ · AS-2403📋 aufgenommenGEDESAG Gemein · ✏️ · 📄 · ⬜ · ⊘ · AS-2402🔧 in BearbeitungHinterleitn · ✏️ · 📄 · ⬜ · ⊘ · AS-2401✅ freigegebenMarktgemeinde  · ✏️ · 📄 · ⬜ · ⊘

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 📋 Arbeitsscheine / Störungen

Tabellenkoepfe: Nummer ▼ · Durchzuführende Arbeiten ↕ · Erf.-Datum ↕ · Vorgeschl. ↕ · Bestätigt ↕ · Status ↕ · Priorität ↕ · Auftragstyp ↕ · SB ↕ · Monteur ↕ · Kundenname ↕ · Projektnr. ↕ · Aktionen

13 Felder, Platzhalter: 🔍 Suche Nr, Kunde, Arbeit...

Auswahlfeld (11 Optionen): Alle Status · — Offen (alle) — · — Fertig (alle) — · 📋 aufgenommen · ✅ freigegeben · 🔧 in Bearbeitung · ⏸️ aufgeschoben · 🔵 erledigt · 💰 abgerechnet · 💵 bar bezahlt · ❌ storniert

Auswahlfeld (10 Optionen): Alle Arten · kein · Störung · Lieferung · Reparatur · Montage · Mangelbehebung · Garantie · Wartung · Regie

Auswahlfeld (4 Optionen): Alle Monteure · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (2 Optionen): Alle SB · Bernadette Wieshofer-Prandtn

Auswahlfeld (8 Optionen): 📋 aufgenommen · ✅ freigegeben · 🔧 in Bearbeitung · ⏸️ aufgeschoben · 🔵 erledigt · 💰 abgerechnet · 💵 bar bezahlt · ❌ storniert

Auswahlfeld (6 Optionen): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (6 Optionen): — · Bernadette Wieshofer-Prandtn · SCHOBER · LINDHUBER · GÜNTHER · SCHMID

Auswahlfeld (4 Optionen): — · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (8 Optionen): 📋 aufgenommen · ✅ freigegeben · 🔧 in Bearbeitung · ⏸️ aufgeschoben · 🔵 erledigt · 💰 abgerechnet · 💵 bar bezahlt · ❌ storniert

Auswahlfeld (6 Optionen): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (6 Optionen): — · Bernadette Wieshofer-Prandtn · SCHOBER · LINDHUBER · GÜNTHER · SCHMID

Auswahlfeld (4 Optionen): — · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (8 Optionen): 📋 aufgenommen · ✅ freigegeben · 🔧 in Bearbeitung · ⏸️ aufgeschoben · 🔵 erledigt · 💰 abgerechnet · 💵 bar bezahlt · ❌ storniert

Auswahlfeld (6 Optionen): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (6 Optionen): — · Bernadette Wieshofer-Prandtn · SCHOBER · LINDHUBER · GÜNTHER · SCHMID

Auswahlfeld (4 Optionen): — · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (8 Optionen): 📋 aufgenommen · ✅ freigegeben · 🔧 in Bearbeitung · ⏸️ aufgeschoben · 🔵 erledigt · 💰 abgerechnet · 💵 bar bezahlt · ❌ storniert

Auswahlfeld (7 Optionen): keine · aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (6 Optionen): — · Bernadette Wieshofer-Prandtn · SCHOBER · LINDHUBER · GÜNTHER · SCHMID

Auswahlfeld (4 Optionen): — · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (8 Optionen): 📋 aufgenommen · ✅ freigegeben · 🔧 in Bearbeitung · ⏸️ aufgeschoben · 🔵 erledigt · 💰 abgerechnet · 💵 bar bezahlt · ❌ storniert

Auswahlfeld (6 Optionen): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (6 Optionen): — · Bernadette Wieshofer-Prandtn · SCHOBER · LINDHUBER · GÜNTHER · SCHMID

Auswahlfeld (4 Optionen): — · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

Auswahlfeld (8 Optionen): 📋 aufgenommen · ✅ freigegeben · 🔧 in Bearbeitung · ⏸️ aufgeschoben · 🔵 erledigt · 💰 abgerechnet · 💵 bar bezahlt · ❌ storniert

Auswahlfeld (6 Optionen): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN

Auswahlfeld (6 Optionen): — · Bernadette Wieshofer-Prandtn · SCHOBER · LINDHUBER · GÜNTHER · SCHMID

Auswahlfeld (4 Optionen): — · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn

48 Knoepfe: 📊 OFFA Excel · Gesamt6Arbeitsscheine · Offen (alle)6zu erledigen · 📋 aufgenommen1offen · ✅ freigegeben2offen · 🔧 in Bearbeitung2offen · ⏸️ aufgeschoben1offen · 🔵 erledigt0fertig · 💰 abgerechnet0fertig · 💵 bar bezahlt0fertig · ❌ storniert0storniert · Fertig (alle)0erledigt+abgerechnet · 📋Liste · 📷QR Scan · 📅Kalender · 🗓Dispo · Alle · 🟡 Offen · 🔧 In Arbeit · ✅ Erledigt · 👤 Meine · 📅 Heute · 🔴 Überfällig · ⚠️ Kein Monteur · ✏️ · 📄 · ⬜ · ⊘ · ✏️ · 📄 · ⬜ · ⊘ · ✏️ · 📄 · ⬜ · ⊘ · ✏️ · 📄 · ⬜ · ⊘ · ✏️ · 📄 · ⬜ · ⊘ · ✏️ · 📄 · ⬜ · ⊘

### Chef-Dashboard  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 👑 Chef-Portal

15 Knoepfe: 👑 Überblick · 🏗️ Projekte · 📋 Arbeit · 👥 Personal · 📦 Ressourcen · Aktive Projekte22 gesamt · Offene AS6→8 gesamt · vs. Vorwoche · Monteure heute0/3aktiv (ZE) · Heutige AS1↑ +12026-09-26 · vs. Vo · Überfällig5↑ +5🔴 kritisch · vs. Vo · 🚨Handlungsbedarf1▸ · ✅ Erledigt, noch nicht fakturiert: · 🎫Mängel & Tickets▸ · …Offene Tickets · …Offene Mängel

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 👑 Chef-Portal

15 Knoepfe: 👑 Überblick · 🏗️ Projekte · 📋 Arbeit · 👥 Personal · 📦 Ressourcen · Aktive Projekte22 gesamt · Offene AS6→8 gesamt · vs. Vorwoche · Monteure heute0/3aktiv (ZE) · Heutige AS1↑ +12026-09-26 · vs. Vo · Überfällig5↑ +5🔴 kritisch · vs. Vo · 🚨Handlungsbedarf1▸ · ✅ Erledigt, noch nicht fakturiert: · 🎫Mängel & Tickets▸ · …Offene Tickets · …Offene Mängel

### Zeiterfassung  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: **keine** (kein h1/h2/h3)

5 Felder, Platzhalter: keine

Auswahlfeld (4 Optionen): — Mitarbeiter wählen — · Gerhard Steinbichler (Monteu · Johannes Hinterleitner (Ober · Bernadette Wieshofer-Prandtn

Auswahlfeld (3 Optionen): — Projekt wählen — · DR.-GSCHMEIDLERSTRASSE 10 (P · BVH Sparkasse Ravelsbach (PA

29 Knoepfe: ◀ · ▶ · 👥 Alle Monteure · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · + Eintrag · 📋 Wochen-Stundenbestätigung · 📊 Übersicht Excel · 🖨️ PDF · Mo 21.09. · Di 22.09. · Mi 23.09. · Do 24.09. · Fr 25.09. · 📊 Export KW 39 · 🖨️ PDF

**1440 px** — Weg: `geklickt/1`

Ueberschriften: **keine** (kein h1/h2/h3)

5 Felder, Platzhalter: keine

Auswahlfeld (4 Optionen): — Mitarbeiter wählen — · Gerhard Steinbichler (Monteu · Johannes Hinterleitner (Ober · Bernadette Wieshofer-Prandtn

Auswahlfeld (3 Optionen): — Projekt wählen — · DR.-GSCHMEIDLERSTRASSE 10 (P · BVH Sparkasse Ravelsbach (PA

29 Knoepfe: ◀ · ▶ · 👥 Alle Monteure · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · ✏️ · ✕ · + Eintrag · + Eintrag · 📋 Wochen-Stundenbestätigung · 📊 Übersicht Excel · 🖨️ PDF · Mo 21.09. · Di 22.09. · Mi 23.09. · Do 24.09. · Fr 25.09. · 📊 Export KW 39 · 🖨️ PDF

### Abwesenheiten  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 📅 Abwesenheiten

25 Knoepfe: ✏️ Bearbeiten · 🏖️ Urlaub beantragen · 🤒 Krankmeldung · ⏰ Zeitausgleich · 📨 Anträge prüfen · ▼ Details · ✏️ Bearbeiten · ⬆️Datei oder Foto hochladenPDF, JP · 📊 Excel · 🖥️ Server (SRVDC02) · 📅 · 📨 · 📊 · 🗓️ · Gerhard Steinbichler193h · 0K · Johannes Hinterleitner193h · 0K · Bernadette Wieshofer-Prandtner193h · Ferdinand Aschenbrennerausgetreten · Roswitha Puchleitnerausgetreten ·  · 🏖️ Urlaub · 🤒 Krankenstand · ⏰ Zeitausgleich · ▸ Weitere… · ◀ · ▶

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 📅 Abwesenheiten

25 Knoepfe: ✏️ Bearbeiten · 🏖️ Urlaub beantragen · 🤒 Krankmeldung · ⏰ Zeitausgleich · 📨 Anträge prüfen · ▼ Details · ✏️ Bearbeiten · ⬆️Datei oder Foto hochladenPDF, JP · 📊 Excel · 🖥️ Server (SRVDC02) · 📅 Kalender · 📨 Anträge (?) · 📊 Übersicht · 🗓️ Team-Timeline · Gerhard Steinbichler193h Rest · 0K · Johannes Hinterleitner193h Rest ·  · Bernadette Wieshofer-Prandtner193h · Ferdinand Aschenbrennerausgetreten · Roswitha Puchleitnerausgetreten ·  · 🏖️ Urlaub · 🤒 Krankenstand · ⏰ Zeitausgleich · ▸ Weitere… · ◀ · ▶

### Monatsabrechnung  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 📄 Monatsabrechnung

Auswahlfeld (14 Optionen): — Mitarbeiter wählen — · Günther Sebastian · Paschinger Norbert · Cracana Sorin · Barger Ian · Pinger Leo · Schmid Wolfgang · Schober Martina · Lindhuber Lucia · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn · Ferdinand Aschenbrenner · Roswitha Puchleitner

Auswahlfeld (12 Optionen): Jänner · Februar · März · April · Mai · Juni · Juli · August · September · Oktober · November · Dezember

Auswahlfeld (5 Optionen): 2024 · 2025 · 2026 · 2027 · 2028

Auswahlfeld (13 Optionen): Alle Monate · Jänner · Februar · März · April · Mai · Juni · Juli · August · September · Oktober · November · Dezember

Auswahlfeld (5 Optionen): 2024 · 2025 · 2026 · 2027 · 2028

Auswahlfeld (14 Optionen): Alle Mitarbeiter · Günther Sebastian · Paschinger Norbert · Cracana Sorin · Barger Ian · Pinger Leo · Schmid Wolfgang · Schober Martina · Lindhuber Lucia · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn · Ferdinand Aschenbrenner · Roswitha Puchleitner

3 Knoepfe: 🖨️ Monatsübersicht drucken · ◀ · ▶

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 📄 Monatsabrechnung

Auswahlfeld (14 Optionen): — Mitarbeiter wählen — · Günther Sebastian · Paschinger Norbert · Cracana Sorin · Barger Ian · Pinger Leo · Schmid Wolfgang · Schober Martina · Lindhuber Lucia · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn · Ferdinand Aschenbrenner · Roswitha Puchleitner

Auswahlfeld (12 Optionen): Jänner · Februar · März · April · Mai · Juni · Juli · August · September · Oktober · November · Dezember

Auswahlfeld (5 Optionen): 2024 · 2025 · 2026 · 2027 · 2028

Auswahlfeld (13 Optionen): Alle Monate · Jänner · Februar · März · April · Mai · Juni · Juli · August · September · Oktober · November · Dezember

Auswahlfeld (5 Optionen): 2024 · 2025 · 2026 · 2027 · 2028

Auswahlfeld (14 Optionen): Alle Mitarbeiter · Günther Sebastian · Paschinger Norbert · Cracana Sorin · Barger Ian · Pinger Leo · Schmid Wolfgang · Schober Martina · Lindhuber Lucia · Gerhard Steinbichler · Johannes Hinterleitner · Bernadette Wieshofer-Prandtn · Ferdinand Aschenbrenner · Roswitha Puchleitner

3 Knoepfe: 🖨️ Monatsübersicht drucken · ◀ · ▶

### Fahrzeuge  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 🚐 Fahrzeugverwaltung

10 Knoepfe: ☰ · ⊞ · 📷 Scan · ⛽ Batch · 🏷️ Labels · 📊 Excel · 🖨️ PDF · + Fahrzeug · ☆ · ☆

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 🚐 Fahrzeugverwaltung

10 Knoepfe: ☰ · ⊞ · 📷 Scan · ⛽ Batch · 🏷️ Labels · 📊 Excel · 🖨️ PDF · + Fahrzeug · ☆ · ☆

### Flotte / Fuhrpark-GPS  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: **keine** (kein h1/h2/h3)

2 Felder, Platzhalter: keine

Auswahlfeld (1 Optionen): 🚐 Alle Fahrzeuge

12 Knoepfe: ▸ 🚐 Fahrzeuge (3) · + · − · Layers · Fahrten · Tageskilometer · Geschwindigkeit · ⛶ · Heute · Woche · Monat · Vormonat

**1440 px** — Weg: `geklickt/1`

Ueberschriften: **keine** (kein h1/h2/h3)

3 Felder, Platzhalter: 🔎 Kennzeichen, Marke, Fahrer …

Auswahlfeld (1 Optionen): 🚐 Alle Fahrzeuge

12 Knoepfe: ▸ ➖ 3 ohne Tracker · + · − · Layers · Fahrten · Tageskilometer · Geschwindigkeit · ⛶ · Heute · Woche · Monat · Vormonat

### Mitarbeiter  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 👷 Mitarbeiter & Zuweisungen

5 Knoepfe: 👤 Mein Profil · Nur Aktive · + Neuer Mitarbeiter · ⏱ Stempel-Pausenregeln▼ · ⚙ KV-Konstanten (Metallgewerbe)▼

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 👷 Mitarbeiter & Zuweisungen

5 Knoepfe: 👤 Mein Profil · Nur Aktive · + Neuer Mitarbeiter · ⏱ Stempel-Pausenregeln▼ · ⚙ KV-Konstanten (Metallgewerbe)▼

### Auswertungen  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 📊 Auswertungen & Dashboards

101 Knoepfe: 📥 Alle als Excel · 🖨️ PDF · 👁️ Alle ausblenden · nach Projektende · nach Projektstart · ▸📋 Arbeitsscheine3 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🏗️ Projekte2 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸⏱️ Zeiterfassung1 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🏖️ Abwesenheiten2 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🔧 Werkzeuge3 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🚐 Fahrzeuge4 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 📊 Auswertungen & Dashboards

101 Knoepfe: 📥 Alle als Excel · 🖨️ PDF · 👁️ Alle ausblenden · nach Projektende · nach Projektstart · ▸📋 Arbeitsscheine3 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🏗️ Projekte2 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸⏱️ Zeiterfassung1 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🏖️ Abwesenheiten2 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🔧 Werkzeuge3 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · ▸🚐 Fahrzeuge4 Diagramme · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶 · Diagramm ausblenden · 📊 · 🥧 · 🍩 · 📈 · 📶

### Büro-Portal  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: 📋 Büro-Export

10 Knoepfe: 📁 Projekte · ⏱ Stempelzeiten · 💶 Zulagen · 📅 Abwesenheiten · ⛽ Tank · 📥 Alle als Excel · ▸ Vorschau · 📥 Excel · ▸ Vorschau · 📥 Excel

**1440 px** — Weg: `geklickt/1`

Ueberschriften: 📋 Büro-Export

10 Knoepfe: 📁 Projekte · ⏱ Stempelzeiten · 💶 Zulagen · 📅 Abwesenheiten · ⛽ Tank · 📥 Alle als Excel · ▸ Vorschau · 📥 Excel · ▸ Vorschau · 📥 Excel

### Admin  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: ⚙️ Administration

1 Felder, Platzhalter: 🔍 Benutzer suchen…

Auswahlfeld (3 Optionen): Sort: Rolle · Sort: Name · Sort: Letzter Login

19 Knoepfe: + Neuer Benutzer · 👤 Benutzer · 📋 Aktivität · 📊 Statistiken · 🏪 Händler · 🔗 Juprowa · ⚙️ System · Alle · 👑 Administrator · 🏗️ Projektleiter · 📋 Büro · ⭐ Obermonteur · 🔬 Techniker · 🔧 Monteur · 👷 Helfer · 👁️ Nur Lesen · ➕ Login erstellen · ➕ Login erstellen · ➕ Login erstellen

**1440 px** — Weg: `geklickt/1`

Ueberschriften: ⚙️ Administration

1 Felder, Platzhalter: 🔍 Benutzer suchen…

Auswahlfeld (3 Optionen): Sort: Rolle · Sort: Name · Sort: Letzter Login

19 Knoepfe: + Neuer Benutzer · 👤 Benutzer · 📋 Aktivität · 📊 Statistiken · 🏪 Händler · 🔗 Juprowa · ⚙️ System · Alle · 👑 Administrator · 🏗️ Projektleiter · 📋 Büro · ⭐ Obermonteur · 🔬 Techniker · 🔧 Monteur · 👷 Helfer · 👁️ Nur Lesen · ➕ Login erstellen · ➕ Login erstellen · ➕ Login erstellen

### Einstellungen  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: ⚙️ Einstellungen

4 Felder, Platzhalter: Altes Passwort · Neues Passwort · Neues Passwort wiederholen

Auswahlfeld (3 Optionen): ⚡🚿 Beide (alles anzeigen) · ⚡ Elektriker · 🚿🔥❄️ Installateur

12 Knoepfe: 👁️ · 👁️ · 👁️ · 💾 Passwort ändern · 🔍 Verbindung testen · ☀️ Hell · 🌙 Dunkel · 🅰️ Auto · 🔄 Jetzt synchronisieren · 🗑️ Lokale Daten löschen · ✓ Smoke-Tests · 🔍 Integrität

**1440 px** — Weg: `geklickt/1`

Ueberschriften: ⚙️ Einstellungen

4 Felder, Platzhalter: Altes Passwort · Neues Passwort · Neues Passwort wiederholen

Auswahlfeld (3 Optionen): ⚡🚿 Beide (alles anzeigen) · ⚡ Elektriker · 🚿🔥❄️ Installateur

12 Knoepfe: 👁️ · 👁️ · 👁️ · 💾 Passwort ändern · 🔍 Verbindung testen · ☀️ Hell · 🌙 Dunkel · 🅰️ Auto · 🔄 Jetzt synchronisieren · 🗑️ Lokale Daten löschen · ✓ Smoke-Tests · 🔍 Integrität

### Gefahrenstoffe  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: ☣️ Gefahrenstoffe — Sicherheitsdatenblätter

1 Felder, Platzhalter: 🔍 Suchen (Name, Lieferant, Notiz)…

2 Knoepfe: 📁 + Ordner · 📤 PDF hochladen

**1440 px** — Weg: `geklickt/1`

Ueberschriften: ☣️ Gefahrenstoffe — Sicherheitsdatenblätter

1 Felder, Platzhalter: 🔍 Suchen (Name, Lieferant, Notiz)…

2 Knoepfe: 📁 + Ordner · 📤 PDF hochladen

### Bauprovisorien  *(Gruppe 12-15)*

**390 px** — Weg: `geklickt/1 (ohne Fussleiste)`

Ueberschriften: **keine** (kein h1/h2/h3)

3 Knoepfe: 🔄 Kunden synchronisieren · + Neu · 📷 Kasten-QR scannen & öffnen

**1440 px** — Weg: `geklickt/1`

Ueberschriften: **keine** (kein h1/h2/h3)

3 Knoepfe: 🔄 Kunden synchronisieren · + Neu · 📷 Kasten-QR scannen & öffnen
