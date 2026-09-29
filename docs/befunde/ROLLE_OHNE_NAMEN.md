# `role="button"` ohne Namen — neun Fälle, alle aus v3.9.975 (28.09.2026)

> **Eine Rolle ohne Namen ist für eine Vorlesehilfe schlechter als gar keine
> Rolle.** Vorher war es Text, danach heißt das Element „Schaltfläche" und
> sonst nichts.

## Wie es dazu kam

v3.9.975 hat 41 anklickbaren Flächen Tastaturzugang gegeben. Das Bauwerkzeug
nahm jede Stelle mit einem `onClick`, gab ihr `tabIndex`, einen
Tastenbehandler und — wo erlaubt — `role="button"`. Der Ansatz war richtig und
ist gemessen worden.

**Was fehlte: die Frage nach dem Namen.** Wer eine Rolle vergibt, schuldet
einen Namen. Neun Stellen hatten keinen.

## Die neun Fälle

| Fundort | Element | Kur |
|---|---|---|
| Werkzeug-Formular | 5 × `<span role=button>★</span>` (Bewertung 1–5) | Name je Wert: „1 von 5" … „5 von 5" |
| Mitarbeiter-Ansicht | 3 × `<span role=button>⭐</span>` (Bewertung 1–3) | Name je Wert, **Rolle nur wenn bedienbar** |
| Hülle | 3 × Hintergrundfläche der Überlagerungen | **Name ergänzt**, Rolle bleibt |

### Die drei Hintergrundflächen — und eine Korrektur an mir selbst

Sie sind `position: fixed; inset: 0`, also **bildschirmfüllend** (1440×880).
Als namenlose „Schaltfläche" angekündigt sind sie für eine Vorlesehilfe ein
riesiges Nichts, und sie stehen als **erster Tab-Stopp** im Weg, sobald eine
Überlagerung offen ist.

🔴 **Mein erster Schluss war: die Rolle muss weg. Das war zu grob, und drei
Prüfungen haben ihn gestoppt.**

```
test_modal_backdrop_notif_has_role
test_modal_backdrop_photoq_has_role
test_modal_backdrop_sync_has_role
```

Sie verlangen `role="button"` + `tabIndex:0` an genau diesen Stellen — eine
**ausdrückliche Entscheidung** des Barrierefreiheits-Durchgangs v3.8.88: der
Klick daneben soll auch mit der Tastatur gehen.

**Der Fehler war nie die Rolle, sondern der fehlende Name.** Wer eine Rolle
vergibt, schuldet einen Namen; beides zusammen ist richtig, die Rolle allein
ist schlechter als nichts. Die Rolle bleibt also, und jeder Hintergrund sagt
jetzt, was er schließt — dieselbe Bauform, die die Mehr-Menü-Fläche daneben
längst trägt („Mehr-Menü schließen").

**Und das ist der Unterschied zwischen einem überholten Zeugen und einer
übersehenen Entscheidung.** An diesem Tag habe ich dreimal einen Zeugen
getauscht, weil er einen ersetzten Mechanismus festnagelte. Hier war es
anders: die Prüfungen hatten recht, ich kannte die Entscheidung nicht. Sie
bleiben unverändert.

Gemessen nach der Korrektur: alle drei Überlagerungen schließen weiterhin
beim Klick auf den Hintergrund (1 → 0 Überlagerungen), und Escape schließt
sie ebenfalls (globaler Behandler seit v3.9.41).

### Die Bewertung 1–3 war zusätzlich ein Phantom

Ihr `onClick` ist `editable ? … : null` — die **Rolle stand unbedingt da**.
Bei `editable === false` war es ein Knopf, der nichts tut: dasselbe Phantom
wie beim Ziehgriff der Dispo, nur an einer zweiten Stelle. Rolle, `tabIndex`
und Name hängen jetzt an derselben Bedingung wie die Wirkung.

## 🔴 Warum kein Riegel das finden konnte

`code_scan.knopf_stellen` findet **jedes `<button>`**, `hat_namen` prüft den
Namen. Beides ist geeicht und hat 17 namenlose Knöpfe gefunden. Und beides ist
hier **prinzipiell blind**: seine Grundgesamtheit ist `button`. Ein
`<span role="button">` liegt außerhalb — egal wie viele Schreibweisen der
Abtaster kennt.

Das ist nicht mehr „zu kleines Alphabet", das ist ein **blindes Messgerät**:
es misst einwandfrei, nur eine andere Menge, und eine Abwesenheit darin belegt
nichts.

Die fünf `★` fand eine **Messung**, die einen Bereich geöffnet hat
(`inline_bereiche_messen.py`). Die vier übrigen fand der neue Quelltext-Melder
`scripts/rolle_ohne_namen.py` — drei davon hätte keine Messung je erreicht,
weil sie nur existieren, solange eine Überlagerung offen ist.

## 🔴 Der Melder hat sich zweimal selbst korrigiert

Beide Zwischenstände sahen nach einem Ergebnis aus.

**Erste Fassung: Literale zählen.** Eine Sortier-Kopfzeile

```
, h.l, h.c?pfeil(h.c):""
```

galt als namenlos. Der Name steht in der **Variablen** `h.l`; das einzige
Literal ist das leere aus dem anderen Zweig, und weil es keine Buchstaben
trägt, war das Element „namenlos". Genau die Form, an der ich am 27.09. schon
zweimal falsch lag — zwei von drei „namenlosen Emoji-Knöpfen" waren keine.

**Zweite Fassung: aufgeben, sobald etwas unbekannt ist.** Damit wurde

```
, "Nummer", pfeil("nummer")
```

zu „muss ein Mensch ansehen". Der zugängliche Name ist die **Verkettung aller
Kinder** — ein wortführendes Literal genügt. Aus 7 unsicheren wurden **55**,
und eine Liste, die niemand mehr durchsieht, ist so wertlos wie eine falsche
Null.

**Jetzt monoton:** ein bekanntes Wort → benannt (sicher); sonst etwas
Unbekanntes → unsicher (ansehen); sonst → namenlos (Befund). Beide Fehlalarme
stehen als Köder im Melder, zusammen mit elf weiteren — 13 Eichfälle, davon
zwei Gegenproben.

## Der Stand

```
role="button" auf Nicht-Knöpfen : 102
  🔴 NAMENLOS : 0   (vor der Kur: 9)
  ❓ UNSICHER : 38
  🟢 BENANNT  : 64
```

**Die 38 unsicheren sind kein Befund.** Der zugängliche Name wird aus dem
gesamten Teilbaum berechnet; ein `div` mit Rolle, das Elemente mit Text
enthält, ist benannt — und diesen Teilbaum sieht der Melder nicht. Die Zahl
ist im Riegel festgeschrieben, damit sie nicht unbemerkt wächst und ein
echter Fall darin verschwindet.

## Werkzeuge

```
python scripts/rolle_ohne_namen.py
```

Riegel: `tests/test_rolle_ohne_namen_v979.py`.
Verwandt: `tests/test_phantom_tabstopp_v978.py` (kein gebauter
Tastenbehandler läuft leer).
