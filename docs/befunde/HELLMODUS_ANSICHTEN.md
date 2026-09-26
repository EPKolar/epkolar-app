# Hellmodus in ALLEN Ansichten - Messung 26.09.2026

> **Stand dieses Dokuments.** Die Abschnitte bis einschliesslich
> "Protokoll" sind die Erstmessung gegen v3.9.939
> (`_mess_stand_939.html`). Danach folgen zwei spaetere Abschnitte:
> **Gegenmessung nach v3.9.942** (der Befund unten ist behoben) und
> **Die vier Schwestern - gemessen** (die damals ungemessenen Stellen).
> Jeder Abschnitt nennt die Datei und den md5, gegen die er gemessen hat.

Gemessen mit `scripts/hellmodus_ansichten.py` gegen die EINGEFRORENE
Kopie `_mess_stand_939.html` (md5 vor dem Lauf `f750cdcb888a46b85f8b8504abec39ea`, danach `f750cdcb888a46b85f8b8504abec39ea`).
`index.html` wurde nicht angefasst. Quelle: `http://127.0.0.1:55097/_mess_stand_939.html`. Laufzeit 612 s.

Aufbau je Ansicht: `epk_theme='light'`, Betriebssystem auf DUNKEL
(`color_scheme="dark"`), 390 px und 1440 px, Rolle `admin` mit
`monteurId='M1'`, alle `/rest/v1/`- und `/auth/v1/`-Anfragen abgebrochen.
Eine Farbe gilt als dunkel bei relativer Helligkeit unter 0.5, eine
Flaeche als TRAGEND ab 25 % des Schirms. Halbdurchsichtige Farben
werden gegen den Untergrund gemischt, `rgba(0,0,0,0)` faellt aus der
Wertung - beides sind behobene Messfehler der Vorgaengerfassung.

**Zwei Masse, je Ansicht zweimal aufgenommen (oben und nach dem
Rollen):**

- **(A) Flaechensuche** (aus `scripts/hellmodus_messen.py` importiert):
  jedes Element ab 8000 px2, gemischte Farbe, Flaeche. Sie findet
  Flaechen, die es GIBT - auch solche, die gerade unter der Kante
  liegen, denn sie rechnet mit dem vollen Rechteck.
- **(B) Raster-Abtastung** des Schirms, 24 x 40 Punkte: je Punkt
  `elementFromPoint`, Farbstapel gemischt, Helligkeit. Sie misst, was
  man SIEHT.

Geurteilt wird nach (B). Der Unterschied ist kein Feinschliff: in der
Ansicht `Projekt/Plaene` meldete (A) bei 390 px 78 % Anteil fuer die
schwarze Planflaeche, waehrend (B) 7,6 % mass - die Flaeche lag knapp
unter der Kante. Erst nach dem Rollen des INNEREN Behaelters
(`.proj-main`; das Fenster rollt in der Projekt-Huelle nicht, sie ist
`100dvh` mit `overflow:hidden`) sind es 57,5 %. Eine Ansicht, in der
(A) etwas findet und (B) nichts sieht, bekommt das Urteil
"Flaeche im Baum, nicht auf dem Schirm" - weder gruen noch Befund.

## Der Koeder

Derselbe Lauf mit `epk_theme='dark'` MUSS in jeder Ansicht in BEIDEN
Massen anschlagen: (A) mindestens eine tragende Flaeche UND (B) ein
Schirm ab 25 % dunkel. Wo eines der beiden versagt, hat das Werkzeug
dort nichts gemessen, und die Aussage ueber den Hellmodus dieser
Ansicht ist wertlos - Urteil dann NICHT GEMESSEN, nicht gruen.

Die Prozentzahl in Klammern ist das Mass (A) der groessten Flaeche. Sie
kann ueber 100 % liegen: (A) teilt das VOLLE Rechteck eines Elements
durch die Schirmflaeche, und ein Element kann laenger sein als der
Schirm. Genau deshalb steht der Schirmanteil (B) davor.

| Ansicht | Koeder 390 px | Koeder 1440 px |
| --- | --- | --- |
| Home | Schirm 100.0 % dunkel, 6 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (305 % groesste) |
| Chef | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (100 % groesste) |
| Projekte | Schirm 96.2 % dunkel, 4 tragend (108 % groesste) | Schirm 99.2 % dunkel, 2 tragend (100 % groesste) |
| Arbeitsscheine | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 3 tragend (136 % groesste) |
| Planung | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 3 tragend (137 % groesste) |
| Zeiterfassung | Schirm 100.0 % dunkel, 7 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (120 % groesste) |
| Abwesenheiten | Schirm 100.0 % dunkel, 5 tragend (108 % groesste) | Schirm 100.0 % dunkel, 3 tragend (207 % groesste) |
| Monatsabrechnung | Schirm 100.0 % dunkel, 3 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (137 % groesste) |
| Fahrzeuge | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 96.2 % dunkel, 2 tragend (151 % groesste) |
| Flotte | Schirm 100.0 % dunkel, 3 tragend (108 % groesste) | Schirm 75.6 % dunkel, 3 tragend (122 % groesste) |
| Werkzeuge | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (111 % groesste) |
| Bauprovisorien | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (100 % groesste) |
| Gefahrenstoffe | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (100 % groesste) |
| Mitarbeiter | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (125 % groesste) |
| Auswertungen | Schirm 100.0 % dunkel, 12 tragend (216 % groesste) | Schirm 100.0 % dunkel, 8 tragend (388 % groesste) |
| Einstellungen | Schirm 100.0 % dunkel, 5 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (229 % groesste) |
| Büro-Portal | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (104 % groesste) |
| Admin | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (183 % groesste) |
| Projekt/Dashboard | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Pläne | Schirm 85.1 % dunkel, 5 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (105 % groesste) |
| Projekt/Mängel | Schirm 85.1 % dunkel, 3 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Fotos | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Zeiterfassung | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Berichte | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Formulare | Schirm 85.1 % dunkel, 3 tragend (156 % groesste) | Schirm 100.0 % dunkel, 3 tragend (105 % groesste) |
| Projekt/Checklisten | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Bautagebuch | Schirm 85.1 % dunkel, 3 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Material | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Dokumente | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/OFFA | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Export | Schirm 85.1 % dunkel, 6 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (105 % groesste) |

## Hellmodus je Ansicht

| Ansicht | 390 px | 1440 px | Urteil |
| --- | --- | --- | --- |
| Home | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 7.4 % dunkel (oben 5.0, gerollt 7.4); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Chef | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekte | Schirm 11.0 % dunkel (oben 11.0, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.2 % dunkel (oben 5.2, gerollt 5.2); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Arbeitsscheine | Schirm 10.1 % dunkel (oben 10.1, gerollt 6.4); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Planung | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.3 % dunkel (oben 5.3, gerollt 5.3); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Zeiterfassung | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Abwesenheiten | Schirm 15.4 % dunkel (oben 15.4, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 6.7 % dunkel (oben 6.7, gerollt 5.0); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Monatsabrechnung | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Fahrzeuge | Schirm 12.0 % dunkel (oben 12.0, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Flotte | Schirm 15.1 % dunkel (oben 15.1, gerollt 2.6); 0 tragend im Baum, 3 dunkel ab 8000 px2 | Schirm 7.2 % dunkel (oben 6.5, gerollt 7.2); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Werkzeuge | Schirm 12.2 % dunkel (oben 12.2, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Bauprovisorien | Schirm 10.9 % dunkel (oben 10.9, gerollt 3.4); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.2 % dunkel (oben 5.2, gerollt 5.2); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Gefahrenstoffe | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Mitarbeiter | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Auswertungen | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.9); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.2 % dunkel (oben 5.2, gerollt 5.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Einstellungen | Schirm 13.9 % dunkel (oben 13.9, gerollt 2.6); 0 tragend im Baum, 3 dunkel ab 8000 px2 | Schirm 6.2 % dunkel (oben 6.2, gerollt 5.2); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Büro-Portal | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 3 dunkel ab 8000 px2 | Schirm 7.5 % dunkel (oben 5.0, gerollt 7.5); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Admin | Schirm 10.1 % dunkel (oben 10.1, gerollt 2.6); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Dashboard | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Pläne | **Schirm 57.5 % dunkel (oben 7.6, gerollt 57.5)**; 1 tragend im Baum, 2 dunkel ab 8000 px2 | **Schirm 72.7 % dunkel (oben 52.0, gerollt 72.7)**; 1 tragend im Baum, 2 dunkel ab 8000 px2 | BEFUND |
| Projekt/Mängel | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.2); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.1 % dunkel (oben 5.1, gerollt 5.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Fotos | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Zeiterfassung | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Berichte | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Formulare | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Checklisten | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Bautagebuch | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Material | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 3 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 3 dunkel ab 8000 px2 | gruen |
| Projekt/Dokumente | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/OFFA | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Export | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |

## Tragende dunkle Flaeche im Baum, aber nicht auf dem Schirm

Keine. In jeder Ansicht stimmten beide Masse ueberein.

## Was die Raster-Abtastung im Hellmodus als dunkel sieht

Die Traeger je Ansicht, nach Punkten. Der orange Streifen
`rgb(249,115,22)` ist das Sync-Warnband, das es nur gibt, weil dieser
Aufbau jede Anfrage abbricht - Akzentfarbe, kein Themenfehler.

### Rolle admin, 390 px, epk_theme=light

| Ansicht | Zustand | Schirm dunkel | Traeger (Punkte von 960) |
| --- | --- | --- | --- |
| Home | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Home | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Chef | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Chef | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Projekte | oben | 11.0 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `button.  rgb(20,26,22)` x9; `span.  rgb(249,115,22)` x1 |
| Projekte | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Arbeitsscheine | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Arbeitsscheine | gerollt | 6.4 % | `div.  rgb(249,115,22)` x24; `button.  rgb(59,130,246)` x18; `button.  rgb(239,68,68)` x18; `span.  rgb(249,115,22)` x1 |
| Planung | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Planung | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Zeiterfassung | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Zeiterfassung | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Abwesenheiten | oben | 15.4 % | `div.  rgb(249,115,22)` x84; `button.  rgb(0,150,64)` x20; `button.  rgb(220,38,38)` x16; `button.  rgb(124,58,237)` x15; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Abwesenheiten | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Monatsabrechnung | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Monatsabrechnung | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Fahrzeuge | oben | 12.0 % | `div.  rgb(249,115,22)` x90; `button.  rgb(250,143,69)` x12; `div.  rgb(14,165,233)` x6; `div.  rgb(0,110,48)` x6; `span.  rgb(249,115,22)` x1 |
| Fahrzeuge | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Flotte | oben | 15.1 % | `div.  rgb(249,115,22)` x84; `div.  rgb(33,41,58)` x48; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Flotte | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Werkzeuge | oben | 12.2 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `div.  rgb(217,119,6)` x10; `div.  rgb(0,110,48)` x10; `span.  rgb(249,115,22)` x1 |
| Werkzeuge | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Bauprovisorien | oben | 10.9 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `button.  rgb(0,150,64)` x8; `span.  rgb(249,115,22)` x1 |
| Bauprovisorien | gerollt | 3.4 % | `div.  rgb(249,115,22)` x24; `button.  rgb(0,150,64)` x8; `span.  rgb(249,115,22)` x1 |
| Gefahrenstoffe | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Gefahrenstoffe | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Mitarbeiter | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Mitarbeiter | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Auswertungen | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Auswertungen | gerollt | 2.9 % | `div.  rgb(249,115,22)` x24; `button.  rgb(34,197,94)` x3; `span.  rgb(249,115,22)` x1 |
| Einstellungen | oben | 13.9 % | `div.  rgb(249,115,22)` x84; `div.  rgb(239,68,68)` x36; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Einstellungen | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Büro-Portal | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Büro-Portal | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Admin | oben | 10.1 % | `div.  rgb(249,115,22)` x84; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Admin | gerollt | 2.6 % | `div.  rgb(249,115,22)` x24; `span.  rgb(249,115,22)` x1 |
| Projekt/Dashboard | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Dashboard | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Pläne | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Pläne | gerollt | 57.5 % | `div.  rgb(26,26,26)` x551; `span.  rgb(34,197,94)` x1 |
| Projekt/Mängel | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Mängel | gerollt | 0.2 % | `span.  rgb(34,197,94)` x1; `span.  rgb(249,115,22)` x1 |
| Projekt/Fotos | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Fotos | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Zeiterfassung | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Zeiterfassung | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Berichte | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Berichte | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Formulare | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Formulare | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Checklisten | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Checklisten | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Bautagebuch | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Bautagebuch | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Material | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Material | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Dokumente | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Dokumente | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/OFFA | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/OFFA | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Export | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Export | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |

### Rolle admin, 1440 px, epk_theme=light

| Ansicht | Zustand | Schirm dunkel | Traeger (Punkte von 960) |
| --- | --- | --- | --- |
| Home | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Home | gerollt | 7.4 % | `div.  rgb(249,115,22)` x44; `div.  rgb(0,150,64)` x18; `div.  rgb(59,130,246)` x5; `button.  rgb(250,143,69)` x4 |
| Chef | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Chef | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekte | oben | 5.2 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(20,26,22)` x2 |
| Projekte | gerollt | 5.2 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(20,26,22)` x2 |
| Arbeitsscheine | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Arbeitsscheine | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Planung | oben | 5.3 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `th.  rgb(0,110,48)` x3 |
| Planung | gerollt | 5.3 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `th.  rgb(0,110,48)` x3 |
| Zeiterfassung | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Zeiterfassung | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Abwesenheiten | oben | 6.7 % | `div.  rgb(249,115,22)` x44; `button.  rgb(0,150,64)` x6; `button.  rgb(124,58,237)` x6; `button.  rgb(220,38,38)` x4; `button.  rgb(250,143,69)` x4 |
| Abwesenheiten | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Monatsabrechnung | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Monatsabrechnung | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Fahrzeuge | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Fahrzeuge | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Flotte | oben | 6.5 % | `div.  rgb(249,115,22)` x44; `div.  rgb(33,41,58)` x14; `button.  rgb(250,143,69)` x4 |
| Flotte | gerollt | 7.2 % | `div.  rgb(249,115,22)` x44; `div.  rgb(33,41,58)` x21; `button.  rgb(250,143,69)` x4 |
| Werkzeuge | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Werkzeuge | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Bauprovisorien | oben | 5.2 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(0,150,64)` x2 |
| Bauprovisorien | gerollt | 5.2 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(0,150,64)` x2 |
| Gefahrenstoffe | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Gefahrenstoffe | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Mitarbeiter | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Mitarbeiter | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Auswertungen | oben | 5.2 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(0,110,48)` x2 |
| Auswertungen | gerollt | 5.1 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(34,197,94)` x1 |
| Einstellungen | oben | 6.2 % | `div.  rgb(249,115,22)` x44; `div.  rgb(239,68,68)` x12; `button.  rgb(250,143,69)` x4 |
| Einstellungen | gerollt | 5.2 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(0,150,64)` x2 |
| Büro-Portal | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Büro-Portal | gerollt | 7.5 % | `div.  rgb(249,115,22)` x50; `div.  rgb(59,130,246)` x6; `div.  rgb(0,150,64)` x6; `div.  rgb(168,85,247)` x6; `button.  rgb(250,143,69)` x4 |
| Admin | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Admin | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Dashboard | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Dashboard | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Pläne | oben | 52.0 % | `div.  rgb(26,26,26)` x450; `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `span.  rgb(6,182,212)` x1 |
| Projekt/Pläne | gerollt | 72.7 % | `div.  rgb(26,26,26)` x650; `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Mängel | oben | 5.1 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `span.  rgb(239,68,68)` x1 |
| Projekt/Mängel | gerollt | 5.1 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `span.  rgb(239,68,68)` x1 |
| Projekt/Fotos | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Fotos | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Zeiterfassung | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Zeiterfassung | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Berichte | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Berichte | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Formulare | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Formulare | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Checklisten | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Checklisten | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Bautagebuch | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Bautagebuch | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Material | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Material | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Dokumente | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Dokumente | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/OFFA | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/OFFA | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Export | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Export | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |

## Jede dunkle Flaeche im Hellmodus, ab 8000 px2

Vollstaendig, nicht nur die tragenden. Die Warnbaender in Amber und
Orange entstehen erst dadurch, dass dieser Aufbau jede Anfrage
abbricht - sie sind Akzente und kein Themenfehler; der Text steht
dabei, damit das nachpruefbar ist.

### Rolle admin, 390 px, epk_theme=light

**Home** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Chef** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Projekte** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Arbeitsscheine** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Planung** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Zeiterfassung** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Abwesenheiten** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Monatsabrechnung** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Fahrzeuge** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Flotte** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(33, 41, 58) (roh rgba(15, 23, 42, 0.92)) | 0.022 | 15996 | 4.7 % | 🛰️ Noch keine Tracker zugeordnet — IMEI in der Liste (ohne Tracker) o |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Werkzeuge** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Bauprovisorien** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Gefahrenstoffe** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Mitarbeiter** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Auswertungen** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Einstellungen** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(239, 68, 68) | 0.229 | 12675 | 3.7 % | System-Config laden fehlgeschlagen: Failed to fetch |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Büro-Portal** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(217, 119, 6) | 0.280 | 13865 | 4.0 % | ⚠️ Fehler beim Laden |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Admin** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 8190 | 2.4 % | ⚠️ SERVER · 5 ausstehend |

**Projekt/Dashboard** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Pläne** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(26, 26, 26) | 0.010 | 267689 | 78.0 % | − 100% + ⊡ ↔ ⬚ ⛶ 📥 📍 |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Mängel** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Fotos** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Zeiterfassung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Berichte** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Formulare** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Checklisten** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Bautagebuch** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Material** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(217, 119, 6) | 0.280 | 13865 | 4.0 % | Anforderungen konnten nicht geladen werden |
| `div.-` | rgb(217, 119, 6) | 0.280 | 13865 | 4.0 % | Bestellungen konnten nicht geladen werden |

**Projekt/Dokumente** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/OFFA** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Export** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

### Rolle admin, 1440 px, epk_theme=light

**Home** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(59, 130, 246) | 0.235 | 8889 | 0.7 % | - |

**Chef** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekte** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Arbeitsscheine** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Planung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Zeiterfassung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Abwesenheiten** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `button.-` | rgb(0, 150, 64) | 0.222 | 8729 | 0.7 % | 🏖️ Urlaub beantragen |

**Monatsabrechnung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Fahrzeuge** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Flotte** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(33, 41, 58) (roh rgba(15, 23, 42, 0.92)) | 0.022 | 21450 | 1.7 % | 🛰️ Noch keine Tracker zugeordnet — IMEI in der Liste (ohne Tracker) o |

**Werkzeuge** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Bauprovisorien** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Gefahrenstoffe** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Mitarbeiter** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Auswertungen** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Einstellungen** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(239, 68, 68) | 0.229 | 13071 | 1.0 % | System-Config laden fehlgeschlagen: Failed to fetch |

**Büro-Portal** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(217, 119, 6) | 0.280 | 15800 | 1.2 % | ⚠️ Fehler beim Laden |

**Admin** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Dashboard** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Pläne** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(26, 26, 26) | 0.010 | 836168 | 66.0 % | − 100% + ⊡ ↔ ⬚ ⛶ 📥 📍 |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Mängel** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Fotos** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Zeiterfassung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Berichte** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Formulare** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Checklisten** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Bautagebuch** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Material** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(217, 119, 6) | 0.280 | 15800 | 1.2 % | Anforderungen konnten nicht geladen werden |
| `div.-` | rgb(217, 119, 6) | 0.280 | 15800 | 1.2 % | Bestellungen konnten nicht geladen werden |

**Projekt/Dokumente** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/OFFA** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Export** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 5 Änderungen warten auf Sync 🔄 Jetzt sync |

## Fest verdrahtete dunkle Hintergruende im Quelltext

Eine Flaeche, deren Hintergrund als feste Farbe geschrieben ist, kann
der Hellmodus nicht erreichen - sie ist in beiden Themen gleich dunkel.
Diese Liste ist eine LEITLISTE und kein Urteil: Druck- und
Exportvorlagen stehen als HTML-Zeichenketten in derselben Datei und
tauchen hier mit auf, obwohl sie nie am Schirm haengen. Was wirklich am
Schirm haengt, sagt die Messung oben.

**65** fest geschriebene Hintergruende mit Helligkeit unter 0.5.
Gezeigt sind die 25 DUNKELSTEN; die vollstaendige Liste steht in
`screenshots/hellmodus_ansichten.json` unter `fest_verdrahtet`.
Gekappt wird nach Helligkeit, nicht nach Farbe - die uebrigen sind
heller, nicht anders gefaerbt (das Markengruen `#009640` mit 0,222
ist als Knopfflaeche unter weisser Schrift gewollt).

| Zeile | Farbe | Helligkeit | Umfeld |
| --- | --- | --- | --- |
| 17124 | `#0a0c14` | 0.004 | `andleTouchEnd, onWheel: handleWheel, style: {flex:1,overflow:"hidden",position:"relative",background:"#0a0c14",borderRadius:8,border:"1px so` |
| 18409 | `#0a0c14` | 0.004 | `>{setSelPlan(pl);setSubView("viewer");}}, React.createElement('div', { style: {height:140,background:"#0a0c14",display:"flex",alignItems:"ce` |
| 19161 | `#0a0c14` | 0.004 | `tion:"relative"}}             , React.createElement('div', { style: {height:isMob?120:160,background:"#0a0c14",display:"flex",alignItems:"ce` |
| 19177 | `#0a0c14` | 0.004 | `Element('div', { style: {width:60,height:60,borderRadius:6,overflow:"hidden",flexShrink:0,background:"#0a0c14",display:"flex",alignItems:"ce` |
| 30183 | `#0f0f0f` | 0.005 | `{minHeight:'100dvh',display:'flex',alignItems:'center',justifyContent:'center',padding:20,background:'#0f0f0f',color:'#e5e5e5',fontFamily:'s` |
| 7257 | `#111827` | 0.009 | `/_fitScale)+'%',display:'flex',flexDirection:'column'}}     ,h('div',{style:{flexShrink:0,background:'#111827',color:'#fff',display:'flex',a` |
| 7268 | `#111827` | 0.009 | `:'15%'}}))         ,h('thead',{},h('tr',{style:{height:'46px'}}           ,h('th',{style:{background:'#111827',color:'#fff',fontSize:15,font` |
| 7610 | `#0f172a` | 0.009 | `,.25)"};     const rahmen=(inhalt,abbruch)=>h('div',{style:{height:"100dvh",width:"100vw",background:"#0f172a",color:"#e2e8f0",         disp` |
| 7663 | `#0f172a` | 0.009 | `v',null,T('Einen Moment …')));   }   return h('div',{style:{height:"100dvh",width:"100vw",background:"#0f172a",color:"#e2e8f0",display:"flex` |
| 9451 | `#0f172a` | 0.009 | `)return React.createElement('div',{style:{height:"100dvh",width:"100vw",overflow:"hidden",background:"#0f172a"}},React.createElement('style'` |
| 18019 | `#1a1a1a` | 0.010 | `ment('div', {ref: viewportRef, style: {flex: 1, position: "relative", overflow: "hidden", background: "#1a1a1a"}},       React.createElement` |
| 23643 | `#161922` | 0.010 | `e: {display:"flex",justifyContent:"space-between",alignItems:"center",padding:"12px 16px",background:"#161922",flexShrink:0}}             , ` |
| 30184 | `#1a1a1a` | 0.010 | `system,sans-serif'}},         React.createElement('div',{style:{maxWidth:520,width:'100%',background:'#1a1a1a',border:'1px solid #3a3a3a',bo` |
| 7272 | `#1f2937` | 0.022 | `Dates[i].getDate())+'.'+_pad(dayDates[i].getMonth()+1)+'.'));})           ,h('th',{style:{background:'#1f2937',color:'#fff',fontSize:15,font` |
| 7629 | `#1e293b` | 0.022 | `  const dIn={padding:"16px 20px",borderRadius:12,border:"1px solid rgba(255,255,255,.25)",background:"#1e293b",                  color:"#fff` |
| 7679 | `#1e293b` | 0.022 | `:{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,.2)",background:"#1e293b",color:"#fff",fontSize:15}}   ` |
| 7683 | `#1e293b` | 0.022 | `,style:{flex:1,padding:"10px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,.2)",background:"#1e293b",color:"#fff",fontSize:15}})  ` |
| 7696 | `#1e293b` | 0.022 | `eader)",style:{padding:"10px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,.2)",background:"#1e293b",color:"#fff",fontSize:15,widt` |
| 30193 | `#2a2a2a` | 0.023 | `set,style:{flex:'1 1 120px',padding:'10px 16px',borderRadius:8,border:'1px solid #3a3a3a',background:'#2a2a2a',color:'#fff',fontSize:14,font` |
| 28989 | `#525659` | 0.092 | `,     React.createElement('div',{onClick:e=>e.stopPropagation(),style:{flex:1,minHeight:0,background:"#525659",display:"flex",flexDirection:` |
| 22225 | `#006e30` | 0.114 | `Bem.")             , React.createElement('th', { style: {borderBottom:"2px solid #004d20",background:"#006e30"}})           ))           , R` |
| 12220 | `#7c3aed` | 0.134 | `line-flex',alignItems:'center',gap:4}},h('span',{style:{width:12,height:12,borderRadius:3,background:'#7c3aed',display:'inline-block'}}),'gr` |
| 22666 | `#7c3aed` | 0.134 | `"12px 20px",fontSize:isMob?12:14,borderRadius:10,display:"flex",alignItems:"center",gap:8,background:"#7c3aed",border:"none",color:"#fff",fo` |
| 22665 | `#dc2626` | 0.167 | `"12px 20px",fontSize:isMob?12:14,borderRadius:10,display:"flex",alignItems:"center",gap:8,background:"#dc2626",border:"none",color:"#fff",fo` |
| 11457 | `#8b5cf6` | 0.198 | `lach", onClick: e=>{e.stopPropagation();setAsShowQR(asShowQR===a.id?null:a.id);}, style: {background:"#8b5cf6",color:"#8b5cf6",border:"1px s` |

## Gesamturteil

- Ansichten, deren Schirm im Hellmodus ab 25 % dunkel ist: **1** - admin/Projekt/Pläne
- Ansichten NICHT GEMESSEN (Koeder versagt oder nicht erreicht): **0**
- Ansichten mit tragender Flaeche im Baum, die die Abtastung nicht
  sieht: **0**
- Ansichten gruen (Koeder schlug in beiden Massen an, Schirm unter
  25 % dunkel): **30**

## WAS DIESER AUFBAU NICHT ABDECKT

- **Ein echtes Geraet.** Hier laeuft Chromium mit gesetzter Breite und
  `is_mobile`, aber ohne Geraeteprofil: kein iOS-Safari, kein
  Android-WebView, keine Systemleiste, keine Hoch/Quer-Drehung, kein
  `prefers-contrast`, keine Bedienungshilfe, die Farben ersetzt.
- **Ein gespeicherter Dienstarbeiter mit einer aelteren Fassung.** Der
  Nutzer kann eine Fassung vor v3.9.711 im Zwischenspeicher haben, in
  der die OS-Einstellung die App-Wahl noch schlug. Dieser Lauf laedt
  die Datei frisch und sieht das nicht.
- **Ansichten hinter Rollen, die hier nicht gemessen wurden.** Gemessen
  wurde `admin`. Was ein anderer Zuschnitt (Buero, Projektleiter, ein
  eigener `perms_override`) zeigt, steht hier nicht.
- **Ansichten hinter Daten, die dieser Aufbau nicht hat.** Alle
  REST-Anfragen sind abgebrochen. Was erst mit echten Zeilen erscheint
  - eine Tabelle, ein Diagramm, eine Karte - ist hier leer oder ein
  Warnband. Eine dunkle Flaeche, die nur bei gefuellter Liste
  entsteht, kann dieser Lauf nicht finden.
- **Ansichten, die einen Absturz voraussetzen.** Die Auffangflaeche der
  Fehlergrenze (`#0f0f0f` mit `#1a1a1a`-Karte, `minHeight:100dvh`) ist
  fest verdrahtet dunkel und erscheint nur, wenn die App wirft. In
  diesem Lauf ist sie nie erschienen - sie steht in der Quelltextliste
  oben und ist NICHT gemessen.
- **Zustaende innerhalb einer Ansicht.** Gemessen sind zwei Zustaende:
  beim Oeffnen und nach dem Rollen aller rollbaren Behaelter ans Ende.
  Was DAZWISCHEN liegt, wird nicht abgetastet, ebensowenig
  Ueberlagerungen, Dialoge, aufgeklappte Karten, quer gerollte Bereiche
  und alles, was erst nach einer Eingabe erscheint.
- **Die Liste je Ansicht zeigt die 12 GROESSTEN dunklen Flaechen.** Die
  Zahl daneben (`... dunkel ab 8000 px2`) ist die vollstaendige Anzahl.
  Fuer das Urteil ist die Kappung ohne Folge, weil nach Flaeche
  sortiert wird und eine tragende Flaeche damit immer in den ersten
  zwoelf steht; fuer die Durchsicht der kleinen Flaechen ist sie eine
  Grenze.
- **Die Messung urteilt nach ANTEIL, nicht nach Farbe.** Eine dunkle
  Flaeche unter 25 % des Schirms erscheint in der vollen Liste, gilt
  aber nicht als Befund. Wer die Grenze anders zieht, bekommt ein
  anderes Urteil - die Rohwerte dafuer stehen in der JSON.
- **Die Abtastung hat 960 Punkte.** Eine dunkle Flaeche, die schmaler
  ist als ein Rasterabstand (16 px bei 390, 60 px bei 1440 Breite),
  kann zwischen den Punkten hindurchfallen. Die Flaechensuche (A)
  faengt diesen Fall ab, deshalb stehen beide Masse nebeneinander.

## Protokoll

- `('admin', 'light', 390): Saat {'monteure': 3, 'arbeitsscheine': 6, 'projects': 2, 'entries': 5} | Reiter aus dem Baum: ['Home', 'Chef', 'Projekte', 'Arbeitsscheine', 'Planung', 'Zeiterfassung', 'Abwesenheiten', 'Monatsabrechnung', 'Fahrzeuge', 'Flotte', 'Werkzeuge', 'Bauprovisorien', 'Gefahrenstoffe', 'Mitarbeiter', 'Auswertungen', 'Einstellungen', 'Büro-Portal', 'Admin']`
- `('admin', 'light', 1440): Saat {'monteure': 3, 'arbeitsscheine': 6, 'projects': 2, 'entries': 5} | Reiter aus dem Baum: ['Home', 'Chef', 'Projekte', 'Arbeitsscheine', 'Planung', 'Zeiterfassung', 'Abwesenheiten', 'Monatsabrechnung', 'Fahrzeuge', 'Flotte', 'Werkzeuge', 'Bauprovisorien', 'Gefahrenstoffe', 'Mitarbeiter', 'Auswertungen', 'Einstellungen', 'Büro-Portal', 'Admin']`
- `('admin', 'dark', 390): Saat {'monteure': 3, 'arbeitsscheine': 6, 'projects': 2, 'entries': 5} | Reiter aus dem Baum: ['Home', 'Chef', 'Projekte', 'Arbeitsscheine', 'Planung', 'Zeiterfassung', 'Abwesenheiten', 'Monatsabrechnung', 'Fahrzeuge', 'Flotte', 'Werkzeuge', 'Bauprovisorien', 'Gefahrenstoffe', 'Mitarbeiter', 'Auswertungen', 'Einstellungen', 'Büro-Portal', 'Admin']`
- `('admin', 'dark', 1440): Saat {'monteure': 3, 'arbeitsscheine': 6, 'projects': 2, 'entries': 5} | Reiter aus dem Baum: ['Home', 'Chef', 'Projekte', 'Arbeitsscheine', 'Planung', 'Zeiterfassung', 'Abwesenheiten', 'Monatsabrechnung', 'Fahrzeuge', 'Flotte', 'Werkzeuge', 'Bauprovisorien', 'Gefahrenstoffe', 'Mitarbeiter', 'Auswertungen', 'Einstellungen', 'Büro-Portal', 'Admin']`
- `Rolle monteur fuehrt 8 Reiter: ['Home', 'Projekte', 'Arbeitsscheine', 'Planung', 'Zeiterfassung', 'Abwesenheiten', 'Gefahrenstoffe', 'Mitarbeiter']`
- `davon NICHT in der Admin-Liste: keine - kein zweiter Lauf noetig`


## Gegenmessung nach v3.9.942

Gemessen mit `scripts/hellmodus_ansichten.py` gegen die **laufende
`index.html`** (nicht gegen die eingefrorene Kopie), md5
`bb71acef0aa9bb7d807250dd961696f8` **vor und nach** dem Lauf - die Datei hat
sich waehrend dieses Laufs NICHT bewegt, die Zahlen gehoeren also zu einem
einzigen Baum. Alle 31 Ansichten, beide Breiten, beide Themen, Rolle `admin`.

Die geaenderte Stelle lautet jetzt `background: _dark?"#1a1a1a":V.bd`
(Zeile 18049): im Dunkelmodus unveraendert `#1a1a1a`, im Hellmodus `V.bd`
= `#d4d8e0`, Helligkeit 0,67 - damit ueber der Dunkelgrenze von 0,5 und
folgerichtig kein Treffer mehr.

### Die Ansicht, um die es ging

| Ansicht, Breite | vor der Aenderung (v3.9.939) | nach der Aenderung (v3.9.942) |
| --- | --- | --- |
| Projekt/Pläne, 390 px, hell | **57,5 %** Schirm dunkel (oben 7,6 / gerollt 57,5), 1 tragend | **7,6 %** (oben 7,6 / gerollt 0,1), 0 tragend |
| Projekt/Pläne, 1440 px, hell | **72,7 %** Schirm dunkel (oben 52,0 / gerollt 72,7), 1 tragend | **5,1 %** (oben 5,1 / gerollt 5,0), 0 tragend |
| Projekt/Pläne, 390 px, dunkel (Koeder) | 85,1 %, 5 tragend | 85,1 %, 5 tragend |
| Projekt/Pläne, 1440 px, dunkel (Koeder) | 100,0 %, 4 tragend | 100,0 %, 4 tragend |

Die Dunkelmodus-Zahlen sind **Ziffer fuer Ziffer dieselben** wie vor der
Aenderung. Das ist die Gegenprobe zur Zusage "der Dunkelmodus bleibt
bytegleich": haette die Aenderung dort etwas verschoben, muesste eine dieser
vier Zahlen wandern.

`rgb(26, 26, 26)` kommt im Hellmodus in KEINER Ansicht mehr vor. Was in
`Projekt/Pläne` im Hellmodus noch als dunkel gemessen wird, ist:

| Breite | Zustand | Schirm dunkel | Traeger |
| --- | --- | --- | --- |
| 390 px | oben | 7,6 % | `rgb(249,115,22)` x60 (Sync-Warnband), `rgb(250,143,69)` x12 (dessen Knopf), 1 gruener Punkt |
| 390 px | gerollt | 0,1 % | 1 gruener Punkt |
| 1440 px | oben | 5,1 % | `rgb(249,115,22)` x44, `rgb(250,143,69)` x4, 1 Punkt |
| 1440 px | gerollt | 5,0 % | `rgb(249,115,22)` x44, `rgb(250,143,69)` x4 |

Das Warnband gibt es nur, weil dieser Aufbau jede Anfrage abbricht. Kein
Befund.

### Der ganze Durchgang

- Ansichten mit dunklem Schirm ab 25 % im Hellmodus: **0** (vorher 1)
- Ansichten NICHT GEMESSEN: **0**
- Ansichten gruen: **31**
- Koeder im Dunkelmodus: schlaegt in **allen 31 Ansichten** an, bei beiden
  Breiten - Schirm 75,6 bis 100,0 % dunkel, je mindestens 2 tragende
  Flaechen. Ohne das waere dieser Durchgang keine Aussage.
- Rueckgabewert des Laufs: **0**.

### Was diese Gegenmessung allein NICHT zeigt

Sie lief **ohne Plan**: in der Ansicht stand "Noch keine Pläne", gemessen war
der leere Zustand. Ob die Aenderung auch dann traegt, wenn wirklich ein Plan
im Betrachter haengt, beantwortet erst der Abschnitt darunter - dort ist ein
Plan gesaet, und auch dann ist `rgb(26, 26, 26)` im Hellmodus **nicht mehr im
Baum** (Zeile "Plaene/Viewer", beide Breiten).

## Die vier Schwestern - gemessen

Gemessen mit `scripts/hellmodus_schwestern.py` gegen eine eingefrorene Kopie
`_mess_stand_schwestern.html`, md5 `837aceae308a947e270a503d4b9dbc60` vor und
nach dem Lauf, `APP_VERSION 3.9.942-supabase`, mit der Aenderung an Zeile
18049 darin. **Warum eine Kopie und nicht die laufende Datei:** ein frueherer
Anlauf lief gegen `index.html`, und die Datei wanderte waehrenddessen von
`420fb60986ede332b7fe08f66214c4c5` auf `837aceae308a947e270a503d4b9dbc60`.
Zahlen aus so einem Lauf gehoeren zu zwei verschiedenen Baeumen.

**Alle vier Stellen brauchen Daten.** Der Durchgang vom 26.09. hat nichts
ausser Monteuren, Arbeitsscheinen, Projekten und Zeiteintraegen gesaet; in
der Ansicht Plaene stand "Noch keine Pläne", in Fotos "Noch keine Fotos".
Die vier Flaechen waren damals **gar nicht im Baum**. Deshalb standen sie zu
Recht als NICHT GEMESSEN da. Hier sind zwei Plaene (1200 x 850) und sechs
Fotos (4:3) gesaet und **zurueckgelesen**; die Ansicht zeigt sie (Plan-Name
im Text, sechs Bilder statt einem, kein Leertext).

### Zwei Masse, und warum das erste allein nicht genuegt

- **Rasterabtastung** (wie im Hauptbericht): 24 x 40 Punkte, je Punkt
  `elementFromPoint`, Farbstapel gemischt. Sie liest **CSS-Hintergruende,
  keine gemalten Bildpunkte.** Ein `<img>` hat keinen eigenen Hintergrund,
  also findet die Suche die Mulde DAHINTER - auch dann, wenn das Foto sie
  vollstaendig verdeckt. Ihre Zahlen sind hier eine **Obergrenze**.
- **Freie Flaeche**: je Mulde das Rechteck im Fenster **minus** dem, was das
  geladene Bild darin wirklich ausmalt (`objectFit` `cover` fuellt den
  Kasten, `contain` passt seitenverhaeltnistreu ein und laesst Balken).
  Das ist die Zahl, die zaehlt.

### Die vier Stellen

| Zeile | Ansicht und Bedingung | Im Hellmodus auf dem Schirm? | frei 390 px | frei 1440 px | Raster (Obergrenze) 390 / 1440 | Urteil |
| --- | --- | --- | --- | --- | --- | --- |
| **17154** `#0a0c14` | `PlanViewer` | **NEIN - die Farbe steht in KEINEM Element des Baums** | – | – | 0,1 % / 5,0 % Schirm dunkel, davon 0 Punkte auf einer Zielfarbe | **Toter Code.** Kein Fehler, keine Absicht: die Stelle ist unerreichbar. |
| **18439** `#0a0c14` | Pläne → Unterreiter Planverwaltung; braucht einen Plan | **JA**, als schwarze Balken links und rechts neben dem Planblatt | **48 832 px² = 14,2 %** des Schirms (2 Kacheln je 372x140, je 24 416 px² frei von 52 080) | **50 137 px² = 4,0 %** (2 Kacheln je 377x140) | 14,5 % / 13,1 % | **Absicht** (Letterbox um ein Planblatt) - aber siehe die Anmerkung unten. |
| **19191** `#0a0c14` | Fotos → Kachelwand; braucht Fotos | **NEIN** | **0 px²** (6 Kacheln 181x120, jede zu 21 720 von 21 720 px² bedeckt) | **0 px²** (6 Kacheln 283x160, je 45 280 von 45 280 bedeckt) | 38,1 % / 27,9 % - reine Obergrenze, siehe oben | **Absicht, und unsichtbar.** `objectFit:"cover"` deckt die Mulde restlos. |
| **19207** `#0a0c14` | Fotos → Listenansicht; braucht Fotos | **NEIN** | **0 px²** | **0 px²** | 7,6 % / 6,2 % - Obergrenze | **Absicht, und unsichtbar.** Dieselbe Bauart, 60x60. |

**Woher das Urteil "Absicht" kommt - aus dem Zusammenhang, nicht aus der
Farbe:** alle drei lebenden Stellen sind derselbe Bauteil, eine **Mulde fuer
Medien**: ein Kasten mit `display:flex; alignItems:center;
justifyContent:center; overflow:hidden`, in dem genau ein Bild sitzt. Das ist
die Bauform, mit der ein Bild mittig eingepasst und der Rest abgedeckt wird.
Bei den Fotos (`cover`) sieht man davon nichts. Bei den Planvorschauen
(`contain`) sieht man Balken - und ein Planblatt ist weiss, sodass der dunkle
Rand die Blattkante ueberhaupt erst sichtbar macht. Das ist dieselbe
Ueberlegung, aus der der grosse Betrachter dunkel war.

**Anmerkung, die eine Entscheidung braucht und keine Messung ist:** seit
v3.9.942 ist der grosse Plan-Betrachter im Hellmodus `V.bd` (`#d4d8e0`),
waehrend die Vorschaukacheln derselben Plaene bei `#0a0c14` geblieben sind.
Gemessen ist beides; ob die beiden zusammenpassen sollen, ist eine
Gestaltungsfrage. Die Kacheln sind mit 14,2 % (390 px) deutlich unter der
Schwelle von 25 % und sind **nicht** der gemeldete Nutzerbefund.

### `#0f172a` mit `height:100dvh; width:100vw` - Zeilen 7640, 7693, 9481

**Die Vermutung "Vollbild-Tore vor dem Anmelden" ist WIDERLEGT.**

Gemessen: der Anmeldeschirm mit leerem Speicher, ohne Sitzung, bei 390 px und
`epk_theme='light'` - **0,0 % des Schirms dunkel, keine der Zielfarben im
Baum.** Sichtbarer Text: "EP: Kolar & Sohn · Der Haustechnikprofi ·
Baustellenmanagement-App". Das Tor vor dem Anmelden ist hell.

Was `#0f172a` wirklich ist: die **Stempeluhr-Tafel** (`StempelTafel`,
Zeile 7336), erreichbar ueber `?screen=stempel`, und zwar fuer
`role==='stempel_terminal'` oder `role==='admin'` (Zeile 9481). Gemessen als
`admin`:

| Aufruf | 390 px | 1440 px |
| --- | --- | --- |
| `?screen=stempel`, `epk_theme='light'` | **100,0 % Schirm dunkel**, `#0f172a` deckt 100 % | **100,0 %**, `#0f172a` deckt 100 % |
| `?screen=stempel`, `epk_theme='dark'` | **100,0 %** | **100,0 %** |

Traeger bei 390 px hell: `rgb(15,23,42)` auf 778 von 960 Punkten, dazu das
Warnband und die Bedienknoepfe. Sichtbarer Text: "⏱ Stempeluhr · Chip
anlernen · Logout · 14:18:52 26.09.2026".

**Urteil: Absicht.** Die Tafel ist **in beiden Themen ziffergleich dunkel**,
sie traegt ihre eigene helle Schrift (`color:#e2e8f0`) und ihre eigenen
Knopffarben. Sie folgt `epk_theme` ueberhaupt nicht - das ist kein Fehler des
Hellmodus, sondern ein eigenstaendig gestalteter Wandbildschirm fuer ein
Stempel-Terminal. Ein Nutzer am Telefon erreicht sie nur, wenn er
`?screen=stempel` aufruft; sie ist nicht der gemeldete Befund.

### NICHT GEMESSEN - und warum

| Stelle | Grund | Was man braeuchte |
| --- | --- | --- |
| `#0f0f0f` / `#1a1a1a`, Zeilen 30183/30184 | Die Auffangflaeche der Fehlergrenze erscheint nur, wenn die App wirft. In keinem der Laeufe ist sie erschienen. Ein erzwungener Absturz waere ein Trick, kein Messergebnis. | Einen echten Absturz, oder eine ausdrueckliche Freigabe, einen zu erzeugen. |
| `#525659`, Zeile 29019 | `PdfViewerModal` haengt an einem PDF in einem Serviceheft, einem Personaldokument oder einer Fahrbewilligung (Aufrufer bei 28975 und 29063). Nichts davon ist in diesem Aufbau gesaet, die Ansicht wurde nie geoeffnet. | Ein gesaetes Fahrzeug mit Serviceheft-Dokument oder ein Personaldokument, jeweils mit PDF-Datenadresse. |

Zu `#525659` laesst sich ohne Messung nur die Bauform sagen, und das ist
ausdruecklich **keine** Messung: der Kasten sitzt in einer Ueberlagerung mit
`position:fixed; inset:0` unter einer Kopfzeile, er wuerde also im offenen
Zustand fast den ganzen Schirm einnehmen - das ist der uebliche Grund eines
PDF-Betrachters. **Ob er im Hellmodus grossflaechig erscheint, ist nicht
gemessen.**

### Eigene Messfehler in dieser Runde

Sechs, und fuenf davon haetten eine Zahl geliefert, die wie ein Ergebnis
aussieht:

1. **Der Foto-Koeder hing an einem Feld, das die Ansicht nicht rendert.**
   Gesucht wurde die Bildunterschrift im Text. Ergebnis: "gesaete Fotos
   erscheinen NICHT" in allen vier Laeufen - obwohl sechs Zeilen im Speicher
   lagen und die Ansicht sieben Bilder statt einem zeigte. Ein Koeder am
   falschen Merkmal macht eine gemessene Stelle zu einer ungemessenen.
2. **Der Unterreiter heisst am Telefon nur "📁 2".** Gesucht wurde das Wort
   "Planverwaltung" - am Telefon steht dort nur das Zeichen. 18439 blieb bei
   390 px ungemessen.
3. **Nach der Korrektur griff "📁" auf den FALSCHEN Knopf.** Die Seitenleiste
   der Projekt-Huelle fuehrt "📁 Dokumente", und der steht im Baum vor der
   Unterreiterzeile. Bei 1440 px landete die Messung in **Dokumente** und
   meldete dort folgerichtig "keine Zielfarbe" - das sah aus wie ein sauberes
   Ergebnis und war eine verfehlte Ansicht.
4. **Die Rasterabtastung sieht keine Bildpunkte.** Sie meldete 38,1 % dunklen
   Schirm fuer die Fotokachelwand. Frei sind **0 px²** - das Foto deckt die
   Mulde ganz. Ohne das zweite Mass waere hier ein Befund gemeldet worden,
   den man auf dem Bildschirmfoto sofort als falsch erkennt.
5. **Die Saat mit einem 1x1-Bild verfaelschte `objectFit:"contain"`.** Ein
   1x1-Bild malt genau einen Bildpunkt aus; die Planmulde schien zu 30,3 %
   frei. Mit einem Bild im echten Verhaeltnis 1200:850 sind es 14,2 %. Die
   erste Zahl war eine Eigenschaft der Saat.
6. **Die Base64-Zeichenkette des Ersatzbildes wurde beim Umbrechen von Hand
   zerstoert** (`Incorrect padding`). Ein kaputtes Bild laedt nicht,
   `naturalWidth` bleibt 0, und die Mulde erschiene zu 100 % frei. Die Bilder
   werden seitdem im Skript GERECHNET, nicht abgeschrieben.

Ein siebter Fall wurde vor der Zahl abgefangen: der Umschalter auf die
Fotoliste traegt "☰" - **dasselbe Zeichen wie der Hamburger**, der am Telefon
eine halbdurchsichtige schwarze Flaeche ueber den ganzen Schirm legt
(`rgba(0,0,0,.5)`, `inset:0`). Ein Klick auf den falschen der beiden haette
100 % dunklen Schirm gemessen - eine Dunkelheit, die die Messung selbst
erzeugt.

### Was dieser Abschnitt NICHT abdeckt

- **Echte Plaene und echte Fotos.** Gesaet sind einfarbige Bilder im richtigen
  Seitenverhaeltnis. Ein echtes Planblatt mit anderem Verhaeltnis hat andere
  Balken; ein Hochformat-Foto in einer `cover`-Mulde deckt sie weiterhin ganz.
- **Der Ladezustand.** Solange ein Bild noch nicht da ist, liegt die Mulde
  frei. Gemessen ist der Zustand NACH dem Laden.
- **PDF-Plaene.** Gesaet sind Bildplaene (`isPdf:false`). Der PDF-Zweig des
  Betrachters nimmt einen anderen Weg und ist hier nicht gemessen.
- **Die Rolle.** Wieder nur `admin`. Ein Monteur sieht in der Projektakte
  weniger Unterseiten.
- **`#525659` und die Auffangflaeche der Fehlergrenze**, siehe die Tabelle
  oben.
