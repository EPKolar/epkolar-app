# Hellmodus in ALLEN Ansichten - Messung 26.09.2026

Gemessen mit `scripts/hellmodus_ansichten.py` gegen die EINGEFRORENE
Kopie `_mess_stand_939.html` (md5 vor dem Lauf `673b493ef06eae01e93cc7898ee7219b`, danach `673b493ef06eae01e93cc7898ee7219b`).
`index.html` wurde nicht angefasst. Quelle: `http://127.0.0.1:57554/index.html`. Laufzeit 651 s.

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
| Home | Schirm 100.0 % dunkel, 5 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (330 % groesste) |
| Chef | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (100 % groesste) |
| Projekte | Schirm 96.2 % dunkel, 4 tragend (108 % groesste) | Schirm 99.2 % dunkel, 2 tragend (100 % groesste) |
| Arbeitsscheine | Schirm 100.0 % dunkel, 5 tragend (108 % groesste) | Schirm 100.0 % dunkel, 3 tragend (137 % groesste) |
| Planung | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 3 tragend (146 % groesste) |
| Zeiterfassung | Schirm 100.0 % dunkel, 7 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (121 % groesste) |
| Abwesenheiten | Schirm 100.0 % dunkel, 5 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (205 % groesste) |
| Monatsabrechnung | Schirm 100.0 % dunkel, 3 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (131 % groesste) |
| Fahrzeuge | Schirm 98.4 % dunkel, 2 tragend (108 % groesste) | Schirm 94.0 % dunkel, 2 tragend (148 % groesste) |
| Flotte | Schirm 92.8 % dunkel, 3 tragend (108 % groesste) | Schirm 75.6 % dunkel, 3 tragend (115 % groesste) |
| Werkzeuge | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (106 % groesste) |
| Bauprovisorien | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (100 % groesste) |
| Gefahrenstoffe | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (100 % groesste) |
| Mitarbeiter | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (120 % groesste) |
| Auswertungen | Schirm 100.0 % dunkel, 12 tragend (216 % groesste) | Schirm 100.0 % dunkel, 8 tragend (379 % groesste) |
| Einstellungen | Schirm 100.0 % dunkel, 6 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (224 % groesste) |
| Büro-Portal | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (100 % groesste) |
| Admin | Schirm 100.0 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (178 % groesste) |
| Projekt/Dashboard | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Pläne | Schirm 85.1 % dunkel, 5 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (105 % groesste) |
| Projekt/Mängel | Schirm 85.1 % dunkel, 3 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Fotos | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Zeiterfassung | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Berichte | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Formulare | Schirm 85.1 % dunkel, 3 tragend (157 % groesste) | Schirm 100.0 % dunkel, 3 tragend (105 % groesste) |
| Projekt/Checklisten | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Bautagebuch | Schirm 85.1 % dunkel, 3 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Material | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Dokumente | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/OFFA | Schirm 85.1 % dunkel, 2 tragend (108 % groesste) | Schirm 100.0 % dunkel, 2 tragend (105 % groesste) |
| Projekt/Export | Schirm 85.1 % dunkel, 6 tragend (108 % groesste) | Schirm 100.0 % dunkel, 4 tragend (105 % groesste) |

## Hellmodus je Ansicht

| Ansicht | 390 px | 1440 px | Urteil |
| --- | --- | --- | --- |
| Home | Schirm 12.6 % dunkel (oben 12.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 7.1 % dunkel (oben 5.0, gerollt 7.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Chef | Schirm 13.6 % dunkel (oben 13.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekte | Schirm 13.6 % dunkel (oben 13.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.2 % dunkel (oben 5.2, gerollt 5.2); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Arbeitsscheine | Schirm 12.6 % dunkel (oben 12.6, gerollt 8.9); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Planung | Schirm 12.6 % dunkel (oben 12.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.3 % dunkel (oben 5.3, gerollt 5.3); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Zeiterfassung | Schirm 12.6 % dunkel (oben 12.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Abwesenheiten | Schirm 18.0 % dunkel (oben 18.0, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 7.5 % dunkel (oben 7.5, gerollt 5.0); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Monatsabrechnung | Schirm 12.6 % dunkel (oben 12.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Fahrzeuge | Schirm 14.9 % dunkel (oben 14.9, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Flotte | Schirm 16.4 % dunkel (oben 16.4, gerollt 5.1); 0 tragend im Baum, 3 dunkel ab 8000 px2 | Schirm 7.2 % dunkel (oben 7.2, gerollt 7.2); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Werkzeuge | Schirm 12.6 % dunkel (oben 12.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Bauprovisorien | Schirm 13.3 % dunkel (oben 13.3, gerollt 5.9); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.3 % dunkel (oben 5.3, gerollt 5.3); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Gefahrenstoffe | Schirm 12.6 % dunkel (oben 12.6, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Mitarbeiter | Schirm 14.8 % dunkel (oben 14.8, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Auswertungen | Schirm 16.4 % dunkel (oben 16.4, gerollt 5.3); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 5.4 % dunkel (oben 5.4, gerollt 5.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Einstellungen | Schirm 16.4 % dunkel (oben 16.4, gerollt 5.1); 0 tragend im Baum, 3 dunkel ab 8000 px2 | Schirm 6.2 % dunkel (oben 6.2, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Büro-Portal | Schirm 12.6 % dunkel (oben 12.6, gerollt 5.1); 0 tragend im Baum, 3 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 2 dunkel ab 8000 px2 | gruen |
| Admin | Schirm 14.8 % dunkel (oben 14.8, gerollt 5.1); 0 tragend im Baum, 2 dunkel ab 8000 px2 | Schirm 7.5 % dunkel (oben 7.5, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Alle Projekte | NICHT GEMESSEN (Projekt-Huelle verlassen) | NICHT GEMESSEN (Projekt-Huelle verlassen) | NICHT GEMESSEN - 390 px: Projekt-Huelle verlassen; 1440 px: Projekt-Huelle verlassen |
| Projekt/Dashboard | Schirm 9.7 % dunkel (oben 9.7, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Pläne | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.1); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.2 % dunkel (oben 5.2, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
| Projekt/Mängel | Schirm 7.6 % dunkel (oben 7.6, gerollt 0.2); 0 tragend im Baum, 1 dunkel ab 8000 px2 | Schirm 5.0 % dunkel (oben 5.0, gerollt 5.0); 0 tragend im Baum, 1 dunkel ab 8000 px2 | gruen |
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
| Home | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Home | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Chef | oben | 13.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `div.  rgb(239,68,68)` x10; `span.  rgb(249,115,22)` x1 |
| Chef | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Projekte | oben | 13.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `button.  rgb(20,26,22)` x10; `span.  rgb(249,115,22)` x1 |
| Projekte | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Arbeitsscheine | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Arbeitsscheine | gerollt | 8.9 % | `div.  rgb(249,115,22)` x48; `button.  rgb(59,130,246)` x18; `button.  rgb(239,68,68)` x18; `span.  rgb(249,115,22)` x1 |
| Planung | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Planung | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Zeiterfassung | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Zeiterfassung | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Abwesenheiten | oben | 18.0 % | `div.  rgb(249,115,22)` x108; `button.  rgb(0,150,64)` x20; `button.  rgb(124,58,237)` x16; `button.  rgb(220,38,38)` x16; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Abwesenheiten | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Monatsabrechnung | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Monatsabrechnung | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Fahrzeuge | oben | 14.9 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `div.  rgb(14,165,233)` x11; `div.  rgb(0,110,48)` x11; `span.  rgb(249,115,22)` x1 |
| Fahrzeuge | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Flotte | oben | 16.4 % | `div.  rgb(249,115,22)` x108; `div.  rgb(33,41,58)` x36; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Flotte | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Werkzeuge | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Werkzeuge | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Bauprovisorien | oben | 13.3 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `button.  rgb(0,150,64)` x7; `span.  rgb(249,115,22)` x1 |
| Bauprovisorien | gerollt | 5.9 % | `div.  rgb(249,115,22)` x48; `button.  rgb(0,150,64)` x8; `span.  rgb(249,115,22)` x1 |
| Gefahrenstoffe | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Gefahrenstoffe | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Mitarbeiter | oben | 14.8 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `div.  rgb(20,184,166)` x11; `div.  rgb(99,102,241)` x10; `span.  rgb(249,115,22)` x1 |
| Mitarbeiter | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Auswertungen | oben | 16.4 % | `div.  rgb(249,115,22)` x118; `button.  rgb(0,110,48)` x16; `button.  rgb(250,143,69)` x12; `div.  rgb(0,110,48)` x10; `span.  rgb(249,115,22)` x1 |
| Auswertungen | gerollt | 5.3 % | `div.  rgb(249,115,22)` x48; `button.  rgb(34,197,94)` x2; `span.  rgb(249,115,22)` x1 |
| Einstellungen | oben | 16.4 % | `div.  rgb(249,115,22)` x108; `div.  rgb(239,68,68)` x36; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Einstellungen | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Büro-Portal | oben | 12.6 % | `div.  rgb(249,115,22)` x108; `button.  rgb(250,143,69)` x12; `span.  rgb(249,115,22)` x1 |
| Büro-Portal | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Admin | oben | 14.8 % | `div.  rgb(249,115,22)` x118; `button.  rgb(250,143,69)` x12; `div.  rgb(0,110,48)` x11; `span.  rgb(249,115,22)` x1 |
| Admin | gerollt | 5.1 % | `div.  rgb(249,115,22)` x48; `span.  rgb(249,115,22)` x1 |
| Projekt/Dashboard | oben | 9.7 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `div.  rgb(0,150,64)` x10; `div.  rgb(59,130,246)` x10; `span.  rgb(34,197,94)` x1 |
| Projekt/Dashboard | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
| Projekt/Pläne | oben | 7.6 % | `div.  rgb(249,115,22)` x60; `button.  rgb(250,143,69)` x12; `span.  rgb(34,197,94)` x1 |
| Projekt/Pläne | gerollt | 0.1 % | `span.  rgb(34,197,94)` x1 |
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
| Home | gerollt | 7.1 % | `div.  rgb(249,115,22)` x44; `div.  rgb(0,150,64)` x15; `div.  rgb(59,130,246)` x5; `button.  rgb(250,143,69)` x4 |
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
| Abwesenheiten | oben | 7.5 % | `div.  rgb(249,115,22)` x44; `button.  rgb(0,150,64)` x9; `button.  rgb(124,58,237)` x9; `button.  rgb(220,38,38)` x6; `button.  rgb(250,143,69)` x4 |
| Abwesenheiten | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Monatsabrechnung | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Monatsabrechnung | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Fahrzeuge | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Fahrzeuge | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Flotte | oben | 7.2 % | `div.  rgb(249,115,22)` x44; `div.  rgb(33,41,58)` x21; `button.  rgb(250,143,69)` x4 |
| Flotte | gerollt | 7.2 % | `div.  rgb(249,115,22)` x44; `div.  rgb(33,41,58)` x21; `button.  rgb(250,143,69)` x4 |
| Werkzeuge | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Werkzeuge | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Bauprovisorien | oben | 5.3 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(0,150,64)` x3 |
| Bauprovisorien | gerollt | 5.3 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(0,150,64)` x3 |
| Gefahrenstoffe | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Gefahrenstoffe | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Mitarbeiter | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Mitarbeiter | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Auswertungen | oben | 5.4 % | `div.  rgb(249,115,22)` x44; `button.  rgb(0,110,48)` x4; `button.  rgb(250,143,69)` x4 |
| Auswertungen | gerollt | 5.1 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(34,197,94)` x1 |
| Einstellungen | oben | 6.2 % | `div.  rgb(249,115,22)` x44; `div.  rgb(239,68,68)` x12; `button.  rgb(250,143,69)` x4 |
| Einstellungen | gerollt | 5.1 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `button.  rgb(0,150,64)` x1 |
| Büro-Portal | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Büro-Portal | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Admin | oben | 7.5 % | `div.  rgb(249,115,22)` x50; `div.  rgb(59,130,246)` x6; `div.  rgb(239,68,68)` x6; `div.  rgb(0,110,48)` x6; `button.  rgb(250,143,69)` x4 |
| Admin | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Dashboard | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Dashboard | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Pläne | oben | 5.2 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4; `span.  rgb(59,130,246)` x1; `span.  rgb(161,98,7)` x1 |
| Projekt/Pläne | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Mängel | oben | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
| Projekt/Mängel | gerollt | 5.0 % | `div.  rgb(249,115,22)` x44; `button.  rgb(250,143,69)` x4 |
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
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Chef** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Projekte** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Arbeitsscheine** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Planung** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Zeiterfassung** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Abwesenheiten** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Monatsabrechnung** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Fahrzeuge** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Flotte** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |
| `div.-` | rgb(33, 41, 58) (roh rgba(15, 23, 42, 0.92)) | 0.022 | 15996 | 4.7 % | 🛰️ Noch keine Tracker zugeordnet — IMEI in der Liste (ohne Tracker) o |

**Werkzeuge** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Bauprovisorien** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Gefahrenstoffe** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Mitarbeiter** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Auswertungen** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Einstellungen** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |
| `div.-` | rgb(239, 68, 68) | 0.229 | 12675 | 3.7 % | System-Config laden fehlgeschlagen: Failed to fetch |

**Büro-Portal** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |
| `div.-` | rgb(217, 119, 6) | 0.280 | 13865 | 4.0 % | ⚠️ Fehler beim Laden |

**Admin** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(249, 115, 22) | 0.325 | 17160 | 5.0 % | ⚠️ SERVER · 3 ausstehend |

**Projekt/Dashboard** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Pläne** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Mängel** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Fotos** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Zeiterfassung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Berichte** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Formulare** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Checklisten** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Bautagebuch** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Material** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(217, 119, 6) | 0.280 | 13865 | 4.0 % | Anforderungen konnten nicht geladen werden |
| `div.-` | rgb(217, 119, 6) | 0.280 | 13865 | 4.0 % | Bestellungen konnten nicht geladen werden |

**Projekt/Dokumente** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/OFFA** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Export** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 21840 | 6.4 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

### Rolle admin, 1440 px, epk_theme=light

**Home** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(59, 130, 246) | 0.235 | 8889 | 0.7 % | - |

**Chef** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekte** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Arbeitsscheine** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Planung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Zeiterfassung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Abwesenheiten** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `button.-` | rgb(0, 150, 64) | 0.222 | 8729 | 0.7 % | 🏖️ Urlaub beantragen |

**Monatsabrechnung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Fahrzeuge** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Flotte** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(33, 41, 58) (roh rgba(15, 23, 42, 0.92)) | 0.022 | 21450 | 1.7 % | 🛰️ Noch keine Tracker zugeordnet — IMEI in der Liste (ohne Tracker) o |

**Werkzeuge** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Bauprovisorien** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Gefahrenstoffe** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Mitarbeiter** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Auswertungen** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Einstellungen** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(239, 68, 68) | 0.229 | 13071 | 1.0 % | System-Config laden fehlgeschlagen: Failed to fetch |

**Büro-Portal** - 2 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(217, 119, 6) | 0.280 | 15800 | 1.2 % | ⚠️ Fehler beim Laden |

**Admin** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Dashboard** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Pläne** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Mängel** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Fotos** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Zeiterfassung** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Berichte** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Formulare** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Checklisten** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Bautagebuch** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Material** - 3 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |
| `div.-` | rgb(217, 119, 6) | 0.280 | 15800 | 1.2 % | Anforderungen konnten nicht geladen werden |
| `div.-` | rgb(217, 119, 6) | 0.280 | 15800 | 1.2 % | Bestellungen konnten nicht geladen werden |

**Projekt/Dokumente** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/OFFA** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

**Projekt/Export** - 1 dunkle Flaechen ab 8000 px2:

| Klasse | Farbe (gemischt) | Helligkeit | px2 | Anteil | Text |
| --- | --- | --- | --- | --- | --- |
| `div.-` | rgb(249, 115, 22) | 0.325 | 63360 | 5.0 % | 📶 📤 3 Änderungen warten auf Sync 🔄 Jetzt sync |

## Fest verdrahtete dunkle Hintergruende im Quelltext

Eine Flaeche, deren Hintergrund als feste Farbe geschrieben ist, kann
der Hellmodus nicht erreichen - sie ist in beiden Themen gleich dunkel.
Diese Liste ist eine LEITLISTE und kein Urteil: Druck- und
Exportvorlagen stehen als HTML-Zeichenketten in derselben Datei und
tauchen hier mit auf, obwohl sie nie am Schirm haengen. Was wirklich am
Schirm haengt, sagt die Messung oben.

**61** fest geschriebene Hintergruende mit Helligkeit unter 0.5.
Gezeigt sind die 25 DUNKELSTEN; die vollstaendige Liste steht in
`screenshots/hellmodus_ansichten.json` unter `fest_verdrahtet`.
Gekappt wird nach Helligkeit, nicht nach Farbe - die uebrigen sind
heller, nicht anders gefaerbt (das Markengruen `#009640` mit 0,222
ist als Knopfflaeche unter weisser Schrift gewollt).

| Zeile | Farbe | Helligkeit | Umfeld |
| --- | --- | --- | --- |
| 17203 | `#0a0c14` | 0.004 | `r ihn wiederbelebt, liest diese Zeile und weiss, dass er die Farbe dann mitnehmen muss. */background:"#0a0c14",borderRadius:8,border:"1px so` |
| 30263 | `#0f0f0f` | 0.005 | `{minHeight:'100dvh',display:'flex',alignItems:'center',justifyContent:'center',padding:20,background:'#0f0f0f',color:'#e5e5e5',fontFamily:'s` |
| 7312 | `#111827` | 0.009 | `/_fitScale)+'%',display:'flex',flexDirection:'column'}}     ,h('div',{style:{flexShrink:0,background:'#111827',color:'#fff',display:'flex',a` |
| 7323 | `#111827` | 0.009 | `:'15%'}}))         ,h('thead',{},h('tr',{style:{height:'46px'}}           ,h('th',{style:{background:'#111827',color:'#fff',fontSize:15,font` |
| 7665 | `#0f172a` | 0.009 | `,.25)"};     const rahmen=(inhalt,abbruch)=>h('div',{style:{height:"100dvh",width:"100vw",background:"#0f172a",color:"#e2e8f0",         disp` |
| 7718 | `#0f172a` | 0.009 | `v',null,T('Einen Moment …')));   }   return h('div',{style:{height:"100dvh",width:"100vw",background:"#0f172a",color:"#e2e8f0",display:"flex` |
| 9506 | `#0f172a` | 0.009 | `)return React.createElement('div',{style:{height:"100dvh",width:"100vw",overflow:"hidden",background:"#0f172a"}},React.createElement('style'` |
| 23723 | `#161922` | 0.010 | `e: {display:"flex",justifyContent:"space-between",alignItems:"center",padding:"12px 16px",background:"#161922",flexShrink:0}}             , ` |
| 30264 | `#1a1a1a` | 0.010 | `system,sans-serif'}},         React.createElement('div',{style:{maxWidth:520,width:'100%',background:'#1a1a1a',border:'1px solid #3a3a3a',bo` |
| 7327 | `#1f2937` | 0.022 | `Dates[i].getDate())+'.'+_pad(dayDates[i].getMonth()+1)+'.'));})           ,h('th',{style:{background:'#1f2937',color:'#fff',fontSize:15,font` |
| 7684 | `#1e293b` | 0.022 | `  const dIn={padding:"16px 20px",borderRadius:12,border:"1px solid rgba(255,255,255,.25)",background:"#1e293b",                  color:"#fff` |
| 7734 | `#1e293b` | 0.022 | `:{width:"100%",padding:"10px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,.2)",background:"#1e293b",color:"#fff",fontSize:15}}   ` |
| 7738 | `#1e293b` | 0.022 | `,style:{flex:1,padding:"10px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,.2)",background:"#1e293b",color:"#fff",fontSize:15}})  ` |
| 7751 | `#1e293b` | 0.022 | `eader)",style:{padding:"10px 12px",borderRadius:8,border:"1px solid rgba(255,255,255,.2)",background:"#1e293b",color:"#fff",fontSize:15,widt` |
| 30273 | `#2a2a2a` | 0.023 | `set,style:{flex:'1 1 120px',padding:'10px 16px',borderRadius:8,border:'1px solid #3a3a3a',background:'#2a2a2a',color:'#fff',fontSize:14,font` |
| 29069 | `#525659` | 0.092 | `,     React.createElement('div',{onClick:e=>e.stopPropagation(),style:{flex:1,minHeight:0,background:"#525659",display:"flex",flexDirection:` |
| 22306 | `#006e30` | 0.114 | `Bem.")             , React.createElement('th', { style: {borderBottom:"2px solid #004d20",background:"#006e30"}})           ))           , R` |
| 12299 | `#7c3aed` | 0.134 | `line-flex',alignItems:'center',gap:4}},h('span',{style:{width:12,height:12,borderRadius:3,background:'#7c3aed',display:'inline-block'}}),'gr` |
| 22747 | `#7c3aed` | 0.134 | `"12px 20px",fontSize:isMob?12:14,borderRadius:10,display:"flex",alignItems:"center",gap:8,background:"#7c3aed",border:"none",color:"#fff",fo` |
| 22746 | `#dc2626` | 0.167 | `"12px 20px",fontSize:isMob?12:14,borderRadius:10,display:"flex",alignItems:"center",gap:8,background:"#dc2626",border:"none",color:"#fff",fo` |
| 11536 | `#8b5cf6` | 0.198 | `lach", onClick: e=>{e.stopPropagation();setAsShowQR(asShowQR===a.id?null:a.id);}, style: {background:"#8b5cf6",color:"#8b5cf6",border:"1px s` |
| 11576 | `#8b5cf6` | 0.198 | `lach", onClick: e=>{e.stopPropagation();setAsShowQR(asShowQR===a.id?null:a.id);}, style: {background:"#8b5cf6",color:"#8b5cf6",border:"1px s` |
| 14392 | `#8b5cf6` | 0.198 | `React.createElement('div', { style: {width:(m.cnt/maxCnt*100)+"%",height:6,borderRadius:3,background:"#8b5cf6"}} )))                   , Rea` |
| 20636 | `#8b5cf6` | 0.198 | `ord,"bestellt"), style: {padding:isMob?"8px 14px":"5px 12px",borderRadius:6,border:"none",background:"#8b5cf6",color:"#fff",fontWeight:600,f` |
| 20989 | `#8b5cf6` | 0.198 | `(so,"bestellt"), style: {padding:isMob?"8px 14px":"5px 12px",borderRadius:6,border:"none",background:"#8b5cf6",color:"#fff",fontWeight:600,f` |

## Gesamturteil

- Ansichten, deren Schirm im Hellmodus ab 25 % dunkel ist: **0**
- Ansichten NICHT GEMESSEN (Koeder versagt oder nicht erreicht): **1** - admin/Projekt/Alle Projekte
- Ansichten mit tragender Flaeche im Baum, die die Abtastung nicht
  sieht: **0**
- Ansichten gruen (Koeder schlug in beiden Massen an, Schirm unter
  25 % dunkel): **31**

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

