# -*- coding: utf-8 -*-
"""Jeder gebaute Tastenbehandler reagiert nur auf Tasten, die IHM gelten.

🔴 DER SCHWERSTE FEHLER AUS v3.9.975 - und kein Quelltextriegel konnte ihn
finden.

Das Bauwerkzeug gab Containern `role="button"`, `tabIndex:0` und einen
Tastenbehandler mit `preventDefault()`. Ein echter `<button>` im Teilbaum
erzeugt seinen Klick aus der VORGABEHANDLUNG des keydown. Der keydown steigt
zum Container auf, dessen Behandler ruft `preventDefault()` - und der Klick
des INNEREN Knopfes faellt aus, waehrend die Aktion des Containers laeuft.

Das vorhandene `onClick: e=>e.stopPropagation()` an den inneren Knoepfen half
NICHT: es stoppt den Klick, nicht den Tastendruck.

AM SCHIRM BEWIESEN (scratchpad/tastenkapern.html, drei Faelle nebeneinander):

    v3.9.975-Bauform           Enter auf dem inneren Knopf -> nur CONTAINER
    Container prueft e.target  -> KNOPF feuert, Container nicht
    Schutz am inneren Knopf    -> KNOPF feuert

WAS DAS GEKOSTET HAT (statisch gefunden von einem Messagenten):
  "✅ Abnahme bestaetigen — Mangel ist behoben" - ein GESCHAEFTSVORGANG in
  der Kundenansicht, per Tastatur nicht ausloesbar. In der
  Arbeitsschein-Karte loeste Enter auf "Storno" das BEARBEITEN aus - eine
  falsche Aktion ist schlimmer als keine. Dazu die Lightbox-Werkzeugleiste
  (◀ ▶ 📥 🗑️ ✕) vollstaendig tot.

🔴 WARUM DREI RIEGEL DAZU GRUEN WAREN. Alle Attribute standen da: `role`,
`tabIndex`, `onKeyDown`, und der Behandler rief den richtigen Ausdruck auf.
Der Mangel entsteht erst aus dem ZUSAMMENSPIEL zweier Elemente im Baum. Das
ist keine Frage der Anwesenheit, und deshalb konnte keine Zaehlung ihn sehen.

DIE KUR ist ein Wort am Anfang jedes Behandlers:

    if(e.target!==e.currentTarget)return;

Bei einem Container ohne innere Bedienelemente ist der Waechter wirkungslos -
der Tastendruck geht dann ohnehin an den Container selbst. Er kostet also
nichts und schliesst die ganze KLASSE, nicht nur die gefundenen Stellen.

🔴 UND ER BEHEBT ETWAS, DAS NIEMAND GEMELDET HAT: in einem solchen Container
konnte man in ein `<input>` KEINE LEERZEICHEN tippen - `e.key===" "` traf zu
und `preventDefault()` schluckte sie.

WAS DIESER RIEGEL MISST UND WAS NICHT. Er zaehlt im Quelltext, dass KEIN
gebauter Behandler ohne den Waechter dasteht. Er sieht nicht, ob am Schirm
wirklich der richtige Knopf feuert - dafuer gibt es

    python scripts/tastenkapern_messen.py <Ansicht> <Breite>

🔴 Dieses Werkzeug erreicht die sechs betroffenen Stellen derzeit NICHT: sie
liegen hinter Zustaenden, die der Pruefstand nicht oeffnet (Kundenansicht,
geoeffnete Lightbox, aufgeklappte Karte). Es meldet das ausdruecklich als
misslungenen Griff statt als gruene Null. Die Wirkung ist damit am Nachbau
belegt, nicht an diesen Stellen - und das steht hier, statt verschwiegen zu
werden.
"""
import io
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import code_scan  # noqa: E402

PFAD = os.path.join(HIER, "..", "index.html")
WACHT = "if(e.target!==e.currentTarget)return;"

# Die fuenf Schreibweisen, in denen das Bauwerkzeug den Behandler erzeugt hat.
# 🔴 Ein Muster, das eine davon nicht kennt, meldet "alle gesichert" - und das
#    ist von einem echten Ergebnis nicht zu unterscheiden.
#
# 🔴 UND SIE MUSS ENG SEIN. Meine erste Fassung nahm JEDES `onKeyDown: e=>{`
#    und wurde rot an handgeschriebenen Behandlern, die direkt am Element
#    sitzen: `if(e.key==="Enter")tryPortal()` an einem Anmeldefeld,
#    `_addTyped()` an einem Eingabefeld, eine Escape-Behandlung. Dort waere
#    der Waechter wirkungslos bis stoerend - der Tastendruck gilt ja dem
#    Element selbst.
#    Gemessen wird deshalb genau die vom Bauwerkzeug erzeugte Form: die
#    Pruefung auf Enter ODER Leertaste, gefolgt von `preventDefault()`.
ANFAENGE = [
    'onKeyDown: e=>{' + WACHT,
    'onKeyDown:e=>{' + WACHT,
]
GEBAUT = [
    'if(e.key==="Enter"||e.key===" "){e.preventDefault();',
    "if(e.key==='Enter'||e.key===' '){e.preventDefault();",
    'const _h=(',
]


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _behandler(text):
    """(Position, Rumpfanfang) jedes GEBAUTEN Tastenbehandlers im CODE.

    Gebaut heisst: die Form, die das Bauwerkzeug aus v3.9.975 erzeugt -
    Pruefung auf Enter ODER Leertaste mit `preventDefault()`, oder die
    bedingte Fassung mit `const _h=(`. Handgeschriebene Behandler an einem
    Eingabefeld gehoeren NICHT dazu.
    """
    ist = code_scan.ist_code(text)
    aus = []
    for anfang in ('onKeyDown: e=>{', 'onKeyDown:e=>{'):
        i = text.find(anfang)
        while i >= 0:
            if ist[i]:
                kopf = text[i:i + len(anfang) + 110]
                rumpf = kopf[len(anfang):]
                # Der Waechter darf schon davorstehen - dann faengt der
                # gebaute Teil danach an.
                ohne = rumpf[len(WACHT):] if rumpf.startswith(WACHT) else rumpf
                if any(ohne.startswith(g) for g in GEBAUT):
                    aus.append((i, kopf))
            i = text.find(anfang, i + 1)
    return aus


def test_koeder_der_sucher_findet_beide_schreibweisen():
    """🔴 Ohne Selbstprobe ist jede Null hier wertlos."""
    for anfang in ANFAENGE:
        kuenstlich = "h('div',{" + anfang + GEBAUT[0] + "go();}}})"
        assert _behandler(kuenstlich), (
            "Der Sucher findet %r nicht einmal in einem Text, der nur daraus "
            "besteht." % anfang)
    # Gegenprobe: im Kommentar zaehlt er nicht mit.
    assert not _behandler("/* onKeyDown: e=>{...} */ var x=1;"), (
        "Ein Vorkommen im KOMMENTAR wird mitgezaehlt - dann wird der Riegel "
        "rot,\n  sobald jemand den Fehler erklaert.")


def test_jeder_behandler_traegt_den_waechter():
    t = _text()
    ohne = []
    for pos, kopf in _behandler(t):
        if WACHT not in kopf:
            ohne.append((t.count("\n", 0, pos) + 1, kopf[:70]))
    assert not ohne, (
        "%d gebaute Tastenbehandler haben den Waechter nicht:\n%s\n"
        "Ohne `%s` ruft der Container `preventDefault()` auch fuer Tasten, "
        "die einem\n  INNEREN Knopf galten - der Klick dieses Knopfes faellt "
        "dann aus, und\n  stattdessen laeuft die Aktion des Containers. Ein "
        "Geschaeftsvorgang war so\n  drei Versionen lang per Tastatur nicht "
        "ausloesbar."
        % (len(ohne), "\n".join("   Zeile %d: %s..." % o for o in ohne),
           WACHT))


def test_die_grundgesamtheit_ist_nicht_leer():
    """🔴 Gegenprobe zur Null: findet der Sucher ueberhaupt Behandler?"""
    n = len(_behandler(_text()))
    assert n >= 90, (
        "Nur %d gebaute Tastenbehandler gefunden. v3.9.975 und die Kuren "
        "danach haben\n  rund 97 erzeugt - bei so wenigen Treffern misst das "
        "Muster nicht mehr die\n  Bauform, und die Null der anderen Pruefung "
        "ist wertlos." % n)


def test_der_waechter_steht_VOR_der_tastenpruefung():
    """Die Reihenfolge ist der ganze Punkt.

    Steht der Waechter hinter `e.preventDefault()`, ist der Klick des inneren
    Knopfes schon verhindert - dann ist er reine Zierde.
    """
    t = _text()
    schief = []
    for pos, kopf in _behandler(t):
        if WACHT not in kopf:
            continue
        w = kopf.index(WACHT)
        p = kopf.find("preventDefault")
        if p >= 0 and p < w:
            schief.append(t.count("\n", 0, pos) + 1)
    assert not schief, (
        "An %d Stellen steht der Waechter HINTER `preventDefault()` "
        "(Zeile %s).\n  Dann ist der Klick des inneren Knopfes bereits "
        "verhindert, wenn der\n  Waechter greift - er waere reine Zierde."
        % (len(schief), schief))
