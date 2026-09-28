# Diagramm-Achsen — feste Schriftgrößen in den SVG-Charts

**Aufgenommen:** 28.09.2026 · **Stand:** `index.html`, md5 `9d7d3ecd8083f45b216b11985be59a93`, 3 724 140 Bytes, 30 255 Zeilen, Arbeitsbaum sauber auf `a438b5a` (v3.9.967).
**Art der Aufnahme:** ausschließlich **Quelltext**. Ich habe die App nicht gestartet. Die Schirmzahlen weiter unten stammen aus einer **fremden, schon vorhandenen** Messung (`scripts/_echtmengen_rohdaten.json`, 27.09.), nicht aus einem eigenen Lauf.
**Werkzeug:** `scripts/code_scan.py` (`ist_code`, `_ERZEUGER`, `_klammer_zu`, `_komponente`) — beide Eichungen bestanden: Zeichenketten 21/21, Elementformen 4/4. Dazu ein eigener Köder je Schreibweise (unten unter „Was diese Aufnahme NICHT abdeckt").
**Geändert wurde nichts.** Kein `index.html`, kein `git add`, kein Commit.

---

## 0. Die drei Korrekturen vorweg

### 0.1 Die „56" stimmt — aber sie zählt etwas anderes als die Diagramme

Gemessen am Quelltext: **genau 56** Stellen tragen eine `fontSize`- bzw. `font-size`-Eigenschaft mit einer **blanken Zahl 8 oder 9.x**. Die Zahl ist auf den Punkt reproduzierbar.

Nur: **3 davon stehen in einem `svg`.** Die anderen **53** sind gewöhnliche `div`/`span`/`button` in `VMaterial`, `VPlan`, `App`, `KundenPortal`, `PhotoSyncStatus` und anderen — sie haben mit den Diagrammen nichts zu tun.

Und die 56 ist zugleich zu klein. Sie kennt nur **eine Schreibweise des WERTS**. Ein zweiter Durchgang über den *bedingten* Wert (`fontSize: isMob?UI.fMeta:8`) findet **8 weitere** Treffer, davon **7 echte** (einer ist ein Fehlfund: Zeile 6470 setzt 16/19/24 px, die „9" dort ist ein `length>9`). Vollständig sind es also **63 Quelltextstellen**, die 8 oder 9 px erzeugen können — **weiterhin 3 davon im `svg`**.

| Grundgesamtheit | Zahl |
|---|---|
| `fontSize`/`font-size` mit blanker Zahl 8 oder 9.x | **56** ← das ist die behauptete Zahl |
| dazu: bedingte Form mit 8/9-Zweig (`isMob?UI.fMeta:8`, `isMob?8:11`, …) | +7 |
| **Summe Quelltextstellen 8/9 px** | **63** |
| davon **innerhalb eines `svg`** | **3** |
| feste Schriftgrößen im `svg` insgesamt (8/9/10/11/15) | **7** |
| davon unter 12 px | **6** |

### 0.2 Die 8/9 px der Schirmmessung stammen von **1440**, nicht von 390

Das ist der wichtigste Befund dieser Aufnahme, und er ist an zwei Stellen unabhängig belegt.

Am Quelltext: die Ausnahmeregel

```
svg text { font-size: 10px !important; }
```

steht in `index.html` **Zeile 319** — und sie steht **innerhalb** des Blocks `@media (max-width: 600px) {` (Zeile 268, schließt Zeile 354). Sie gilt also **nur auf dem Telefon**. Auf dem Schreibtisch gibt es sie nicht.

Dazu die Kaskade: React schreibt `fontSize: 8` an einem SVG-`text` als **Präsentationsattribut** `font-size="8"`. Ein Präsentationsattribut ist die **schwächste** Stufe der Kaskade; eine Autorenregel mit `!important` schlägt sie in jedem Fall.

Am Schirm (fremde Messung, `_echtmengen_rohdaten.json`, Ansicht `auswertungen`):

| Breite | Elemente < 12 px | Stichprobe (12 Zeilen) |
|---|---|---|
| **390** | **264** | **12 × 10 px**, alle `text` in `svg`/`g` — `'aufgenommen (24)'`, `'185'`, … |
| **1440** | **338** | **7 × 8 px + 5 × 9 px**, alle `text` in `svg`/`g` — `'Mo'`, `'Di'`, … |

Die Auftragsbeschreibung führt „264 bei 390 px" und „8 px und 9 px" als **eine** Aussage. Sie sind aus **zwei** Aufnahmen. Bei 390 px ist in den Diagrammen **nichts** kleiner als 10 px, weil die Ausnahmeregel dort greift. Die 8 und 9 px sieht **nur der Schreibtisch**.

Damit dreht sich die Frage um: **Die Ausnahme schützt das Telefon nicht — sie schützt nur dort, wo sie gilt, und dort, wo es weh tut (8 px), gilt sie nicht.**

### 0.3 Die Ausnahme drückt eine schon gehobene Schrift wieder herunter

`SvgBar` Zeile 23092 — die x-Achsen-Beschriftung unter den Balken — steht im Quelltext bereits auf `UI.fMeta` (= 12, Zeile 3554). Die Kur hat sie also schon gehoben. Auf dem Telefon setzt `svg text { font-size:10px !important }` sie wieder auf **10** zurück. Das ist keine Ausnahme mehr, das ist eine Rücknahme.

---

## 1. Alle Stellen

Vollzählig: **7 feste Schriftgrößen** in `svg`-Zusammenhängen, dazu die eine Stelle mit Token. Es gibt **4 Diagramm-Bauteile** und darüber hinaus **kein** `svg` mit Text in der Datei (die 8 `svg`-Elemente im Code verteilen sich auf `_ik`, `WifiStatusIcon`, `PlanPin`, `VMaterial` — reine Symbole ohne `text` — und die vier Chart-Bauteile). `tspan` kommt in der Datei **null** mal vor.

| # | Zeile | Bauteil | Achse / Rolle | Wert im Quelltext | wirksam @390 | wirksam @1440 |
|---|---|---|---|---|---|---|
| 1 | 23092 | `SvgBar` | **x-Achse**, Kategoriename unter dem Balken (auf `maxL` = 8 bzw. 10 Zeichen gekappt, Rest im `<title>`) | `many?UI.fMeta:UI.fMeta` → **12** | **10** (CSS drückt herunter) | 12 |
| 2 | 23093 | `SvgBar` | **Wert über dem Balken** | **10** | 10 | 10 |
| 3 | 23102 | `SvgHBar` | **Reihenbeschriftung links** (das ist hier die y-Achse; auf 16 Zeichen gekappt, Rest im `<title>`) | **10** | 10 | 10 |
| 4 | 23104 | `SvgHBar` | **Wert am Balkenende** | **11** | 10 | 11 |
| 5 | 23120 | `SvgPie` | **Summe in der Ringmitte** (nur `donut`) | **15** | 10 (!) | 15 |
| 6 | 23121 | `SvgPie` | **Legende rechts**, `Label (Wert)` | **9** | 10 | **9** |
| 7 | 23135 | `SvgLine` | **x-Achse**, Zeit-/Tagesbeschriftung unter der Kurve | **8** | 10 | **8** ← die kleinste Schrift der App |
| 8 | 23136 | `SvgLine` | **Wert über dem Punkt** | **9** | 10 | **9** |

Zeile 5 ist eine Nebenwirkung, die niemand gewollt haben kann: die **Summe in der Ringmitte** ist die größte Schrift des Diagramms (15 px) und wird auf dem Telefon von der Ausnahmeregel auf 10 px **gestaucht**.

### Welche Diagramme das sind — 18 Instanzen in 3 Ansichten

**A) Ansicht `auswertungen` (`AuswertungView`, ab Zeile 25034) — 15 Diagramme**
Jedes läuft über `ChartBox` (23139) und ist vom Nutzer auf **jeden der fünf Typen** umschaltbar (`CHART_TYPES`, Zeile 4574: bar · pie · donut · line · hbar). Jedes der 15 kann also jedes der vier Bauteile erreichen. Die Vorgabe (Zeilen 25086–25102):

| Schlüssel | Titel | Vorgabe-Typ | Zahl der Marken |
|---|---|---|---|
| `asStatus` | Arbeitsscheine nach Status | donut | **8** (`AS_STATUS`, Z. 3702) |
| `asArt` | Arbeitsscheine nach Art | pie | **9** (`AS_ART`, Z. 3771) |
| `asMont` | Scheine pro Monteur | hbar | = Monteure mit Beitrag (Saat: 11, davon 9 aktiv) |
| `prjStatus` | Projekte Status | donut | 3, +1 wenn „Sonstige" auftritt |
| `prjFort` | Projektfortschritt (aktiv) | bar | = aktive Projekte (Saat: 3) |
| `absTyp` | Abwesenheiten nach Typ | pie | **15** (`AT_T`, Z. 3682) |
| `absPers` | Abwesenheit pro Person | hbar | = Monteure mit Beitrag |
| `wzStatus` | Werkzeuge nach Status | donut | **6** (`WZ_STATUS`, Z. 4568) |
| `wzKat` | Werkzeuge nach Kategorie | hbar | **9** (`WZ_KAT`, Z. 4569) |
| `wzWert` | Werkzeugwert (€) pro Kategorie | hbar | **9** |
| `zeit7` | Stunden letzte 7 Tage | line | **genau 7** (Z. 25074) |
| `fzTank` | Tankkosten pro Fahrzeug (€) | hbar | = nicht stillgelegte Fahrzeuge (Saat: ≤ 21) |
| `fzLiter` | Liter pro Fahrzeug | hbar | dito |
| `fzKm` | km-Stand Fahrzeuge | hbar | = Fahrzeuge mit `kmStand>0` |
| `fzSchaden` | Offene Schäden pro Fahrzeug | hbar | = Fahrzeuge mit Schäden |

Verteilung der Vorgaben: **8 × hbar**, 3 × donut, 2 × pie, 1 × bar, 1 × line.

**B) Chef-Dashboard (`ChefDashboard`, Reiter Projekte, Karte „Auftragsvolumen-Trend", Zeile 24718–24721) — 1 Diagramm**
`trendData` = **genau 12** Monate (Zeile 24613/24615), Vorgabe `bar`, Beschriftung im Format `Sep 26`.

**C) Fahrtenbuch (`FahrtenbuchView`, ab Zeile 26920) — 2 Diagramme, direkt ohne `ChartBox`**
* Zeile 27355: `SvgLine` **Geschwindigkeit**. `data = speedReihe.map(x => ({l:_zeit(x.t), v:x.v}))`. `_fzSpeedReihe` (26587) liefert **einen Punkt je GPS-Position** der Fahrt — **ohne jede Obergrenze und ohne Ausdünnung**. Bei einem Tracker mit 10-s-Takt sind das über eine 20-Minuten-Fahrt **120 Punkte** und damit 120 Zeitmarken zu 8 px plus 120 Wertzahlen zu 9 px.
* Zeile 27368: `SvgBar` **Tageskilometer**, eine Marke je Tag mit Fahrten im gewählten Zeitraum.

---

## 2. Die drei Wege

Alle Geometrie unten ist **aus den `viewBox`-Angaben des Quelltextes gerechnet**, nicht gemessen. Angenommene Zeichenbreite: gemischte Antiqua in `system-ui` ≈ 0,53 em, Ziffern ≈ 0,60 em. Angenommene gerenderte Breite der Chart-Karte bei 390 px Schirm: 390 − 16 (`.main-pad`) − 28 (Abschnittspolster) − 36 (`CC()`-Polster, Z. 6214) = **310 px**. Der `svg` selbst hat `width:100%`, der Maßstab ist also `310 / viewBox-Breite`.

### (i) So lassen

**Was es kostet:** auf dem **Schreibtisch** bleiben die x-Achse der Liniendiagramme bei **8 px** und drei weitere Rollen bei **9–11 px** — das sind **338** Elemente unter 12 px allein in `auswertungen`. Auf dem **Telefon** bleibt alles bei **10 px** — **264** Elemente, also 2 px unter dem Hausboden, nicht 4. Betroffen sind **6 Quelltextstellen** in **4 Bauteilen** und damit **alle 18 Diagramm-Instanzen** in drei Ansichten.

**Und es kostet mehr, als der Auftrag annimmt:** die Wertzahl über dem Balken (`SvgBar`, 10 px, `fontWeight:700`, **ohne** Versatz) hat im Auftragsvolumen-Trend bei 12 Monaten eine Spalte von 27,67 `viewBox`-Einheiten × 0,861 = **23,8 px**, und `€ 12,4k` braucht bei 10 px etwa **40 px**. Die Wertzahlen **überlappen dort schon heute**. Nichts zu tun heißt also nicht „Zustand halten", sondern „einen vorhandenen Überlauf weiter tragen".

Nullkosten hat dieser Weg an **einer** Stelle wirklich: `SvgHBar`. Dort stehen die Zeilen untereinander (`bh=18`, `gap=3` → 21 Einheiten Abstand bei `viewBox`-Breite 300, Maßstab 1,03 → **21,6 px Zeilenabstand**), und 10-px-Text in 21,6 px überlappt nie. Das betrifft **8 der 15** Auswertungs-Diagramme.

### (ii) Auf Mobil hochziehen und weniger Achsenmarken zeigen

Die entscheidende Zahl zuerst: **in 17 der 18 Diagramm-Instanzen fällt beim Heben auf 12 px KEINE einzige Marke weg.** Gerechnet, Bauteil für Bauteil:

| Bauteil | betroffene Diagramme | Marken heute | Marken nach dem Heben auf 12 px | Verlust |
|---|---|---|---|---|
| `SvgHBar` | 8 von 15 in `auswertungen` | alle | alle | **0** — Zeilenabstand 21,6 px, 12-px-Text passt mit Reserve |
| `SvgPie` (Legende) | 5 von 15 | Zeilenabstand 18 Einh. × 1,15 = **20,7 px** | passt senkrecht | **0 senkrecht** — aber siehe Warnung unten |
| `SvgBar` (x-Achse) | `prjFort` (3 Marken), Trend (12), Tages-km (n) | Versatz in zwei Reihen ab n > 6 (Z. 23089/23091) | Trend: `Sep 26` braucht 38 px von 47,7 px verfügbar | **0** bei 3 und bei 12 Marken |
| `SvgLine` (x-Achse) | `zeit7` (**genau 7**) | Abstand 260/6 = 43,3 Einh. × 0,97 = **42 px**, `Mo` braucht 13 px | `Mo` braucht 16 px von 42 px | **0** |
| `SvgLine` (x-Achse) | Fahrtenbuch-Geschwindigkeit | **eine Marke je GPS-Punkt** | — | **der einzige echte Fall** |

**Die einzige Stelle, an der wirklich Marken fallen müssen, ist die Geschwindigkeitskurve im Fahrtenbuch — und sie muss es heute schon.** Rechnung: Abstand = 260/(n−1) Einheiten ≈ ebenso viele Pixel. Eine Uhrzeit `14:32` ist bei 10 px rund **27 px** breit, bei 12 px rund **32 px**.

* Überlappung ab **n = 11 Punkten** bei den heutigen 10 px.
* Überlappung ab **n = 10 Punkten** bei 12 px.

Das Heben kostet dort also **genau einen Punkt** Schwelle. Bei einer realen Fahrt mit 40–120 Punkten müssten in beiden Fällen **rund 90 % der Marken weg** — etwa jede `ceil(n/8)`-te behalten, also 8 statt 120. Das ist eine Ausdünnung, die **unabhängig von der Schriftgröße fällig ist**; im Quelltext gibt es sie nirgends: `pts.map(...)` in Zeile 23134–23136 beschriftet jeden einzelnen Punkt.

Zweiter, kleinerer Fall: **Tageskilometer** im Fahrtenbuch. Mit `bw` am Boden von 18 Einheiten ist der Maßstab `310/(28+24n)`, mit Zwei-Reihen-Versatz stehen `14880/(28+24n)` px je Marke zur Verfügung. `17.9.` braucht bei 10 px 28 px, bei 12 px 32 px:

* heute (10 px): eng ab **n = 22 Tagen**;
* nach dem Heben (12 px): eng ab **n = 19 Tagen**.

Kosten: **3 Tage Schwelle**, danach jede zweite Marke — bei einem Monatszeitraum also **11 von 22**.

**Die Warnung zu `SvgPie`:** dort kostet das Heben **waagrecht**. Die Legende beginnt bei x = 171 in einer `viewBox` von 270 — **99 Einheiten × 1,15 = 114 px** für `Label (Wert)`. `Pflegefreistellung (3)` sind 21 Zeichen: bei 10 px ≈ 105 px (passt knapp), bei **12 px ≈ 126 px** (steht über dem Rand und wird abgeschnitten, denn der äußerste `svg` hat `overflow:hidden`). Das ist die **einzige** Stelle, an der das Heben etwas sichtbar kaputt macht, und sie braucht keine „weniger Marken", sondern eine **breitere `viewBox`**.

**Aufwand:** 6 `fontSize`-Werte, die `svg text`-Regel in Zeile 319, eine Ausdünnungsregel in `SvgLine` (≈ 2 Zeilen, neue Logik, eigene Messung nötig), und die `viewBox`-Breite von `SvgPie`.

### (iii) Auf Mobil durch die Zahlenliste ersetzen, die darunter ohnehin steht

**Am Quelltext beantwortet: diese Liste steht dort nicht. In keinem einzigen der 18 Diagramme.**

`ChartBox` (Zeilen 23139–23167) rendert: Kopfzeile mit Schalter und Titel, die fünf Typ-Knöpfe, und dann **genau eines** der fünf `Svg*`-Bauteile — bzw. „Keine Daten verfügbar". Danach schließt die Klammer. Keine `table`, keine Werteliste, nichts.

Was **tatsächlich** da ist:

| Ort | Zeilen | Was |
|---|---|---|
| `AuswertungView`, Excel-Ausgabe | 25123–25146 | läuft **schon heute** über alle 15 Diagramme und schreibt `[Diagramm, Kategorie, Wert]` — die Daten für eine Liste sind **an einer Stelle bereits zusammengestellt** |
| `AuswertungView`, „💶 Auftragsvolumen nach Geschäftsjahr" | 25162–25185 | **die fertige Vorlage**: je Zeile Bezeichnung + Anzahl + Betrag, darunter ein reiner CSS-Balken, am Schluss eine Summe — alles gewöhnliches HTML bei 13 px / `UI.fMeta`, **kein `svg`**, kein Zeichen unter 12 px |
| `AuswertungView`, KPI-Reihe | 25151–25159 | 5–6 **Gesamtzahlen** (`Kpi`), keine Werte je Kategorie |
| `FahrtenbuchView` | 27356–27359, 27369–27372 | ein Kennzahlenstreifen unter jedem Diagramm (`max`/`Ø`/`Messpunkte` bzw. `Ø km/Tag`/`Spitze`/`Tage`) bei **11 px** — Aggregate, keine Einzelwerte |

Weg (iii) heißt also nicht „das Vorhandene zeigen", sondern **„es bauen"**. Der Aufwand ist allerdings klein, weil beides schon existiert: die **Form** (Auftragsvolumen-Block) und die **Daten** (`ch.data` = `[{l,v,c}]`, dieselbe Liste, die die Excel-Ausgabe durchläuft). Ein Bauteil, in `ChartBox` unter dem `svg` eingehängt, bedient **alle 15** Auswertungs-Diagramme und den Chef-Dashboard-Trend auf einen Schlag.

**Wo (iii) nicht trägt:** die Geschwindigkeitskurve im Fahrtenbuch. 120 Zeilen `14:32 — 63 km/h` sind keine Liste, die jemand liest. Dort hilft nur Ausdünnen.

---

## 3. Empfehlung

**Keiner der drei rein. Eine Mischung — und zwar in dieser Reihenfolge, weil die ersten beiden Schritte die Begründung des dritten verändern.**

**Schritt 1 — die Ausnahme in Zeile 319 streichen und die sechs Werte auf den Boden heben.**
Begründung, gerechnet und nicht vermutet: in **17 der 18** Diagramm-Instanzen fällt dabei **keine** Marke weg. Die Ausnahme schützt außerdem gar nicht das, was sie schützen soll — sie gilt nur unter 600 px, und die 8 px stehen auf dem **Schreibtisch**. Solange sie steht, drückt sie zusätzlich zwei Schriften, die bereits richtig sind, wieder herunter: die x-Achse von `SvgBar` (12 → 10) und die Ringsumme von `SvgPie` (15 → 10).
Zwei Nebenbedingungen, die mitmüssen: die **`viewBox`-Breite von `SvgPie`** von 270 auf mindestens 300 (sonst wird `Pflegefreistellung (3)` bei 12 px am rechten Rand abgeschnitten), und die Wertzahl über dem Balken in `SvgBar` braucht denselben Zwei-Reihen-Versatz, den die Kategoriebeschriftung darunter schon hat — sie überlappt bei 12 Monaten **heute schon**.

**Schritt 2 — Marken ausdünnen an genau einer Stelle: `SvgLine` im Fahrtenbuch.**
Nicht wegen der Schrift. Wegen `_fzSpeedReihe`, das **eine Marke je GPS-Punkt** liefert und keine Obergrenze kennt. Bei 40–120 Punkten ist die Achse bei 8 px unlesbar und bei 12 px unlesbar; der Unterschied ist **ein** Punkt Schwelle. Regel: jede `ceil(n/8)`-te Marke beschriften, die Punkte selbst alle zeichnen. Das ist neue Logik und braucht eine eigene Messung — sie gehört **nicht** in denselben Schritt wie Schritt 1, sonst kann man hinterher nicht sagen, welcher der beiden gewirkt hat.
Die Tageskilometer bekommen dieselbe Regel bei n > 18.

**Schritt 3 — die Zahlenliste bauen, aber UNTER das Diagramm, nicht anstelle.**
Der Auftrag stellt (iii) als Ersatz auf dem Telefon. Das wäre schade: das Diagramm ist auf 390 px nach Schritt 1 lesbar, und die Form der Liste gibt es bereits als Vorlage (Auftragsvolumen-Block, 25162–25185), die Daten als `ch.data`. Untergehängt trägt sie den Wert ein zweites Mal — in gewöhnlichem HTML, das jeder Vorleser findet, jede Suche im Text trifft und keine `!important`-Regel je wieder herunterdrücken kann. Das ist der einzige der drei Wege, der die Frage „steht der Wert nur in der kleinen Schrift?" **dauerhaft** mit Nein beantwortet.

**Schritt 4 — davon getrennt und unabhängig von jeder Schriftgröße: die abgeschnittene Legende.**
`SvgPie` zeichnet die Legendenzeile i bei `y = i*18+16` in eine `viewBox` von nur **150** Höhe. Ab der **9.** Zeile (`y = 160`) steht sie außerhalb und wird nicht gezeichnet. Gerechnet auf die heutigen Kategorienzahlen:

* `asArt` (pie, `AS_ART` = 9): **1 Eintrag unsichtbar**
* `absTyp` (pie, `AT_T` = 15): **7 von 15 Einträgen unsichtbar**
* `asStatus` (donut, 8): passt gerade noch (`y = 142`)
* `wzStatus` (6), `prjStatus` (3–4): passen

Das ist kein Schriftgrößenproblem, und keine Schriftarbeit behebt es. Es gehört vor oder neben Schritt 1 gemeldet, sonst wird es von der Schriftkur zugedeckt.

---

## 4. Was diese Aufnahme NICHT abdeckt

1. **Es gibt keinen Melder für ÜBERLAPPUNG — und ohne ihn ist die Frage nicht endgültig entscheidbar.**
   Weder diese Aufnahme noch irgendetwas im Repository fragt einen Renderer, ob sich zwei `text`-Kästen schneiden. Jede Aussage oben über „überlappt ab n = 11" ist **aus der `viewBox`-Arithmetik des Quelltextes gerechnet**, mit einer **geschätzten** Zeichenbreite (0,53 em gemischt, 0,60 em Ziffern) und einer **geschätzten** Kartenbreite von 310 px. Eine tatsächliche Textbreite hängt von der aufgelösten `system-ui`-Schrift des Geräts ab und kann um 10–15 % danebenliegen. Solange es keinen Melder gibt, der `getBBox()` je `text` einsammelt und die Kästen paarweise schneidet, ist **jede** dieser Schwellen eine begründete Schätzung und kein Befund.
2. **Quelltextstellen und gerenderte Elemente sind zwei verschiedene Grundgesamtheiten.** 6 Quelltextstellen erzeugen über `.map()` die 264 bzw. 338 gemessenen Elemente. Keine der beiden Zahlen lässt sich ohne die Daten in die andere umrechnen, und diese Aufnahme hat keine Daten gelesen.
3. **Die Schirmzahlen sind fremd und die Stichprobe ist 12 Zeilen lang.** Sie stammen aus `scripts/_echtmengen_rohdaten.json` vom 27.09.; der Aufzeichner hat die Liste bei 12 Einträgen gekappt (`anzahl_klein` 264 bzw. 338, `klein` je 12). „Ausschließlich `text` in `svg`/`g`" ist ein Schluss aus **12 von 264** bzw. **12 von 338**, nicht aus allen. Dieselbe Datei führt die Ansicht `auswertungen` in beiden Breiten als **„nicht aussagekräftig"**.
4. **Mein Zähler kennt zwei Schreibweisen der Eigenschaft und zwei des Werts** — `fontSize` und `'font-size'`/`"font-size"`, blanke Zahl und `'10px'` in Anführungszeichen, Kommazahlen eingeschlossen. Geeicht ist er mit einem Köder je Schreibweise (`fontSize:8`, `fontSize:9.5`, `fontSize:"10px"`, `'font-size':11`, `"font-size":'9px'`, `style:{fontSize:7}` → gefunden `[8, 9.5, 10, 11, 9, 7]`) und einer Gegenprobe, die nicht treffen darf (`fontSizeXY:8`, `a.fontSize:9`, `fontSize:varX`, `fontSize:UI.fMeta` → leer). **Die bedingte Form fehlte in der ersten Fassung** und wurde erst im zweiten Durchgang nachgetragen — genau daher kommt die Differenz 56 → 63. Wenn es eine **vierte** Form gibt, die ich nicht kenne, meldet diese Aufnahme „kommt nicht vor", und das ist von einem echten Befund nicht zu unterscheiden.
5. **Eine Schriftgröße aus einer Variablen oder aus einer CSS-Klasse sieht mein Zähler überhaupt nicht.** `UI.fMeta` wird nicht aufgelöst; ich habe den Wert 12 von Hand an Zeile 3554 abgelesen. Eine `svg`-Stelle, die ihre Größe aus einer Zustandsgröße bezieht, wäre bei mir als „keine feste Größe" geführt.
6. **Die Kaskadenbehauptung ist nicht im Browser bewiesen.** Dass eine Autorenregel mit `!important` ein SVG-Präsentationsattribut schlägt, ist Lehrbuch, und die 12 Stichprobenzeilen bei 390 px mit **10 px** passen dazu. Belegt ist damit der **Effekt**, nicht der **Mechanismus**. Ebenso: dass der äußerste `svg` `overflow:hidden` hat und die 9. Legendenzeile deshalb **gar nicht** gezeichnet wird, ist aus der Vorgabe geschlossen, nicht am Schirm nachgesehen.
7. **Das Fahrtenbuch wurde nie mit Daten gemessen.** Dieselbe Messdatei führt „Flotte / Fuhrpark-GPS" in beiden Breiten als „nicht aussagekräftig" (2 bzw. 13 kleine Elemente). Alles, was hier über die Geschwindigkeitskurve steht — auch die 40–120 Punkte —, ist aus `_fzSpeedReihe` (Zeile 26587) **gelesen**, nicht **gezählt**. Der 10-Sekunden-Takt ist eine **Annahme** über den Tracker; die Datei sagt darüber nichts.
8. **Die Zahl der Marken der datenabhängigen Diagramme ist hier nicht gemessen.** Für `asMont`, `absPers`, `prjFort`, `fzTank`, `fzLiter`, `fzKm`, `fzSchaden` und die Tageskilometer nenne ich die **Regel** aus dem Quelltext und die **Saat** der fremden Messung (`monteure: 11`, davon 9 aktiv, `projects: 3`, `fahrzeuge: 21`, `werkzeuge: 300`). Die echte Produktionsmenge kann davon abweichen, und keine Abfrage ist dafür gelaufen.
9. **Der Umschalter ist nicht berücksichtigt.** Jedes der 15 Auswertungs-Diagramme lässt sich vom Nutzer auf jeden der fünf Typen stellen, und die Einstellung liegt in `chartCfg`. Alle Aussagen über „8 × hbar, 3 × donut …" gelten für die **Vorgabe**. Was ein Nutzer eingestellt hat, sieht diese Aufnahme nicht.
10. **Nicht angesehen, weil tabu:** Auth-Pfade, `_juprowaPush`/`_juprowaSanitize`, `.github/workflows/*`, die Kiosk-Hash-Schreibpfade `#planung`/`#monteure`/`#stempel`. Sollte dort ein weiteres `svg` mit Text stehen, ist es in dieser Zählung nicht enthalten — die Zählung der `svg`-Elemente lief allerdings über die **ganze** Datei und fand 8, davon 4 Symbole ohne `text`.
11. **Ich habe nichts geändert und nichts gebaut.** Kein `index.html`, kein `git add`, kein Commit, kein Lauf der App. Die Datei, über die ich urteile, ist ein Schnappschuss mit md5 `9d7d3ecd8083f45b216b11985be59a93`; ein anderer Agent schreibt parallel an `index.html`, und meine Zeilennummern können deshalb schon veraltet sein. Gegenlesen mit demselben md5.
