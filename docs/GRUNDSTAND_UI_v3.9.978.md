# Grundstand UI v3.9.978 — die Flächen, die nie jemand geöffnet hat

> Vorgänger: `GRUNDSTAND_UI_v3.9.973.md` („der Schriftboden gilt überall").
> Dieser Stand fügt zwei Flächen hinzu, über die vorher **niemand etwas sagen
> konnte**, und korrigiert einen Satz, der in jedem Grundstand seit Wochen
> stand.

## Die Zahlen

| | 390 px | 1440 px |
|---|---:|---:|
| Elemente unter **12 px** (44 Aufnahmen) | 0 | 0 |
| Tippziele unter **24 px** | 1 | 1 |
| Tippziele unter **44 px** | 1 | 1956 |
| Beschnitt (verlorener Inhalt) | 0 | 0 |
| Icon-Knöpfe ohne Namen | 0 | 0 |

**Das eine Element unter 24 px gehört nicht uns.** Es ist der Urheberhinweis
der Kartenbibliothek Leaflet (51.4×14, `div.leaflet-control-attribution > a`),
dessen Darstellung Teil der Lizenzbedingung der Kartendaten ist. Vor v3.9.976
waren es **50** in sechs Gruppen.

Dazu, und das ist neu:

| Geöffnete Fläche | Bereiche | <12 px | <24 px | ohne Namen |
|---|---:|---:|---:|---:|
| Hüllen-Überlagerungen | 4 | 0 | 0 | 0 |
| Inline-Bereiche (7 Ansichten) | 58 | 0 | 0 | 0 |

## 🔴 Der Satz, der korrigiert gehört

Jeder Grundstand endete mit *„keine geöffneten Dialoge. Ein erheblicher Teil
des Bestands ist damit ungemessen."* Das war ehrlich gemeint und **irreführend**.

`scripts/dialoge_erkunden.py` hat je Ansicht bis zu 40 Knöpfe geklickt und
gefragt, ob eine neue Überlagerung entsteht. Ergebnis: **vier Öffner, alle in
der Hülle** — Suchpalette, Benachrichtigungen, Sync-Fenster,
Foto-Warteschlange. Aus den Ansichten selbst **keine einzige**.

**Diese App benutzt Inline-Bereiche, keine Modale.** Was anderswo ein Dialog
wäre, schiebt sich in den Seitenfluss. Der ungemessene Teil war also nicht
„ein erheblicher Teil des Bestands", sondern zwei klar benennbare Flächen —
und beide sind jetzt gemessen.

## Was in den geöffneten Flächen steckte

**In den vier Überlagerungen:** zwei Knöpfe unter 24 px (der ESC der
Suchpalette, 42×22, und der ✕ des Sync-Fensters, 23×24). Beim Heben kam ein
dritter dazu, den die Messung gar nicht gesehen hatte — der Schließer der
Foto-Warteschlange ist zeichengleich. Gefunden hat ihn `safe_edit`, weil der
Anker zweimal traf.

**In den Inline-Bereichen:** 165 Elemente unter 24 px, darunter **136 allein
in der Dispo-Ansicht**, und — der schwerste Fund — **fünf namenlose Knöpfe**.

### 🔴 Die zwei Fehler, die aus v3.9.975 stammen

Beide von **mir** eingebaut, beide erst durch das Öffnen eines Bereichs
sichtbar:

1. **Die fünf Bewertungssterne wurden zu namenlosen Knöpfen.** Das
   Bauwerkzeug gab ihnen `role="button"`, weil sie ein `onClick` tragen, und
   keinen Namen dazu. Vorher war es vorlesbarer Text; danach fünf
   „Schaltflächen" ohne Inhalt. **Eine Rolle ohne Namen ist schlechter als
   gar keine Rolle.** Sie heißen jetzt „1 von 5" bis „5 von 5" — der Wert,
   den der Klick setzt.

2. **Ein Tab-Stopp, der drei Versionen lang nichts tat.** Der Ziehgriff eines
   Dispo-Blocks bekam Rolle, `tabIndex` und einen Tastenbehandler; sein
   `onClick` ist aber reines `stopPropagation`. Genau das Phantom, das der
   Auftrag ausschloss. Rolle und Behandler sind wieder weg.

**Drei Riegel zum Tastaturzugang standen dabei die ganze Zeit grün.** Sie
zählen die Anwesenheit von `tabIndex` und `onKeyDown` — und beides war ja da.
Gefunden hat es eine Messung, kein Riegel.

## Was dabei sonst herauskam

**Die Quelle der 22 px, zweimal vergeblich gesucht.** v3.9.974 hob
`input[type="checkbox"]` im `<style>`-Block auf 24 px, und das Kästchen blieb
bei 22×22. Ursache: eine **zweite Regel derselben Spezifität**, später im
Dokument, **in einem JavaScript-Template-Literal**. **CSS lebt in dieser Datei
an drei Orten** — `<style>`-Block, Template-Literale, Inline-Objekte. Wer
einen davon durchsucht, hat die Datei nicht durchsucht.

**Die Wochenplanung war der einzige harte Fall.** Ihre vier Zeilenknöpfe
(▲▼🗑✕) waren mit 8.4×14 px die kleinsten Bedienelemente des Bestands.
Nebeneinander auf je 24 px hätten sie 96 statt 43 px gebraucht — sicherer
Überlauf. Sie stehen jetzt als **2×2-Raster** (50×50) in einer Spalte von
54 px; gemessen: `roll=0, verl=0`.

## 🔴 Was ich selbst korrigiert habe

**Ich hatte zwei Knöpfe gemessen und über 25 geurteilt.** Aus zwei zu kleinen
Schließern mit derselben Hausform (`minHeight:isMob?40:0`) baute ich einen
Riegel, der diese Form *nirgends* mehr dulden wollte. Sie stand 25 mal da —
und über alle Schreibweisen gezählt **110 mal in 17 Formen**. Diesmal
Schreibweisen von **Zahlen**, nicht von Anführungszeichen.

Die Sperre ist **ersatzlos entfallen**, nicht weicher gemacht: die Form ist
gar nicht der Mangel. Das Verzeichnis führt jetzt
`scripts/hausform_mindestmass.py` — mit Ködern je Schreibweise und
ausdrücklich **ohne Urteil**.

## 🔴 Was dieser Grundstand NICHT abdeckt

* **1954 Tippziele zwischen 24 und 44 px**, alle bei 1440 px. 44 px ist die
  Marke für einen **Finger**; am Schreibtisch mit Maus ist die Lücke eine
  Gestaltungsentscheidung, keine Messung → **Frage 28**.
* **Die Inline-Bereiche der übrigen Ansichten.** Gemessen sind sieben von 22.
* **Inline-Bereiche bei 390 px.** Der Durchgang misst bei 1440 px.
* **Bereiche hinter einem zerstörenden Knopf.** Die Sperrliste des Melders
  fällt zur sicheren Seite: lieber ein Bereich ungemessen als eine Messreihe,
  die sich selbst zerstört. Betroffen sind die Export- und Druckwege.
* **Bereiche hinter zwei Klicks.** Gemessen wird ein Klick ab Ruhezustand.
* **Die Dauer eines Dispo-Blocks ist per Tastatur nicht änderbar.** Die
  Lücke ist jetzt ehrlich (kein Phantom mehr), aber sie ist da → **Frage 29**.
* **Die `pt`-Größen im Druck- und Export-HTML.** Papier, nicht Schirm.
* **Kein Melder für Überlappung.** Die Ausdünnung in `SvgLine` ist gerechnet,
  nicht am Schirm gemessen.

## Werkzeuge

```
python scripts/echtmengen_messen.py              # 44 Aufnahmen
python scripts/dialog_messen.py                  # die vier Überlagerungen
python scripts/inline_bereiche_messen.py <ansicht ...>
python scripts/hausform_mindestmass.py           # Verzeichnis, kein Urteil
python scripts/kosten_24px_messen.py             # was kostet das Heben?
python scripts/torkette.py                       # die sieben Tore
```

Berichte: `docs/befunde/UNTER24.md` · `docs/befunde/DIALOGE.md` ·
`docs/befunde/INLINE_BEREICHE.md` · `docs/befunde/TOTE_WAHLMUSTER.md`
