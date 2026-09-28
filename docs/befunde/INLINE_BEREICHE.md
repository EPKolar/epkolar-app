# Die Inline-Bereiche — der Rest des blinden Flecks (28.09.2026)

> `docs/befunde/DIALOGE.md` hat gezeigt: **diese App hat fast keine Modale.**
> Als echte Überlagerung gibt es genau vier, und alle vier gehören zur Hülle.
> Was anderswo ein Dialog wäre — ein Formular, eine Detailansicht, eine
> Auswahl — schiebt sich hier **inline** in den Fluss der Seite.
>
> Die Messreihe misst Ansichten im **Ruhezustand**. Alles, was erst nach einem
> Klick erscheint, war nie gemessen. Das ist die größere Hälfte des blinden
> Flecks, und dieser Befund öffnet sie.

## Das Werkzeug

```
python scripts/inline_bereiche_messen.py [ansicht ...]
```

Es klickt je Ansicht bis zu 30 **verschiedene** Bedienelemente **innerhalb des
Inhaltsbereichs**, misst danach mit denselben Meldern wie die Messreihe und
setzt vor jedem Klick den Zustand zurück.

**Zwei Arten von Bereich**, und beide zählen:

* **ergänzend** — etwas klappt auf und legt Elemente dazu (Zuwachs ≥ 5).
* **ersetzend** — Meister-Detail: die Karte öffnet die Detailansicht *an Ort
  und Stelle* und ersetzt die Liste. Erkannt am **Erhalt**: weniger als 80 %
  der Knopf-Beschriftungen des Ruhezustands sind noch da.

Bei einem **ersetzenden** Bereich wird der **absolute** Stand beurteilt, nicht
die Differenz — wenn der Ruhezustand verschwindet, heißt „unter 12 px: +0"
nicht „nichts Kleines dazugekommen", sondern „zufällig gleich viele".

## Ergebnis: Fahrzeugansicht

**20 Bereiche** — 18 Fahrzeug-Detailansichten, ein Batch-Fenster, ein
Erfassungsformular. Über alle:

| | |
|---|---:|
| Schrift unter 12 px | **0** |
| Knöpfe ohne Namen | **0** |
| Tippziele unter 24 px | **2** |

Die beiden sind in v3.9.977 gehoben:

```
Favoritenstern der Detailansicht   16.7x27    -> minWidth 24
Zulassungsschein-Zeile             1340x19.5  -> minHeight 24
```

Der Stern ist der **dritte** seiner Art. v3.9.976 hat zwei gehoben — Liste und
Karte; dieser saß hinter einem Klick und war damit für jedes Werkzeug
unsichtbar, das nur den Ruhezustand misst.

## Ergebnis: sechs weitere Ansichten

**38 Bereiche** in mitarbeiter, werkzeuge, as_liste, zeit, planung, abwesend.
Schrift unter 12 px: **0** in allen. Gefunden wurden:

| Ansicht | Bereich | Fund | Kur (v3.9.978) |
|---|---|---|---|
| werkzeuge | drei Formular-Bereiche | 5 × `★` 13.3×24, **namenlos** | Name je Wert + 24×24 |
| as_liste | 🗓 Dispo | **136** unter 24 px | vier Knopfarten gehoben |
| mitarbeiter | + Neuer Mitarbeiter | 16 × Kästchen 14×14 | 24×24 |
| abwesend | 📊 Übersicht | 4 × Namenszeile 120×18 | minHeight 24 |
| abwesend | 🗓️ Team-Timeline | 3 × `6/12/26 Wo` 49.8×22 | minHeight 24 |
| planung | Wochenwechsel | `KW40` 46.8×20 | minHeight 24 |

Nach der Kur ist in allen sechs Bereichen **nichts** mehr unter 24 px —
außer einem, siehe unten.

### 🔴 Der wichtigste Fund ist einer über mich selbst

Die fünf `★` sind eine **Bewertungsanzeige**, und sie sind erst durch
**v3.9.975** zu Knöpfen geworden: mein Bauwerkzeug gab ihnen `role="button"`,
weil sie ein `onClick` tragen — und keinen Namen dazu. **Eine Rolle ohne Namen
ist für eine Vorlesehilfe schlechter als gar keine Rolle**: vorher war es
Text, danach ein Knopf, der „Schaltfläche" heißt und sonst nichts.

Sie heißen jetzt „1 von 5" bis „5 von 5" — der **Wert**, den der Klick setzt,
nicht das Zeichen.

### 🔴 Und ein Phantom, drei Versionen lang

Der Ziehgriff eines Dispo-Blocks bekam in v3.9.975 ebenfalls `role="button"`,
`tabIndex` und einen Tastenbehandler. Sein `onClick` tut aber **nur**
`stopPropagation` — es verhindert, dass ein Klick auf den Griff den
Arbeitsschein öffnet. Die eigentliche Funktion (ziehen = Dauer ändern) hängt
an `onPointerDown` und hat gar keinen Tastenweg.

Ergebnis: **ein Tab-Stopp, der nichts tut.** Genau das Phantom, das der
Auftrag ausgeschlossen hat — *lieber ein fehlender Zugang als ein Phantom in
der Tab-Reihenfolge*.

**Warum es durchkam: eine zweite Schreibweise.** Mein Klassifizierer schließt
reine `stopPropagation`-Behandler aus und hat 29 von 30 richtig erwischt.
Dieser eine steht als `function(e){…}` statt als Pfeilfunktion da. Nach der
Verbreiterung des Musters auf die **Form** stellte sich heraus: es waren
**zwei**, nicht einer — die Zahl der Elemente ohne Tastaturzugang fällt von 69
auf 68, **nicht durch eine Kur, sondern weil sie vorher falsch war**.

Der Griff hat Rolle, `tabIndex` und Behandler wieder verloren. Dass sich die
Dauer per Tastatur gar nicht ändern lässt, ist ein eigener Mangel und gehört
in die offenen Entscheidungen — nicht in einen Tab-Stopp, der so tut als ob.

Zwei neue Riegel decken beide Hälften ab:
`tests/test_phantom_tabstopp_v978.py` (kein gebauter Behandler läuft leer,
mit Köder je Schreibweise) und die verbreiterte `NUR_STOP` in
`tests/test_anklickbar_ohne_tastatur_v964.py` (fünf Köder, eine Gegenprobe).

### Die eine Ausnahme: der Ziehgriff selbst

Er ist **242.6×10 px** und bleibt es. Seine Höhe ist die Griffzone am unteren
Rand eines Zeitblocks, dessen Höhe die **Dauer** kodiert; ein 24 px hoher
Griff würde auf einem 40-Minuten-Block ein Viertel der Fläche verdecken und
den Block selbst unklickbar machen. Die Größe ist hier Teil der Funktion.

## 🔴 Sechs Anläufe, und fünfmal sah der Fehlgriff aus wie ein Ergebnis

Dieses Werkzeug ist sechsmal umgebaut worden. Jeder Zwischenstand hätte sich
als Befund lesen lassen. Alle fünf Fehlformen stehen jetzt im Quelltext an der
Stelle, an der sie zugeschlagen haben — nicht als Merksatz, sondern als
Begründung für die Zeile, die sie behebt.

**1. Zu große Grundgesamtheit.** Der erste Lauf meldete 23 „Bereiche" in der
Fahrzeugansicht, darunter „🚐 Fahrzeuge", „🔧 Werkzeuge", „👷 Mitarbeiter".
Das sind **Navigationsknöpfe** — die andere Ansicht hat eben mehr Elemente.

**2. Falsche Wurzel.** Eingeengt auf `.main-pad`, aber die *Kandidaten* kamen
weiter aus dem ganzen Dokument. Klicks auf die Hülle ergaben `+0` (die
Überlagerungen liegen außerhalb des Inhaltsbereichs), Klicks auf die
Reiterzeile einen vollständigen Austausch. Beides sah aus wie ein Befund.
*Dieselbe Fehlerform wie beim Dialog-Hintergrund, zwei Stunden vorher.*

**3. Position statt Beschriftung.** Der Melder meldete für **vierzehn**
verschiedene Knöpfe hintereinander exakt `+0` in jeder Spalte. Vierzehn
identische Nullen sind keine Eigenschaft der App, sondern die Signatur eines
Messfehlers: die Liste der Klickbaren war *einmal* erhoben, und nach jedem
Neuaufbau zeigte derselbe Index auf ein anderes Element.

**4. Neu navigieren ist kein Zurücksetzen — und neu laden auch nicht.** Die
ersten beiden Knöpfe der Fahrzeugansicht sind `☰` und `⊞`, Listen- gegen
Kachelansicht. Diese Wahl wird **gespeichert** und überlebt beides; 19 von 27
Knöpfen waren danach „nicht mehr gefunden". Erst ein eigener Browser-Kontext
je Klick räumt `localStorage` weg. Das kostet zehn Sekunden je Knopf und ist
der Preis dafür, dass zwei Messungen überhaupt vergleichbar sind.

**5. Nur eine Art von Bereich gekannt.** Ich suchte nach *Zuwachs*. In dieser
App ist das die seltenere Form. Die häufigere ist Meister-Detail — und der
Melder sah sie **18 mal** und verbuchte sie als „Navigation". Dass es keine
sein *kann*, ist strukturell: geklickt wird nur innerhalb des Inhaltsbereichs,
und dort steht kein Navigationsknopf. Der Eimer hieß falsch, nicht die
Messung.

### Was den Lauf gerettet hat

Die Selbstprobe des Melders:

> 🔴 KEIN einziger Bereich gefunden. Das ist kein Ergebnis, das ist ein
> misslungener Griff.

Sie hat bei **jedem** der fünf Fehlstände angeschlagen. Ohne sie wäre
„0 Bereiche" fünfmal als Befund durchgegangen — und „die Inline-Bereiche sind
sauber" wäre in den Grundstand gewandert, ohne dass je einer geöffnet worden
wäre.

## Weitere Schutzvorrichtungen im Melder

* **Sperrliste für zerstörende Knöpfe** (löschen, senden, export, drucken,
  speichern …) mit **sieben Eichfällen, davon drei Gegenproben**. Eine
  Sperrliste, die nie greift, sieht aus wie eine, die schützt.
* **Belegter Ruhezustand:** trägt der Inhaltsbereich weniger als drei
  verschiedene Knopf-Beschriftungen, wird **nicht** gemessen — sonst wäre jeder
  Erhalt 0 und jeder Klick ein „Bereich".
* **Kein Treffer beim Wiederfinden** wird als *„nicht geklickt"* gebucht, nicht
  als *„öffnet nichts"*.
* **Strukturprobe:** der Eimer „navigiert" **muss** leer bleiben. Ist er je
  gefüllt, greift die Einengung auf den Inhaltsbereich nicht mehr — und dann
  misst der Melder wieder fremde Ansichten als „Bereiche".

## Was weiterhin nicht gemessen ist

* **Bereiche hinter einem zerstörenden Knopf.** Die Sperrliste fällt zur
  sicheren Seite: lieber ein Bereich ungemessen als eine Messreihe, die sich
  selbst zerstört. Betroffen sind unter anderem die Export- und
  Druckdialoge.
* **Bereiche hinter zwei Klicks.** Gemessen wird ein Klick ab Ruhezustand.
* **390 px.** Der Lauf misst bei 1440 px.
* **Mehr als 30 verschiedene Bedienelemente je Ansicht.**

Rohdaten: `docs/befunde/INLINE_BEREICHE.json`.
