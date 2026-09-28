# Die erste Dialogmessung — 28.09.2026

> Jeder Grundstand seit Wochen endete mit dem Satz **„keine geöffneten
> Dialoge"**. Das war ehrlich und es war eine Lücke: die Messreihe misst
> Ansichten im Ruhezustand. Modale, Schubladen und Detailfenster waren nie
> erfasst. Dieser Befund schließt die Lücke — teilweise, und er sagt genau,
> welcher Teil offen bleibt.

## 1. Was überhaupt ein Dialog ist — und was die App stattdessen tut

`scripts/dialoge_erkunden.py` hat je Ansicht bis zu 40 Knöpfe geklickt und
danach gefragt, ob eine **neue** Überlagerung entstanden ist. Merkmal einer
Überlagerung: `position: fixed`, mehr als ein Drittel Schirmfläche, sichtbar,
im Ruhezustand nicht da.

**Ergebnis: vier Öffner je Ansicht, und alle vier gehören zur HÜLLE.**

| Öffner | Überlagerung |
|---|---|
| `🔍 ⌘K` | Suchpalette |
| `🔔` | Benachrichtigungen |
| `12 Server ❌` | Sync-Fenster |
| `📷` | Foto-Warteschlange |

Aus den Ansichten selbst kam **keine einzige**. Das ist kein Messfehler,
sondern die Bauweise: **die App benutzt Inline-Bereiche, keine Modale.** Ein
Formular schiebt sich in den Fluss der Seite, es legt sich nicht darüber.

Damit ändert sich die Bedeutung des alten Satzes. Er las sich wie „ein großer
Teil des Bestands ist ungemessen". Richtig ist: der größte Teil dessen, was
man anderswo Dialog nennen würde, **steht in den Ansichten und wird von der
Messreihe längst mitgemessen** — nur eben erst, wenn er aufgeklappt ist. Was
wirklich fehlte, waren die vier Überlagerungen der Hülle.

## 2. Was in den vier Überlagerungen steht

`scripts/dialog_messen.py` misst mit **denselben Meldern** wie die Messreihe,
aber innerhalb der obersten Überlagerung. Bei 1440 px:

| Überlagerung | Elemente | unter 12 px | unter 24 px | Knöpfe ohne Namen |
|---|---:|---:|---:|---:|
| Suchpalette | 25 | 0 | 0 | 0 |
| Benachrichtigungen | 39 | 0 | 0 | 0 |
| Sync-Fenster | 18 | 0 | 0 | 0 |
| Foto-Warteschlange | 12 | 0 | 0 | 0 |

Beim **ersten** Lauf standen dort zwei Funde:

```
Suchpalette   ESC  42x22   padding 4px 10px bei 12 px Schrift
Sync-Fenster  ✕    23x24   padding 0 4px, minHeight ausdrücklich 0
```

Beide sind in v3.9.976 gehoben (`minHeight: 24` bzw. `minWidth: 24`, jeweils
nur am Schreibtisch — am Telefon standen sie ohnehin auf 40).

## 3. 🔴 Zwei eigene Fehlgriffe, die wie Ergebnisse aussahen

**(a) Der erste Messer griff den Hintergrund.** Er nahm das *größte* feste
Element. Das ist die Abdunklung hinter dem Fenster; sie hat keine Kinder mit
Text. Gemeldet wurden **„0 Elemente"** für zwei von drei Überlagerungen — von
einem makellosen Ergebnis nicht zu unterscheiden. Korrigiert: gewählt wird das
feste Element mit den **meisten texttragenden Nachfahren**, und ein leeres
Ergebnis wird ausdrücklich verweigert statt als Null gemeldet.

**(b) Der dritte Knopf, den niemand gesucht hatte.** Beim Heben traf der Anker
des Sync-Schließers **zweimal**. `safe_edit` verweigerte den Schnitt und nannte
beide Zeilen: der Schließer der **Foto-Warteschlange** ist zeichengleich und
hatte denselben Mangel — nur hatte die Messung diese Überlagerung gar nicht
geöffnet. Ohne die Weigerung wäre die Hälfte des Mangels stehen geblieben, und
die Messung hätte es nicht gemerkt. Die Foto-Warteschlange steht seither in
der Liste.

## 3b. 🔴 Der Riegel hatte recht, ich hatte unrecht — und dann war auch das noch zu eng

Meine erste Fassung des Riegels verlangte, die Hausform
`minHeight:isMob?40:0` dürfe **nirgends** mehr vorkommen. Ich hatte geglaubt,
sie stehe nur an den zwei Schließern. Sie stand **25 mal** da.

Dann hielt ich 23 (die übrigen) für die Grundgesamtheit — bis beim Suchen nach
einem anderen Knopf `isMob?44:0` auftauchte, eine Schreibweise, die mein
Muster nicht kannte. Über alle Formen gezählt: **110 Vorkommen in 17
Schreibweisen.** Mein Riegel hatte 87 davon nicht gesehen und dabei ausgesehen,
als hätte er die Datei vermessen.

**Das ist kein Grund, die Prüfung weicher zu machen, bis sie grün wird.** Es
ist ein Grund, die *Behauptung* zu verwerfen: die Form ist gar nicht der
Mangel — der Mangel ist die gerenderte Größe, und die sieht nur der Browser.
Die Sperre ist deshalb ersatzlos entfallen, das Verzeichnis führt jetzt
`scripts/hausform_mindestmass.py` mit Ködern je Schreibweise und ohne Urteil.

Was die Messung tatsächlich ergab, steht in **`docs/befunde/UNTER24.md`**:
50 Bedienelemente unter 24 px über 44 Aufnahmen, in sechs Gruppen, fünf davon
in v3.9.976 gehoben.

## 4. Was weiterhin NICHT gemessen ist

* **Die Inline-Bereiche der Ansichten selbst.** Sie sind Teil der Ansicht und
  werden gemessen, *wenn sie offen sind* — die Messreihe klappt sie nicht auf.
  Das ist die verbleibende Lücke, und sie ist größer als die geschlossene.
* **Die Kamera-Überlagerung im echten Betrieb.** Sie öffnet ohne Kamerarecht
  nur als Warteschlangenfenster.
* **390 px.** Die Messung oben lief bei 1440 px. Am Telefon greift die
  Grobzeiger-Regel, die Tippziele ohnehin auf 44 px hebt.

## 5. Werkzeuge

```
python scripts/dialoge_erkunden.py      # welche Öffner gibt es
python scripts/dialog_messen.py         # was steht drin
```

Berichte: `docs/befunde/DIALOGE.json`, `docs/befunde/DIALOG_MESSUNG.json`.
Riegel: `tests/test_dialogknoepfe_v976.py`.
