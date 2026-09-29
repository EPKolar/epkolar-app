# -*- coding: utf-8 -*-
"""Ein unterschriftsreifes Blatt muss aufgehen.

## P2 — die Arbeitszeit-Bestaetigung ging um 0,1 h nicht auf

Die Tageszellen rundeten auf EINE Nachkommastelle, die Summe rechnete mit
dem ungerundeten Wert und rundete erst am Ende - auch auf eine Stelle.

Mo-Sa je 07:00-16:25 mit 1 h Pause ergibt **8,42 h** am Tag
(`_zeitRundBis` laesst 16:25 unveraendert, es ist ein Rasterwert):

    gedruckte Spalte    6 x "8,4"      = 50,4
    Summenkasten        _n(50,52 , 1)  = "50,5"

**Das Blatt geht nicht auf - und wird unterschrieben.**

🔴 DER ZWILLING WURDE AUS GENAU DIESEM GRUND SCHON EINMAL GEKURT.
`generateBWB` steht seit v3.9.665 auf zwei Stellen, mit dem Kommentar *„bei
1 Stelle stimmten Viertelstunden-Buchungen nicht … unterschriebenes
Kunden-/OEBA-Dokument mit nicht aufgehenden Spalten"*. Diese vier Vorkommen
wurden dabei uebersehen - im **selben** Bauteil, wenige hundert Zeilen
entfernt.

🔴 UND EINE KORREKTUR AN DER MELDUNG, DIE ZU DIESEM RIEGEL GEFUEHRT HAT.
Der Messagent nannte ZWEI Dokumente: dieses Blatt und das Wochen-Excel. Das
Wochen-Excel ist **bereits** auf zwei Stellen, samt v3.9.665-Kommentar
daneben - nachgemessen, bevor etwas geaendert wurde. Ein Agentenbefund ist
eine Behauptung wie jede andere; die Haelfte davon war schon erledigt.

## Was dieser Riegel misst - und was NICHT

🔴 **Mein erster Entwurf wollte die REGEL messen** („im gedruckten Blatt gibt
es keine Stundenzahl mit einer Nachkommastelle") und hat den Bereich des
Blattes an zwei Textmarken abgegrenzt. Das ging schief: die Marke war nicht
eindeutig, der Ausschnitt umfasste **26** Stellen aus dem Bildschirmcode, und
der Riegel wurde rot an Dingen, die kein gedrucktes Blatt sind.

Das ist die Hausregel gegen mich selbst: **der AUSSCHNITT eines Riegels ist
selbst die Luecke.** Ein `slice` zwischen zwei Namen kann verrutschen, und
dann misst er eine fremde Grundgesamtheit.

Fuer die Regel braeuchte es den Rumpf der umgebenden Funktion, also einen
verlaesslichen Klammerabgleich. Genau der ist als offener Punkt bekannt:
`code_scan._klammer_zu` **kennt keine Regex-Literale**, gemessen in derselben
Nacht (`scripts/klammer_regex_luecke.py`). Auf einem Werkzeug, von dem man
weiss, dass es hier falsch messen kann, wird kein Riegel gebaut.

Deshalb misst dieser Riegel die **vier Stellen selbst**, an eindeutigen
Ankern - und sagt hier, dass das die kleinere Aussage ist. Die Klassenregel
kommt nach, sobald der Klammerabgleich Regex-Literale kennt.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")

# Die vier Vorkommen des Blattes, an eindeutigen Ankern. Die Zahl dahinter
# ist die erwartete Haeufigkeit - weicht sie ab, wird der Riegel rot statt
# stillschweigend weniger zu pruefen.
GEKURT = [
    ('dt>0?_n(dt,2):""', 2, "die beiden Tageszellen"),
    ("_n(weekTotal,2)}", 1, "die Wochensumme"),
    ('"eventuelle Mehrstunden: "+_n(diff,2)+"h"', 1, "die Mehrstunden"),
]
ALT = [
    ('dt>0?_n(dt,1):""', "die Tageszelle"),
    ("_n(weekTotal,1)}", "die Wochensumme"),
    ('"eventuelle Mehrstunden: "+_n(diff,1)+"h"', "die Mehrstunden"),
]


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    """🔴 Die Kur-Kommentare zitieren die ALTE Form (`_n(dt,1)`) - sie
    erklaeren ja, was dort stand. Wer den rohen Text durchsucht, misst seine
    eigene Begruendung mit und wird rot."""
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def test_koeder_die_kommentarbehandlung_traegt():
    """🔴 Ohne diese Probe waere der Riegel entweder immer rot oder blind."""
    mit = "/* HIER STAND " + ALT[0][0] + " - entfernt. */ " + GEKURT[0][0]
    ohne = _ohne_kommentare(mit)
    assert ALT[0][0] not in ohne, (
        "Ein Kommentar, der die alte Form zitiert, gilt als Wiederkehr.\n"
        "  Dann muss die Begruendung weg, damit der Riegel gruen wird - "
        "genau verkehrt herum.")
    assert GEKURT[0][0] in ohne, (
        "Die Kommentarentfernung frisst auch die reparierte Form mit - dann "
        "ist der\n  Riegel immer rot.")


def test_die_vier_stellen_stehen_auf_zwei_nachkommastellen():
    t = _ohne_kommentare(_text())
    schief = []
    for anker, erwartet, was in GEKURT:
        n = t.count(anker)
        if n != erwartet:
            schief.append("%s: %r trifft %d mal, erwartet %d"
                          % (was, anker, n, erwartet))
    assert not schief, (
        "%d Anker stimmen nicht:\n%s\n"
        "  Steht dort wieder eine Stelle, ergibt die gedruckte Spalte "
        "6 x 8,4 = 50,4,\n  waehrend die Summe aus dem ungerundeten Wert "
        "50,5 zeigt - und das Blatt wird\n  unterschrieben. Weicht die "
        "ANZAHL ab, ist eine Spalte dazugekommen oder\n  weggefallen; "
        "beides gehoert angesehen."
        % (len(schief), "\n".join("   " + s for s in schief)))


def test_die_alte_form_ist_nirgends_im_blatt_zurueck():
    t = _ohne_kommentare(_text())
    zurueck = [was for anker, was in ALT if anker in t]
    assert not zurueck, (
        "Die alte Form ist zurueck bei: %s.\n"
        "  Der Zwilling generateBWB steht seit v3.9.665 aus genau diesem "
        "Grund auf zwei\n  Stellen - dort steht der Kommentar "
        "„unterschriebenes Kunden-/OEBA-Dokument mit\n  nicht "
        "aufgehenden Spalten“." % ", ".join(zurueck))


def test_der_zwilling_bleibt_auf_zwei_stellen():
    """Er wurde in v3.9.665 gekurt. Faellt er zurueck, ist die Lehre weg.

    🔴 Und hier steht die KORREKTUR an der Meldung, die zu diesem Riegel
    gefuehrt hat: der Messagent nannte ZWEI Dokumente - dieses Blatt und das
    Wochen-Excel. Das Wochen-Excel war **bereits** auf zwei Stellen, samt
    v3.9.665-Kommentar daneben. Nachgemessen, bevor etwas geaendert wurde.
    Ein Agentenbefund ist eine Behauptung wie jede andere.
    """
    t = _ohne_kommentare(_text())
    for form in ("_n(rowSum,2)", "_n(grandTotal,2)"):
        assert form in t, (
            "`%s` steht nicht mehr im Wochenblatt. Das war die Kur aus "
            "v3.9.665 -\n  ohne sie gehen dort dieselben Spalten nicht "
            "mehr auf." % form)
