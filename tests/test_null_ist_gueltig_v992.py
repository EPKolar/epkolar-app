# -*- coding: utf-8 -*-
"""Ein Urlaubsanspruch von 0 Stunden ist 0, nicht 192,5.

## P4 — `x||192.5` liest die 0 als FEHLEND

In JavaScript ist `0` falsy. An **vierzehn** Stellen stand
`(ks.stunden||192.5)`, und damit wurde ein ausdruecklich eingetragener
Anspruch von 0 Stunden zu 192,5.

Gemessen am geschnittenen Code:

    getippt 150    -> 150      richtig
    getippt 192.5  -> 192.5    richtig
    getippt 0      -> 192.5    FALSCH
    getippt 0.0    -> 192.5    FALSCH
    getippt ""     -> 192.5    FALSCH - das Feld laesst sich nicht leeren
    DB-Wert 0      -> 192.5    FALSCH
    Anspruch 0     -> Resturlaub 192,5 h statt 0

Das geht auch in `Kontingent_<jahr>.xls` samt Gesamtzeile.

## Die Kur: EIN Helfer statt vierzehn Abschriften

    function _ktgStd(v){
      if(v===null||v===undefined||v==="")return 192.5;
      const _k=parseFloat(v); return isNaN(_k)?192.5:_k;
    }

Fehlend sind nur `null`, `undefined`, Leertext und alles, was sich nicht in
eine Zahl lesen laesst. **0 ist eine Angabe.**

🔴 Vierzehn Abschriften waeren vierzehn Gelegenheiten, dass eine davon
zurueckfaellt - und die naechste faellt immer zurueck. Deshalb ein Helfer,
und deshalb misst dieser Riegel die **Regel** (es gibt keine
`||192.5`-Stelle mehr im Code) und nicht die vierzehn Orte.

🔴 UND ER MISST IM CODE, NICHT IM ROHEN TEXT. Der Kommentar am Helfer
ZITIERT die alte Form - er erklaert ja, was dort stand. Ein Riegel, der den
rohen Text durchsucht, waere daran sofort rot, und die Begruendung muesste
weg, damit er gruen wird. Genau verkehrt herum.

Ein Objekt-Vorgabewert wie `{stunden:192.5, …}` fuer einen **fehlenden**
Satz bleibt unangetastet - der ist richtig.
"""
import io
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import code_scan  # noqa: E402

PFAD = os.path.join(HIER, "..", "index.html")
FALSCHE_FORM = "||192.5"
HELFER = "function _ktgStd(v){"
# Vierzehn Kurstellen plus die Definition.
ERWARTET_AUFRUFE = 15


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _im_code(text, marke):
    """Wie oft steht `marke` im CODE - Kommentare und Zeichenketten zaehlen
    nicht mit."""
    ist = code_scan.ist_code(text)
    n, i = 0, text.find(marke)
    while i >= 0:
        if i < len(ist) and ist[i]:
            n += 1
        i = text.find(marke, i + 1)
    return n


def test_koeder_der_sucher_trennt_code_von_kommentar():
    """🔴 Ohne diese Probe waere die Null unten wertlos - oder der Riegel
    waere an seiner eigenen Begruendung rot."""
    kunst = 'var a = x||192.5;'
    assert _im_code(kunst, FALSCHE_FORM) == 1, (
        "Der Sucher findet die falsche Form nicht einmal in einem Text, der "
        "nur daraus besteht.")
    nur_kommentar = '/* frueher stand hier x||192.5 - entfernt. */ var a=1;'
    assert _im_code(nur_kommentar, FALSCHE_FORM) == 0, (
        "Ein KOMMENTAR, der die alte Form zitiert, wird mitgezaehlt.\n"
        "  Dann muss die Begruendung weg, damit der Riegel gruen wird - "
        "genau verkehrt herum.")


def test_der_helfer_ist_da_und_behandelt_die_null_richtig():
    t = _text()
    assert HELFER in t, (
        "Der Helfer `_ktgStd` ist weg. Dann stehen die vierzehn Stellen "
        "wieder einzeln da,\n  und die naechste faellt zurueck.")
    i = t.find(HELFER)
    rumpf = t[i:i + 260]
    assert 'v===null' in rumpf and 'v===undefined' in rumpf, (
        "Der Helfer prueft nicht mehr ausdruecklich auf `null` und "
        "`undefined`.\n  Ohne das ist er wieder eine falsy-Pruefung, und "
        "die 0 gilt wieder als fehlend.")
    assert 'isNaN' in rumpf, (
        "Der Helfer faengt keinen ungueltigen Text mehr ab - dann wird aus "
        "einem Tippfehler\n  eine NaN-Stunde statt der Vorgabe.")


def test_keine_stelle_liest_die_null_mehr_als_fehlend():
    n = _im_code(_text(), FALSCHE_FORM)
    assert n == 0, (
        "%d Stellen im Code lesen wieder `x||192.5`.\n"
        "  Damit wird ein ausdruecklich eingetragener Anspruch von 0 Stunden "
        "zu 192,5 -\n  und der Resturlaub steht auf 192,5 statt 0. Benutze "
        "`_ktgStd(x)`." % n)


def test_die_grundgesamtheit_ist_nicht_leer():
    """🔴 Gegenprobe zur Null: der Helfer wird auch wirklich gerufen."""
    n = _text().count("_ktgStd(")
    assert n >= ERWARTET_AUFRUFE, (
        "Nur %d Vorkommen von `_ktgStd(` gefunden, erwartet waren mindestens "
        "%d\n  (vierzehn Kurstellen plus die Definition). Weniger heisst: "
        "eine Stelle ist auf\n  etwas anderes umgestellt worden - das "
        "gehoert angesehen, nicht weggezaehlt."
        % (n, ERWARTET_AUFRUFE))
