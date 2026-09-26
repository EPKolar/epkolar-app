# Grundstand vor dem UI-Umbau

Aufgenommen am 25.09.2026 an der Live-App **v3.9.930** (`f77b53f`),
Mobil-Viewport 390x844 (iframe derselben Origin, weil `resize_window`
bei maximiertem Fenster `innerWidth` nicht ändert).

**Zweck:** Nach jedem Design-Commit wird dieselbe Aufnahme wiederholt.
Was hier steht, muss danach noch da sein. Verschwundene Knöpfe, Felder,
Auswahloptionen oder Zahlen sind ein Regressionsfehler — auch dann,
wenn die Seite hübscher aussieht und alle Tests grün sind.

**Nicht enthalten und bewusst so:** Aussehen, Reihenfolge, Gruppierung,
Beschriftungstexte. Die dürfen sich ändern — darum geht es ja. Geprüft
wird nur, dass die *Handlung* und die *Zahl* erhalten bleiben.

---

## Mengengerüst je Seite

| Seite | Knöpfe | Eingabefelder | Auswahlfelder | erkannte Zahlen |
|---|---|---|---|---|
| Home | 34 | 0 | 0 | 7 |
| Projekte | 19 | 4 | 0 | 6 |
| Arbeitsscheine | 228 | 2 | 1 | 0 |
| Planung | 45 | 0 | 0 | 2 |
| Werkzeuge | 25 | 5 | 3 | 1 |
| Mitarbeiter | 14 | 0 | 0 | 0 |
| Fahrzeuge | 19 | 0 | 0 | 0 |
| Abwesenheiten | 38 | 0 | 0 | 21 |

Die 228 auf Arbeitsscheinen kommen aus der Liste selbst (Aktionsknöpfe je
Schein) — die Zahl schwankt mit dem Datenbestand und ist kein harter Wert.
Bei allen anderen Seiten ist die Zahl stabil und taugt als Prüfgröße.

---

## Home (34 Knöpfe)

Kopf: Sync-Anzeige, Theme, Benachrichtigungen (3), Abmelden, Neu laden,
Einstellungen.

Schnellzugriff: Neues Projekt · Arbeitsscheine · Wochenplanung ·
Urlaub beantragen · Fahrzeuge · Auswertungen · Tanken

Kacheln: Projekte aktiv · Scheine offen · Fahrzeuge · Werkzeugwert
(16 490 €, 296 Geräte) · Abwesenheiten (164, alle bearbeitet) ·
Monatsabrechnung (0/0) · Material (0 von 6) · Bautagebuch (0 diese Woche)

Baustellen-Karten: DR.-GSCHMEIDLERSTRASSE 10 (PA241923, GEDESAG, 523.4h) ·
BVH Sparkasse Ravelsbach (PA242467, 85.2h) · Weingut Gerald Waltner
(PA242231, 39.8h), plus "Alle →"

Zahlen: 48% · 3.5h · 40.5h · 523.4h · 85.2h · 39.8h

Bottom-Bar: Home · Baustelle · Zeit · Fuhrpark · Mehr

## Projekte (19 Knöpfe, 4 Felder)

Ansichtsumschalter (Kachel/Liste) · + Neues Projekt ·
Filter Aktiv 3 / Abgeschlossen 0 / Archiv 0 / Alle 3 ·
je Karte: Bearb. / Archiv / Löschen

## Arbeitsscheine (228 Knöpfe, 2 Felder, 1 Auswahlfeld)

OFFA Excel · Statuskacheln: Gesamt 185 · Offen (alle) 37 · aufgenommen 0 ·
freigegeben 0 · in Bearbeitung 37 · aufgeschoben 0 · erledigt 6 ·
abgerechnet 124 · bar bezahlt 0 · storniert 18 · Fertig (alle) 130

Unterreiter: Liste · QR Scan · Kalender · Dispo

Filter: Alle · Offen · In Arbeit · Erledigt · Meine · Heute · Überfällig ·
Kein Monteur · Filter (aufklappbar)

Suchfeld: "Suche Nr, Kunde, Arbeit..."
Sortierung: Nummer · Erf.-Datum · Termin (best.) · Termin (vorg.) ·
Status · Kunde · Monteur

**Die elf Statuswerte und die sieben Sortierkriterien sind die harte
Prüfliste dieser Seite.**

## Planung (45 Knöpfe)

Woche zurück/vor · KW-Sprungmarken KW12, KW16, KW26–KW38, KW40 ·
Nächste Woche · + Zeile · Vorlage · Vorwoche
Tageszahlen: 5 MA / 4 MA

Beim Umbau entfallen die KW-Sprungmarken als Knöpfe — das ist gewollt.
Erhalten bleiben muss: jede dort erreichbare KW ist weiterhin erreichbar.

## Werkzeuge (25 Knöpfe, 5 Felder, 3 Auswahlfelder)

+ Neues Gerät · Labels · Excel · PDF
Fünf unbeschriftete Icon-Reiter (📷 📋 📤 🔧 ✏️) — **ohne Text, ohne title,
ohne aria-label.** Was sie tun, ist aus dem DOM nicht ermittelbar.
Vor dem Umbau muss geklärt werden, wofür jeder steht.

Filter: Alle (296) · Verfügbar (290) · Ausgegeben (0) ·
Kalibrierung fällig (6) · Defekt (0)
Suchfeld: "Name, Seriennr, Inventar..."
Auswahlfeld Status: Verfügbar · Ausgegeben · In Reparatur ·
Kalibrierung fällig · Verloren/Defekt · Stillgelegt
Auswahlfeld Kategorie: Elektrowerkzeug · Messgeräte · Handwerkzeug ·
Maschinen · Sicherheit/PSA · Verbrauchsmaterial · Kabelwerkzeug ·
Leiter/Gerüst · Sonstiges
Je Gerät: Ausleihen

## Mitarbeiter (14 Knöpfe)

Mein Profil · **Nur Aktive** (der Ehemalige-Umschalter) · + Neuer Mitarbeiter ·
Stempel-Pausenregeln (aufklappbar) · KV-Konstanten Metallgewerbe (aufklappbar)

## Fahrzeuge (19 Knöpfe)

Listen-/Kachelumschalter · Scan · Batch · Labels · Excel · PDF · + Fahrzeug ·
Favoritenstern je Fahrzeug

## Abwesenheiten (38 Knöpfe, 21 Zahlen)

Bearbeiten · Urlaub beantragen · Krankmeldung · Zeitausgleich ·
Anträge prüfen · Details · Datei/Foto hochladen · Excel ·
Server (SRVDC02) · vier Ansichtsreiter

Kontingente: Aliti 193h/0K · Barger 193h/5K · Cracana 193h/9K ·
Günther -13h/0K · Kiener 116h/9K · Lindhuber 116h/0K · Paschinger 116h/0K ·
Pinger 56h/2K · Riedmann 137h/5K · Schmid 116h/0K · Schober 69h/0K

**Aliti und Cracana stehen hier noch drin** — das ist der bekannte
Ehemalige-Fund und wird vom laufenden Ehemalige-Auftrag behoben. Nach
dessen Abschluss ist der Grundstand an dieser Stelle zu aktualisieren,
sonst schlägt die Prüfung fälschlich an.

---

# NACHTRAG (Claude Code, 25.09.2026) — eine Stelle ist bereits überholt

## Abwesenheiten/Kontingente: erwartete Abweichung ab v3.9.931

Der Ehemalige-Auftrag ist seit **v3.9.931** (`1cb8dcc`) angewandt. Die
Kontingentliste in `AbsView` ist damit über `_maIstEhemalig` gefiltert.

**Erwartet ab v3.9.931 — das ist KEIN Regressionsfehler, sondern der Fix:**

- **Aliti und Cracana fehlen in der Kontingentliste.** Elf Namen werden zu
  neun, die "21 erkannten Zahlen" auf der Seite sinken entsprechend.
- Dieselbe Filterung greift in der **Detailtabelle**, im **Excel-Blatt** und
  in dessen **Kopfzeile** ("N Mitarbeiter") — die Gesamtzeile rechnet
  seither über die gefilterte Menge.
- **Home, Kachel "Team aktiv"**: Zähler und Kachelband zeigen nur noch aktive
  Monteure. Die Knopfzahl auf Home kann dadurch unter 34 fallen.

**Was sich dort ausdrücklich NICHT ändern darf** (und wogegen eigene Riegel
laufen, `tests/test_ausgetretene_live_v931.py`):

- Der Arbeitsschein eines Ausgetretenen zeigt seinen Namen weiter — keine
  Fragezeichen, kein leeres Feld. Historie verliert niemanden.
- Die **Auswahl- und Filterlisten** führen ihn weiter (Arbeitsschein-Filter,
  Mängel-Filter, Stundenzettel, Auswertung, Abwesenheits-Kalender).

  🟡 **Präzisiert am 26.09.2026.** Hier stand „Filter-, Report- und
  Kalenderlisten“, und „Auswertung“ in dieser Aufzählung liest sich, als
  müssten auch die **Diagramme** jeden Ausgetretenen zeigen. Gemeint waren
  **Listen, aus denen man auswählt** — und gemessen hat `AuswertungView`
  überhaupt keine: *„Auswahlfelder mit dem ausgetretenen M5: 0 von 0“*. Die
  Mitarbeiterliste speist dort ausschließlich zwei Balkendiagramme.
  Seit v3.9.946 zeigen diese beiden einen Ausgetretenen nur noch, wenn er im
  Zeitraum auch einen **Beitrag** hat. Ein Ausgetretener **mit** Beitrag
  bleibt (Historie verliert niemanden), ein **aktiver** mit 0 bleibt
  („diese Woche nichts“ ist eine Aussage über jemanden, der da ist).
  Die Entscheidung aus v3.9.874 ist damit **nicht** berührt.
  🔴 `tests/test_ausgetretene_live_v931.py` prüft die Auswertungen
  übrigens **nicht** (`grep -ic auswert` = 0) — das war eine Absicht ohne
  Riegel. Seit v3.9.946 gibt es einen.
- Eine **bestehende** Zuweisung bleibt wählbar: der eigene Schein, die
  geladene Fahrerbescheinigung, das getragene Werkzeug.

## Ein zweiter Punkt, der vor dem Umbau geklärt gehört

Der Grundstand nennt die **fünf unbeschrifteten Icon-Reiter in Werkzeuge**
(📷 📋 📤 🔧 ✏️) als "aus dem DOM nicht ermittelbar". Das deckt sich mit dem
Bestandsschutz-Zusatz: sie werden **nicht angefasst, nicht umbenannt, nicht
entfernt**, bis ihr Zweck geklärt ist. Offen, siehe
`docs/ENTSCHEIDUNGEN-OFFEN.md`.

## Wogegen abgenommen wird

Diese Datei ist die Abnahmegrundlage. Bei einer Abweichung gilt die Reihenfolge
aus dem Bestandsschutz-Zusatz: **zurückrollen statt nachbessern.** Eine
Abweichung ohne Begründung ist ein Fehler, kein Detail.

---

# NACHTRAG, 26.09.2026 — „Arbeitsschein bearbeiten"

🔴 **Dies ist NICHT Teil des ursprünglichen Grundstands.** Die Aufnahme oben
wurde am 25.09. an v3.9.930 gemacht, *vor* dem Umbau. Der folgende Abschnitt
ist an **v3.9.942** gemessen, also *mitten im* Umbau, und **niemand hat ihn
abgenommen**. Er steht hier, weil die inhaltsreichste Ansicht der App sonst
überhaupt keine Abnahmegrundlage hätte — nicht, weil er denselben Rang hätte
wie der Rest dieser Datei.

Wer damit vergleicht, vergleicht gegen einen Stand, der schon Änderungen
enthält. Das ist besser als nichts und schlechter als ein echter Grundstand.

Erreicht über den Deep-Link `window.__asOpenId` (v3.9.489, derselbe Weg, den
das Chef-Portal benutzt), die Ansicht belegt über `.as-form-grid` **und** einen
Speichern-Knopf — nicht über den Klickweg, der in dieser Sitzung schon einmal
die falsche Seite bewiesen hat.

## Oberhalb des Formulars (deckungsgleich mit der Liste)

* **11 Statuskacheln**: Gesamt · Offen (alle) · aufgenommen · freigegeben ·
  in Bearbeitung · aufgeschoben · erledigt · abgerechnet · bar bezahlt ·
  storniert · Fertig (alle)
* **4 Unterreiter**: Liste · QR Scan · Kalender · Dispo
* `OFFA Excel`

## Das Formular, in beiden Breiten gleich

* **22 Eingabefelder / Textbereiche.** Platzhalter: `Uhrzeit`, `z.B. 03:00`,
  `z.B. 01:30` (2×), `Was wurde erledigt?`, `Interne Notizen, Anmerkungen...`,
  `Neuer Punkt… (Enter)`, `Kommentar… (@Name = Mention, Ctrl+Enter = Senden)`;
  dazu `date`- und `time`-Felder.
* **4 Auswahlfelder mit zusammen 21 Optionen**:
  * Monteur (3)
  * Priorität (6): aufgeschoben · niedrig · normal · hoch · sehr hoch · FIXTERMIN
  * Scheinstatus (8)
  * Verrechnung (4): — · verrechenbar · nicht verrechenbar · Garantiefall
* **Aktionsknöpfe**: Abbrechen · Verschieben · −/+ (Fahrzeit) · −/+ (Arbeitszeit) ·
  Diktat (3×) · + Material · Aktualisieren · PDF · Storno · Löschen ·
  Speichern & PDF erstellen · Vorschau · + (Checkliste) · Senden (Kommentar)
* **22 Feldbeschriftungen**: Kunden-Nr. · Kundenname \* · Straße · PLZ · Ort ·
  Bestätigt · Vorschlag · Dauer (hh:mm) · Monteur · Fahrzeit (hh:mm) ·
  Arbeitszeit (hh:mm) · Gesamtzeit · Störungsmelder · Durchzuführen \* ·
  Kontakt · Notizen · Projektnr. · Priorität · Scheinstatus ·
  Auftragstyp (OFFA) · Verrechnung · Sachbearbeiter

**Rohzahlen:** 44 Knöpfe / 22 Felder / 4 Auswahlfelder bei 390 px,
59 / 22 / 4 bei 1440 px. Die *Knopfzahlen* sind nur eingeschränkt vergleichbar
— die Zählvorschrift ist nirgends festgelegt, und der Datenbestand der
Messumgebung ist ein anderer als der echte. **Hart sind die benannten Stücke**:
die 21 Auswahloptionen, die 22 Beschriftungen, die 11 Statuskacheln.

---

# OFFENE STELLE IM BESTANDSSCHUTZ (26.09.2026)

**Planung: der Knopf „Vorlage" erscheint in keiner gemessenen Breite.**
Im Grundstand oben steht er (Zeile „+ Zeile · Vorlage · Vorwoche"), und im
Quelltext steht er genau einmal — am Schirm war er bei 375, 390 und 1440 px
nicht zu sehen. Vermutung: er hängt an einer leeren `wpHistory`.

🔴 **Vermutung, nicht Messung.** Damit ist dieser Punkt **nicht bestanden**,
sondern **nicht gemessen** — und ein „nicht gemessen" darf nicht als „in
Ordnung" durchgehen. Was fehlt: ein Lauf mit gefüllter `wpHistory`.
