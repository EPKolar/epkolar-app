# -*- coding: utf-8 -*-
"""Erzeugt `docs/befunde/BEDIENELEMENTE_124.md` - die Einordnung, je eine Zeile.

Der Auftrag verlangt ausdruecklich eine Zeile Begruendung JE STELLE. Bei 124
Stellen ist eine ERZEUGTE Tabelle die einzige Form, die nachpruefbar bleibt:
wer sie anzweifelt, laesst dieses Skript neu laufen und vergleicht.

(Der Name `bedienelemente_bericht.py` war schon vergeben - dort liegt der
Bericht ueber Bedienelemente OHNE NAMEN vom 27.09. Zwei verschiedene Fragen,
zwei Dateien.)
"""
import io
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
import bedienelemente_klassen as K  # noqa: E402

WURZEL = os.path.dirname(HIER)
ZIEL = os.path.join(WURZEL, "docs", "befunde", "BEDIENELEMENTE_124.md")

KOPF = """# Die anklickbaren Nicht-Knoepfe, einzeln eingeordnet

**Erzeugt von `scripts/bedienelemente_124_bericht.py`.** Wer eine Einordnung
anzweifelt, laesst das Skript neu laufen und vergleicht - eine von Hand
geschriebene Liste ueber 124 Stellen waere nicht nachpruefbar.

🔴 **Die Tabellen unten zeigen den Stand NACH dem Bau.** Vor
v3.9.969 waren es **124** Stellen; die vierzehn Sortierkoepfe haben ihren
Tastaturzugang bekommen und fallen damit aus der Aufnahme heraus. Was hier
steht, sind die **110**, die noch offen sind. Wer die urspruenglichen 124
sehen will, laesst das Skript gegen `git show a57663b:index.html` laufen.

## Die Klassen

| Klasse | heisst | Folge |
|---|---|---|
| **BEDIENELEMENT** | loest eine Handlung aus, die es sonst nirgends gibt | bekommt Tastaturzugang |
| **DOPPELWEG** | ein echter Knopf in der Naehe ruft dasselbe | unveraendert |
| **KEIN ELEMENT** | der `onClick` tut etwas Nebensaechliches | unveraendert |
| **UNSICHER** | am Quelltext nicht entscheidbar | **unveraendert**, und gemeldet |

Die vierte Klasse steht im Auftrag selbst: *"Wenn du bei einem unsicher bist:
unveraendert lassen und als unsicher melden. Lieber ein fehlender Zugang als
ein Phantom in der Tab-Reihenfolge."*

## 🔴 Warum nicht alle 82 BEDIENELEMENTE gebaut worden sind

Die Arbeitsscheinliste hat **bei 1440 px schon heute 1882 Tab-Stopps**, bei
390 px 941 - gemessen mit `scripts/tabreihenfolge_messen.py` an der echten
Saat. Sie rendert 185 Zeilen mit je mehreren Formularfeldern und Knoepfen.

Drei ihrer anklickbaren Tabellenzellen rufen **alle dieselbe** Funktion
(`_openEditGuarded`). Gaebe man jeder einen Tab-Stopp, waeren das **555
weitere**. Eine Tab-Reihenfolge, durch die niemand mehr durchkommt, ist kein
Zugang - sie ist ein neuer Mangel mit dem Aussehen einer Kur.

Der richtige Weg dort ist **ein Stopp je ZEILE**, nicht je Zelle. Das ist ein
Umbau der Tabellenstruktur, kein Ergaenzen von Attributen, und es braucht eine
eigene Messung. **Frage an Sebastian.**

Gebaut wurden deshalb die **Sortierkoepfe**: ein Stopp je SPALTE, Sortieren
ist nirgends sonst erreichbar, und die Tab-Reihenfolge der Arbeitsscheinliste
ist dadurch von 1882 auf **1894** gewachsen - exakt um die zwoelf.

## 🔴 Was an dieser Einordnung unsicher ist

* Der Zaehler, der "steht in einer Wiederholung" erkennen sollte, hat sich
  **als unbrauchbar erwiesen**: er meldet `7` fuer die Sortierkoepfe, die
  einmal je Spalte gerendert werden. Er zaehlt umschliessende `.map(` ueber
  eine Klammerbilanz, und die verrechnet sich an Klammern in Zeichenketten.
  **Die Spalte steht deshalb nicht in dieser Tabelle** - eine Zahl, von der
  ich weiss, dass sie falsch ist, gehoert nicht in einen Bericht.
* "Ein Knopf in der Naehe ruft dasselbe" sucht in einem Fenster von 4000
  Zeichen. Ein Knopf weiter weg wird nicht gefunden; dann steht hier
  faelschlich BEDIENELEMENT statt DOPPELWEG.
* Ob ein `div` mit `onClick` am Schirm wirklich erreichbar und sinnvoll ist,
  sagt diese Tabelle nicht. Sie liest den Quelltext.

"""

SCHLUSS = """## Was mit den zehn "eigener Knopf: ja" passieren muss

Zehn der BEDIENELEMENTE enthalten **selbst einen Knopf**. Sie duerfen **kein**
`role="button"` bekommen: ein Knopf in einem Knopf ist ungueltiges ARIA, und
eine Vorlesehilfe liest dann Unsinn. Fuer sie ist `tabIndex` plus
Tastenbehandler **ohne** `role` die richtige Form - so ist es am 27.09.2026 in
`ProjList` gebaut worden.

Sie brauchen ausserdem eine eigene Fokusring-Regel: die vorhandene greift auf
`[role="button"]:focus-visible`, und ohne `role` greift sie nicht. Das ist eine
Zeile CSS, aber sie fehlt heute - und ein Tab-Stopp ohne sichtbaren Ring ist
fuer einen sehenden Tastaturnutzer wertlos.
"""


def main():
    a = K.alle()
    zeilen = [KOPF, "## Die Zahlen\n\n", "| Klasse | Anzahl |\n|---|---|\n"]
    for k, v in Counter(x["klasse"] for x in a).most_common():
        zeilen.append("| %s | %d |\n" % (k, v))
    zeilen.append("| **gesamt** | **%d** |\n\n" % len(a))

    for klasse in ("BEDIENELEMENT", "DOPPELWEG", "UNSICHER", "KEIN ELEMENT"):
        teil = [x for x in a if x["klasse"] == klasse]
        zeilen.append("## %s (%d)\n\n" % (klasse, len(teil)))
        zeilen.append("| Ansicht | Tag | eigener Knopf | `onClick` | "
                      "Begruendung |\n|---|---|---|---|---|\n")
        for x in sorted(teil, key=lambda y: (y["ansicht"], y["pos"])):
            r = (x["rumpf"] or "").replace("|", "\\|").replace("\n", " ")
            b = x["begruendung"].replace("|", "\\|").replace("\n", " ")
            zeilen.append("| %s | `%s` | %s | `%s` | %s |\n"
                          % (x["ansicht"], x["tag"],
                             "ja" if x.get("enthaelt_knopf") else "nein",
                             r[:70], b[:150]))
        zeilen.append("\n")

    zeilen.append(SCHLUSS)
    io.open(ZIEL, "w", encoding="utf-8", newline="").write("".join(zeilen))
    print("geschrieben: %s (%d Stellen)" % (ZIEL, len(a)))


if __name__ == "__main__":
    main()
