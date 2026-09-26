# Schlussmessung v3.9.954 — am gerenderten Schirm gemessen, 26.09.2026

**Auftrag.** Bestätigen, dass die zwanzig heute ausgelieferten Commits
(v3.9.935 … v3.9.954) nichts kaputt gemacht haben — und wo doch, es benennen.
Gemessen wird **nicht** im Quelltext, sondern an der **gerenderten** Seite.
Genau die vier Fehlerklassen, die der Abschlussbericht unter „Was ein
Quelltext-Prüfstand grundsätzlich nicht fangen kann" aufzählt, sind hier der
Gegenstand.

`index.html` wurde von dieser Messung **nicht angefasst** — kein Byte.

---

## 0. Welche Datei wurde gemessen, und mit welchem md5

Mitten in dieser Messung hat ein anderer Agent begonnen, `index.html` zu
schreiben (v3.9.955, dann v3.9.956). Das ist in der Tafel unten je Lauf
ausgewiesen. **Ein Wert ohne bekannten Messgegenstand ist keine Messung.**

| Lauf | Werkzeug | gemessene Datei | md5 | Aufnahmen | Rückgabe |
|---|---|---|---|---|---|
| Grundstand, **1. Versuch** | `grundstand_erheben.py` | `index.html` | **wanderte** 359be144 → f5b6b8b9 um 21:31:28 | 17 von 44 im Protokoll | **abgebrochen, verworfen** |
| Grundstand, **gültig** | `grundstand_erheben.py` | `_mess_stand_954.html` | `359be144407d9b033949cbeccd866892` | **44** | 0 |
| Regeln, Stufe 4–7 | `b3_vier_ansichten_messen.py` | `_mess_stand_954.html` | `359be144…` | 12 (4 Ansichten × 375/390/1440) | 0 |
| Regeln, Stufe 8–11 | `b3_stufen_8_11_messen.py` | `_mess_stand_954.html` | `359be144…` | 30 (15 dunkel + 15 hell) | 0 |
| Regeln, Stufe 12–15 | `b3_stufen_12_15_messen.py --dunkel` | `_mess_stand_954.html` | `359be144…` | 39 (13 × 3 Breiten) | 0 |
| Hellmodus, alle Ansichten | `hellmodus_ansichten.py` | `_mess_stand_954.html` | `359be144…` (vor **und** nach dem Lauf) | **124** (31 Ansichten × 390/1440 hell **und** dunkel) | 0 |
| Bestandsprüfung | `bestand.py` | `index.html` | `359be144…` (vor dem ersten Schreibzugriff) | 118 Begriffe | 0 |
| Eichproben | `bestand.py --selbst` + eigene Hülle | `index.html` | `359be144…` | 3 + 3 | 0 |
| Torkette, **voll** | `torkette.py` | `index.html` | **wanderte während des Laufs** | 4 Tore | **1 (Klammerbilanz rot)** |
| Torkette, **schnell** | `torkette.py --schnell` | `index.html` | `d646cb4c…` **vor und nach** dem Lauf | 3 Tore | 0 |
| pytest einzeln | `python -m pytest tests/ -q` | `index.html` | `d646cb4c…` **vor und nach** dem Lauf | **3153 Fälle** | 0 |
| Klammerbilanz einzeln | `_bracket_check.py` | `_mess_stand_954.html` · `_mess_stand_955.html` · `index.html` | 359be144 · 24d8565d · d646cb4c | 3 | 0 · 0 · 0 |
| VBautag, Liste | eigene Hülle über B4/B8/B12 | drei Stände | 359be144 · 24d8565d · 51f140dd | 12 | **1 (nicht gemessen)** |
| VBautag, Formular offen | dieselbe Hülle, `--formular` | drei Stände | 359be144 · 24d8565d · 51f140dd | 12 | 0 |

**Alle Regel- und Grundstandsläufe liegen auf `359be144407d9b033949cbeccd866892`** —
der eingefrorenen, bytegleichen Kopie von v3.9.954. Sie sind untereinander
vergleichbar. Die Tor- und Bestandsläufe liegen auf `index.html` und tragen
ihren md5 einzeln.

**Die 22 Ansichten sind je bei drei Breiten gemessen: 375, 390 und 1440 px.**
Kein Wert unten stammt aus nur einer Breite; wo doch, steht es dabei.

---

## 1. Je Zusage: gemessen, Wert, Urteil

### Zusage 1 — Tippziele unter 44 px bei 375 und 390 px: **0**

| | |
|---|---|
| **gemessen** | 22 Ansichten × 375 px und 390 px = **44 Läufe** (plus 22 bei 1440) |
| **Wert** | **0** in 21 von 22 Ansichten, bei **beiden** mobilen Breiten. **Flotte: 1** bei 375 **und** 390 px |
| **Köder** | **K2** — ein Knopf 30×20 px mit `!important` gegen die 44-px-Hausregel: in **allen 66 Läufen** gefunden (12 + 15 + 39) |
| **Urteil** | **HÄLT.** Der eine Fall in Flotte ist der im Auftrag ausdrücklich benannte Leaflet-Zuschreibungslink — kein Befund |

Die Zahlen bei 1440 px (9 bis 99 je Ansicht) sind **kein** Befund: die
Hausregel gilt unter `@media(pointer:coarse),(max-width:768px)`, und bei
1440 px mit feinem Zeiger greift sie nicht. Sie stehen in den Rohdaten und
sind dort als „Zeiger fein" gekennzeichnet.

### Zusage 2 — Bedienelemente ohne Buchstaben, ohne `title`, ohne `aria-label`: **0**

| | |
|---|---|
| **gemessen** | 22 Ansichten × 3 Breiten = **66 Läufe**, mit **zwei** Meldern (`EMOJI_JS` „ohne Text" und `EMOJI_ZAHL_JS` „ohne BUCHSTABEN") |
| **Wert** | **0** in 21 von 22 Ansichten. **Fahrzeuge: 2** — und zwar bei **375, 390 UND 1440 px** |
| **Köder** | **K3** (zwei Knöpfe, einer nur `🔧`, einer nur `▲`) in allen 66 Läufen · **K13** (Knopf `🔩7`: alter Melder `False`, neuer `True`) in allen 39 Läufen der Stufe 12–15 |
| **Urteil** | **HÄLT NICHT.** Siehe Befund **S-1** |

### Zusage 3 — waagrechter Roller: keiner

| | |
|---|---|
| **gemessen** | 66 Läufe, und zwar **zweifach**: der Regelwortlaut (`document.scrollingElement`) **und** jeder Behälter einzeln |
| **Wert Seite** | `rollt` = **False** in **allen 66** Läufen. Das sagt für sich genommen **nichts** — `body{overflow-x:hidden}` lässt diesen Vergleich nie rot werden, und genau deshalb steht die zweite Zahl daneben |
| **Wert Behälter** | **Admin: 0** Roller bei 375, 390 und 1440 — der Umbruch aus v3.9.948 **wirkt**, D5 ist zu. Ebenso 0 in Chef, Zeiterfassung, Abwesenheiten, Monatsabrechnung, Fahrzeuge, Flotte, Mitarbeiter, Auswertungen, Büro-Portal, Einstellungen, Gefahrenstoffe, Bauprovisorien, Werkzeuge, Planung, Home, AS-Formular, AS-Liste (375/390) |
| **die Roller, die es gibt** | **nur in der Projekt-Hülle**, in allen vier Unterseiten: `div.tab-bar.pf-hauptnav` **+601 px** (375) · **+586 px** (390) · **+158 px** (1440), breitestes Kind `📄Monatsabrechnung` 113 px · dazu die obere Projekt-Reiterzeile **+31 px** (390) / **+46 px** (375) · in Berichte zusätzlich der Tabellenbehälter **+346 px** (390) · in der AS-Liste bei 1440 der Tabellenbehälter **+117 px** |
| **Köder** | **K5** — ein 3000 px breites Kind, in allen 66 Läufen als 3000-px-Rechteck gemeldet, samt abschneidendem Vorfahren (`html > body overflow-x:hidden`) |
| **Urteil** | **HÄLT für alle 18 Ansichten außerhalb der Projekt-Hülle.** Die Projekt-Reiterzeile ist die im Abschlussbericht ausdrücklich getroffene Entscheidung („bleibt rollbar", 13 Reiter). **Neu gegen den Abschlussbericht:** sie rollt **auch bei 1440 px** (+158 px). Das steht dort nicht; die 586 px sind dort nur für das Telefon genannt |

### Zusage 4 — Tabellen breiter als der Schirm bei 390 px: **0**

| | |
|---|---|
| **gemessen** | 22 Ansichten × 375/390 px |
| **Wert** | **0** in 21 von 22 Ansichten. **Projektakte / Berichte (Wochenbericht): 1** — Tabelle **720 px** gegen 390 px (und gegen 375 px) |
| **Köder** | **K7** — eine 3000 px breite Tabelle, in allen 66 Läufen gemeldet. Ohne ihn wäre „keine Tabelle zu breit" bei 390 px wertlos, weil es in 17 der 22 Ansichten dort überhaupt keine Tabelle gibt |
| **Urteil** | **HÄLT NICHT nach dem Wortlaut.** Siehe Befund **S-2** |

### Zusage 5 — verdeckte Bedienelemente hinter der Fußleiste: **0**

| | |
|---|---|
| **gemessen** | 22 Ansichten × 375/390 px, **am Ende jedes Rollers** (jeder Roller wurde ans Ende gefahren und das Ankommen belegt) |
| **Wert** | **0** in **allen 44** mobilen Läufen |
| **Köder** | **K8** — ein Knopf `position:fixed` über der Leiste, in allen 44 mobilen Läufen gemeldet; bei 1440 px meldet die Sonde ausdrücklich „entfällt", weil `.bottom-nav` in `@media(max-width:600px)` lebt |
| **Urteil** | **HÄLT** |

### Zusage 6 — wirklich gekürzter Text bei 1440 px: **0**

| | |
|---|---|
| **gemessen** | 18 Ansichten (Stufen 8–11 und 12–15) mit `BESCHNITT_ECHT_JS`, das **wirklich gekürzt** von **blossem Kastenüberlauf** trennt — über die Rechtecke des Textes, nicht über `scrollWidth` |
| **Wert 1440** | **0** in 17 von 18 Ansichten. **Arbeitsscheine-LISTE: 6** — sechs `<td>` der Spalte „Durchzuführende Arbeit", bis zu **493,6 px verloren**, `overflow:hidden` + `ellipsis` |
| **Wert 390** | **7** gekürzte Stellen, **alle** in `.bottom-nav > button > span`: `Zeiterfassung` 80/74 · `Abwesenheiten` 89/74 · `Monatsabrechnung` 112/74 · `Gefahrenstoffe` 86/74 · `Bauprovisorien` 88/74 · `Arbeitsscheine` 87/74 — plus `Monatsabrechnung` 84/73 bei **375** |
| **Köder** | **K9** — **zwei** Baits: einer kürzt wirklich (240 Zeichen in 80 px `overflow:hidden`), einer läuft nur über (`overflow:visible`). „falsch eingeordnet: 0" in allen 54 Läufen der Stufen 8–15. Ein Melder, der alles „abgeschnitten" nennt, hätte recht ohne zu messen |
| **Urteil** | **HÄLT NICHT.** Siehe Befund **S-3** (1440) und **S-4** (390) |

**Der Kastenüberlauf, der KEIN Befund ist:** in fast jedem Lauf meldet der
Melder 1 bis 4 Stellen als „nur Überlauf" — es ist der Sync-Knopf der
Kopfzeile (`Offline4` / `Offline4Server ❌`, 48/44 bzw. 85/81,
`overflow:visible`, `ellipsis: clip`). Dort geht **nichts** verloren; der Text
wird ausserhalb des Kastens gezeichnet. Das ist derselbe Fall, den
`b7_syncknopf_messen.py` schon einmal gemessen hat.

### Zusage 7 — feste dunkle Farben im Hellmodus: **0 tragende Flächen in allen 31 Ansichten**

| | |
|---|---|
| **gemessen** | **31 Ansichten** × 390 und 1440 px, `epk_theme='light'` bei **Betriebssystem auf dunkel**, je **zweimal** (oben und nach dem Rollen an jedes Rollerende), mit **zwei** Massen: Flächensuche ab 8000 px² **und** Raster-Abtastung 24×40 Punkte |
| **Wert** | **0** Ansichten mit dunklem Schirm ab 25 % · **0** Ansichten „nicht gemessen" · je Ansicht 1–3 dunkle Flächen ab 8000 px², **0 davon tragend** |
| **Köder** | derselbe Lauf mit `epk_theme='dark'`: **100,0 % Schirm dunkel** und **2 bis 7 tragende** Flächen in **jeder** der 31 Ansichten, Hülle `rgb(15, 17, 23)`. Ohne ihn wäre „im Hellmodus nichts dunkel" die Aussage eines Melders, der keine Farbe sieht |
| **zweiter Köder** | in den Stufen 8–11 zusätzlich 15 eigene Hellmodus-Läufe (375/390/1440): 1–3 dunkle Flächen, **0 tragend**, und **K12** schlug in allen an |
| **Urteil** | **HÄLT.** Der Befund aus v3.9.942 (Plan-Betrachter `#1a1a1a`, 57,5 % bei 390 px) ist **nicht zurückgekehrt** |

---

## 2. Die vier Befunde

### S-1 — Zwei Bedienelemente in **Fahrzeuge** tragen weder Buchstaben noch `title` noch `aria-label`. *(375, 390 und 1440 px)*

**Messwert.** `EMOJI_ZAHL_JS`, alle drei Breiten, identisch:

```
{"zeichen": "☰", "title": null, "aria": null, "weg": "div > div > div > button", "h": 44, "w": 44}
{"zeichen": "⊞", "title": null, "aria": null, "weg": "div > div > div > button", "h": 44, "w": 44}
```

Es ist der **Listen-/Kachelumschalter** der Fahrzeugliste. Beide sind
44×44 px groß — die Tippziel-Regel ist erfüllt, die Beschriftungs-Regel nicht.
Im selben Lauf tragen `🌙`, `🔔`, `🚪` und die beiden `☆` je einen `title`; der
Melder unterscheidet also, er ist nicht blind.

**Das ist D3 aus `B3_STUFEN_12_15.md`, und es ist offen.** Der Abschlussbericht
zählt unter v3.9.942 „sieben Symbol-Knöpfe beschriftet" und unter v3.9.946
„acht Pfeile beschriftet" — diese beiden sind in keiner der beiden Runden
dabei. Für eine Vorlesehilfe heißen sie heute „Schaltfläche".

**Nicht reparieren, ohne es zu melden:** ein `title` je Knopf
(`title: "Listenansicht"` / `"Kachelansicht"`) ist die kleinste Änderung; sie
verändert kein Pixel.

### S-2 — Der Wochenbericht ist bei 390 px eine **720-px-Tabelle**. *(375 und 390 px)*

**Messwert**, Projektakte / Berichte:

```
{"breite": 720, "scrollWidth": 720, "innerWidth": 390, "ueber": true,
 "behaelter": "div.proj-shell > div > div.proj-main > div.fade-in > div",
 "behaelter_overflowX": "auto"}
```

Bei 375 px derselbe Wert. Der Behälter ist `overflow-x: auto` und rollt
tatsächlich (+346 px bei 390, +361 bei 375) — **der Inhalt ist erreichbar**,
er passt nur nicht auf den Schirm.

**Das ist die im Abschlussbericht getroffene Entscheidung** („Der
Wochenbericht bleibt eine 720-px-Tabelle in einem 374-px-Kasten", begründet
mit der Messung aus v3.9.937). **Es ist also kein neuer Schaden — aber die
Zusage „0 Tabellen breiter als der Schirm bei 390 px" ist nach ihrem
Wortlaut falsch.** Die Zusage und der eigene Beschluss des Laufs
widersprechen sich; das gehört benannt, nicht weggerechnet.

### S-3 — In der Arbeitsschein-Liste werden bei 1440 px **sechs** Textstellen wirklich gekürzt, bis zu **493,6 px**.

**Messwert** (eine von sechs, alle in der Spalte „Durchzuführende Arbeit",
Spaltenbreite 220 px):

```
{"tag": "td", "text": "Zaehlerkasten tauschen, Hauptleitung neu ziehen, F…",
 "scroll": 722, "sicht": 220, "eigen_overflowX": "hidden",
 "textOverflow": "ellipsis", "verloren_px": 493.6}
```

Die übrigen fünf verlieren 357, 270, 249, 182 und 153 px.

**Das ist Entscheidung 5 des Abschlussberichts**, dort wörtlich: „verliert bis
zu **494 px**. Der ganze Text steht jetzt im `title`, **abgeschnitten wird
weiter**." Die Messung bestätigt beide Hälften des Satzes. **Die Zusage „0
wirklich gekürzt bei 1440 px" ist damit falsch** — sie widerspricht dem
eigenen Beschluss desselben Laufs.

### S-4 — Die Fußleisten-Beschriftung wird bei 390 px in **sechs** Reitern gekürzt. *(nur 390/375 px)*

**Messwert**, alle sechs im selben Element (`.bottom-nav > button > span`,
`overflow:hidden` + `ellipsis`, Schlitz **74 px**):

| Reiter | Textbreite | sichtbar | verloren |
|---|---|---|---|
| Monatsabrechnung | 112 | 74 | **38 px** |
| Abwesenheiten | 89 | 74 | 15 px |
| Bauprovisorien | 88 | 74 | 14 px |
| Arbeitsscheine | 87 | 74 | 13 px |
| Gefahrenstoffe | 86 | 74 | 12 px |
| Zeiterfassung | 80 | 74 | 6 px |

Bei **375 px** kürzt nur `Monatsabrechnung` (84/73).

**Das ist D1 aus `B3_STUFEN_12_15.md`, unverändert offen.** Es ist die Folge
von v3.9.943 (Fußleisten-Schrift von 10 auf 12 px gehoben) und der teuerste
Beschnitt der Messreihe, weil er in **jeder** Ansicht bei 390 px steht. Die
Zusagenliste nennt nur 1440 px, deshalb ist das kein Bruch einer Zusage —
aber es ist der Fall, der die meisten Nutzer trifft.

---

## 3. Grundstand — 44 Aufnahmen, **null** Abweichungen

`grundstand_erheben.py` gegen `_mess_stand_954.html` (md5 `359be144…`),
44 Aufnahmen in 817 s, **keine** Ansicht „NICHT ERREICHT", Rückgabewert 0.

**Das Ergebnis ist mit der eingecheckten Datei
`docs/GRUNDSTAND_UI_v3.9.954.md` byteweise identisch.** `diff -u` gibt
**0 Zeilen** aus. Das gilt nicht nur für das Mengengerüst, sondern für die
ganze Datei: Überschriften, Tabellenköpfe, Platzhalter, jede Auswahloption und
jeden Knopfnamen in allen 22 Ansichten bei beiden Breiten.

**Der Vergleich hat drei Köder** (`vergleich.py`), damit „0 Abweichungen"
etwas bedeutet:

| Köder | gesetzte Änderung | Ergebnis |
|---|---|---|
| **K1** | Knopfzahl Chef 390 von 15 auf 14 | **ANGESCHLAGEN** — „Knoepfe 15 -> 14" |
| **K2** | die ganze Zeile `Gefahrenstoffe 390` entfernt | **ANGESCHLAGEN** — „fehlt in der neuen Aufnahme" |
| **K3** | ein Wort in eine Überschrift eingefügt | **ANGESCHLAGEN** — „INHALT-WEG Werkzeuge 390 Ueberschriften: 🔧 Werkzeuge & Geräte" |

Alle drei schlagen an, und derselbe Vergleicher gibt für die echten Dateien
0 Abweichungen. **Die eingecheckte Aufnahme ist reproduzierbar.**

Die eingecheckte Datei wurde vom Lauf überschrieben und danach **bytegleich
wiederhergestellt** (md5 `19c1a2b0d4fdd3953bed4eca4f3edb85` vor und nach der
Messung). Dasselbe für `docs/befunde/HELLMODUS_ANSICHTEN.md`
(`812d9f58b436d5849d8bbf78683ffc1a`).

---

## 4. Bestandsprüfung und die **beiden** Eichfälle

| | Ergebnis |
|---|---|
| `bestand.py` | **BESTAND GRÜN — 118 Begriffe in 17 Gruppen gefunden**, Rückgabewert 0 |
| `bestand.py --selbst` | drei entfernte Begriffe machen **alle drei** rot: `'Stillgelegt'` (Werkzeuge: sechs Status) · `'bar bezahlt'` (Arbeitsscheine: elf Statuswerte) · `'Checklisten'` (Projektakte: dreizehn Unterseiten). Rückgabewert 0 |
| **leere Begriffsliste** | `BESTAND = {}` über denselben Aufrufweg: **ROT, Rückgabewert 2** — „Nichts gemessen ist kein Ergebnis." |
| **Gegenprobe dazu** | dieselbe Hülle mit der **echten** Liste: Rückgabewert **0**. Der rote Fall beweist also das Leeren und nicht, dass der Aufruf immer rot ist |
| **dritter Fall, zusätzlich** | eine **verstümmelte** Liste (1 Gruppe, 1 Begriff): ebenfalls **ROT, Rückgabewert 2** |

Der Rückgabewert wurde in jedem Fall **getrennt von der Ausgabe** gelesen,
nie hinter einer Pipe.

**Zusätzlich belegt der Bestandsschutz-Melder der Sonden** (aus der Doku
gelesen, nicht abgetippt), mit **K15** als Gegenprobe („der Zähler findet das
Wort `Kalibrierungsintervallpruefung` **nicht**", `k15_falschtreffer: False`
in allen Läufen):

* **Arbeitsscheine-Liste**: Statuskacheln **11/11** · Sortierkriterien **7/7**
  (bei 390 px in der Kopfzeile, bei 1440 im Auswahlfeld — dieselben sieben) ·
  Chips **8/8** · Suchfeld **da** · OFFA-Excel **da** · Unterreiter
  `['Liste', 'QR Scan', 'Kalender', 'Dispo']`
* **Mitarbeiter** 5/5 · **Abwesenheiten** 10/10 nach Gleichsetzung ·
  **Fahrzeuge** 6/8 wörtlich, 8/8 nach Gleichsetzung (die zwei „fehlenden"
  sind `☰`/`⊞` und der Favoritenstern — die Oberfläche *zeichnet*, wo der
  Grundstand *beschreibt*; siehe aber S-1)
* **K14 Ehemalige** schlug in allen 39 Läufen an:
  `{M1:F, M2:F, M3:F, M4:T, M5:T}`, `waehlbar=[M1,M2,M3]`, mit getragenem
  `M5=[M1,M2,M3,M5]` — der Austritts-Fix aus v3.9.950/952 **wirkt** am
  gerenderten Schirm

---

## 5. Torkette — vier Tore, jedes ein eigener Prozess

| Tor | Ergebnis | gemessene Datei |
|---|---|---|
| `node_check` | **grün** | `index.html` |
| Klammerbilanz | **ROT: `() -4 / {} 0 / [] 0`** | `index.html`, **mitten in einem fremden Schreibvorgang** |
| Versionsabgleich | **grün** | `index.html` |
| `pytest tests/` | **grün**, 283,1 s (einzeln nachgemessen: **3153 passed, 11 skipped, 8 xfailed**) | `index.html` |

**Das rote Tor ist ein Messartefakt, und das ist belegt, nicht vermutet.**
Unmittelbar danach einzeln nachgemessen:

| Datei | md5 | Klammerbilanz |
|---|---|---|
| `_mess_stand_954.html` (die zwanzig Commits) | `359be144…` | **`() -1 / {} 0 / [] 0` — grün** |
| `_mess_stand_955.html` | `24d8565d…` | **grün** |
| `index.html`, nach dem fremden Schreibvorgang | `d646cb4c…` | **grün** |

Die Basislinie ist `() -1`; der Lauf sah `() -4`, also **drei offene Klammern
mitten im Schreiben**. Genau diese Verwechslung steht im Abschlussbericht
schon einmal: „eine offene Klammer im Kommentar machte das Klammer-Tor rot,
während `node_check` grün blieb."

**Torkette danach erneut, `--schnell`:** `index.html` trug **vor und nach**
dem Lauf `d646cb4c…`, **ALLE 3 TORE GRÜN**, Rückgabewert 0. Das ist der erste
Torlauf dieser Messung mit einem **zuordenbaren** Messgegenstand.

**Und pytest danach noch einmal einzeln**, mit md5-Stempel vor und nach dem
Lauf (beide `d646cb4c…`, die Datei stand also still):

```
3153 passed, 11 skipped, 8 xfailed in 291.89s
```

Rückgabewert **0**, getrennt von der Ausgabe gelesen — keine Pipe. Die acht
`xfailed` sind die offenen Entscheidungsfragen aus
`docs/ENTSCHEIDUNGEN-OFFEN.md`; sie sind `strict`, würden also rot, wenn
jemand sie unbemerkt behebt. **Damit sind alle vier Tore an einem
zuordenbaren Stand grün.**

**Für die zwanzig Commits selbst** sind damit zwei Tore stabil belegt
(Klammerbilanz und Versionsabgleich an der eingefrorenen Kopie); `node_check`
und `pytest` lesen `index.html` fest verdrahtet und lassen sich nicht auf die
Kopie richten — ihr grünes Ergebnis gilt für den Baum **zum Zeitpunkt des
Laufs**, nicht für v3.9.954. Das ist eine Grenze des Werkzeugs, keine
Unsicherheit über das Ergebnis.

---

## 6. Zusatzauftrag: `VBautag` vorher/nachher — 390, 640, 767, 1440 px

**Drei Stände, nicht zwei.** `index.html` trug beim Messen schon v3.9.956
(die D9-Seitenüberschriften). Ein Vergleich 954 gegen 956 hätte **zwei**
Änderungen in einen Topf geworfen, und damit wäre der Köder „bei 390 und
1440 darf sich nichts unterscheiden" wertlos geworden. Das Beweispaar ist
deshalb **954 gegen 955**; v3.9.956 ist zusätzlich gemessen und getrennt
ausgewiesen.

| Stand | Datei | md5 |
|---|---|---|
| VORHER v3.9.954 | `_mess_stand_954.html` | `359be144407d9b033949cbeccd866892` |
| NACHHER v3.9.955 | `_mess_stand_955.html` (aus `git show 11e365a:index.html`) | `24d8565d8f91acad24dbdd64bb14c6cb` |
| HEUTE v3.9.956 | `index.html` | `51f140dd7109e8e22007217ba595b3b8` |

Alle drei md5 verschieden — **K-STAND angeschlagen.** 954 gegen 955
unterscheiden sich in genau **drei Zeilen**: `SW_VER`, `APP_VERSION` samt
Kommentar, und `const isMob=ww<768` → `const isMob=ww<BP_MOB`.

### 6.1 Der erste Lauf war eine **leere Grundgesamtheit** — und das ist der eigentliche Fund

Erster Durchgang, Listenansicht, alle vier Breiten: **kein einziger
Unterschied**, auch nicht bei 640 und 767. K-640 und K-767 **stumm**,
Rückgabewert 1, Urteil **NICHT GEMESSEN**.

Der Grund steht in der Datei: **alle 29 `isMob`-Stellen in `VBautag`** liegen
entweder im **Bearbeitungsformular** (`editing`) oder in einer
**Eintragskarte** (`btEntries.map`). Ohne Server ist `btEntries` **leer** —
es gibt also keine Karte —, und mit geschlossenem Formular kann die Änderung
**gar nicht** sichtbar werden. Der Lauf hätte „bei 640/767 ändert sich nichts"
gemeldet und damit das Gegenteil der Wahrheit belegt.

Zweiter Durchgang mit **geöffnetem Formular** (Klick auf `➕ Neuer Eintrag`,
Nachweis `{datum_feld: True, speichern: True, abbrechen: True}`): alle vier
Köder stimmen.

### 6.2 Die Tafel — Formular offen, Breite × Stand

| Größe | 390 v954 | 390 v955 | 640 v954 | 640 **v955** | 767 v954 | 767 **v955** | 1440 v954 | 1440 v955 |
|---|---|---|---|---|---|---|---|---|
| Knöpfe | 50 | 50 | 56 | 56 | 56 | 56 | 56 | 56 |
| Felder | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| Auswahlfelder | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| Optionen | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |
| **Schrift < 12 px** | 13 | 13 | **33** | **15** | **33** | **15** | 15 | 15 |
| Textstellen gemessen | 83 | 83 | 87 | 87 | 87 | 87 | 87 | 87 |
| wirklich gekürzt | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 0 |
| nur Kastenüberlauf | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tabellen > Schirm | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tippziele < 44 px | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Überschrift | `📋 Neuer Tagesbericht` in allen acht Aufnahmen | | | | | | | |
| Tabellenköpfe | keine, in allen acht | | | | | | | |

v3.9.956 ist in **allen** Größen mit v3.9.955 identisch — die
D9-Überschriften berühren `VBautag` nicht.

### 6.3 Was sich bei 640 und 767 px ändert, in Worten

**Genau eine Größe ändert sich, und sie wird besser: die Zahl der
Textstellen unter 12 px fällt von 33 auf 15.** Achtzehn Stellen verlassen
den Bereich unter 12 px. Ursache im Quelltext: die Chips und
Schnellwahl-Knöpfe des Formulars tragen `fontSize: isMob ? 11 : 12`, und die
Kategoriechips zusätzlich `padding: isMob ? "4px 8px" : "5px 10px"`. Mit der
Desktop-Fassung greift überall der 12-px-Wert.

**Nichts wird dabei verloren:**

* **kein Knopf und kein Feld verschwindet** — 56 Knöpfe, 5 Felder, 2
  Auswahlfelder mit 10 Optionen, vorher und nachher gleich
* **keine neue Kürzung** — „wirklich gekürzt" bleibt 1, und diese eine ist
  **nicht** `VBautag`, sondern der Projektname in der Kopfzeile der
  Projekt-Hülle: `DR.-GSCHMEIDLERSTRASSE 10`, 202 px Text in 84 px (640) bzw.
  150 px (767), `overflow:hidden` + `ellipsis`. Sie steht in **beiden**
  Ständen mit denselben Zahlen
* **kein neuer waagrechter Roller** — die Liste der Roller ist Zeichen für
  Zeichen dieselbe (+778 px bei 640, +651 bei 767, beides die
  Projekt-Reiterzeile)
* **kein Tippziel unter 44 px** — 0 in allen acht Aufnahmen
* **keine Tabelle breiter als der Schirm** — 0 in allen acht

**Die drei Formen des Beschnitts, getrennt:** (1) `overflow:hidden` + `ellipsis`
— 1 Stelle bei 640/767, in beiden Ständen dieselbe, oben benannt. (2)
Kastenüberlauf bei `overflow:visible`, wo nichts verloren geht — **0** in allen
acht Aufnahmen. (3) **in JavaScript gekappter Text** — **diese Sonde kann das
nicht sehen**, weil der volle Wert nie im Baum steht. Für Form (3) lautet das
Ergebnis **nicht gemessen**, nicht 0.

### 6.4 Urteil zum Zusatzauftrag

**Die Änderung wirkt genau dort, wo sie soll, und nur dort.** Bei 390 und
1440 px sind die Stände in allen 13 gemessenen Größen identisch (K-390 und
K-1440 stimmen); bei 640 und 767 px ändert sich genau eine Größe, und zwar
zum Besseren. **Kein Befund, nichts nachzubessern.**

Die Köder, die das belegen: **K-STAND** (drei verschiedene md5) · **K-390 /
K-1440** (müssen gleich sein — sind gleich) · **K-640 / K-767** (müssen sich
unterscheiden — unterscheiden sich) · **K-SCHRIFT** (ein eingesetzter 9-px-Text
wird in jeder der zwölf Aufnahmen gefunden) · **K-BESCH** (zwei Baits, hart und
weich, in jeder Aufnahme richtig einsortiert).

---

## 7. WAS NICHT GEMESSEN WURDE — das sind **keine** bestandenen Fälle

1. **Unterzustände.** Je Ansicht ist der EINE Zustand aufgenommen, in den die
   Navigation führt. Chef hat fünf Unterreiter, Admin sechs, das Büro-Portal
   fünf; aufgenommen ist jeweils der erste. Die einzige Ausnahme ist das
   `VBautag`-Formular (Abschnitt 6), und es hat genau dort den Fund erzwungen.
2. **Alles hinter einem Klick**: Dialoge, Menüs, Aufklapper, das
   Bestätigungsfenster, der zweite Reiter von `VMaterial` (Warenkorb/Lager —
   `--mat-tab` war nicht gesetzt).
3. **Alle Rollen außer `admin`** (`rolle=Geschäftsführer`, `monteurId=M1`).
   Für die Rolle `monteur` ist **nur** gemessen, dass sie 8 Reiter führt und
   keinen, den der Admin nicht hat. Ein Monteur sieht in Werkzeuge drei statt
   fünf Reiter und in der Projektakte weniger Unterseiten — **dort ist keine
   einzige Regel gemessen.**
4. **Serverleere Ansichten.** REST und Auth sind abgeklemmt. Flotte,
   Gefahrenstoffe, Bauprovisorien, `VBautag`-Einträge, `VMaterial`-Bestellungen
   und `VDoku` sind **leer**. Ihre Zahlen sind die eines leeren Blatts. Wie
   teuer das ist, zeigt Abschnitt 6.1: dort hätte die leere Liste eine saubere,
   falsche Antwort geliefert.
5. **In JavaScript gekappter Text** (die dritte Form des Beschnitts). Keine
   DOM-Messung kann sie sehen; der volle Wert steht nie im Baum. Für alle 22
   Ansichten lautet das Ergebnis dazu **nicht gemessen**. Der Abschlussbericht
   nennt zwölf solche Stellen, behoben in v3.9.949/953 — **diese Messung
   bestätigt davon keine einzige.**
6. **Hellmodus bei 375 px.** Gemessen ist der Hellmodus bei 390 und 1440 px
   (alle 31 Ansichten) sowie bei 375 px in den fünf Ansichten der Stufe 8–11.
   Für die übrigen 17 Ansichten ist 375 px im Hellmodus **nicht gemessen**.
7. **Schriftgrößen sind keine Zusage und stehen hier nur als Messwert.** Die
   Auswertungen führen bei 1440 px **217 von 306** Textstellen unter 12 px, bei
   390 px 142 von 290; Planung/Wochenplanung 49 von 133 bei 375 px. `WeekPlan`
   ist laut Abschlussbericht **bewusst** draußen. Ob die übrigen Zahlen gewollt
   sind, ist nicht entschieden und war nicht mein Auftrag.
8. **Farbkontrast von Text.** Gemessen ist nur Fläche und Helligkeit, nie
   Text-gegen-Grund.
9. **Echtes Gerät, Drehung, iOS.** Gemessen ist ein Chromium-Viewport mit
   `is_mobile`/`has_touch` unter 600 px. Der Hoch-/Querformatwechsel eines
   echten Geräts ist nicht gemessen.
10. **`node_check` und `pytest` für v3.9.954.** Beide lesen `index.html` fest
    verdrahtet. Ihr grünes Ergebnis (3153 Fälle) gilt für **`d646cb4c…`, also
    v3.9.956**, nicht für die eingefrorene Kopie v3.9.954. Für v3.9.954 sind
    nur Klammerbilanz und Versionsabgleich stabil belegt. Ein grünes
    `pytest` an v3.9.956 ist für die zwanzig Commits ein **starker Hinweis**
    und kein Beweis — v3.9.956 enthält sie alle, aber auch zwei weitere
    Änderungen.
11. **Die Tastaturbedienung** und die Reihenfolge des Tabulators.
12. **Der Auslieferungsstand.** Gemessen ist eine lokal servierte Datei, nicht
    die veröffentlichte App.

---

## 8. ABWEICHUNGEN GEGEN DEN EINGECHECKTEN GRUNDSTAND

**Keine.** `diff -u` zwischen der neu erhobenen und der eingecheckten
`docs/GRUNDSTAND_UI_v3.9.954.md` gibt **0 Zeilen** aus — die beiden Dateien
sind byteweise identisch, in allen 44 Aufnahmen, samt Überschriften,
Tabellenköpfen, Platzhaltern, Auswahloptionen und Knopfnamen.

Das ist mit drei Ködern abgesichert (Abschnitt 3); ohne sie wäre „keine
Abweichung" die Aussage eines Vergleichers, der vielleicht nichts vergleicht.

**Was dabei gleich geblieben ist, obwohl es hätte wandern können:** die
Zeitstempel. Der Grundstand führt keine „heute"-Werte in den verglichenen
Feldern; die erwartete Abweichung durch das Wandern des Datums ist
**ausgeblieben** und musste nicht eingeordnet werden.

**Eine Abweichung, die nicht den Grundstand betrifft, aber hierher gehört:**
die Zusagenliste des Auftrags nennt drei Nullen, die die eigenen Beschlüsse
des Laufs nicht hergeben — Tabellen > Schirm bei 390 px (Wochenbericht, S-2),
wirklich gekürzter Text bei 1440 px (AS-Liste, S-3) und Bedienelemente ohne
Beschriftung (Fahrzeuge, S-1). Die ersten beiden sind im Abschlussbericht
ausdrücklich als „bewusst nicht gebaut" begründet; die dritte ist in
`B3_STUFEN_12_15.md` als D3 aufgenommen und schlicht offen.

---

## Läufe und Rohdaten

Alle Rohdaten liegen unter
`%TEMP%\claude\C--Users-technik\a0610c25-…\scratchpad\schluss\`:
`grundstand2.txt` · `GRUNDSTAND_neu.md` · `grundstand_diff.txt` (0 Zeilen) ·
`vergleich_ergebnis.txt` · `b4.txt`/`b4.json` · `b8.txt`/`b8.json` ·
`b12.txt`/`b12.json` · `hell.txt` · `HELLMODUS_neu.md` · `bestand.txt` ·
`bestand_selbst.txt` · `leere_liste.txt` · `torkette.txt` ·
`torkette_schnell.txt` · `klammer_954.txt`/`klammer_955.txt`/`klammer_heute.txt` ·
`vbautag.txt`/`vbautag.json` · `vbautag_form.txt`/`vbautag_formular.json` ·
`index_wache.log` (der md5 von `index.html` im 15-Sekunden-Takt, mit dem
Zeitpunkt des fremden Schreibvorgangs: 21:31:28).

Die drei eigenen Hüllen (`vergleich.py`, `leere_liste.py`,
`vbautag_vorher_nachher.py`) liegen im selben Ordner. Sie bauen **keine**
Messvorschrift nach: jede Regel ist aus `b3_vier_ansichten_messen`,
`b3_stufen_8_11_messen` und `b3_stufen_12_15_messen` **importiert**.

**Kein bestehender Riegel wurde angepasst, keine Sonde erleichtert, und
`index.html` wurde nicht geschrieben.**
