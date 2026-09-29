# Tippziele - Histogramm ueber die GANZE Menge

Erzeugt von `scripts/tippziel_histogramm.py` am 2026-09-29 19:46.
Breite des Fensters: 1440 px.

🔴 Dieses Werkzeug ersetzt eine Aussage, die auf einer nach HOEHE
sortierten und auf zwoelf gekappten Beispielliste beruhte. Fuer die
BREITE war diese Liste blind: ein hohes, schmales Ziel sortiert ans
Ende und faellt heraus. Hier wird gezaehlt, nicht ausgewaehlt.

Grundgesamtheit je Ansicht: `button, [role="button"], a, summary, .clickable, input[type="checkbox"], input[type="radio"], input[type="submit"], input[type="button"]`

## Zusammenzug

| Ansicht | Ziele | <24 nur hoch | <24 nur BREIT | <24 beides | <44 nur hoch | <44 nur BREIT | <44 beides |
|---|---:|---:|---:|---:|---:|---:|---:|
| abwesend | 66 | 0 | 0 | 0 | 12 | 3 | 3 |
| admin | 59 | 0 | 0 | 0 | 19 | 1 | 3 |
| as_form | 60 | 0 | 0 | 0 | 4 | 6 | 6 |
| as_liste | 780 | 0 | 0 | 0 | 12 | 1 | 721 |
| auswertungen | 127 | 0 | 0 | 0 | 6 | 1 | 93 |
| baupro | 29 | 0 | 0 | 0 | 7 | 1 | 3 |
| bautagebuch | 30 | 0 | 0 | 0 | 28 | 0 | 0 |
| berichte | 30 | 0 | 0 | 0 | 28 | 2 | 0 |
| buero | 38 | 0 | 0 | 0 | 9 | 1 | 3 |
| chef | 42 | 0 | 0 | 0 | 13 | 1 | 3 |
| einstell | 38 | 0 | 0 | 0 | 4 | 4 | 3 |
| fahrzeuge | 52 | 0 | 0 | 0 | 4 | 1 | 23 |
| flotte | 39 | 1 | 0 | 0 | 13 | 2 | 5 |
| gefahr | 28 | 0 | 0 | 0 | 6 | 1 | 3 |
| home | 59 | 0 | 0 | 0 | 4 | 1 | 5 |
| material | 36 | 0 | 0 | 0 | 36 | 0 | 0 |
| mitarbeiter | 40 | 0 | 0 | 0 | 6 | 1 | 3 |
| monatsabr | 33 | 0 | 0 | 0 | 4 | 3 | 3 |
| plaene | 57 | 0 | 0 | 0 | 44 | 0 | 8 |
| planung | 55 | 0 | 0 | 0 | 6 | 1 | 25 |
| werkzeuge | 751 | 0 | 0 | 0 | 110 | 301 | 305 |
| zeit | 57 | 0 | 0 | 0 | 15 | 3 | 15 |
| **Summe** | **2506** | **1** | **0** | **0** | **390** | **335** | **1233** |

Dieselbe Stelle kann in mehreren Ansichten vorkommen (Kopf-
und Fussleiste). Die Summe ist eine Summe von VORKOMMEN, nicht von
verschiedenen Stellen - das steht hier, statt verschwiegen zu
werden.

## abwesend

66 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 2, 32 px: 1, 36 px: 9, 40 px: 3, 44 px: 30, 48 px: 21
- **Breite** — 32 px: 2, 36 px: 2, 40 px: 2, 48 px: 60

  Beispiele unter 44 px BREIT (Auszug aus 6):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 44x33.2 px — 'Monat zurück'
  - `button` 44x33.2 px — 'Monat vor'

## admin

59 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 1, 28 px: 8, 32 px: 1, 36 px: 11, 40 px: 1, 44 px: 29, 48 px: 8
- **Breite** — 36 px: 2, 40 px: 2, 44 px: 1, 48 px: 54

  Beispiele unter 44 px BREIT (Auszug aus 4):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'

## as_form

60 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 1, 36 px: 8, 40 px: 1, 44 px: 39, 48 px: 11
- **Breite** — 32 px: 1, 36 px: 9, 40 px: 2, 48 px: 48

  Beispiele unter 44 px BREIT (Auszug aus 12):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 44x37.5 px — '−15 Min'
  - `button` 44x37.5 px — '+15 Min'
  - `button` 44x37.5 px — '−15 Min'
  - `button` 44x37.5 px — '+15 Min'

## as_liste

780 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 718, 28 px: 8, 32 px: 1, 36 px: 5, 40 px: 1, 44 px: 24, 48 px: 23
- **Breite** — 24 px: 163, 28 px: 555, 36 px: 2, 40 px: 2, 48 px: 58

  Beispiele unter 44 px BREIT (Auszug aus 722):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 24x30.5 px — 'Bearbeiten'
  - `button` 24x30.5 px — 'PDF Vorschau & Drucken'
  - `button` 24x30.5 px — 'QR-Code anzeigen'
  - `button` 24x27 px — 'Stornieren'

## auswertungen

127 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 15, 28 px: 75, 32 px: 3, 36 px: 5, 40 px: 1, 44 px: 28
- **Breite** — 32 px: 75, 36 px: 17, 40 px: 2, 48 px: 33

  Beispiele unter 44 px BREIT (Auszug aus 94):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 24x36 px — 'Diagramm ausblenden'
  - `button` 28x34.5 px — 'Balken'
  - `button` 28x34.5 px — 'Torte'
  - `button` 28x34.5 px — 'Ring'

## baupro

29 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 1, 36 px: 7, 40 px: 2, 44 px: 19
- **Breite** — 36 px: 2, 40 px: 2, 48 px: 25

  Beispiele unter 44 px BREIT (Auszug aus 4):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'

## bautagebuch

30 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 15, 36 px: 13, 44 px: 2
- **Breite** — 48 px: 30

## berichte

30 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 15, 36 px: 13, 44 px: 2
- **Breite** — 32 px: 2, 48 px: 28

## buero

38 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 1, 36 px: 10, 40 px: 1, 44 px: 26
- **Breite** — 36 px: 2, 40 px: 2, 48 px: 34

  Beispiele unter 44 px BREIT (Auszug aus 4):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'

## chef

42 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 28 px: 2, 32 px: 1, 36 px: 10, 40 px: 3, 44 px: 19, 48 px: 7
- **Breite** — 36 px: 2, 40 px: 2, 48 px: 38

  Beispiele unter 44 px BREIT (Auszug aus 4):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'

## einstell

38 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 1, 36 px: 5, 40 px: 1, 44 px: 31
- **Breite** — 36 px: 5, 40 px: 2, 48 px: 31

  Beispiele unter 44 px BREIT (Auszug aus 7):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 44x36.6 px — 'Passwort anzeigen'
  - `button` 44x36.6 px — 'Passwort anzeigen'
  - `button` 44x36.6 px — 'Passwort anzeigen'

## fahrzeuge

52 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 19, 36 px: 5, 40 px: 3, 44 px: 25
- **Breite** — 24 px: 18, 32 px: 2, 36 px: 2, 40 px: 2, 48 px: 28

  Beispiele unter 44 px BREIT (Auszug aus 24):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 42x32.6 px — 'Listenansicht'
  - `button` 42x34.7 px — 'Kachelansicht'
  - `button` 32x24 px — 'Als Favorit markieren'
  - `button` 32x24 px — 'Als Favorit markieren'

## flotte

39 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 12 px: 1, 24 px: 4, 28 px: 2, 32 px: 2, 36 px: 8, 40 px: 1, 44 px: 21
- **Breite** — 28 px: 2, 32 px: 1, 36 px: 2, 40 px: 2, 44 px: 1, 48 px: 31

  Beispiele unter 44 px BREIT (Auszug aus 7):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `a[role=button]` 30x30 px — 'Zoom in'
  - `a[role=button]` 30x30 px — 'Zoom out'
  - `button` 44x32.3 px — 'Fahrtenbuch maximieren'

## gefahr

28 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 1, 36 px: 7, 40 px: 1, 44 px: 19
- **Breite** — 36 px: 2, 40 px: 2, 48 px: 24

  Beispiele unter 44 px BREIT (Auszug aus 4):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'

## home

59 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 28 px: 1, 32 px: 2, 36 px: 5, 40 px: 1, 44 px: 37, 48 px: 13
- **Breite** — 28 px: 1, 32 px: 1, 36 px: 2, 40 px: 2, 48 px: 53

  Beispiele unter 44 px BREIT (Auszug aus 6):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 29x30 px — 'Daten aktualisieren'
  - `button` 32x32.7 px — 'Bereiche anpassen'

## material

36 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 3, 32 px: 15, 36 px: 18
- **Breite** — 44 px: 1, 48 px: 35

## mitarbeiter

40 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 1, 36 px: 7, 40 px: 1, 44 px: 22, 48 px: 9
- **Breite** — 36 px: 2, 40 px: 2, 48 px: 36

  Beispiele unter 44 px BREIT (Auszug aus 4):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'

## monatsabr

33 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 32 px: 1, 36 px: 5, 40 px: 1, 44 px: 22, 48 px: 4
- **Breite** — 36 px: 2, 40 px: 4, 48 px: 27

  Beispiele unter 44 px BREIT (Auszug aus 6):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 44x43.8 px — 'Monat zurück'
  - `button` 44x43.8 px — 'Monat vor'

## plaene

57 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 18, 28 px: 1, 32 px: 20, 36 px: 13, 44 px: 5
- **Breite** — 24 px: 2, 28 px: 4, 36 px: 2, 48 px: 49

## planung

55 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 20, 28 px: 2, 32 px: 3, 36 px: 5, 40 px: 1, 44 px: 24
- **Breite** — 24 px: 20, 32 px: 2, 36 px: 2, 40 px: 2, 48 px: 29

  Beispiele unter 44 px BREIT (Auszug aus 26):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 31x34.1 px — 'Woche zurück'
  - `button` 31x34.1 px — 'Woche vor'
  - `span[role=button]` 24x24 px — 'Zeile nach oben'
  - `span[role=button]` 24x24 px — 'Zeile nach unten'

## werkzeuge

751 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 353, 28 px: 55, 32 px: 1, 36 px: 5, 40 px: 1, 44 px: 328, 48 px: 8
- **Breite** — 24 px: 302, 32 px: 300, 36 px: 2, 40 px: 2, 48 px: 145

  Beispiele unter 44 px BREIT (Auszug aus 606):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `input` 24x24 px — 'div > div.header-row > div.mob-stack > label > input'
  - `input` 24x24 px — 'table > thead > tr > th > input'
  - `input` 24x24 px — 'table > tbody > tr > td > input'
  - `button` 44x34.5 px — 'Bearbeiten'

## zeit

57 Ziele. Klassen zu 4 px, `48` ist der Sammeltopf „48 px und mehr“.

- **Hoehe** — 24 px: 17, 28 px: 6, 32 px: 1, 36 px: 5, 40 px: 1, 44 px: 27
- **Breite** — 24 px: 12, 32 px: 2, 36 px: 2, 40 px: 2, 48 px: 39

  Beispiele unter 44 px BREIT (Auszug aus 18):
  - `button` 36x38 px — 'Foto-Warteschlange'
  - `button` 36x38 px — 'Theme: Auto (System) — tippen für Hell · Auto in den Einstellungen'
  - `button` 36x40.7 px — 'Benachrichtigungen'
  - `button` 44x42.5 px — 'Abmelden'
  - `button` 44x33.2 px — 'Woche zurück'
  - `button` 44x33.2 px — 'Woche vor'
  - `span[role=button]` 24x24.5 px — 'Eintrag bearbeiten'
  - `span[role=button]` 24x24 px — 'Eintrag löschen'

