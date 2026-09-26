# B3, Stufen 12–15 — dreizehn Hauptansichten gemessen, je bei 390 px UND 1440 px

Gemessen am **26.09.2026** an der eingefrorenen Kopie
`_mess_stand_944.html`, md5 **`cadd5f6c4ca871e5f256930e32d61283`**
(zu Beginn **und** am Ende der Sitzung derselbe Wert; `index.html` wurde nicht
geschrieben — `git status` nennt am Ende nur drei neue Dateien unter
`scripts/` und die Messkopie selbst).

| Stufe | Ansichten | Komponente |
|---|---|---|
| **12** | Chef-Dashboard · Zeiterfassung · Abwesenheiten | `ChefDashboard` · `ZeiterfassungView` · `AbsView` |
| **13** | Monatsabrechnung · Fahrzeuge · Flotte | `StundenzettelView` · `FahrzeugView` · `FlotteView` |
| **14** | Mitarbeiter · Auswertungen · Büro-Portal | `MitarbeiterView` · `AuswertungView` · `VBueroExport` |
| **15** | Admin · Einstellungen · Gefahrenstoffe · Bauprovisorien | `AdminPanel` · `VerbindungView` · `VGefahrstoff` · `BauprovisorienView` |

**Alle dreizehn sind gemessen**, je bei **390×844** (`is_mobile`, `has_touch`,
also `pointer: coarse`) und **1440×900** (`pointer: fine`), dazu je ein
eigener Lauf im **Hellmodus**. Das sind **52 Läufe**, alle mit Rückgabewert
**0** und der Schlusszeile `Alle Koeder haben angeschlagen`; der Rückgabewert
wurde getrennt von der Ausgabe gelesen (keine Pipe).
Rolle `admin`, `rolle=Geschäftsführer` (sonst fehlt der Chef-Reiter),
`monteurId=M1`, REST und Auth abgeklemmt. **Die Amber-/Orange-Warnbänder
(„4 Änderungen warten auf Sync", „Offline") sind Aufbau-Artefakt und kein
Befund.**

Sonden:

| Datei | was sie tut |
|---|---|
| `scripts/b3_stufen_12_15_messen.py` | **neu.** Die sieben Regeln aus Stufe 4–7 (unverändert importiert) plus die drei aus Stufe 8–11 auf dreizehn Ansichten × zwei Breiten × zwei Themen. **16 Köder.** Dateikopf sagt, was gemessen wird und was nicht. |
| `scripts/b3_12_15_quelltext.py` | **neu.** Schriftgrößen **je Komponente** aus dem Quelltext, Komponente abgegrenzt an der nächsten `\nfunction`-Deklaration (keine Klammerzählung), `code_scan.ist_code` + `eichen`. 3 Köder. |
| `scripts/b3_fussleiste_beschnitt.py` | **neu.** Einziger Zweck: die Frage „war die Fußleisten-Beschriftung auch bei 10 px schon gekürzt?" **messen** statt rechnen. 1 Köder. |
| `scripts/b3_stufen_8_11_messen.py` | als **Modul** benutzt: `EMOJI_ZAHL_JS`, `BESCHNITT_ECHT_JS`, `DUNKEL_JS`, `KOEDER_BESCH2_*`, `KOEDER_EMOJIZAHL_*`, `SEED2_JS`, `_scheine8`, `_plandaten`, `_formulare` |
| `scripts/b3_vier_ansichten_messen.py` | als **Modul**: `SCHRIFT_JS`, `TIPP_JS`, `EMOJI_JS`, `QUER_JS`, `BESCHNITT_JS`, `TABELLE_JS`, `MENGEN_JS`, `VERDECKUNG_JS`, `BIS_UNTEN_JS`, `NAV_TOP_JS`, `NAV_MEHR_JS`, `MEHR_ZU_JS`, `_koeder()` (K1–K8) |
| `scripts/anker_schneiden.py` | jeder Anker unten ist **aus der Datei geschnitten**, mit Vorkommenzahl. Kein abgetippter Anker in diesem Bericht. |

---

## 0. Zuerst: die eigenen Messfehler

### 0.1 Die zehn der Vorgänger — **nicht wiederholt**, und das ist belegt

| Vorgänger-Fehler | was hier dagegen getan wurde | Beleg |
|---|---|---|
| Der Klick bewies die **falsche Seite** (Gruppenknopf der Fußleiste) | `NAV_MEHR_JS` schließt `.bottom-nav` aus; danach ein **inhaltlicher** Nachweis je Ansicht, aus einem Erkundungslauf an *dieser* Datei abgelesen | 26 Nachweise `da: True`, Überschriften im JSON |
| Der **falsche Roller** (`window.scrollTo`) | `BIS_UNTEN_JS` fährt **jeden** Roller ans Ende und belegt das Ankommen | z. B. Auswertungen 390: `div.main-pad 5201/5845 am Ende` |
| **Tippziel und Beschriftung in einem Topf** | `TIPP_JS` führt zwei Töpfe; „Felder/Beschriftungen < 44 px" steht getrennt und ist **kein** Knopfbefund | in allen 26 Läufen ausgewiesen |
| Zählung nach **Wort statt Emoji+Wort** | `MENGEN_BENANNT_JS` vergleicht nach Abzug aller Nicht-Buchstaben | Mitarbeiter 5/5 |
| Dieselbe Zählung fand die Wörter in **`<option>`** | gesucht wird nur in `button`/`[role=button]`/`th`/`h1-3`/`label`/`a`, **nicht** in `option` | — |
| **Serverleere Reiter** als Ist-Zustand | §5 führt sie ausdrücklich als leere Grundgesamtheit | Flotte, Gefahrenstoffe, Bauprovisorien |
| `document.scrollingElement` beim Querrollen | `QUER_JS` prüft **jeden** Behälter, K5 als Positivkontrolle | K5 in allen 26 Läufen |
| `scrollWidth > clientWidth` trennt nicht | `BESCHNITT_ECHT_JS` + K9 mit **zwei** Baits | „falsch eingeordnet: 0" in allen Läufen |
| Zähler-Abzeichen rutscht am Emoji-Melder vorbei | `EMOJI_ZAHL_JS` (**ohne BUCHSTABEN**) + K13 | K13 in allen Läufen |
| Klammerzählung läuft davon | Komponenten an der **nächsten `\nfunction`-Deklaration** abgegrenzt, Größe geprüft (Rahmen 10–260 kB) | 13–163 kB, keine aus dem Rahmen |

### 0.2 **Drei neue eigene Messfehler**, hier behoben — jeder hat vorher eine saubere, falsche Zahl geliefert

**N-1 · `innerText` ist blind für SVG — und die Diagramme dieser App sind
SVG.** Der erste Namensmelder las `document.querySelector('.main-pad').innerText`
und meldete für die Auswertungen: **alle fünf Monteursnamen „nicht im Bild"**.
Das war die Kernfrage des Sonderauftrags, und die Antwort wäre gewesen:
„in den Diagrammen steht kein Mitarbeitername, also gibt es das Problem
nicht." Tatsächlich stehen **vier von fünf** als Balkenbeschriftung da.
`textContent` und `svg text` werden jetzt mitgelesen, und der Melder sagt,
**in welchem der beiden** der Name steht. Köder **K16**: mindestens ein Name
muss als SVG-Text gefunden werden, sonst lautet das Ergebnis „nicht gemessen".

**N-2 · Die Diagrammkarte war ihre eigene Überschrift.** Der erste
Kartensucher nahm „den kleinsten sichtbaren `div`, der den Titel enthält".
Das ist die Titelzeile selbst; zurück kam für alle 15 Karten
`inhalt: 'Scheine pro Monteur'` und sonst nichts — 15 Karten „gefunden", null
Inhalt gemessen. Gesucht wird jetzt der kleinste Behälter, der den Titel
**und ein `<svg>`** führt.

**N-3 · „Das ist eine Folge von v3.9.943" wäre gerechnet gewesen.** Für den
Beschnitt der Fußleisten-Beschriftung (§3, D1) lag die Rechnung nahe:
112 px × 10/12 = 93 px, also auch bei 10 px zu breit. Die Rechnung stimmt
für *ein* Wort und ist für die anderen vier **falsch**. Gemessen
(`b3_fussleiste_beschnitt.py`, 10-px-Regel per CSS eingesetzt, K-F1 belegt
das Greifen): bei 10 px war **nur** „Monatsabrechnung" gekürzt, die anderen
vier passten **genau** (74/74, 73/73, 72/72, 66/66). v3.9.943 hat also
**vier** neue Kürzungen erzeugt, nicht null und nicht fünf.

### Die sechzehn Köder, alle in allen Läufen angeschlagen

| Köder | Fall | Nachweis |
|---|---|---|
| K1–K8 | unverändert aus Stufe 4–7 | K8 **entfällt** bei 1440 px (`.bottom-nav` lebt in `@media(max-width:600px)`) — die Sonde sagt das ausdrücklich |
| K9 | Beschnitt-Einordnung, zwei Baits | „hart 1636/80; weich 305/60; falsch eingeordnet: 0" |
| K12 | Flächenmelder im **Dunkelmodus** | 7–19 tragende dunkle Flächen, Hülle `rgb(15, 17, 23)` |
| K13 | Knopf `🔩7` | alter Melder `False`, neuer `True` |
| **K14 Ehemalige** | Die Saat trägt **fünf** Monteure: drei aktive, **M4 ausgetreten MIT Beitrag** (2 Scheine, 1 Abwesenheit, 2 Zeiteinträge), **M5 ausgetreten OHNE jeden Beitrag**. `_maIstEhemalig` muss für M4/M5 wahr und für M1–M3 falsch sein; `_maWaehlbar(liste,null)` darf M5 **nicht** enthalten, `_maWaehlbar(liste,'M5')` **muss** ihn enthalten | in allen 26 Läufen: `{M1:F, M2:F, M3:F, M4:T, M5:T}`, `waehlbar=[M1,M2,M3]`, `mit getragenem M5=[M1,M2,M3,M5]`. **Ohne M4 wäre „Ausgetretene raus" nicht widerlegbar, ohne M5 wäre „mit Null im Bild" nicht messbar** |
| **K15 Bestandsschutz** | zu jeder Prüfliste wird zusätzlich ein Wort gesucht, das es dort **nicht** gibt (`Kalibrierungsintervallpruefung`) | `k15_falschtreffer: False` in allen Läufen — der Zähler zählt, was er behauptet |
| **K16 Namen im SVG** | mindestens ein Monteursname muss als SVG-Text gefunden werden | `ANGESCHLAGEN`, fünf von fünf |
| K-Q1 | die `UI`-Tabelle muss gefunden werden und `fMeta:12` tragen | `{fMeta:12, fKlein:13, fText:14, fTitel:15, fTitelGross:17, fZahl:20, fZahlGross:24, fUeber:28}` |
| K-Q2 | **Gegenprobe:** in `HomeView`/`WerkzeugView` sind die 9/10/11er laut v3.9.943/944 gehoben — der Zähler muss dort **0** finden | **0 und 0.** Der Zähler misst also dasselbe, was v3.9.943/944 behoben hat |
| K-Q3 | Komponentengröße im Rahmen 10–260 kB | 13–163 kB, keine verworfen |
| K-F1 | die eingesetzte 10-px-Regel muss greifen | gemessene Schriftgröße nach dem Einsetzen: 10 |

---

## 1. Messwerte, alle 26 Dunkelmodus-Läufe

| Ansicht | Breite | Schrift < 12 px | kleinste | Tippziel < 44 px | nur Symbol ohne title/aria | **ohne BUCHSTABEN** | quer (Wortlaut) | quer (tatsächlich) | **wirklich gekürzt** | nur Überlauf | verdeckt | Tabelle > Schirm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Chef | 390 | **17** von 63 (27 %) | 10 px | **0** | 0 | 0 | nein | keiner | 0 | 1 | 0 | – |
| Chef | 1440 | 22 von 79 | 10 px | 15 (Zeiger fein) | 0 | 0 | nein | keiner | 0 | 1 | entfällt | – |
| Zeiterfassung | 390 | **39** von 103 (38 %) | **9 px ×10** | **0** | 2 | 2 | nein | keiner | **1** | 1 | 0 | – |
| Zeiterfassung | 1440 | **56** von 131 (43 %) | 9 px ×10 | 30 (fein) | 2 | 2 | nein | keiner | 0 | 1 | entfällt | – |
| Abwesenheiten | 390 | **37** von 141 | **9 px ×5** | **0** | **6** | **6** | nein | keiner | **1** | 1 | 0 | – |
| Abwesenheiten | 1440 | 47 von 163 | 9 px ×5 | 17 (fein) | 2 | 2 | nein | keiner | 0 | 1 | entfällt | – |
| Monatsabrechnung | 390 | 11 von 51 | 10 px | **0** | 2 | 2 | nein | keiner | **1** | 1 | 0 | – |
| Monatsabrechnung | 1440 | 16 von 67 | 10 px | 9 (fein) | 2 | 2 | nein | keiner | 0 | 1 | entfällt | – |
| Fahrzeuge | 390 | 12 von 53 | **9 px ×1** | **0** | 2 | 2 | nein | keiner | 0 | 1 | 0 | – |
| Fahrzeuge | 1440 | 17 von 69 | 9 px ×1 | 11 (fein) | 2 | 2 | nein | keiner | 0 | 1 | entfällt | – |
| Flotte | 390 | 2 von 42 | 10 px | **1** ⚠ | 0 | 0 | nein | keiner | 0 | 2 | 0 | – |
| Flotte | 1440 | 13 von 59 | 10 px | 19 (fein) | 0 | 0 | nein | keiner | 0 | 2 | entfällt | – |
| Mitarbeiter | 390 | 16 von 66 | 10 px | **0** | 0 | 0 | nein | keiner | 0 | 1 | 0 | – |
| Mitarbeiter | 1440 | 24 von 82 | 10 px | 9 (fein) | 0 | 0 | nein | keiner | 0 | 1 | entfällt | – |
| **Auswertungen** | 390 | **155** von 294 (**53 %**) | 10 px ×135 | **0** | 0 | 0 | nein | keiner | 0 | 1 | 0 | – |
| **Auswertungen** | 1440 | **237** von 310 (**76 %**) | **8 px ×7**, 9 px ×50 | 99 (fein) | 0 | 0 | nein | keiner | 0 | 5 | entfällt | – |
| Büro-Portal | 390 | 10 von 57 | 10 px | **0** | 0 | 0 | nein | keiner | 0 | 1 | 0 | – |
| Büro-Portal | 1440 | 19 von 73 | 10 px | 12 (fein) | 0 | 0 | nein | keiner | 0 | 1 | entfällt | – |
| Admin | 390 | 25 von 103 | 10 px | **0** | 0 | 0 | nein | **1 Roller** | 0 | 1 | 0 | – |
| Admin | 1440 | 39 von 119 | 10 px | 22 (fein) | 0 | 0 | nein | keiner | 0 | 1 | entfällt | – |
| Einstellungen | 390 | 10 von 66 | **9 px ×4** | **0** | 0 | 0 | nein | keiner | 0 | 1 | 0 | – |
| Einstellungen | 1440 | 15 von 82 | 9 px ×4 | 10 (fein) | 0 | 0 | nein | keiner | 0 | 1 | entfällt | – |
| Gefahrenstoffe | 390 | 2 von 29 | 10 px | **0** | 0 | 0 | nein | keiner | **1** | 1 | 0 | – |
| Gefahrenstoffe | 1440 | 7 von 45 | 10 px | 9 (fein) | 0 | 0 | nein | keiner | 0 | 1 | entfällt | – |
| Bauprovisorien | 390 | 2 von 29 | 10 px | **0** | 0 | 0 | nein | keiner | **1** | 1 | 0 | – |
| Bauprovisorien | 1440 | 7 von 42 | 10 px | 9 (fein) | 0 | 0 | nein | keiner | 0 | 1 | entfällt | – |

**„Tippziel < 44 px" bei 1440 px ist KEIN Regelbruch** — die Hausregel gilt
`@media (pointer: coarse), (max-width: 768px)`. Bei **390 px**, wo sie gilt,
ist die Zahl in **zwölf von dreizehn** Ansichten **0**; die eine Ausnahme ist
**Flotte** (§3, D6). Und das ist ein Messwert, kein blinder Fleck: K2 (Knopf
30×20 px mit `!important` gegen die Hausregel) wurde in **jedem** Lauf mit
genau 1 gefunden.

**„nur Überlauf 1"** ist in **allen** Ansichten dasselbe Element: der
Sync-Knopf im Kopf (`Offline4` bzw. `Offline4Server ❌`). Das ist **B7 aus
Stufe 4–7**, dort bereits als „nichts geht verloren" abgeschlossen — hier
also kein neuer Befund, sondern die Bestätigung, dass er in allen dreizehn
Ansichten steht.

**Seitenfehler: 0 in allen 52 Läufen** (nach Abzug der erwarteten
REST-/Auth-Abbrüche).

### 1.1 Schriftgrößen **je Komponente** aus dem Quelltext

`python scripts/b3_12_15_quelltext.py` — Obergrenze für den Quelltext, nicht
Messwert am Schirm (eine Komponente kann Stellen führen, die dieser Aufbau
nie erreicht; die Spalte daneben sagt, wie viele davon im Bild ankamen).

| Komponente | Stufe | Größe | Stellen < 12 px im **Quelltext** | Verteilung | davon **gerendert** (390 px) |
|---|---|---|---|---|---|
| **FahrzeugView** | 13 | 163 kB | **113** | 9 px ×29 · 10 px ×40 · 11 px ×44 | 12 (1× 9 px) |
| **AdminPanel** | 15 | 115 kB | **76** | 9 px ×7 · 10 px ×21 · 11 px ×48 | 25 |
| **AbsView** | 12 | 98 kB | **66** | 9 px ×10 · 10 px ×35 · 11 px ×21 | 37 (5× 9 px) |
| **VBueroExport** | 14 | 105 kB | **25** | 9 px ×1 · 10 px ×2 · 11 px ×22 | 10 |
| **ChefDashboard** | 12 | 55 kB | **24** | 10 px ×15 · 11 px ×9 | 17 |
| **StundenzettelView** | 13 | 46 kB | **22** | 10 px ×10 · 11 px ×12 | 11 |
| **ZeiterfassungView** | 12 | 81 kB | **16** | 9 px ×2 · 10 px ×9 · 11 px ×5 | 39 (10× 9 px) |
| **AuswertungView** | 14 | 20 kB | **10** | 10 px ×3 · 11 px ×7 | 155 ⚠ |
| **FlotteView** | 13 | 34 kB | **8** | 10 px ×1 · 11 px ×7 | 2 |
| **MitarbeiterView** | 14 | 50 kB | **8** | 10 px ×2 · 11 px ×6 | 16 |
| **BauprovisorienView** | 15 | 39 kB | **7** | 10 px ×1 · **10,5 px ×1** · 11 px ×3 · **11,5 px ×2** | 2 |
| **VerbindungView** | 15 | 15 kB | **2** | 11 px ×2 | 10 |
| **VGefahrstoff** | 15 | 13 kB | **2** | 11 px ×2 | 2 |
| *HomeView* (K-Q2) | – | 87 kB | **0** | – | – |
| *WerkzeugView* (K-Q2) | – | 97 kB | **0** | – | – |

**Drei Zahlen dieser Tabelle brauchen eine Erklärung, sonst werden sie falsch
gelesen:**

1. **FahrzeugView, 113 Stellen, davon 12 im Bild.** Von den 29 `fontSize:9`
   sind **24 Feld-Beschriftungen** (`{...LL(),fontSize:9}`) in der
   Fahrerbescheinigung und im Serviceheft — Formulare, die in diesem Aufbau
   nicht offen waren. Die 113 sind die Arbeit, die dort liegt; die 12 sind,
   was der Nutzer beim Öffnen der Ansicht sieht.
2. **AuswertungView, 10 im Quelltext, 155 im Bild.** Die Differenz sind die
   **SVG-Diagramme**: `SvgHBar`/`SvgPie`/`SvgBar`/`SvgLine` sind eigene
   Funktionen außerhalb von `AuswertungView` und tragen `fontSize: 8/9/10/11`
   als **SVG-Attribut**. Sie skalieren mit dem `viewBox` — deshalb ist
   dieselbe Beschriftung bei **1440 px 9 px und bei 390 px 10 px**
   (schmalere Karte = größerer Maßstab). Das ist die Ursache dafür, dass die
   Auswertungen bei der **größeren** Breite die **kleinere** Schrift haben.
3. **BauprovisorienView** führt als einzige **gebrochene** Werte
   (`fontSize:10.5`, `fontSize:11.5`). Der Zähler aus Stufe 4–7 kannte nur
   ganze Zahlen; er hätte hier 10 und 11 gemeldet. Gemeldet wird jetzt der
   echte Wert.

---

## 2. Bestandsschutz — IST gegen `docs/GRUNDSTAND_UI_v3.9.930.md`

Der Grundstand kennt von den dreizehn Ansichten **drei**: Mitarbeiter,
Fahrzeuge, Abwesenheiten. Verglichen wird gegen die **benannten Stücke**,
nicht gegen die rohen Knopfzahlen — die Zählvorschrift des Grundstands ist
nirgends festgelegt, und der Datenbestand der Messumgebung ist ein anderer
(3 Monteure + 2 Ausgetretene, 3 Fahrzeuge, 8 Scheine gegen die echten
Bestände). Die Stücke werden **aus der Datei gelesen**, nicht abgetippt
(`_grundstand_zerlegen`).

### 2.1 Mitarbeiter — **5 von 5 benannten Stücken. Bestanden, 390 und 1440.**

| Grundstand nennt | IST 390 | IST 1440 |
|---|---|---|
| Mein Profil | ✔ `👤 Mein Profil` | ✔ |
| **Nur Aktive** (der Ehemalige-Umschalter) | ✔ `Nur Aktive` | ✔ |
| + Neuer Mitarbeiter | ✔ | ✔ |
| Stempel-Pausenregeln (aufklappbar) | ✔ `⏱ Stempel-Pausenregeln ▼` | ✔ |
| KV-Konstanten Metallgewerbe (aufklappbar) | ✔ `⚙ KV-Konstanten (Metallgewerbe) ▼` | ✔ |

Rohzahlen zur Einordnung, **nicht** als Prüfgröße: 15 Knöpfe (390) · 30
(1440), davon 5 aus dem Inhalt, der Rest Hülle. Der Grundstand nennt 14 an
einem anderen Bestand. Die Liste zeigt `Mitarbeiter (3)` — die beiden
Ausgetretenen fehlen, wie es der Schalter vorsieht.

### 2.2 Fahrzeuge — **6 von 8 wörtlich, 8 von 8 nach Gleichsetzung. Bestanden.**

| Grundstand nennt | IST | Gleichsetzung |
|---|---|---|
| Scan · Batch · Labels · Excel · PDF · + Fahrzeug | ✔ 6/6 wörtlich | – |
| **Listen-/Kachelumschalter** | ✔ **als `☰` und `⊞`** | der Grundstand **beschreibt**, die Oberfläche **zeichnet**. Zwei Knöpfe, beide gemessen, beide 44×44 px bei 390 px |
| **Favoritenstern je Fahrzeug** | ✔ **2× `☆`** (ein Stern je nicht stillgelegtem Fahrzeug) | dito |

**Kein Regressionsfehler.** Rohzahlen: 20 Knöpfe (390) · 35 (1440), davon 10
Inhalt. Der Grundstand nennt 19 — an 19 echten Fahrzeugen gegen 3 hier; die
Sterne skalieren mit dem Bestand, die Zahl ist deshalb nicht vergleichbar.
Beide `☰`/`⊞` sind **ohne `title` und ohne `aria-label`** (§3, D3).

### 2.3 Abwesenheiten — **8 von 10 wörtlich, 10 von 10 nach Gleichsetzung. Bestanden.**

| Grundstand nennt | IST | Gleichsetzung |
|---|---|---|
| Bearbeiten · Urlaub beantragen · Krankmeldung · Zeitausgleich · Anträge prüfen · Details · Excel · Server (SRVDC02) | ✔ 8/8 wörtlich | – |
| **Datei/Foto hochladen** | ✔ als `⬆️ Datei oder Foto hochladen — PDF, JPG, PNG` | der Wortlaut hat sich geändert, die **Handlung** ist da. Der Grundstand sagt ausdrücklich: Beschriftungstexte dürfen sich ändern |
| **vier Ansichtsreiter** | ✔ `📅` · `📨` · `📊` · `🗓️` bei 390 px; `📅 Kalender` · `📨 Anträge` · `📊 Übersicht` · `🗓️ Team-Timeline` bei 1440 px | dieselbe Zählung, andere Darstellung. **Bei 390 px tragen alle vier weder Text noch `title` noch `aria-label`** (§3, D2) |

**Die 21 Zahlen und die Kontingentliste:** Der Grundstand nennt elf Namen und
sagt im Nachtrag, dass ab v3.9.931 **zwei davon fehlen müssen**. Gemessen:
die Kontingent-Kompaktliste führt **drei** Namen (M1, M2, M3) — die beiden
Ausgetretenen fehlen. **Der Fix aus v3.9.931 wirkt.** Daneben steht eine
zweite Namensreihe, die **alle fünf** führt; die ist die Auswahl-Pillenreihe
und gehört zu den Filter-/Kalenderlisten — dort ist das gewollt. **Aber sie
zeigt einen Resturlaub** (§4, E2).

### 2.4 Die zehn übrigen Ansichten — **NEUER Grundstand, NICHT ABGENOMMEN**

`GRUNDSTAND_UI_v3.9.930.md` kennt **Chef-Dashboard, Zeiterfassung,
Monatsabrechnung, Flotte, Auswertungen, Büro-Portal, Admin, Einstellungen,
Gefahrenstoffe und Bauprovisorien nicht**. Die folgende Aufnahme ist ein
**neuer Grundstand, und niemand hat ihn abgenommen.** Er gehört vor dem
Umbau nachgetragen, sonst hat der Umbau in zehn von dreizehn Ansichten keine
Abnahmegrundlage.

**Chef-Dashboard** (`ChefDashboard`) — Überschrift `👑 Chef-Portal`,
Untertitel `Live-Status nach Bereichen · <Datum>`
* **5 Unterreiter**: `👑 Überblick` (Voreinstellung) · `🏗️ Projekte` ·
  `📋 Arbeit` · `👥 Personal` · `📦 Ressourcen`
* **5 KPI-Kacheln**: `Aktive Projekte` · `Offene AS` · `Monteure heute` ·
  `Heutige AS` · `Überfällig` — jede mit Wert, Trendpfeil und Untertitel
* **2 aufklappbare Blöcke**: `🚨 Handlungsbedarf (N) ▸` ·
  `🎫 Mängel & Tickets ▸`
* 0 Eingabefelder, 0 Auswahlfelder. 15 Knöpfe im Inhalt (beide Breiten).

**Zeiterfassung** (`ZeiterfassungView`) — **keine `<h1>/<h2>/<h3>`**
* Kopf: `◀` · `KW nn / jjjj` · `▶` · `<von>. – <bis>.` · `Aktuell` ·
  `👥 Alle Monteure`
* Erklärtext „Arbeitsstunden pro Monteur und Woche erfassen…"
* **1 Auswahlfeld `👷 Mitarbeiter:`** (4 Optionen: Platzhalter + **3 aktive**
  Monteure — `_maWaehlbar` greift), **1 Auswahlfeld `📋 Bauwochenbericht:`**
  (3 Optionen)
* Wochensumme `38.5h / Woche`, Tageszeilen `Mo21.09. · 8.0h` mit
  `📁Projekt`-Chip (9 px), `✏️`, `✕`, Zeitspanne `07:00–16:00` (9 px)
* 29 Knöpfe / 5 Felder / 2 Auswahlfelder im Inhalt

**Monatsabrechnung** (`StundenzettelView`) — `📄 Monatsabrechnung`
* **4 KPI**: `Gesamt` · `Offen` · `Freigegeben` · `Abgeglichen`
* `🖨️ Monatsübersicht drucken` · `◀` · `<Monat Jahr>` · `▶`
* Block `📊 Meine Monatssumme`: `Ist-Stunden` · `Entfernungszulage` ·
  `N klein · N mittel · N groß`
* Block `📤 Monatszettel hochladen` mit Auswahlfeldern `Mitarbeiter`
  (14 Optionen), `Monat` (12), `Jahr` (5)
* Filterzeile mit `Alle Monate` (13), `Jahr` (5), `Alle Mitarbeiter` (14)
* **6 Auswahlfelder**, 3 Knöpfe im Inhalt

**Flotte** (`FlotteView`) — **keine `<h1>/<h2>/<h3>`**
* `▸ 🚐 Fahrzeuge (N)` · Leaflet-Karte mit `+` / `−` / `Karte` / `Satellit`
* Band `🛰️ Noch keine Tracker zugeordnet — IMEI in der Liste … eintragen`
* Block `📖 Fahrtenbuch` mit **3 Reitern** `Fahrten` · `Tageskilometer` ·
  `Geschwindigkeit`, `⛶`, Auswahlfeld `🚐 Alle Fahrzeuge`, Zeitraum
  `–` · `Heute` · `Woche` · `Monat` · `Vormonat`, Summenzeile
* 12 Knöpfe / 2 Felder / 1 Auswahlfeld im Inhalt
* **Die Positionen und Fahrten kommen vom SERVER** — §5

**Auswertungen** (`AuswertungView`) — `📊 Auswertungen & Dashboards`
* **3 Kopfknöpfe**: `📥 Alle als Excel` · `🖨️ PDF` · `👁️ Alle ausblenden`
* **6 KPI**: `Arbeitsscheine` · `Projekte aktiv` · `Werkzeugwert` ·
  `Fahrzeuge` · `Abwesenheiten` · `Auftragsvolumen`
* Block `💶 Auftragsvolumen nach Geschäftsjahr` mit Umschalter
  `nach Projektende` / `nach Projektstart`
* **6 aufklappbare Bereiche** mit **15 Diagrammen**:
  `📋 Arbeitsscheine` (3) · `🏗️ Projekte` (2) · `⏱️ Zeiterfassung` (1) ·
  `🏖️ Abwesenheiten` (2) · `🔧 Werkzeuge` (3) · `🚐 Fahrzeuge` (4)
* je Diagramm **5 Typ-Umschalter** (`📊` `🥧` `🍩` `📈` `📶`) und ein
  Sichtbarkeits-Schalter — **alle 78 tragen `title`** (gemessen, nicht
  angenommen: „nur-Symbol ohne title/aria: 0, mit: 78")
* 101 Knöpfe im Inhalt, 0 Felder, 0 Auswahlfelder

**Büro-Portal** (`VBueroExport`) — `📋 Büro-Export`
* **5 Unterreiter**: `📁 Projekte` (Voreinstellung) · `⏱ Stempelzeiten` ·
  `💶 Zulagen` · `📅 Abwesenheiten` · `⛽ Tank`
* **4 KPI**: `Buchungen` · `Tagesberichte` · `Projekte` · `Stunden total`
* Block `📊 Bauwochenberichte` mit `📥 Alle als Excel`, je Projekt
  `▸ Vorschau` und `📥 Excel`
* 10 Knöpfe im Inhalt

**Admin** (`AdminPanel`) — `⚙️ Administration`
* `+ Neuer Benutzer`
* **6 Unterreiter**: `👤 Benutzer` (Voreinstellung) · `📋 Aktivität` ·
  `📊 Statistiken` · `🏪 Händler` · `🔗 Juprowa` · `⚙️ System`
* **4 KPI**: `Benutzer` · `Gesperrt` · `Admins` · `Online heute`
* **8 Rollenfilter-Chips**: `Alle` · `👑 Administrator` · `🏗️ Projektleiter` ·
  `📋 Büro` · `⭐ Obermonteur` · `🔬 Techniker` · `🔧 Monteur` · `👷 Helfer` ·
  `👁️ Nur Lesen`
* Sortierung `Sort: Rolle` / `Sort: Name`, 1 Suchfeld, 1 Auswahlfeld
* 19 Knöpfe / 1 Feld / 1 Auswahlfeld im Inhalt
* Die Benutzerliste kommt **nicht** vom Server, sondern aus `INIT_USERS`
  (8 eingebaute Zeilen) — gemessen, siehe §5

**Einstellungen** (`VerbindungView`) — `⚙️ Einstellungen`
* `👤 Mein Profil` (Name, Benutzername, Rolle, **Gewerk** mit 3 Optionen)
* `🔑 Passwort ändern` (3 Felder + 3× `👁️` + `💾 Passwort ändern`)
* `☁️ Supabase-Verbindung` (URL-Feld, `🔍 Verbindung testen`)
* Thema: `☀️ Hell` · `🌙 Dunkel` · `🅰️ Auto`
* `🔄 Jetzt synchronisieren` · `🗑️ Lokale Daten löschen` ·
  `✓ Smoke-Tests` · `🔍 Integrität`
* 12 Knöpfe / 4 Felder / 1 Auswahlfeld im Inhalt

**Gefahrenstoffe** (`VGefahrstoff`) —
`☣️ Gefahrenstoffe — Sicherheitsdatenblätter`
* `📁 + Ordner` · `📤 PDF hochladen` · Brotkrume `🏠 Start` · 1 Suchfeld
* Leerzustand `☣️ Leerer Ordner — Lege einen Ordner an oder lade ein PDF hoch.`
* **Die Ordner und PDFs kommen vom SERVER** — §5

**Bauprovisorien** (`BauprovisorienView`) — **keine `<h1>/<h2>/<h3>`**
(Überschrift `🚧 Bauprovisorien` steht in einem `div`)
* `🔄 Kunden synchronisieren` · `+ Neu` · `📷 Kasten-QR scannen & öffnen`
* Leerzustand `Noch keine Bauprovisorien erfasst. Lege oben das erste an.`
* **Die Zeilen kommen vom SERVER** — §5

---

## 3. Die Befunde, mit Vorschlag

Reihenfolge nach Wirkung. Jeder Anker ist **aus der Datei geschnitten**
(`scripts/anker_schneiden.py`); zu jedem steht die Zahl der Vorkommen im
**ganzen** Dokument — steht dort 1, ist `grep -F` eindeutig.

---

### D1 — v3.9.943 hat die Fußleisten-Beschriftung auf 12 px gehoben. Seither werden **vier zusätzliche** Reiternamen abgeschnitten. *(nur 390 px, betrifft ALLE Ansichten)*

**Messwert, 390 px.** Der aktive Gruppenknopf der Fußleiste zeigt den Namen
des aktiven Reiters. Sein Schlitz ist **74 px** breit, der Text trägt
`overflow:hidden` + `text-overflow:ellipsis`:

| Reiter | Textbreite bei **12 px** | verloren | Textbreite bei **10 px** (gemessen) | verloren |
|---|---|---|---|---|
| **Monatsabrechnung** | 112 | **37,5 px** | 93 | 19 px |
| **Abwesenheiten** | 89 | **15,3 px** | **74** | **0** |
| **Bauprovisorien** | 88 | **13,7 px** | **73** | **0** |
| **Gefahrenstoffe** | 86 | **11,9 px** | **72** | **0** |
| **Zeiterfassung** | 80 | **5,6 px** | **66** | **0** |

Die 10-px-Spalte ist **gemessen, nicht gerechnet** — siehe Messfehler N-3.
Die Leiste wächst dabei von **55 auf 58 px**; das bleibt genau auf
`--epk-bar-h: 58px` und ist der Wert, den der Kommentar zu v3.9.943
ausdrücklich gemessen hat. **Die Breite hat er nicht gemessen.**

Das ist der teuerste Beschnitt der ganzen Messreihe, und er steht in
**jeder** Ansicht bei 390 px.

**Anker** (`grep -F`, **1×**, 52 Zeichen) — der Ausdruck, der den Namen wählt:

```
isActive&&gr.g<4&&tabs[safeKat]?tabs[safeKat].l:gr.l
```

Die beschneidende Regel (`grep -F`, im GCSS-Block):

```
.bottom-nav button > span {
    overflow: hidden !important;
```

**Vorschlag, drei Wege, in dieser Reihenfolge zu prüfen.**

1. **Der kleinste:** dem `span` `title={...}` geben — dann steht der ganze
   Name wenigstens beim langen Antippen/Zeigen. Kostet kein Pixel, ändert
   nichts am Bild. **Löst das Problem am Telefon aber nur halb**, weil `title`
   dort kaum erreichbar ist.
2. **Der richtige:** die Gruppenbeschriftung **kürzen statt zeichnen lassen**
   — die Leiste zeigt heute den Namen des aktiven *Reiters*
   (`tabs[safeKat].l`), obwohl daneben schon das Gruppen-Symbol steht. Ein
   Kurzname je Reiter (`Monatsabr.`, `Abwesenh.`, `Bauprov.`,
   `Gefahrst.`, `Zeiterf.`) in der Reiter-Tabelle `_allTabs` als neues Feld
   `k` und `tabs[safeKat].k||tabs[safeKat].l` an dieser Stelle. **Das ist
   eine Textentscheidung und gehört Sebastian vorgelegt**, weil es
   Beschriftungen erfindet.
3. **Zurück auf die Gruppenbeschriftung** (`gr.l` immer, also `isActive&&…`
   entfernen): die fünf Gruppennamen (`Home · Baustelle · Zeit · Fuhrpark ·
   Mehr`) passen alle in 74 px. Das nimmt dem Nutzer aber die Information,
   **welcher** Reiter der Gruppe gerade offen ist — und genau die war der
   Grund, warum der Ausdruck so gebaut ist.

**Risiko.** Weg 1: null. Weg 2: neue Wörter im Bild, aber keine
Layout-Änderung. Weg 3: Informationsverlust, den jemand entscheiden muss.
**Gegenmessung:** `python scripts/b3_fussleiste_beschnitt.py`. In der Spalte
„12px … gekuerzt" muss aus **True/True/True/True/True** ein
**False/False/False/False/?** werden, und die Leistenhöhe muss **58 px**
bleiben (sonst ist die Endreserve des Inhalts aus v3.9.932 verletzt).

---

### D2 — Die vier Unterreiter der Abwesenheiten sind bei 390 px vier Ikonen ohne jedes Wort. *(nur 390 px)*

**Messwert.** Abwesenheiten bei 390 px: `📅` · `📨` · `📊` · `🗓️`, je
44×44 px, **kein `title`, kein `aria-label`, keine Beschriftung** — gemessen,
nicht gelesen: `{'zeichen': '📅', 'title': None, 'aria': None, 'h': 44,
'w': 44}`. Bei 1440 px heißen dieselben Knöpfe `📅 Kalender`,
`📨 Anträge (N)`, `📊 Übersicht`, `🗓️ Team-Timeline`.

**Das ist exakt C1 aus Stufe 8–11** (Plan-Unterreiter) und **exakt der Fall,
den v3.9.942 bei den fünf Werkzeug-Reitern behoben hat.** Der Griff steht
also schon im Code und kann abgeschrieben werden. Die Beschriftung
**existiert** im Objekt (`l`) — es wird kein Wort erfunden.

**Anker** (`grep -F`, **1×**, 62 Zeichen):

```
setSubView(t.id), style: {padding:isMob?"8px 10px":"10px 18px"
```

Die ausblendende Stelle steht in derselben Zeile:
`whiteSpace:"nowrap",minHeight:44}}, t.i, " " , isMob?"":t.l))` — die kommt
im Dokument **2×** vor und taugt deshalb **nicht** als Anker.

**Vorschlag.** Dem Reiterknopf `title: t.l` und `'aria-label': t.l`
mitgeben. **Risiko: null sichtbare Änderung.**
**Gegenmessung:** `python scripts/b3_stufen_12_15_messen.py --nur abwesend
--dunkel`. „OHNE BUCHSTABEN ohne title/aria" muss bei 390 von **6 auf 2**
fallen (die verbleibenden 2 sind `◀`/`▶`, siehe D4).

---

### D3 — Der Listen-/Kachelumschalter der Fahrzeuge trägt keinen Hinweis. *(beide Breiten)*

**Messwert.** Fahrzeuge, beide Breiten: `☰` und `⊞`, **ohne `title`, ohne
`aria-label`, ohne Text**. 44×44 px bei 390 px; bei 1440 px **33×42** bzw.
**35×42 px**. Der Grundstand nennt sie als „Listen-/Kachelumschalter" — die
Oberfläche sagt das Wort nirgends.

**Anker** (`grep -F`, **1×**, 84 Zeichen):

```
setView("liste"), style: {padding:"6px 10px",border:"none",background:view==="liste"
```

Der Zwilling (`⊞`) steht in derselben Reihe mit `setView("kacheln")`.

**Vorschlag.** `title` / `aria-label`: „Listenansicht" bzw. „Kachelansicht",
dazu `aria-pressed={view==="liste"}` — das Paar ist ein Umschalter, und ohne
`aria-pressed` sagt es nicht, welcher Zustand gerade gilt.
**Risiko: null sichtbare Änderung.**
**Gegenmessung:** `--nur fahrzeuge --dunkel`; „OHNE BUCHSTABEN ohne
title/aria" muss bei beiden Breiten von **2 auf 0**.

---

### D4 — Sechs `◀`/`▶`-Knöpfe in drei Ansichten tragen keinen Hinweis. *(beide Breiten)*

**Messwert.** Je ein Paar in **Zeiterfassung** (Kalenderwoche),
**Abwesenheiten** (Monat) und **Monatsabrechnung** (Monat), alle **ohne
`title`, ohne `aria-label`**. Höhe 44 px; Breite bei 1440 px **33 px**
(Zeiterfassung, Abwesenheiten) bzw. 44 px (Monatsabrechnung).
Derselbe Fall wie **B5 a/b aus Stufe 4–7** (Planung) und **C9 aus Stufe 8–11**
(Wochenbericht) — inzwischen der dritte Fundort desselben Musters.

**Anker**, alle **1×**:

| Ansicht | Anker | Länge |
|---|---|---|
| Zeiterfassung | `onClick:()=>switchKw(kw-1)` | 26 |
| Abwesenheiten | `onClick: ()=>setMo(Math.max(0,mo-1))` | 36 |
| Monatsabrechnung | `setSelMonat(m);setSelJahr(y);}, style: {...bsS(),padding:"6px 14px",fontSize:16,lineHeight:1}}, "◀")` | 100 |

Der jeweilige `▶`-Zwilling steht in derselben Zeile.

**Vorschlag.** `title` / `aria-label`: „Kalenderwoche zurück/vor" bzw.
„Monat zurück/vor". **Risiko: null sichtbare Änderung.**
**Anmerkung:** Dieses Muster ist inzwischen **dreimal in drei Messreihen**
gefunden worden (Planung, Wochenbericht, hier). Es wäre billiger, einmal
**alle** `◀`/`▶`-Paare der Datei zu suchen und in **einem** Schritt zu
versorgen, als die Fundstellen einzeln nachzuziehen.
**Gegenmessung:** `--nur zeit --dunkel`, `--nur abwesend --dunkel`,
`--nur monatsabr --dunkel`; „OHNE BUCHSTABEN ohne title/aria" muss in
Zeiterfassung und Monatsabrechnung bei **beiden** Breiten von **2 auf 0**
gehen, in Abwesenheiten bei 390 von 6 auf 4 (Rest ist D2) und bei 1440 von
**2 auf 0**.

---

### D5 — Die sechs Admin-Unterreiter rollen bei 390 px quer, drei davon sind nicht zu sehen. *(nur 390 px)*

**Messwert.** Admin bei 390 px: ein waagrechter Roller,
**scrollWidth 562 gegen clientWidth 374** — **188 px zu viel**. Darin liegen
die sechs Unterreiter `👤 Benutzer · 📋 Aktivität · 📊 Statistiken ·
🏪 Händler · 🔗 Juprowa · ⚙️ System`; breitestes Kind **100 px**
(`📊 Statistiken`). Im Bild sind **drei** zu sehen.

Es ist der **einzige** tatsächliche Querroller in allen 26 Läufen — und das
ist ein Messwert, kein blinder Fleck: K5 (3000 px breites Kind) wurde in
jedem Lauf gemeldet, samt abschneidendem Vorfahren
`html > body overflow-x:hidden`.

**Anker** (`grep -F`, **1×**, 71 Zeichen):

```
display:"flex",gap:4,marginBottom:14,overflowX:"auto",paddingBottom:4}}
```

**Vorschlag.** **Umbrechen statt rollen** (`flexWrap: "wrap"` statt
`overflowX: "auto"`, und `flexShrink:0` an den Knöpfen kann bleiben) — genau
der Griff, mit dem v3.9.930 die Chip-Leiste der Arbeitsscheine und die
Kachelreihe behoben hat, mit derselben Begründung: ein quer rollbarer Kasten
**verbraucht die waagrechte Wischgeste selbst**, und die Wischgeste ist in
dieser App der Reiterwechsel. Kosten: zwei Zeilen statt einer, also ~44 px
Höhe.
**Risiko:** gering und örtlich begrenzt. Zu bedenken: `whiteSpace:"nowrap"`
an den Knöpfen bleibt richtig, sonst bricht der Reitertext selbst um.
**Gegenmessung:** `--nur admin --dunkel`; in „quer, TATSAECHLICH" muss
`… div.main-pad > div > div 374/562` **verschwinden**, und die Zahl der
Unterreiter muss **vorher und nachher 6** sein.

---

### D6 — Ein Bedienelement unter 44 px bei 390 px, und es ist das einzige der ganzen Messreihe. *(nur Flotte, nur 390 px)*

**Messwert.** Flotte bei 390 px: **1** Knopf unter 44 px. In den anderen
zwölf Ansichten: **0**. Der Melder ist nicht stumm — K2 (Knopf 30×20 px mit
`!important` gegen die Hausregel) wurde in jedem Lauf mit genau 1 gefunden,
und dieser eine kommt **zusätzlich**.

**Der Verdacht, der sich NICHT bestätigt hat, und warum das hier steht.**
Der Auftrag nennt den Fall, in dem eine CSS-Regel die 44-px-Hausregel durch
**höhere Spezifität** schlägt (`.header-row .mob-stack button` = 0,2,1 gegen
`button` = 0,0,1). Die Sonde fragt bei jedem zu kleinen Element **das Element
selbst**, welche `min-height`/`height`-Regeln auf es passen und mit welcher
Spezifität. Ergebnis in allen 26 Läufen: die Liste der konkurrierenden
Regeln ist **leer**; die zu kleinen Elemente tragen einen **Inline-Stil**
(`inline=32px`, `inline=36px`). **Es gibt in diesen dreizehn Ansichten keinen
zweiten Spezifitäts-Fall.** Bei 390 px schlägt die Hausregel (`!important`)
den Inline-Stil, deshalb sind die Zahlen dort 0.

**Was das eine Element bei 390 px ist, ist NICHT ermittelt.** Die Sonde
meldet die Zahl und die ersten sechs Proben; die sechs Proben, die im Log
stehen, sind die aus dem **1440er**-Lauf (`🔄 Jetzt sync` 93×32,
`Offline4Server ❌` 81×36, `📷` 38×36, `🔍⌘K` 59×36, `🌙` 38×36, `🔔` 41×36 —
allesamt **Kopfleiste**, also nicht Flotte-eigen). **Der eine Fall bei
390 px in Flotte ist damit gezählt, aber nicht benannt** — siehe §6.

**Vorschlag.** Erst benennen, dann reparieren. Die Sonde ist dafür schon
gebaut (`WER_GEWINNT_JS`); sie muss nur mit `--nur flotte` bei 390 px
gefahren und ihre `proben`-Liste gelesen werden. Der wahrscheinlichste
Kandidat nach der Aufnahme sind die **Leaflet-Kartensteuerungen** (`+` / `−`
/ `Karte` / `Satellit`) — die kommen aus fremdem CSS und stehen nicht unter
`button` in der App-Hülle. Ist es das, gehört die Hausregel um
`.leaflet-control a` erweitert, **nicht** das Leaflet-CSS angefasst.
**Risiko:** unbekannt, solange das Element unbenannt ist — deshalb kein Fix
in diesem Durchgang.
**Gegenmessung:** `--nur flotte --dunkel`; „Tippziele (Knoepfe) < 44 px" muss
bei 390 von **1 auf 0**, und K2 muss weiter anschlagen.

---

### D7 — Schrift unter 12 px: die Auswertungen sind der dichteste Fall der ganzen Messreihe, und bei der **größeren** Breite ist die Schrift **kleiner**

**Messwert.** Anteil der sichtbaren Textstellen unter 12 px:

| Ansicht | 390 px | 1440 px | kleinster Wert |
|---|---|---|---|
| **Auswertungen** | **155 von 294 (53 %)** | **237 von 310 (76 %)** | **8 px** (7 Stellen, **nur 1440**) |
| Zeiterfassung | 39 von 103 (38 %) | 56 von 131 (43 %) | **9 px** (10 Stellen, beide Breiten) |
| Abwesenheiten | 37 von 141 (26 %) | 47 von 163 | **9 px** (5 Stellen, beide Breiten) |
| Admin | 25 von 103 | 39 von 119 | 10 px |
| Chef-Dashboard | 17 von 63 | 22 von 79 | 10 px |
| Mitarbeiter | 16 von 66 | 24 von 82 | 10 px |
| Fahrzeuge | 12 von 53 | 17 von 69 | **9 px** (1 Stelle) |
| Monatsabrechnung | 11 von 51 | 16 von 67 | 10 px |
| Einstellungen | 10 von 66 | 15 von 82 | **9 px** (4 Stellen) |
| Büro-Portal | 10 von 57 | 19 von 73 | 10 px |
| Flotte | 2 von 42 | 13 von 59 | 10 px |
| Gefahrenstoffe | 2 von 29 | 7 von 45 | 10 px |
| Bauprovisorien | 2 von 29 | 7 von 42 | 10 px |

**Die 8 px in den Auswertungen bei 1440 px sind der kleinste Wert der ganzen
Messreihe** — und sie stehen **nur** dort. Ursache: die Diagramm-Beschriftung
ist SVG-Text in einem `viewBox`; der Maßstab hängt an der **Kartenbreite**.
Bei 390 px liegen die Karten untereinander und sind breit im Verhältnis zum
`viewBox` (Beschriftung rendert 10 px), bei 1440 px liegen sie im Raster
nebeneinander (9 px, Linien-Diagramm 8 px). **Eine Vergrößerung des Fensters
verkleinert hier die Schrift.**

**Anker für die kleinsten Stellen** (`grep -F`, alle **1×**):

| # | Stelle | Wert | Anker | Länge |
|---|---|---|---|---|
| a | Zeiterfassung: Zeitspanne `07:00–16:00` in der Tageszeile | **9** | `fontSize:9,color:V.dm,marginLeft:"auto"}},entry.von` | 50 |
| b | Zeiterfassung: Art-Chip `📁Projekt` | **9** | `gap:3,fontSize:9,fontWeight:600,color:x.c,background:x.bg` | 57 |
| c | Abwesenheiten: Resturlaub im Auswahl-Pill (`193h · 0K`) | **9** | `display:"block",fontSize:9,opacity:.85,fontFamily:mono` | 54 |
| d | Abwesenheiten: Antrags-Abzeichen am Pill | **9** | `width:16,height:16,fontSize:9,fontWeight:800` | 44 |
| e | Fahrzeuge: Abzeichen `MEIN` | **9** | `isMine&&React.createElement('span', { style: {fontSize:9,padding:"2px 6px"` | 74 |
| f | SVG-Diagramme: Beschriftung der Balken | **8/9/10** | `const maxChars=14` (in `SvgHBar`, dieselbe Zeile trägt `bh=18`, `gap=3`) | 17 |

**Vorschlag — dieselbe Dreistufigkeit wie in Stufe 4–7/8–11:**

1. **Alles unter 10 px zuerst.** Das sind a–e (fünf Anker, alle 9 px) plus
   die SVG-Beschriftungen. → `UI.fMeta` (12). **Bei den SVG-Texten geht das
   NICHT über `UI.fMeta`**: dort ist `fontSize` ein SVG-Attribut in
   `viewBox`-Einheiten, 12 dort ist nicht 12 px auf dem Schirm. Der richtige
   Griff ist, dem `<svg>` eine feste `font-size` in **CSS-Pixeln** zu geben
   (`style={{fontSize:12}}` am `svg` und `fontSize` an den `<text>` entfernen)
   — dann skaliert die Schrift **nicht** mehr mit der Kartenbreite. Das
   ändert das Aussehen aller 15 Diagramme und gehört **allein** gemacht, mit
   Bildvergleich.
2. **Die 10er**, ansichtsweise. Schwerpunkt: Chef-Dashboard (15 Stellen im
   Quelltext), Abwesenheiten (35), Fahrzeuge (40), Admin (21).
3. **Die 11er zuletzt** — das ist die Masse (Admin 48, Fahrzeuge 44,
   Büro-Portal 22, Abwesenheiten 21) und die einzige Stufe, die Layout in der
   Breite bewegt.

**Risiko.** Stufe 1 ist eng begrenzt und je Anker gegenmessbar — **außer bei
f**, das ist ein eigener Umbau. Stufe 3 gehört **nach** D1 und D5.
**Gegenmessung:** dieselbe Sonde, Spalte „Schrift < 12 px" je Ansicht und
Breite, plus `python scripts/b3_12_15_quelltext.py` für die Quelltextzahl je
Komponente. **Beide müssen fallen** — fällt nur die eine, ist die Stelle
verschoben und nicht behoben.

---

### D8 — Die Balkenbeschriftung der Diagramme wird bei **14 Zeichen** gekappt, und das sieht der Beschnitt-Melder nicht. *(beide Breiten)*

**Messwert.** In `SvgHBar` steht `const maxChars=14`; gerendert:

```
Gerhard Steinb…   Johannes Hinte…   Bernadette Wie…
Ferdinand Asch…   Roswitha Puchl…   Elektrowerkzeu…
Verbrauchsmate…   DR.-GSCH…         BVH Spar…
```

Drei von fünf Monteursnamen sind so **nicht unterscheidbar**, sobald zwei
Personen dieselben ersten vierzehn Zeichen tragen — bei Doppelnamen und
gleichen Vornamen ist das keine Theorie.

**Das ist die dritte Form des Beschnitts, und keiner der bisherigen Melder
kennt sie.** `BESCHNITT_ECHT_JS` unterscheidet (a) `overflow:hidden` +
`ellipsis` von (b) Kastenüberlauf bei `overflow:visible`. Hier wird der Text
**in JavaScript gekappt, bevor er ins DOM kommt** — es gibt kein
`overflow`, kein `ellipsis` und keinen Kasten, an dem man messen könnte.
Der Melder meldete für Auswertungen **0 wirklich gekürzt** — korrekt nach
seiner Vorschrift und trotzdem die falsche Antwort auf die Frage
„geht Text verloren?".

**Anker** (`grep -F`, **1×**, 17 Zeichen):

```
const maxChars=14
```

**Vorschlag.** `maxChars` an die tatsächliche Beschriftungsbreite koppeln:
`lw` (die Beschriftungsspalte) wird zwei Zeilen darunter schon aus
`longestLabel` berechnet und auf 80–140 px geklemmt. Statt bei 14 Zeichen zu
kappen, die Spalte bei **langen** Namen bis 140 px wachsen zu lassen und erst
dort zu kappen (das ist ~17–18 Zeichen bei 10 px). Zusätzlich dem `<text>`
ein `<title>` mit dem vollen Wert geben — im SVG ist das der Tooltip.
**Risiko:** gering, aber es verschiebt die Balkenanfänge; bei 390 px ist die
Karte schmal und die Balken werden kürzer. **Erst messen, dann setzen.**
**Gegenmessung:** `--nur auswertungen --dunkel`; in der Zeile
„Scheine pro Monteur" darf kein Eintrag mehr auf `…` enden, und die
Kartenhöhe darf sich nicht ändern.

---

### D9 — Drei Ansichten haben **keine einzige Überschrift** im Sinne von `<h1>/<h2>/<h3>`. *(beide Breiten)*

**Messwert.** `Zeiterfassung`, `Flotte` und `Bauprovisorien` liefern
`ueberschriften: []`. Die Ansichten **haben** eine Überschrift im Bild
(`🚧 Bauprovisorien`, `📖 Fahrtenbuch`), sie steht nur in einem `div`. Die
anderen zehn Ansichten tragen jeweils genau eine `h2`.

**Das ist kein Befund nach den sieben Regeln** — es steht hier, weil es
während der Messung aufgefallen ist und weil es der Grund war, warum der
erste Nachweis für Zeiterfassung und Flotte fehlschlug (§0). Für eine
Vorlesehilfe ist eine Seite ohne Überschrift eine Seite ohne Gliederung.

**Vorschlag.** Keine Änderung in diesem Durchgang vorschlagen — das ist eine
Frage an die Gestaltung, nicht an die Geometrie. **Aufnehmen und Sebastian
vorlegen.**

---

### D10 — Was gemessen wurde und in Ordnung ist (mit dem Köder, der es belegt)

Diese Punkte sind **keine** Befunde, und sie sind es nachweislich, nicht
mangels Suche:

| Regel | Ergebnis | der Köder, der angeschlagen hat |
|---|---|---|
| Tippziel < 44 px bei **390 px** | **0 in zwölf von dreizehn Ansichten** (Ausnahme Flotte, D6) | K2: Knopf 30×20 px mit `!important` gegen die Hausregel, in jedem Lauf genau 1 gefunden |
| **Spezifitäts-Fall** wie in v3.9.942 | **keiner.** Jedes zu kleine Element wurde gefragt, welche Regeln auf es passen — die Liste ist leer, die Ursache ist ein **Inline-Stil** | `WER_GEWINNT_JS` fragt `e.matches(selektor)` je Regel, rechnet (a,b,c) aus und prüft `matchMedia` — es ist also nicht „nichts gefunden", sondern „nichts passt" |
| Verdeckung durch die Fußleiste | **0** verdeckte Bedienelemente in **allen dreizehn** Ansichten bei 390 px, am **Ende** jedes Rollers gemessen | K8: Knopf `position:fixed` über der Leiste wurde in jedem 390er-Lauf gemeldet; bei 1440 px meldet die Sonde ausdrücklich „ENTFAELLT" |
| Querrollen nach dem **Wortlaut** | in allen 26 Läufen „rollt nicht" — und das sagt **nichts**, weil `body{overflow-x:hidden}` diesen Vergleich nie rot werden lässt | K5: 3000 px breites Kind, als Rechteck gemeldet, abschneidender Vorfahr benannt. Der **eine echte** Roller steht unter D5 |
| **Beschnitt-Einordnung** | in zwölf von dreizehn Ansichten **0** wirklich gekürzte Stellen im Inhalt; die fünf Kürzungen sind **alle** die Fußleiste (D1) | K9, **zwei** Baits, „falsch eingeordnet: 0" in allen Läufen |
| Tabellen breiter als der Schirm | **0 Tabellen** in allen dreizehn Ansichten bei 390 px — und das ist ein Messwert, kein blinder Fleck | K7: eine 3000 px breite Tabelle wurde in jedem Lauf gemeldet. Ohne ihn wäre „keine Tabelle zu breit" bei 390 px wertlos, weil es dort gar keine gibt |
| **Feste dunkle Farben** im Hellmodus | **0 feste dunkle Farben im Bild** in **allen 26 Hellmodus-Läufen**, oben **und** nach dem Rollen an jedes Rollerende. 1–3 dunkle Flächen ab 8000 px², **0 davon tragend** (Schwelle 25 % Schirmanteil) | K12: derselbe Lauf im **Dunkelmodus** meldet 7–19 tragende dunkle Flächen, Hülle `rgb(15, 17, 23)`. Ohne ihn wäre „im Hellmodus nichts dunkel" die Aussage eines Melders, der keine Farbe sieht |
| Sync-Knopf im Kopf | derselbe Kastenüberlauf wie in Stufe 4–7/8–11, **es geht nichts verloren** | K9, Bait (b) |
| Bestandsschutz | Mitarbeiter 5/5, Fahrzeuge 8/8, Abwesenheiten 10/10 (nach Gleichsetzung) | K15: der Zähler findet das Wort `Kalibrierungsintervallpruefung` **nicht** — er zählt, was er behauptet |
| Seitenfehler | **0** in allen 52 Läufen | – |

**Zur Flächenfarbe ausdrücklich:** In keiner der dreizehn Ansichten gibt es
eine fest eingetragene dunkle Fläche im Bild, **auch nicht unter der
25-%-Schwelle**. Die Zeile „feste dunkle Farben im Bild: 0" steht in allen 26
Hellmodus-Läufen, oben und gerollt. Das ist der Fall, in dem ich einen Fund
unter der Schwelle melden müsste — es gibt keinen.

---

## 4. Ehemalige nur mit Beitrag *(Sonderauftrag zu Stufe 14)*

### 4.0 Die harte Grenze, vorab

`_maIstEhemalig` und `_maWaehlbar` sind in diesem Bericht **gelesen und
benutzt, nicht angefasst**. Kein Vorschlag unten sieht eine Änderung an ihnen
vor, und kein Vorschlag dreht die in v3.9.874 festgehaltene Entscheidung um
(„FILTER- und REPORT-Listen benutzen das bewusst NICHT"). `tests/
test_ausgetretene_live_v931.py::test_6` pinnt beide Rümpfe bytegenau; die
Vorschläge unten lassen diesen Riegel unberührt.

### 4.1 IST-Stand — welche Auswertungen und Diagramme es gibt, und woher ihre Mitarbeiterliste kommt

**`AuswertungView` führt 15 Diagramme in 6 Bereichen.** Alle 15 wurden bei
beiden Breiten gerendert und ihre SVG-Zeilen ausgelesen (K16 belegt, dass
die Sonde dort überhaupt Namen sehen **kann**).

**Zwei der 15 sind pro Mitarbeiter, und beide nehmen die Liste ungefiltert:**

| Diagramm | Datenquelle | Filter auf Ausgetretene? | Filter auf Beitrag? |
|---|---|---|---|
| `Scheine pro Monteur` (`asMont`, hbar) | `monteure.map(m => ({l:m.n, v:arbeitsscheine.filter(a=>a.monteur===m.id).length}))` | **nein** | **nein** |
| `Abwesenheit pro Person` (`absPers` → `absPerName`, hbar) | `monteure.map(m => {…zählt Schlüssel in `abs`…})` | **nein** | **nein** |

Die übrigen 13 sind nach **Kategorie** aufgeschlüsselt (Status, Art, Gewerk,
Fahrzeug, Wochentag) und gehen niemanden an.

### 4.2 Erscheinen Ausgetretene heute mit Null? **Ja — gemessen, beide Breiten.**

Die Saat setzt fünf Monteure: **M1–M3 aktiv**, **M4 ausgetreten MIT Beitrag**
(2 Scheine, 1 Abwesenheit), **M5 ausgetreten OHNE jeden Beitrag**.
K14 belegt in jedem Lauf, dass `_maIstEhemalig` M4 und M5 als ehemalig
erkennt und M1–M3 nicht.

Ausgelesen aus dem gerenderten SVG:

**`Scheine pro Monteur`**

| Balken | Wert | Status |
|---|---|---|
| Gerhard Steinb… | 2 | aktiv |
| Johannes Hinte… | 2 | aktiv |
| Bernadette Wie… | 2 | aktiv |
| Ferdinand Asch… | **2** | **ausgetreten, MIT Beitrag** |
| **Roswitha Puchl…** | **0** | **ausgetreten, OHNE Beitrag ← Rauschen** |

**`Abwesenheit pro Person`**

| Balken | Wert | Status |
|---|---|---|
| Gerhard Steinb… | 3 | aktiv |
| Johannes Hinte… | 1 | aktiv |
| **Bernadette Wie…** | **0** | **AKTIV, ohne Beitrag ← muss BLEIBEN** |
| Ferdinand Asch… | **1** | **ausgetreten, MIT Beitrag ← muss BLEIBEN** |
| **Roswitha Puchl…** | **0** | **ausgetreten, OHNE Beitrag ← Rauschen** |

**Die Nullzeile ist keine leere Zeile.** `SvgHBar` zeichnet für `v=0` einen
Balkenstummel `Math.max(2, 0)` = 2 px, die Beschriftung und die Ziffer `0` —
eine volle Zeile von 18 px Höhe plus 3 px Abstand, genau so hoch wie jede
andere. Bei elf Mitarbeitern (Grundstand) und zwei Ausgetretenen ohne Beitrag
sind das **42 px Diagrammhöhe für nichts**, in **zwei** Diagrammen.

**Der Unterschied, auf den es ankommt, ist im Messwert sichtbar:** Bernadette
ist **aktiv** und hat **0** — sie muss bleiben, denn „diese Woche keine
Abwesenheit" ist eine Aussage über eine Person, die da ist. Ferdinand ist
**ausgetreten** und hat **1** — er muss bleiben, denn das ist Historie.
Nur Roswitha ist **ausgetreten UND ohne Beitrag** — und nur dort ist die
Zeile Rauschen. **Ohne M4 und ohne die aktive Bernadette mit 0 wäre dieser
Satz eine Behauptung; mit ihnen ist er ein Messwert.**

### 4.3 Was die drei Nachbarstellen **schon** tun — und warum sie nicht dasselbe tun

| Stelle | Vorschrift | Wirkung |
|---|---|---|
| `MitarbeiterView` | `showEhem ? monteure : monteure.filter(m=>!_maIstEhemalig(m,_hkMV))`, umschaltbar über `Nur Aktive` | **gemessen:** `Mitarbeiter (3)`, M4 und M5 fehlen |
| `AbsView` Kontingent | `_kontNames = monteure.filter(m=>!_maIstEhemalig(m,_hkAK)).map(m=>m.n)` (v3.9.931) | **gemessen:** drei Namen in der Kompaktliste, M4 und M5 fehlen |
| `ChefDashboard` Kapazität | `_kapMont = monteure.filter(m => !String(m.austritt||'').trim() && !_kapNonField(m))` | **gemessen:** `Monteure heute 0/3` — M4 und M5 fehlen |
| **`AuswertungView`** | **keine** | **M4 und M5 stehen beide da** |

**Ein Nebenbefund, der hierher gehört und den ich nicht vorschlage zu
ändern:** `ChefDashboard` benutzt **nicht** `_maIstEhemalig`, sondern eine
eigene Prüfung „`austritt` ist nicht leer". Die beiden sind **nicht
gleichbedeutend**: wer am 31.12. austritt, ist für `_maIstEhemalig` heute
noch da (`austritt < heute` ist falsch) und für `_kapMont` schon weg. Das ist
eine **dritte Datumslogik** in derselben Datei. Gemessen ist das hier nicht
(die Saat trägt nur Austrittsdaten in der Vergangenheit) — es steht in §6.

### 4.4 Der Vorschlag

**Zweck:** In den **Diagrammen** erscheint ein Ausgetretener nur noch, wenn er
im ausgewerteten Zeitraum einen Beitrag hat. **Auswahllisten, Filter und
Reportlisten bleiben unberührt** — die v3.9.874-Entscheidung wird nicht
umgedreht.

**Die Abgrenzung in einem Satz, damit sie nicht verrutscht:**
`AuswertungView` hat **keine Auswahlliste über Mitarbeiter**. Gemessen:
„Auswahlfelder mit M5: **0 von 0**" — in dieser Ansicht gibt es überhaupt
kein `<select>`. Die `monteure`-Liste dort speist **ausschließlich zwei
Balkendiagramme**. Wer in dieser Ansicht filtert, filtert also keine Auswahl
weg, sondern eine Zeile in einem Bild. Das ist genau der Fall, den
v3.9.874 und v3.9.931 **nicht** ausgenommen haben.

**Ein Prädikat, an EINER Stelle, ohne neue Datumslogik.** Vor den beiden
`useMemo` in `AuswertungView`:

```
/* v3.9.9xx EINE NULLZEILE FUER JEMANDEN, DER NICHT MEHR DA IST, IST RAUSCHEN.
   Nur DIAGRAMME - Auswahl-, Filter- und Reportlisten bleiben vollstaendig
   (v3.9.874/v3.9.931). Ein AKTIVER mit 0 bleibt stehen: "diese Woche nichts"
   ist eine Aussage ueber jemanden, der da ist. Ein AUSGETRETENER mit Beitrag
   bleibt stehen: das ist Historie. Praedikat _maIstEhemalig unveraendert. */
const _awMitBeitrag=(liste,wert)=>(liste||[]).filter(x=>
  !_maIstEhemalig((monteure||[]).find(m=>m.n===x.l))||(+x.v)>0);
```

und dann `data: _awMitBeitrag(asMont)` bzw. `data: _awMitBeitrag(absPerName)`.

*Anker 1* — die Datenquelle von `Scheine pro Monteur` (`grep -F`, **1×**,
103 Zeichen):

```
const asMont=_react.useMemo.call(void 0, ()=>monteure.map(m=>({l:m.n,v:arbeitsscheine.filter(a=>a.monte
```

*Anker 2* — die Datenquelle von `Abwesenheit pro Person` (`grep -F`, **1×**,
107 Zeichen):

```
const absPerName=_react.useMemo.call(void 0, ()=>monteure.map(m=>{let cnt=0;const idPrefix=(m.id||"")+"_";c
```

*Anker 3* — der Diagramm-Eintrag `asMont` (`grep -F`, **1×**, 103 Zeichen):

```
{key:"asMont",title:"Scheine pro Monteur",data:asMont,def:"hbar",color:"#f97316"},\r\n    {key:"prjStatus
```

*Anker 4* — der Diagramm-Eintrag `absPers` (`grep -F`, **1×**, 104 Zeichen):

```
{key:"absPers",title:"Abwesenheit pro Person",data:absPerName,def:"hbar",color:"#3b82f6"},\r\n    {key:"wz
```

**Die sauberere Stelle ist Anker 1 und 2, nicht 3 und 4.** Wer in der
`charts`-Aufzählung filtert, filtert nur das, was gerade gezeichnet wird; der
**Excel-Export** (`📥 Alle als Excel`) liest dieselbe `charts`-Liste und würde
dann mitgefiltert — was richtig ist. Wer dagegen in `asMont`/`absPerName`
filtert, hat die Nullzeile an der Quelle weg und beide Wege stimmen
automatisch überein. **Empfehlung: Anker 1 und 2.**

**Was der Vorschlag ausdrücklich NICHT tut:**
* Er ändert **kein Zeichen** an `_maIstEhemalig` oder `_maWaehlbar`.
* Er baut **keine zweite Datumslogik** — das Prädikat wird benutzt, nicht
  nachgebaut.
* Er fasst **keine Auswahlliste** an. `AuswertungView` hat keine.
* Er löscht **nichts** und schreibt **nichts** in die Datenbank.
* Er lässt `ChefDashboard`, `AbsView` und `MitarbeiterView` unberührt.

**Der Widerspruch, den ich nicht selbst auflösen kann, und der Sebastian
vorgelegt gehört.** Der Nachtrag in `GRUNDSTAND_UI_v3.9.930.md` nennt
unter „Was sich ausdrücklich NICHT ändern darf" die Zeile:

> Die Filter-, Report- und Kalenderlisten führen ihn weiter
> (Arbeitsschein-Filter, Mängel-Filter, Stundenzettel, **Auswertung**,
> Abwesenheits-Kalender).

Dort steht das Wort **Auswertung**. Der Riegel
`tests/test_ausgetretene_live_v931.py` prüft diese Stelle **nicht** (er prüft
Team-Block, Kontingent, Historie im Schein/Zeiteintrag, AbsView-Kalenderliste
und die bestehende Zuweisung — `Auswertung` kommt im Riegel nicht vor; das
ist gemessen: `grep -i auswert` auf die Datei ergibt **0 Treffer**).
Der Satz im Grundstand ist damit eine **Absicht ohne Riegel**, und mein
Vorschlag berührt sie: er lässt einen Ausgetretenen **mit** Beitrag stehen
(Historie bleibt) und nimmt nur den **ohne** Beitrag heraus. Ob das im Sinne
des Satzes ist, entscheidet Sebastian — **ich schlage es vor und setze es
nicht um.** Wird es gemacht, gehört der Satz im Grundstand nachgezogen,
sonst schlägt der Bestandsschutz später fälschlich an.

**Risiko.** Gering und begrenzt: zwei `useMemo`, kein neuer Zustand, keine
neue Datumslogik. Die Abhängigkeitslisten müssen `monteure` schon führen —
tun sie (`[monteure,arbeitsscheine]` und `[monteure,abs]`).
**Die eine Falle:** `_awMitBeitrag` löst über den **Namen** auf (`m.n===x.l`),
weil `asMont`/`absPerName` nur `{l,v}` führen. Bei zwei Mitarbeitern mit
identischem Namen greift das daneben. Sauberer ist, die `id` in den
Datensatz mitzunehmen (`{l:m.n, v:…, id:m.id}`) und darüber aufzulösen —
das ist eine Zeile mehr und **die Fassung, die ich empfehle**.

**Gegenmessung** (`python scripts/b3_stufen_12_15_messen.py --nur
auswertungen --dunkel`, die Sonde misst diese Felder heute schon):

| heute | nach der Änderung |
|---|---|
| `Scheine pro Monteur`: 5 Balken, `Roswitha Puchl… 0` | **4 Balken**, `Roswitha Puchl…` **fehlt**, `Ferdinand Asch… 2` **steht** |
| `Abwesenheit pro Person`: 5 Balken, `Bernadette Wie… 0`, `Roswitha Puchl… 0` | **4 Balken**, `Bernadette Wie… 0` **steht** (aktiv!), `Ferdinand Asch… 1` **steht**, `Roswitha Puchl…` **fehlt** |
| K14 `{M1:F,M2:F,M3:F,M4:T,M5:T}` | **unverändert** — ändert sich das, ist das Prädikat angefasst worden |
| K16 `ANGESCHLAGEN` | **unverändert** — sonst hat die Messung aufgehört zu messen |
| `pytest tests/test_ausgetretene_live_v931.py` grün | **grün**, alle 8 Fälle |
| `pytest tests/test_ma_waehlbar_v874.py` grün | **grün** |

Die vorletzte Zeile ist die wichtigste: **Riegel 3 (Historie) und Riegel 4
(bestehende Zuweisung) sind die, die ein zu scharfer Filter reißt** — und
genau sie sind die, die der Riegel selbst als „die wichtigeren" bezeichnet.

### 4.5 Zwei weitere Stellen derselben Familie, gemessen — **kein Vorschlag, sondern eine Frage**

**E1 · `StundenzettelView`, das Auswahlfeld „Monatszettel hochladen".**
Gemessen: **2 von 6** Auswahlfeldern in der Monatsabrechnung enthalten M5
(ausgetreten, ohne Beitrag). Eines davon ist der **Filter** `Alle
Mitarbeiter` — das ist die dokumentierte Ausnahme und richtig so. Das andere
ist das Feld **`Mitarbeiter` im Block `📤 Monatszettel hochladen`** mit dem
Platzhalter `— Mitarbeiter wählen —`. Das ist **keine Filterliste**, sondern
die Zuordnung eines hochgeladenen Zettels zu einer Person — also derselbe
Fall wie die 18 Stellen aus v3.9.874, und diese Stelle ist dort **nicht**
dabei.

Anker (`grep -F`, **1×**, 55 Zeichen):

```
const allMA=[...(users||[]).filter(u=>u.active!==false)
```

**Warum ich hier keinen fertigen Vorschlag mache:** `allMA` mischt `users`
und `monteure`. `_maWaehlbar` prüft `m.austritt` — und **`INIT_USERS` führt
kein Feld `austritt`** (gemessen: die acht eingebauten Zeilen tragen
`id, username, name, email, role, active, monteurId, lastLogin, created,
locked, permsOverride`). Ein `_maWaehlbar(allMA, selMA)` würde den
`users`-Teil also **unverändert durchlassen** und nur den `monteure`-Teil
filtern — je nachdem, wie die echte `users`-Tabelle aussieht, ist das die
halbe Lösung oder die ganze. **Das ist nicht gemessen** (die `users` kommen
im Echtbetrieb vom Server, hier stehen die eingebauten). Erst messen, dann
vorschlagen.

**E2 · `AbsView`, die Auswahl-Pille zeigt einem Ausgetretenen einen
Resturlaub.** Gemessen bei 390 px und 1440 px: die Pillenreihe führt **alle
fünf** Namen, und unter jedem steht `193h · 0K` (390 px) bzw.
`193h Rest · 0K` (1440 px) — **auch unter Ferdinand Aschenbrenner und
Roswitha Puchleitner**, beide ausgetreten.

Der **Name** gehört dorthin: die Pille ist die Auswahl, über die man den
Kalender und die Krankenstände einer Person ansieht, und v3.9.931 sagt
ausdrücklich, dass diese Liste vollständig bleiben muss („wer die alten
Krankenstände eines Ausgetretenen sucht, muss ihn dort weiter finden").
**Der Resturlaub gehört nicht dorthin** — und das sagt derselbe Kommentar
mit denselben Worten: *„Ein Anspruch fuer jemanden, der nicht mehr da ist,
ist keine Historie."* v3.9.931 hat die Kompaktliste, die Detailtabelle und
das Excel-Blatt versorgt; **die Pille nicht.**

Anker (`grep -F`, **1×**, 54 Zeichen):

```
(isAdmin?names:names.filter(m=>m===myMonteurName)).map
```

Der Resturlaub steht in derselben Zeile:
`display:"block",fontSize:9,opacity:.85,fontFamily:mono` (**1×**, 54 Zeichen)
— und das ist zugleich Anker **c** aus D7 (9 px).

**Vorschlag.** Den Namen lassen, das Abzeichen ersetzen: bei
`_maIstEhemalig(<worker>)` statt `193h Rest · 0K` ein neutrales
`ausgetreten` zeigen. Die Zeile bleibt gleich hoch, die Auswahl bleibt
vollständig, und der Anspruch verschwindet dort, wo er keiner mehr ist.
**Risiko:** gering, aber die Pille löst heute über den **Namen** auf
(`names` ist `monteure.map(m=>m.n)`) — für `_maIstEhemalig` braucht es das
Objekt. `monteure.find(x=>x.n===m)` ist derselbe Namensabgleich, den
`resturlaub(m)` schon macht, also keine neue Klasse von Risiko.
**Gegenmessung:** `--nur abwesend --dunkel`; im Melder „Ausgetretene im Bild"
müssen M4 und M5 **weiterhin `True`** sein (der Name bleibt!), und in der
Umgebung ihres Namens darf `Rest` bzw. `h · ` **nicht mehr** stehen.
Zusätzlich `pytest tests/test_ausgetretene_live_v931.py` — Riegel 3 verlangt
genau, dass diese Liste den Ausgetretenen weiterführt.

---

## 5. Leere Grundgesamtheit — was in diesem Aufbau NICHTS zu messen hatte

REST und Auth sind abgeklemmt. Diese Zustände sind **gemessen, aber leer** —
das ist **kein Bestehen**:

| Zustand | was fehlt | Folge |
|---|---|---|
| **Flotte** | GPS-Positionen und Fahrten (Server) | Band `🛰️ Noch keine Tracker zugeordnet`, Fahrtenbuch `Keine Fahrten im gewählten Zeitraum`. **Die Fahrzeugliste auf der Karte, die Marker, die Track-Darstellung, die drei Fahrtenbuch-Reiter mit Inhalt und die IMEI-Zuordnung sind NICHT gemessen.** Die Zahlen für Flotte in §1 sind die Zahlen einer leeren Karte |
| **Gefahrenstoffe** | `gefahrstoff_files` (Server) | `☣️ Leerer Ordner`. **Ordnerbaum, Suche, PDF-Viewer, Upload und die Lösch-Knöpfe sind NICHT gemessen.** 2 Knöpfe im Inhalt sind der Leerzustand |
| **Bauprovisorien** | `/api/bauprovisorien` (Server) | `Noch keine Bauprovisorien erfasst`. **Die Liste, die Jahresmieten, das Kasten-Formular und der QR-Weg sind NICHT gemessen** |
| **Büro-Portal / Stempelzeiten, Zulagen, Abwesenheiten, Tank** | `time_entries`, `bautagebuch`, `forms`, `defects` (Server) | alle KPI stehen auf 0. Der Reiter `📁 Projekte` hat Inhalt aus der Saat; **die vier anderen Reiter sind NICHT gemessen** |
| **Monatsabrechnung / Zettel** | `stundenzettel` ist gesät (2 Zeilen), `pdf_data` nicht | `— Kein Zettel` im Monatsumschalter. **Die Freigabe, der PDF-Viewer und der FinkZeit-Abgleich sind NICHT gemessen** |
| **Admin / Aktivität, Statistiken, Händler, Juprowa, System** | `activity_log`, `supplier_configs`, Juprowa-Konfiguration (Server) | **fünf von sechs Unterreitern sind NICHT gemessen.** Der Reiter `👤 Benutzer` **ist** gemessen — seine acht Zeilen kommen aus `INIT_USERS` und nicht vom Server |

---

## 6. WAS NICHT GEMESSEN WURDE — das sind keine bestandenen Fälle

1. **Die Unterreiter.** Gemessen ist je Ansicht der **Startzustand**. Nicht
   gemessen sind: **Chef** 4 von 5 (`🏗️ Projekte`, `📋 Arbeit`,
   `👥 Personal`, `📦 Ressourcen`), **Abwesenheiten** 3 von 4 (`📨 Anträge`,
   `📊 Übersicht`, `🗓️ Team-Timeline`), **Admin** 5 von 6, **Büro-Portal** 4
   von 5, **Flotte** 2 von 3 Fahrtenbuch-Reitern, **Fahrzeuge** die
   Kachelansicht und die Fahrzeug-Detailseite. Das sind **19 Unterzustände**.
   Eine Ansicht, von der nur der erste Reiter gemessen ist, ist zu einem
   Teil gemessen — die Zahlen in §1 gelten für diesen Teil.
2. **Das eine zu kleine Bedienelement in Flotte bei 390 px** (D6) ist
   **gezählt, aber nicht benannt**. Die `proben`-Liste im JSON stammt aus dem
   1440er-Lauf.
3. **Die Rollen-Gatter.** Gefahren wurde `admin` + `rolle=Geschäftsführer`.
   **Chef** hängt an `role==="admin" || Geschäftsführer`, **Flotte** an
   `admin/projektleiter/buero`, **Einstellungen** an
   `!(monteur||helfer)`, **Admin** an `admin_panel`, **Gefahrenstoffe**
   lesen alle / bearbeiten Admin+Pinger+Schmid, **Monatsabrechnung** an
   `hasPerm(stunden)`. Ein Monteur sieht sechs dieser dreizehn Ansichten gar
   nicht. **Alle Befunde oben gelten für die Admin-Sicht.**
4. **`users` im Echtbetrieb.** Der Admin-Reiter und die
   Monatsabrechnungs-Auswahlfelder rechnen mit `INIT_USERS` (8 eingebaute
   Zeilen ohne `austritt`). Ob die echte `users`-Tabelle ein `austritt`
   führt, ist **nicht gemessen** — und davon hängt ab, ob der Vorschlag E1
   ganz oder halb wirkt.
5. **Die dritte Datumslogik.** `ChefDashboard` prüft
   `!String(m.austritt||'').trim()`, `_maIstEhemalig` prüft
   `austritt < heute`. Für einen Austritt in der **Zukunft** widersprechen
   sich die beiden. Die Saat trägt nur vergangene Austritte — **der Fall ist
   nicht gemessen**, nur im Quelltext gelesen.
6. **1440 px mit grobem Zeiger.** Die 9 bis 99 Tippziele unter 44 px bei
   1440 px sind unter der Hausregel **kein** Bruch. Auf einem Touch-Notebook
   oder Tablet im Querformat bei 1440 px trifft `pointer: coarse` zu und
   `max-width: 768px` nicht. Derselbe offene Punkt wie in Stufe 4–7 und
   8–11 — **hier wäre er in den Auswertungen der ernsteste**: 99 Elemente,
   darunter die 78 Diagramm-Umschalter.
7. **Ob 12 px die Layouts halten.** Jeder Vorschlag in D7 ist ein Vorschlag
   **mit Gegenmessung**, keine Behauptung. Besonders D7/f: die SVG-Schrift
   von `viewBox`-Einheiten auf CSS-Pixel umzustellen ändert das Aussehen
   aller 15 Diagramme, und wie viel Beschriftung dann noch in eine Karte
   passt, ist **nicht gemessen**.
8. **Farbkontrast von TEXT.** Gemessen wurde nur die **Fläche** (Helligkeit
   der Hintergrundfarbe, gegen den Untergrund gemischt, ab 8000 px²,
   geurteilt ab 25 % Schirmanteil). Ob die 8-px- und 9-px-Schriften in den
   Diagrammen ihren Kontrast halten, sagt diese Messung **nicht** — und bei
   8 px auf farbigem Balken ist das die Frage, die ich als Nächstes stellen
   würde.
9. **Die Tastaturbedienung** und die Reihenfolge des Fokus — in keiner der
   dreizehn Ansichten.
10. **Der Excel-/PDF-Export.** `📥 Alle als Excel`, `🖨️ PDF`,
    `🖨️ Monatsübersicht drucken`, `📊 Excel` (Abwesenheiten) und die
    Bauwochenberichte wurden **nicht ausgelöst**. Der Vorschlag in §4.4
    betrifft den Excel-Export der Auswertungen mittelbar (er liest dieselbe
    `charts`-Liste) — **gemessen ist das nicht**.
11. **Das „letzte bedienbare Element".** Die Sonde nimmt es weiterhin in
    **DOM-Reihenfolge**, nicht als das visuell unterste. Die
    Verdeckungsaussage hängt nicht daran (sie prüft **alle** sichtbaren
    Bedienelemente gegen die Leistenzone), aber die Zeile im JSON ist so
    nicht zu gebrauchen. Unverändert aus Stufe 4–7.

---

## 7. Reihenfolge, die ich vorschlagen würde

1. **D2, D3, D4** — `title` / `aria-label` an **zehn** Stellen (4 Reiter,
   2 Umschalter, 6 Pfeile). Kein Pixel bewegt sich, sofort gegenmessbar.
   **D4 bitte als Dateisuche**, nicht als drei Einzelgriffe — das Muster ist
   jetzt zum dritten Mal gefunden worden.
2. **D1, Weg 1** (`title` an der Fußleisten-Beschriftung). Kostet nichts und
   nimmt dem Beschnitt die Schärfe, bis Weg 2 entschieden ist.
3. **§4.4, der Diagramm-Filter** — zwei `useMemo` in `AuswertungView`.
   **Vorher** die Frage aus §4.4 („der Widerspruch") beantworten lassen.
4. **§4.5 E2** — der Resturlaub in der Abwesenheits-Pille. Klein, örtlich,
   und v3.9.931 hat den Satz dazu schon geschrieben.
5. **D5** — die Admin-Reiterzeile umbrechen statt rollen.
6. **D7 Stufe 1** ohne f — die fünf 9-px-Anker.
7. **D6** — erst das Element benennen, dann entscheiden.
8. **D1, Weg 2 oder 3** — Textentscheidung, Sebastian vorlegen.
9. **D8 und D7/f zusammen** — beides fasst `SvgHBar`/die SVG-Schrift an;
   getrennt gemacht hat ein neuer Bildfehler zwei Ursachen.
10. **D7 Stufe 2 und 3** — die 10er und die 11er, ansichtsweise,
    **nach** D1 und D5.
11. **§4.5 E1** — erst die echte `users`-Tabelle messen.
12. **D9** — aufnehmen, nicht anfassen.

**Vor Punkt 1:** den Nachtrag aus §2.4 (zehn Ansichten) in
`GRUNDSTAND_UI_v3.9.930.md` eintragen **und als noch nicht abgenommen
kennzeichnen**. Ohne ihn hat der Umbau in zehn von dreizehn Ansichten keine
Abnahmegrundlage.

---

### Läufe und Rohdaten

```
set EPK_INDEX=_mess_stand_944.html
set EPK_BREITEN=390,1440
python scripts/b3_stufen_12_15_messen.py --json b3_12_15.json      (52 Laeufe, RC 0)
python scripts/b3_stufen_12_15_messen.py --nur auswertungen --dunkel
python scripts/b3_stufen_12_15_messen.py --erkunden                (Inventar)
python scripts/b3_12_15_quelltext.py                               (RC 0)
python scripts/b3_fussleiste_beschnitt.py                          (RC 0)
python scripts/anker_schneiden.py --suche "<anker>"
```

Alle Läufe endeten mit `Alle Koeder haben angeschlagen - die Zahlen oben sind
Messwerte.` und **Rückgabewert 0**, getrennt von der Ausgabe gelesen.
Bildschirmfotos: `screenshots/b3_<ansicht>_<breite>.png` (Dunkelmodus) und
`screenshots/b3_<ansicht>_<breite>_hell.png` (Hellmodus), 52 Stück.
md5 der gemessenen Datei bei Beginn **und** Ende:
**`cadd5f6c4ca871e5f256930e32d61283`**.
