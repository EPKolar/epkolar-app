# Grundstand UI v3.9.967 — 22 Ansichten, 44 Aufnahmen, echte Saat

**Erhoben am 27.09.2026 abends.** `origin/main = 7fda3e3`, index.html auf
v3.9.967. Saat: 9 aktive Monteure + 2 ausgetretene · 21 Fahrzeuge · 296
Werkzeuge · 185 Arbeitsscheine · 3 Projekte. Jede Ansicht bei **390 und
1440 px**. Keine Ansicht unerreicht.

**Die Messanordnung hat sich zuerst selbst geprüft:** 16 Köder, alle
angeschlagen — darunter die vier Piktogramm-Formen, die Kreuzprobe M4/M5 und
drei Gegenproben, die *nicht* anschlagen dürfen (Währungszeichen, ASCII,
hochgestelltes m²). Tor B trägt (leere Saat → Meldung, volle Saat → Ruhe).
Köder restlos entfernt.

## Die Gesamtzahlen — und wo die Arbeit dieses Tages steckt

| | heute Mittag (v3.9.962) | jetzt (v3.9.967) |
|---|---|---|
| **Elemente < 12 px** | 1354 | **911** |
| … davon `auswertungen` | | **602** |
| … **alles andere** | | **309** |
| Tippziele < 44 px | 1952 | 1952 |
| Emoji im Knopftext | 1444 | 1444 |
| Tabellenzeilen | 502 | 502 |
| **Icon-Knöpfe ohne `aria-label` und `title`** | **0** | **0** |

Die letzte Zeile ist eine **gemessene** Null: der Köder schlug in beiden Formen
an. Sie hält jetzt bei 3513 Knöpfen.

Tippziele, Emoji und Zeilen sind **unverändert** — das ist richtig, sie waren
nicht Gegenstand dieser fünf Punkte. Wer aus ihrer Konstanz auf „nichts
passiert" schließt, mischt zwei Fragen.

## 🔴 Zwei Drittel des Rests sind EINE Ansicht — und es ist meine benannte Ausnahme

`auswertungen` trägt **264** Stellen bei 390 px und **338** bei 1440 px, zusammen
**602 der 911**. In der Stichprobe sind es **ausschließlich `text`-Elemente in
`svg`/`g`** — die Achsen- und Reihenbeschriftungen der Diagramme.

Ich habe `svg text { font-size: 10px !important }` in v3.9.966 **absichtlich**
stehengelassen, mit der Begründung, Achsenschriften stünden dicht nebeneinander.
Diese Begründung halte ich für richtig. Aber **die Größenordnung habe ich
unterschätzt**, und zwar zweifach:

1. Es ist der **größte verbleibende Block der ganzen App**, nicht eine Fußnote.
2. Bei 1440 px sind es **8 px und 9 px**, nicht nur 10 — also gibt es dort
   außerdem **inline** gesetzte SVG-Schriftgrößen, die meine CSS-Regel nicht
   erklärt. 8 px ist der kleinste Wert, den diese Messung heute in der ganzen
   App findet.

Frage **19** in `ENTSCHEIDUNGEN-OFFEN.md` ist damit deutlich gewichtiger als
dort beschrieben. Was zu messen wäre, bleibt dasselbe: **Überlappung**, nicht
Schriftgröße — und dafür gibt es noch keinen Melder.

## Die 22 Ansichten, < 12 px bei 390 / 1440 px

| Ansicht | 390 | 1440 | woraus der Rest besteht |
|---|---|---|---|
| bautagebuch | **0** | 14 | |
| material | **1** | 15 | |
| fahrzeuge | 2 | 7 | nur Hülle |
| arbeitsscheine (Liste) | 2 | 7 | nur Hülle |
| arbeitsscheine (Formular) | 2 | 7 | nur Hülle |
| planung | 2 | 9 | nur Hülle + 2 |
| werkzeuge | 2 | 7 | nur Hülle |
| zeit | 2 | 7 | nur Hülle |
| abwesend | 2 | 7 | nur Hülle |
| monatsabr | 2 | 7 | nur Hülle |
| mitarbeiter | 2 | 7 | nur Hülle |
| buero | 2 | 7 | nur Hülle |
| admin | 2 | 7 | nur Hülle |
| chef | 2 | 7 | nur Hülle |
| gefahr | 2 | 7 | nur Hülle |
| baupro | 2 | 7 | nur Hülle |
| flotte | 2 | 13 | |
| **home** | 2 | **26** | Wochentagskürzel `Mo`…`Sa` bei 10 px |
| berichte | 7 | 26 | sieben `span` **in** `th` (Datumsspalten), 10 px |
| einstell | 8 | 13 | `Gesamt`/`Ausstehend` bei 9 px |
| **plaene** | 12 | **42** | Ebenen- und Gewerke-Chips, 10–11 px |
| **auswertungen** | **264** | **338** | SVG-Diagrammtext, 8–10 px |

**18 von 22 Ansichten liegen bei 390 px auf ≤ 2** — und diese 2 sind
ausschließlich die App-Hülle (Sync-Banner in `div.bottom-nav`, `18 ausstehend`).
Aus dem Inhalt dieser Ansichten selbst: **null**.

## Warum keine Zahl auf 0 geht — je Ursache benannt

1. **Die App-Hülle** (`header`, `div.bottom-nav`, Sync-Banner): 2 bei 390 px,
   7 bei 1440 px, in **jeder** Ansicht. Sie trägt alle 22 — ein Griff dort
   verändert 22 Messwerte gleichzeitig. → Frage **18**.
2. **`auswertungen`**: SVG-Diagrammtext, siehe oben. → Frage **19**.
3. **`plaene`**: Ebenen- und Gewerke-Chips als `span` mit 10–11 px inline.
   Nicht angefasst, weil `VPlan` in diesem Lauf schon zwei Änderungen bekommen
   hat (Freigabe-Knopf benannt, Zeilenknöpfe entpolstert) und eine dritte ohne
   eigene Messung dazukäme.
4. **`home` bei 1440**: die Wochentagskürzel der Wetterzeile bei 10 px. Genau
   diese Zeile hat v3.9.943 schon einmal angefasst (damals 7 px) und dabei
   `slice(0,isMob?4:7)` eingebaut — wer sie hebt, muss diese Kürzung mitdenken.
5. **`berichte`**: sieben `span` **innerhalb** von `th` mit eigener Inline-Größe.
   Der in v3.9.966 gehobene `th`-Wert erreicht sie nicht, weil das Kind seinen
   eigenen trägt.
6. **`einstell`**, **`flotte`**, **`material`**, **`bautagebuch`**: kleinere
   Gruppen, alle bei 1440 px sichtbar und bei 390 px nicht — dasselbe Muster:
   die mobile CSS-Stufe verdeckte sie, am Schreibtisch stehen die Inline-Werte.

## 🔴 Was dieser Grundstand NICHT abdeckt

* **14 der 44 Aufnahmen sind „nicht aussagekräftig" gestempelt** —
  `auswertungen`, `baupro`, `chef`, `einstell`, `flotte`, `gefahr`, `planung`.
  Das Tor verweigert dort die Aussage, und es hat recht: diese Ansichten zeigen
  den Bestand als **Zahl** oder erreichen ihn gar nicht.
* **Die Wochenplanung erreicht die Saat prinzipiell nicht.** Der Wochenplan
  liegt in keinem der 21 Offline-Speicher; `rows` kommt aus `_wpGet(kw)||W0`,
  und `W0` ist ein fest eingebauter Vorgabeplan mit Zwei-Zeichen-Kürzeln. Der
  Befund aus v3.9.967 (`_kurz(nm,6)`) ist deshalb am **Quelltext** belegt, nicht
  am Schirm — und er wäre am Schirm auch nie sichtbar geworden.
* **Kein Melder für Überlappung.** Die Frage, die `auswertungen` entscheidet,
  kann dieser Aufbau nicht beantworten.
* **`tipp44` ist nicht gemessen worden, sondern nur mitgezählt.** 1952 Tippziele
  unter 44 px sind eine große Zahl, und sie ist heute nicht kleiner geworden.
  Sie gehört in einen eigenen Lauf.

---

## 🔴 Korrektur vom 28.09.2026 — meine „eine benannte Ausnahme" war zweifach falsch beschrieben

Drei Messagenten haben diesen Grundstand nachgeprüft. An drei Stellen haben sie
mich widerlegt, und alle drei Widerlegungen habe ich selbst nachgemessen.

### 1. Die Regel gilt nur am Telefon

Oben steht `svg text { font-size: 10px !important }` als Erklärung für **beide**
Zahlen — 264 bei 390 px und 338 bei 1440 px. Das ist falsch.

**Die Regel steht in Zeile 319, innerhalb von `@media (max-width: 600px)`.** Sie
gilt ausschließlich am Telefon. Damit zerfallen die zwei Zahlen in zwei
verschiedene Ursachen:

| Breite | was dort klein ist | Ursache |
|---|---|---|
| 390 px | alles im Diagramm auf **10 px** | meine CSS-Regel |
| 1440 px | **8 px und 9 px** | **inline** gesetzte SVG-Größen, die die Regel gar nicht erreicht |

Die Stichproben belegen es: bei 390 px zwölfmal 10 px, bei 1440 px siebenmal
8 px und fünfmal 9 px. Ich habe zwei Aufnahmen als eine Aussage geführt.

### 2. Die Ausnahme macht zwei richtige Schriften wieder kaputt

Weil eine `!important`-Autorenregel ein SVG-Präsentationsattribut schlägt,
drückt meine Ausnahme am Telefon zwei Werte **herunter**, die im Quelltext
bereits richtig stehen: die x-Achse von `SvgBar` (steht auf `UI.fMeta` = 12 →
wird 10) und die Ringsumme von `SvgPie` (15 → 10).

Eine Ausnahme, die etwas schützen soll und dabei zwei gute Werte verschlechtert,
ist keine Ausnahme mehr, sondern ein Nebenschaden.

### 3. Drei meiner neun gehobenen CSS-Regeln treffen überhaupt kein Bauteil

v3.9.966 hat neun Regeln von unter 12 px auf 12 px gehoben. Drei davon waren
schon vorher wirkungslos, sind es nachher noch, und der Quelltextriegel ist an
allen dreien grün — **und war es auch, als sie noch 11 px trugen**:

* **`.ber-table`** — kommt als Klasse in der ganzen Datei nicht vor.
* **`.badge`** — nur in Druck- und Export-HTML-Zeichenketten, die ihre eigenen
  Stilblöcke mitbringen. Im Hauptdokument: nichts.
* **Das Sync-Banner** — beide Arme tot. `[style*="Änderungen warten"]` sucht den
  Text im *style-Attribut*, er steht aber im *Textinhalt*; und kein Knopf der
  Datei trägt ein `title` mit „Jetzt sync".

Das ist Anwesenheit statt Wirkung an meiner eigenen Kur. Die Konsequenz steht
in `tests/test_wirkung_frisch_v968.py`: die berechnete Größe wird jetzt am
gerenderten Baum gemessen, mit einer Klinke, die anschlägt, sobald sich eine
Schriftquelle ändert, ohne dass nachgemessen wurde.

### 4. Und ein Befund, der gar kein Schriftproblem ist

`SvgPie` zeichnet die Legendenzeile *i* bei `y = i*18+16` in eine `viewBox` von
nur 150 Höhe. **Ab der neunten Zeile liegt sie außerhalb und wird nie
gezeichnet.** Gemessen: `absTyp` verliert **7 von 15** Einträgen, `asArt` **1
von 9**. Keine Schriftgröße der Welt behebt das — es ist fehlende Information,
nicht kleine Information, und es gehört in eine eigene Kur.

### Was sich dadurch an der Gesamtaussage ändert

Die Zahlen oben (1354 → 911, davon 602 in `auswertungen`) bleiben richtig — sie
sind gemessen. Was sich ändert, ist die **Begründung**: die 602 sind nicht eine
Ursache, sondern zwei, und meine Ausnahme deckt nur die eine davon ab. Die
vollständige Aufnahme steht in `docs/befunde/DIAGRAMM_ACHSEN.md`, mit allen
Stellen, drei Wegen und einer Empfehlung. Entschieden wird es von Sebastian
(Frage 19).
