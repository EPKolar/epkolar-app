# Tippziele unter 24 px — gefunden, gehoben, gemessen (28.09.2026)

Gemessen mit `scripts/echtmengen_messen.py`: 22 Ansichten × 390 und 1440 px =
**44 Aufnahmen**, an realitätsnahen Mengen (300 Werkzeuge, 185 Arbeitsscheine,
21 Fahrzeuge, 11 Monteure). Alle fünf Melder haben ihre Köder angeschlagen,
Tor A und Tor B tragen.

## Das Ergebnis vorweg

**50 Bedienelemente unter 24 px — nach der Kur noch 2**, und die beiden sind
derselbe fremde Verweis bei 390 und 1440 px (Leaflet, siehe unten). Gemessen
vorher und nachher mit demselben Werkzeug und derselben Saat:

```
vorher   1440 px : 50 unter 24 px   in sechs Gruppen
nachher  1440 px :  1 unter 24 px   (Leaflet)
nachher   390 px :  1 unter 24 px   (Leaflet)
<12 px           :  0 in allen 44 Aufnahmen, vorher wie nachher
Beschnitt (verl) :  0 in allen 44 Aufnahmen, vorher wie nachher
Querroller       :  unveraendert — kein neuer, keiner weggefallen
```

Die Zahl der Tippziele unter **44** px ist mit **1956** gleich geblieben: die
gehobenen Elemente sind aus dem Bereich unter 24 in den Bereich 24–44
gewandert, es ist keines dazugekommen und keines verschwunden.

## Der Befund

**1956 Tippziele unter 44 px, davon 50 unter 24 px — alle 50 bei 1440 px.**
Bei 390 px war es **eines**, und das ist keines von uns (siehe Leaflet).

Der Unterschied ist keine Zufälligkeit: bei 390 px greift
`@media (pointer: coarse), (max-width: 768px)`, die jedes Bedienelement auf
44 px hebt. Am Schreibtisch greift sie nicht — und dort stand nichts an ihrer
Stelle. **Die 24-px-Untergrenze gilt unabhängig vom Zeigegerät.**

Keine einzige Stichprobe war gekappt (die Melder führen bis zu 60 Beispiele je
Aufnahme), die 50 sind also vollständig und nicht eine Untergrenze.

## Die sechs Gruppen

| Ansicht | Element | vorher | Kur | Kosten |
|---|---|---|---|---|
| werkzeuge | Kästchen in der Kopfzeile | 22×22 | zweite CSS-Regel 22 → 24 px | keine |
| fahrzeuge | Favoritenstern ☆ (Liste **und** Karte) | 23×32 | `minWidth: 24` | keine |
| zeit | ✏️ / ✕ am Eintrag | 24.5×22 / 17.8×22 | `inline-flex`, 24×24 | +2 px je Zeile |
| zeit | Tagesknöpfe des Stundenzettels | ~68×22 | `minHeight: 24` | keine |
| auswertungen | Diagramm-Schalter | 36×20 | Hülle 24, Knauf 20 | keine |
| planung | ▲ ▼ 🗑 ✕ der Zeile | 10.3×14, 8.4×14, 13.8×14 | **2×2-Raster** | Spalte 44 → 54 px |
| flotte | Leaflet-Urheberhinweis | 51.4×14 | **keine** — fremd | — |

### 🔴 Die Wochenplanung war der einzige harte Fall

Die vier Zeilenknöpfe waren mit 8.4×14 px die **kleinsten Bedienelemente des
ganzen Bestands**. Sie nebeneinander auf je 24 px zu setzen hätte 96 statt
43 px gebraucht — und an dieser Zelle stand bereits ein Messprotokoll: die
Schrifthebung von 9 auf 12 px (v3.9.967) hatte die Tabelle 7 px quer rollen
lassen, zurückgewonnen durch 8 px Polsterung. **Die Zelle lag am Anschlag.**

Deshalb stehen sie jetzt als **2×2-Raster**: 50×50 px statt 43×14, die Höhe
kostet nichts (die Zeile ist ohnehin 38 px hoch und die Tabelle rollt
senkrecht), die Breite kostet 11 px, die aus der Bemerkungsspalte kommen
(14 % → 12 %).

Gemessen, nicht gerechnet:

```
mit 48 px Raster, Spalte 44:  roll=1, Überschuss 5 px (1403 gegen 1398)
mit 50 px Raster, Spalte 54:  roll=0, verl=0
```

Der Zwischenstand mit Spalte 50 rollte noch — deshalb 54.

**Der Abstand des Löschknopfs ist nicht verschwunden, er ist umgezogen.**
v3.9.967 gab dem ✕ als einzigem der vier eine Polsterung, mit Begründung: *ein
zerstörender Knopf, der die Nachbarn berührt, wird verklickt.* Mein erstes,
lückenloses Raster stellte ihn wieder Kante an Kante an 🗑 und ▼. Der Abstand
steckt jetzt als `gap: 2` im Raster. Die Begründung gilt unverändert, und der
Riegel `test_b6_stufe3_v944` prüft sie an dieser Stelle mit.

### 🔴 Die Quelle der 22 px — zweimal vergeblich gesucht, jetzt gefunden

v3.9.974 hob `input[type="checkbox"]` im `<style>`-Block von 20 auf 24 px, und
das Kästchen der Werkzeugansicht blieb bei **22×22**. Der Riegel las den
`<style>`-Block, fand 24 und war grün.

Die Ursache war eine **zweite Regel derselben Spezifität**, später im Dokument,
**in einem JavaScript-Template-Literal** (sie trägt `${V.ac}`):

```
input[type="checkbox"]{width:22px;height:22px;accent-color:${V.ac};cursor:pointer}
```

Wer nur den `<style>`-Block durchsucht, findet sie nie — und meldet „die Regel
steht auf 24", während das Kästchen 22 ist. Dieselbe Fehlerform wie bei den
`!important`-Schriften in v3.9.965/966, nur an einer anderen Stelle versteckt.

### Die eine Ausnahme: Leaflet

Bei 390 **und** 1440 px steht in der Flottenansicht ein Verweis von 51.4×14 px:
der Urheberhinweis der Kartenbibliothek
(`div.leaflet-control-attribution > a`, geladen von
`cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/`). Er gehört nicht zu dieser
App, seine Darstellung ist Teil der Lizenzbedingung der Kartendaten, und ihn
zu vergrößern hieße, in eine fremde Komponente hineinzugreifen.

Die Ausnahme steht als **Prüfung**, nicht als Satz in einem Kommentar: fällt
Leaflet weg, wird der Riegel rot und die Ausnahme gehört gelöscht.

## 🔴 Was dabei über meine eigenen Riegel herauskam

Ich hielt die Hausform `minHeight: isMob ? 40 : 0` für den Mangel und baute
einen Riegel, der sie nirgends mehr dulden wollte. Zwei Fehler übereinander:

1. Ich hatte **zwei** Knöpfe gemessen und über alle geurteilt. Die Form stand
   nicht zweimal da, sondern **23 mal**.
2. Dann hielt ich 23 für die Grundgesamtheit — bis beim Suchen nach einem
   anderen Knopf `isMob?44:0` auftauchte. Über alle Formen gezählt: **110
   Vorkommen in 17 Schreibweisen.** Mein Riegel hatte 87 davon nicht gesehen
   und dabei ausgesehen, als hätte er die Datei vermessen.

Und die Messung sagt: **die Form ist gar nicht der Mangel.** Die allermeisten
der 110 Stellen sind groß genug, weil Inhalt und Polsterung sie tragen — nur
50 Elemente im ganzen Bestand lagen unter 24 px, und die meisten davon tragen
die Form gar nicht.

Der Mangel ist die **gerenderte** Größe, und die sieht nur der Browser. Das
Verzeichnis der Hausform führt deshalb `scripts/hausform_mindestmass.py` — mit
Ködern je Schreibweise, drei Gegenproben, und dem ausdrücklichen Hinweis, dass
es **kein Urteil** fällt. Bericht: `docs/befunde/HAUSFORM_MINDESTMASS.json`.

## Was weiterhin offen ist

* **1954 Tippziele zwischen 24 und 44 px**, alle bei 1440 px. Das ist ein
  Schreibtisch-Befund; 44 px ist die Berührungsmarke, nicht die Mausmarke. Ob
  sie gehoben werden sollen, ist eine Gestaltungsentscheidung, keine Messung.
* **Die Inline-Bereiche der Ansichten.** Sie werden gemessen, wenn sie offen
  sind — die Messreihe klappt sie nicht auf. Siehe `docs/befunde/DIALOGE.md`.

## Werkzeuge

```
python scripts/echtmengen_messen.py            # 44 Aufnahmen
python scripts/echtmengen_messen.py --nur planung
python scripts/dialog_messen.py                # die vier Überlagerungen
python scripts/hausform_mindestmass.py         # Verzeichnis, kein Urteil
```

Riegel: `tests/test_dialogknoepfe_v976.py`, `tests/test_b6_stufe3_v944.py`.
