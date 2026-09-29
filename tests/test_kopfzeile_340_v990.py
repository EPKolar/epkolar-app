# -*- coding: utf-8 -*-
"""Bei 340 px laeuft keine Kopfzeile quer aus dem Bild.

🔴 WAS DIESER RIEGEL NICHT TUT, UND WARUM. Er nagelt NICHT fest, dass die
Icon-Only-Regel tot ist. Ein Riegel, dessen Nachweis vom FORTBESTEHEN eines
Mangels lebt, wird bei der naechsten Kur rot oder blind - und hier steht eine
Kur ausdruecklich zur Entscheidung (Frage 22).

Festgehalten wird stattdessen die Eigenschaft, die in BEIDEN Faellen gelten
muss: **auf dem schmalsten unterstuetzten Geraet laeuft nichts quer aus dem
Bild.** Wer die Absicht herstellt (Text weg, Symbol bleibt), aendert die
Breiten - und dieser Riegel bleibt gruen. Wer die tote Regel loescht, auch.
Wer aber einen fuenften Knopf in die Kopfzeile legt, ohne die Umbruch-Form
zu pruefen, wird rot.

GEMESSEN AM 29.09.2026 (`python scripts/kopfzeile_340_messen.py 340`), in
allen Ansichten, die eine `.header-row` tragen - nicht nur in der ersten:

    werkzeuge     4 Knoepfe, zusammen 416 px, Ueberlauf +0
    mitarbeiter   3 Knoepfe, zusammen 352 px, Ueberlauf +0
    zeit          3 Knoepfe, zusammen 221 px, Ueberlauf +0
    plaene        2 Knoepfe, zusammen 226 px, Ueberlauf +0
    as_liste      1 Knopf,   zusammen 104 px, Ueberlauf +0

Die Zeile ist 324 px breit, die Knoepfe zusammen 416 - und trotzdem kein
Querlauf: sie brechen um. Die tote Regel kostet also HOEHE, nicht
Richtigkeit. Das ist der Grund, warum sie jahrelang niemandem aufgefallen
ist.

🔴 DIESER RIEGEL LIEST DEN BEFUND, ER MISST NICHT SELBST. Die Aufnahme bei
340 px braucht einen Browser und gehoert nicht in den Riegelbestand, der bei
jeder Freigabe laeuft. Fehlt die Datei, wird er rot und sagt, wie man sie
erzeugt - eine stillschweigend uebersprungene Pruefung waere schlimmer.
"""
import io
import json
import os

HIER = os.path.dirname(os.path.abspath(__file__))
BEFUND = os.path.join(HIER, "..", "docs", "befunde", "KOPFZEILE_340.json")
ERZEUGEN = "python scripts/kopfzeile_340_messen.py 340"


def _befund():
    assert os.path.exists(BEFUND), (
        "Die Aufnahme bei 340 px fehlt: %s\n"
        "  Erzeugen mit:  %s\n"
        "  Ein Riegel, der sich beim Fehlen der Messung selbst ueberspringt, "
        "meldet gruen,\n  ohne etwas zu wissen." % (BEFUND, ERZEUGEN))
    return json.load(io.open(BEFUND, encoding="utf-8"))


def test_die_aufnahme_ist_bei_340_px_entstanden():
    """🔴 Gegenprobe: eine Aufnahme bei 390 px wuerde hier alles gruen
    melden und nichts ueber das schmalste Geraet sagen."""
    d = _befund()
    assert d.get("fenster") == 340, (
        "Die Aufnahme ist bei %s px entstanden, nicht bei 340.\n"
        "  Neu aufnehmen:  %s" % (d.get("fenster"), ERZEUGEN))


def test_die_kopfzeile_laeuft_nicht_quer_aus_dem_bild():
    d = _befund()
    assert not d.get("zeile_laeuft_ueber"), (
        "Die Kopfzeile laeuft bei 340 px um %d px aus dem Bild.\n"
        "  Auf einem iPhone SE der ersten Generation ist dann ein Teil der "
        "Knoepfe nicht\n  erreichbar. Entweder weniger Knoepfe, oder die "
        "Icon-Only-Absicht aus Frage 22\n  herstellen - dann brauchen die "
        "Knoepfe vorher ein `aria-label`."
        % d.get("ueberlauf_px", 0))


def test_das_dokument_bekommt_keinen_querbalken():
    d = _befund()
    assert not d.get("dokument_laeuft_ueber"), (
        "Das Dokument ist bei 340 px breiter als das Fenster - die ganze "
        "Seite laesst\n  sich quer schieben. Das ist auf einem Telefon "
        "immer ein Fehler.")


def test_jeder_kopfzeilen_knopf_traegt_ein_zeichen_oder_einen_namen():
    """🔴 DIE VORBEDINGUNG FUER FRAGE 22.

    Wird der Text ausgeblendet, bleibt nur das Symbol. Ein Knopf, dem dann
    weder ein Zeichen noch ein `aria-label` bleibt, ist stumm - fuer eine
    Vorlesehilfe UND fuer das Auge. Diese Pruefung sagt, ob die Entscheidung
    „Text weg" ueberhaupt gefahrlos moeglich waere.
    """
    d = _befund()
    stumm = [b["text"] for b in d.get("knoepfe", [])
             if not b.get("zeichen_bleibt")
             and not (b.get("aria") or b.get("titel"))]
    assert not stumm, (
        "%d Kopfzeilen-Knoepfe haetten ohne Text keinen Namen mehr: %s\n"
        "  Solange das so ist, ist die Icon-Only-Absicht aus Frage 22 nicht "
        "umsetzbar,\n  ohne vorher `aria-label` zu vergeben."
        % (len(stumm), stumm))
