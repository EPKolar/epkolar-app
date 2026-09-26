# -*- coding: utf-8 -*-
"""v3.9.955 - BP_MOB ist die EINZIGE Mobilschwelle der App.

WARUM ES DIESE DATEI GIBT
─────────────────────────
`VBautag` war die einzige Stelle, an der eine Variable namens `isMob` an die
TABLETBREITE gebunden war:

    const isMob = ww < 768;     // vorher, seit dem aeltesten Stand

Ueberall sonst heisst die Mobilschwelle `BP_MOB` und ist 600. Die Folge war
kein Schoenheitsfehler: zwischen 600 und 767 px - also auf einem Tablet im
Hochformat - zeigte das Bautagebuch die HANDY-Fassung, waehrend jede andere
Ansicht derselben App die Desktop-Fassung zeigte. Zwei Mobilschwellen in einer
App sind eine Falle mit Ansage: wer BP_MOB anfasst, aendert 28 Stellen und
diese eine nicht, und der Unterschied faellt erst einem Benutzer auf.

Seit v3.9.955 steht dort `ww < BP_MOB`.

DAS IST EINE VERHALTENSAENDERUNG, NICHT EINE UMBENENNUNG
────────────────────────────────────────────────────────
Zwischen 600 und 767 px sieht das Bautagebuch ab jetzt anders aus als vorher.
Das ist gewollt und bei 390, 640, 767 und 1440 px vorher UND nachher gemessen;
der Vorher-Stand liegt als eingefrorene Kopie vor. Wer diese Datei liest, weil
sie rot ist, soll das wissen: die Zahl 768 hier wiederherzustellen holt den
Fehler zurueck.

DIE SECHS ERLAUBTEN STELLEN - EINZELN GENANNT, NICHT ALS ZAHL
─────────────────────────────────────────────────────────────
`ww<768` bleibt an sechs Stellen stehen. Sie meinen ausdruecklich die
Tablet-Schwelle und heissen entweder `isTab` oder vergleichen absichtlich
inline. Eine Obergrenze "hoechstens sechs" waere hier wertlos - sie wuerde
gruen bleiben, wenn eine erlaubte Stelle verschwindet und eine neue,
unerlaubte dazukommt. Deshalb wird jede Stelle mit ihrer umschliessenden
Ansicht genannt:

    ProjectShell   const isTab=ww<768             Reiterzeile der Projektakte
    VDash          gridTemplateColumns:ww<768?..   Kennzahlengitter
    VPlan          const isTab=ww<768             neben isMob=ww<BP_MOB
    VFotos         const isTab=ww<768             neben isMob=ww<BP_MOB
    WerkzeugView   (ww<768)&&...                   zwei inline-Vergleiche,
    WerkzeugView   (ww<768)&&...                   Kartenliste statt Tabelle

Zwei davon - VPlan und VFotos - fuehren isMob UND isTab in derselben Zeile.
Das ist der Beleg, dass die beiden Schwellen absichtlich verschieden sind und
768 dort kein vergessenes 600 ist.

🔴 EINE KORREKTUR AM AUFTRAG, sichtbar statt stillschweigend: der Auftrag
nannte fuer die erste Stelle `HomeView`. Gemessen liegt sie in `ProjectShell`
(Deklaration Zeile 15748; HomeView endet bei ProjList@15562). Die Liste hier
folgt der Messung.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Sie liest Quelltext. Ob das Bautagebuch bei 640 px wirklich umbricht oder ob
etwas abgeschnitten wird, kann sie nicht sehen - das steht im Bericht, am
Schirm gemessen. Und sie prueft nicht, ob 768 die richtige Tablet-Schwelle
ist; sie haelt nur fest, dass es genau diese sechs Stellen sind.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Die umschliessende Ansicht je erlaubter Stelle. Reihenfolge = Dateireihenfolge.
ERLAUBT = [
    "ProjectShell",
    "VDash",
    "VPlan",
    "VFotos",
    "WerkzeugView",
    "WerkzeugView",
]


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes. Das ist Datenverlust, keine "
            "Schwellenfrage - die Pruefung waere sonst gruen, weil sie "
            "nichts findet." % len(roh))
    return roh


def _umschliessende_ansicht(text, pos):
    """Die letzte `function X(`-Deklaration VOR pos.

    Nicht `code_scan._komponente`: das nimmt auch `const X = (` und nennt
    fuer die beiden WerkzeugView-Stellen `Stars` - eine Pfeilfunktion INNERHALB
    von WerkzeugView. Beide Antworten sind richtig; hier ist die umschliessende
    Ansicht gemeint, weil danach die Ausnahme benannt ist.
    """
    treffer = list(re.finditer(r"function\s+([A-Za-z_]\w*)\s*\(", text[:pos]))
    return treffer[-1].group(1) if treffer else "?"


def _tabletstellen(text):
    """(Ansicht, Zeile) je `ww<768` im CODE - Kommentare zaehlen nicht mit."""
    aus = []
    for pos in code_scan.nur_code_stellen(text, r"ww\s*<\s*768\b", regex=True):
        aus.append((_umschliessende_ansicht(text, pos),
                    text.count("\n", 0, pos) + 1))
    return aus


def _neue_mobilschwellen(text):
    """Jede `isMob`-Deklaration im Code, die NICHT an BP_MOB haengt."""
    aus = []
    for pos in code_scan.nur_code_stellen(
            text, r"\bisMob\s*=\s*ww\s*<\s*(?!BP_MOB\b)", regex=True):
        aus.append((_umschliessende_ansicht(text, pos),
                    text.count("\n", 0, pos) + 1,
                    text[pos:pos + 40].split("\n")[0]))
    return aus


def test_vbautag_haengt_an_bp_mob():
    """Die eigentliche Aussage: im Bautagebuch steht BP_MOB, nicht 768."""
    roh = _lies()
    stellen = code_scan.nur_code_stellen(roh, "const isMob=ww<BP_MOB;")
    ansichten = {_umschliessende_ansicht(roh, p) for p in stellen}
    assert "VBautag" in ansichten, (
        "VBautag fuehrt keine Zeile `const isMob=ww<BP_MOB;`. Gefunden wurde "
        "die Form in: %s.\nSteht dort wieder 768, ist der Fehler zurueck: ein "
        "Tablet im Hochformat zeigt dann im Bautagebuch die Handy-Fassung und "
        "im Rest der App die Desktop-Fassung."
        % (sorted(ansichten) or "keiner Ansicht"))


def test_keine_zweite_mobilschwelle():
    """Kein `isMob` haengt an einer Zahl statt an BP_MOB.

    Das ist die Eigenschaft, die der Umbau herstellt - nicht die Abwesenheit
    der Ziffern 768. Eine neue Stelle `isMob=ww<900` waere derselbe Fehler mit
    einer anderen Zahl, und der Name BP_MOB steht genau dafuer da.
    """
    fund = _neue_mobilschwellen(_lies())
    assert not fund, (
        "%d Stelle(n) binden `isMob` an eine Zahl statt an BP_MOB:\n%s\n"
        "BP_MOB ist die einzige Mobilschwelle der App. Wer eine zweite "
        "einfuehrt, baut wieder die Falle: ein Aendern von BP_MOB fasst sie "
        "nicht mit an."
        % (len(fund), "\n".join("  %-14s Zeile %-6d %s" % f for f in fund)))


def test_die_sechs_tabletschwellen_sind_namentlich_erlaubt():
    """Genau diese sechs Stellen, in genau diesen Ansichten.

    Namentlich statt als Obergrenze: "hoechstens sechs" bliebe gruen, wenn
    eine erlaubte Stelle verschwindet und dafuer eine unerlaubte dazukommt.
    """
    roh = _lies()
    stellen = _tabletstellen(roh)
    ist = [a for a, _ in stellen]
    assert ist == ERLAUBT, (
        "Die Tablet-Schwellen `ww<768` stehen nicht mehr dort, wo sie erlaubt "
        "sind.\n  erwartet: %s\n  gemessen: %s\n%s\n"
        "Ist eine Stelle DAZUGEKOMMEN: sie meint vermutlich die "
        "Mobilschwelle - dann gehoert dort BP_MOB hin. Ist eine WEGGEFALLEN: "
        "pruefen, ob die Tablet-Fassung dieser Ansicht verlorenging, und "
        "diese Liste erst danach nachziehen."
        % (ERLAUBT, ist,
           "\n".join("  %-14s Zeile %d" % s for s in stellen)))


def test_der_riegel_wird_bei_einer_neuen_mobilschwelle_rot():
    """KOEDER auf beide Zaehler.

    Beide Pruefungen oben ZAEHLEN. Ein Zaehler, der ins Leere greift - weil
    das Muster nicht mehr passt, weil der Abtaster irrt, weil die Datei
    anders geschrieben ist - meldet nichts gefunden, und nichts gefunden
    sieht aus wie in Ordnung. Also wird beiden eine absichtlich kaputte
    Fassung vorgelegt, in der sie ROT werden MUESSEN.
    """
    roh = _lies()
    anker = "const isMob=ww<BP_MOB;"
    assert anker in roh, "Anker fuer den Koeder fehlt: %s" % anker
    kaputt = roh.replace(anker, "const isMob=ww<768;" + anker, 1)

    fund = _neue_mobilschwellen(kaputt)
    assert fund, (
        "KOEDER NICHT GEFUNDEN. In der kaputten Fassung steht "
        "`const isMob=ww<768;` - test_keine_zweite_mobilschwelle findet sie "
        "nicht und wuerde auch im Echtfall gruen melden. Der Zaehler ist "
        "blind, nicht die App ist sauber.")

    stellen = [a for a, _ in _tabletstellen(kaputt)]
    assert stellen != ERLAUBT, (
        "KOEDER NICHT GEFUNDEN. Die kaputte Fassung hat eine siebte "
        "`ww<768`-Stelle, und die Ortsliste meldet sie unveraendert. Dann "
        "unterscheidet sie nicht mehr.")


def test_der_abtaster_hat_sich_geeicht():
    """Ohne bestandene Eichung ist jede Zahl hier wertlos.

    `code_scan` verweigert die Auskunft von selbst; das hier steht dabei,
    damit im roten Fall die Ursache in der Meldung steht und nicht nur ein
    SystemExit aus einer fremden Datei.
    """
    ok, gefunden, erwartet = code_scan.eichen(_lies())
    assert ok, (
        "Eichung gescheitert: %d von %d isMob-Deklarationen als Code "
        "erkannt. Der Abtaster irrt sich, also sind die Zahlen dieser Datei "
        "ohne Wert - er findet dann zu WENIG und das sieht gruen aus."
        % (gefunden, erwartet))
    assert erwartet >= 5, (
        "Nur %d isMob-Deklarationen als Grundgesamtheit. Eine (fast) leere "
        "Menge besteht keine Probe." % erwartet)
