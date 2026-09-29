# -*- coding: utf-8 -*-
"""Ein bestmuehender Cache-Schreibvorgang darf nichts mittragen.

🔴 DER MANGEL, DER HIER FESTGEHALTEN WIRD (gefunden 29.09.2026).

`_geoSelbstnachzieh` fragt bis zu zwoelf Postleitzahlen bei Nominatim ab -
mit 1,1 s Pause dazwischen, wie deren Richtlinie es verlangt - und danach die
Fahrstrecken bei OSRM. Das Ergebnis wurde so zwischengespeichert:

    try{ await _sbPost("plz_geo",{...}); geoMap[plz]={...}; geocoded++; }
    catch(_w){ /* Tabelle fehlt/RLS -> still weiter */ }

Der Kommentar versprach „still weiter". Der Code tat etwas anderes: schlug
der Cache-Schreibvorgang fehl, wurden `geoMap[plz]` und `geocoded` **gar
nicht erst gesetzt**.

🔴 UND DAS BLIEB NICHT BEIM CACHE. Der Aufrufer veroeffentlicht das Ergebnis
nur unter einer Bedingung:

    if(rr && (rr.geocoded>0 || rr.matrixRows>0)){ window.__dispoGeo={...}; }

`matrixRows` stand ebenfalls im `try` - es sah wie ein Meldezaehler aus und
war in Wahrheit das **Tor**. Blieben beide auf 0, war die ganze Arbeit des
Laufs verworfen: Geokodierung UND Entfernungsmatrix, obwohl beide im Speicher
fertig dastanden. Bei einem Monteur, dem die RLS das Schreiben auf `plz_geo`
verwehrt, bei **jedem** Lauf aufs Neue.

AM SCHIRM GEMESSEN, in beide Richtungen (`scripts/geo_nachzieh_wirkung.py`):

    _sbPost laeuft    -> geocoded=2, matrixRows=1, geoMap=2
    _sbPost wirft 403 -> geocoded=0, matrixRows=0, geoMap=0   VORHER
    _sbPost wirft 403 -> geocoded=2, matrixRows=1, geoMap=2   NACHHER

🔴 WAS DIESER RIEGEL MISST UND WAS NICHT. Er misst im Quelltext, dass im
`try` um einen Cache-Schreibvorgang **nichts weiter** steht - keine
Zuweisung, kein Zaehler. Das ist Anwesenheit, und das ist hier ausdruecklich
gewollt: die WIRKUNG ist am Schirm belegt, und dieser Riegel haelt nur fest,
dass die Reihenfolge nicht zurueckrutscht. Der Beleg ist das Skript oben, ein
Tor ist dieser Riegel.

DIE ALLGEMEINE FORM, falls die Stellen einmal umziehen: **was nach einem
`await` im selben `try` steht, faellt bei einem Fehler aus.** Wer ein
`try/catch` um einen bestmuehenden Aufruf legt, packt in dieses `try` genau
den einen Aufruf - und sonst nichts.
"""
import io
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import code_scan  # noqa: E402

PFAD = os.path.join(HIER, "..", "index.html")

# Die beiden bestmuehenden Cache-Schreibvorgaenge in `_geoSelbstnachzieh`.
CACHES = ["plz_geo", "plz_distanz"]
# Was in einem solchen `try` NICHTS zu suchen hat.
TRAEGT = re.compile(r"\+\+|--|[^=!<>]=[^=]")


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _try_um(text, pos, ist):
    """Der Rumpf des innersten `try`, das `pos` umschliesst.

    Gesucht wird rueckwaerts das naechste `try{`, dessen Klammerabgleich
    ueber `pos` hinausreicht. Rueckwaerts, weil ein `try` beliebig weit vorn
    stehen kann und `index.html` kaum Zeilenumbrueche hat.
    """
    bester = None
    for m in re.finditer(r"\btry\s*\{", text[:pos]):
        auf = m.end() - 1
        if auf < len(ist) and not ist[auf]:
            continue
        ende = code_scan._klammer_zu(text, auf, "{", "}")
        if ende > pos:
            bester = (auf, ende)
    if not bester:
        return None
    return text[bester[0] + 1:bester[1] - 1]


def _rumpf_ohne_kommentare(rumpf):
    """🔴 Ein Kommentar darf den Riegel weder erfuellen noch brechen.

    Die Begruendung im `catch` und die Erklaerung im `try` enthalten beide
    Gleichheitszeichen (`geocoded>0||matrixRows>0`). Wer den ROHEN Text
    durchsucht, misst seine eigene Begruendung mit und wird rot - das ist die
    Regel [[mlg-regel-kommentar-erfuellt-den-riegel]] in der Umkehrung.
    """
    ohne = re.sub(r"/\*.*?\*/", "", rumpf, flags=re.S)
    return re.sub(r"//[^\n]*", "", ohne)


def _cache_trys(text):
    """(Name, Rumpf ohne Kommentare) je Cache-Schreibvorgang."""
    ist = code_scan.ist_code(text)
    aus = []
    for name in CACHES:
        marke = '_sbPost("%s"' % name
        i = text.find(marke)
        while i >= 0:
            if i < len(ist) and ist[i]:
                rumpf = _try_um(text, i, ist)
                if rumpf is not None:
                    aus.append((name, _rumpf_ohne_kommentare(rumpf)))
            i = text.find(marke, i + 1)
    return aus


def test_koeder_der_sucher_sieht_die_ALTE_form():
    """🔴 Ohne Selbstprobe waere jede Null hier wertlos."""
    alt = ('try{await _sbPost("plz_geo",{plz:plz});geoMap[plz]={a:1};'
           'geocoded++;}catch(_w){/* still weiter */}')
    ist = [True] * len(alt)
    i = alt.find('_sbPost("plz_geo"')
    rumpf = _rumpf_ohne_kommentare(_try_um(alt, i, ist))
    assert TRAEGT.search(rumpf), (
        "Der Melder sieht die ALTE Form nicht - Zuweisung und Zaehler im "
        "selben `try`.\n  Dann ist seine Null an der echten Datei wertlos.")

    neu = ('geoMap[plz]={a:1};geocoded++;try{await _sbPost("plz_geo",'
           '{plz:plz});}catch(_w){/* still weiter */}')
    ist = [True] * len(neu)
    i = neu.find('_sbPost("plz_geo"')
    rumpf = _rumpf_ohne_kommentare(_try_um(neu, i, ist))
    assert not TRAEGT.search(rumpf), (
        "Der Melder haelt auch die REPARIERTE Form fuer schlecht - dann ist "
        "er nicht\n  rot wegen des Mangels, sondern immer.")


def test_koeder_ein_kommentar_macht_den_riegel_nicht_rot():
    """🔴 Die Gegenprobe zur Kommentarbehandlung.

    Der echte `catch`-Kommentar enthaelt `geocoded>0||matrixRows>0`. Wer den
    rohen Text misst, wird daran rot und haelt seine eigene Begruendung fuer
    den Mangel.
    """
    mit = ('try{/* erklaert: geocoded>0||matrixRows>0 und x=1 */'
           'await _sbPost("plz_geo",{plz:plz});}catch(_w){}')
    ist = [True] * len(mit)
    i = mit.find('_sbPost("plz_geo"')
    rumpf = _rumpf_ohne_kommentare(_try_um(mit, i, ist))
    assert not TRAEGT.search(rumpf), (
        "Ein Kommentar im `try` macht den Riegel rot. Dann wird er rot, "
        "sobald jemand\n  erklaert, warum er gruen ist.")


def test_die_grundgesamtheit_ist_nicht_leer():
    """🔴 Gegenprobe zur Null: gibt es die beiden Stellen ueberhaupt noch?"""
    gefunden = {n for n, _ in _cache_trys(_text())}
    fehlt = [n for n in CACHES if n not in gefunden]
    assert not fehlt, (
        "Diese Cache-Schreibvorgaenge findet der Sucher nicht mehr: %s.\n"
        "  Entweder sind sie weg - dann gehoert dieser Riegel angepasst -, "
        "oder der\n  Sucher greift daneben und die andere Pruefung misst "
        "nichts." % ", ".join(fehlt))


def test_im_cache_try_steht_NUR_der_cache_aufruf():
    schief = []
    for name, rumpf in _cache_trys(_text()):
        m = TRAEGT.search(rumpf)
        if m:
            schief.append((name, rumpf.strip()[:150]))
    assert not schief, (
        "%d Cache-Schreibvorgaenge tragen etwas mit:\n%s\n"
        "  Was nach einem `await` im selben `try` steht, faellt bei einem "
        "Fehler aus.\n  Hier hiess das: `geoMap` blieb leer, `geocoded` und "
        "`matrixRows` blieben 0 -\n  und weil der Aufrufer nur bei "
        "`geocoded>0||matrixRows>0` veroeffentlicht,\n  war die ganze Arbeit "
        "des Laufs weg, samt zwoelf Nominatim-Anfragen mit je\n  1,1 s "
        "Pause. Der Beleg dazu: python scripts/geo_nachzieh_wirkung.py"
        % (len(schief), "\n".join("   %s: %s" % s for s in schief)))
