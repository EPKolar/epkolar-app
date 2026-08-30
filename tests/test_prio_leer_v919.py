# -*- coding: utf-8 -*-
"""v3.9.919 - Ein Schein OHNE Prioritaet sah aus wie ein AUFGESCHOBENER.

Zwei Zeilen derselben Auswahl widersprachen sich:

    value: a.prioritaet||"keine"                       <- prueft den ZUSTAND
    ...filter(([k])=>k!=="keine"||a.prioritaet==="keine")  <- prueft die ZEICHENKETTE

Der Wert faellt bei jedem leeren Feld auf "keine" - und leer kommt in drei
Formen vor: das Feld fehlt, es ist null, es ist ein leerer Text. Der Filter
liess "keine" aber nur stehen, wenn `a.prioritaet` woertlich "keine" war.

Damit stand der Wert auf einer Option, die es gar nicht gab. Ein select zeigt
dann die ERSTE - und `AS_PRIO` beginnt mit "aufgeschoben".

IM BROWSER GEMESSEN (scripts/prio_leer_messen.py, vor der Reparatur):

    Nummer    value            ANGEZEIGT      Index
    AS-2005   'normal'         normal         2      <- Gegenprobe
    AS-2004   'keine'          keine          0      <- woertlich
    AS-2003   'aufgeschoben'   aufgeschoben   0      <- leerer Text
    AS-2002   'aufgeschoben'   aufgeschoben   0      <- null
    AS-2001   'aufgeschoben'   aufgeschoben   0      <- Feld fehlt

Es war nicht nur die Anzeige: der DOM-Wert des Feldes WAR 'aufgeschoben'. Wer
die Liste las, las eine Planungsaussage, die niemand getroffen hatte - ein
aufgeschobener Auftrag ruht.

WAS DIESER RIEGEL MISST
───────────────────────
Nicht die Schreibweise der Bedingung, sondern die Eigenschaft, aus der der
Fehler ueberhaupt entstand:

    DER GEWAEHLTE WERT MUSS UNTER DEN ANGEBOTENEN OPTIONEN SEIN.

Solange das gilt, kann die Anzeige nicht auf eine fremde Option kippen - egal,
wie die Bedingung spaeter geschrieben wird. Beide Ausdruecke werden woertlich
aus index.html geschnitten und mit Node AUSGEFUEHRT.

Die Gegenprobe baut die alte Bedingung zurueck und verlangt, dass sie bricht.
"""
import json
import re
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

WERT = 'a.prioritaet||"keine"'
FILTER = ('Object.entries(AS_PRIO).filter(([k])=>k!=="keine"'
          '||(a.prioritaet||"keine")==="keine")')
ALT_FILTER = ('Object.entries(AS_PRIO).filter(([k])=>k!=="keine"'
              '||a.prioritaet==="keine")')

# Alle Formen, in denen "keine Prioritaet" im Bestand vorkommt, plus zwei
# gesetzte Werte als Gegenprobe.
FAELLE = [
    ("Feld fehlt", {}),
    ("null", {"prioritaet": None}),
    ("leerer Text", {"prioritaet": ""}),
    ("keine (woertlich)", {"prioritaet": "keine"}),
    ("normal", {"prioritaet": "normal"}),
    ("FIXTERMIN", {"prioritaet": "FIXTERMIN"}),
]


def _as_prio(quelle):
    i = quelle.index("const AS_PRIO=")
    j = quelle.index("};", i) + 2
    return quelle[i:j]


def _programm(quelle, filter_ausdruck):
    return (
        "const COLORS={ERROR:'#ef4444'};" + chr(10)
        + _as_prio(quelle) + chr(10)
        + "const faelle = JSON.parse(process.argv[2]);" + chr(10)
        + "console.log(JSON.stringify(faelle.map(function(f){" + chr(10)
        + "  const a = f.schein;" + chr(10)
        + "  const wert = " + WERT + ";" + chr(10)
        + "  const optionen = " + filter_ausdruck + ".map(function(p){return p[0];});" + chr(10)
        + "  return {name: f.name, wert: wert, optionen: optionen," + chr(10)
        + "          dabei: optionen.indexOf(wert) >= 0," + chr(10)
        + "          gezeigt: optionen.indexOf(wert) >= 0 ? wert : (optionen[0] || null)};" + chr(10)
        + "})));" + chr(10))


def _lauf(programm, tmp_path, name):
    p = tmp_path / name
    p.write_text(programm, encoding="utf-8")
    r = subprocess.run(["node", str(p), json.dumps(
        [{"name": n, "schein": s} for n, s in FAELLE])],
        capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_beide_fundorte_bieten_die_gewaehlte_stufe_an():
    """Es gibt ZWEI Prioritaets-Auswahlen: die Liste und das Detailformular.

    Der zweite Fundort trug denselben Fehler in reinerer Form - dort stand der
    Wert ganz ohne Rueckfall. Eine Reparatur an einer von zwei Stellen waere
    keine gewesen; deshalb steht diese Zaehlung hier und nicht als Randnotiz.
    """
    quelle = INDEX.read_text(encoding="utf-8")
    fundorte = quelle.count('Object.entries(AS_PRIO).filter(([k])=>')
    assert fundorte == 2, (
        "Erwartet werden ZWEI Prioritaets-Auswahlen (Liste und Detailformular), "
        "gefunden: %d. Kommt eine dritte dazu, gehoert sie in FAELLE und in "
        "diesen Riegel - sonst repariert der naechste wieder nur die Haelfte."
        % fundorte)
    for name, ausdruck in (("Liste", 'a.prioritaet'), ("Detailformular", 'form.prioritaet')):
        muster = ('Object.entries(AS_PRIO).filter(([k])=>k!=="keine"||('
                  + ausdruck + '||"keine")==="keine")')
        assert quelle.count(muster) == 1, (
            "%s prueft nicht den ZUSTAND, sondern wieder die Zeichenkette - "
            "genau daraus entstand v3.9.919." % name)


def test_der_gewaehlte_wert_ist_immer_unter_den_optionen(tmp_path):
    quelle = INDEX.read_text(encoding="utf-8")
    assert quelle.count(FILTER) == 1, (
        "Die Prioritaets-Auswahl der LISTE ist nicht mehr eindeutig zu finden - "
        "dieser Riegel misst dann nichts. Treffer: %d" % quelle.count(FILTER))

    aus = _lauf(_programm(quelle, FILTER), tmp_path, "jetzt.js")
    for r in aus:
        assert r["dabei"], (
            "Fall '%s': der Wert %r steht NICHT unter den Optionen %r - "
            "das Auswahlfeld zeigt dann %r, also eine Prioritaet, die niemand "
            "gesetzt hat." % (r["name"], r["wert"], r["optionen"], r["gezeigt"]))

    leer = [r for r in aus if r["name"] in ("Feld fehlt", "null", "leerer Text")]
    assert len(leer) == 3, "Die drei leeren Formen fehlen im Messaufbau"
    for r in leer:
        assert r["gezeigt"] == "keine", (
            "Fall '%s' zeigt %r statt 'keine'" % (r["name"], r["gezeigt"]))

    gesetzt = {r["name"]: r["gezeigt"] for r in aus if r["name"] in ("normal", "FIXTERMIN")}
    assert gesetzt == {"normal": "normal", "FIXTERMIN": "FIXTERMIN"}, gesetzt

    # "keine" darf NUR auftauchen, wo es gebraucht wird - sonst waere es eine
    # waehlbare Stufe geworden, und genau das wollte v3.9.798 verhindern.
    fuer_normal = next(r for r in aus if r["name"] == "normal")
    assert "keine" not in fuer_normal["optionen"], (
        "Bei einem Schein MIT Prioritaet darf 'keine' nicht waehlbar sein "
        "(v3.9.798). Optionen: %r" % fuer_normal["optionen"])


def test_gegenprobe_die_alte_bedingung_zeigt_aufgeschoben(tmp_path):
    """Ohne diese Umkehr waere nicht belegt, dass der Aufbau den Fehler SIEHT."""
    quelle = INDEX.read_text(encoding="utf-8")
    aus = _lauf(_programm(quelle, ALT_FILTER), tmp_path, "alt.js")

    kaputt = [r for r in aus if not r["dabei"]]
    assert len(kaputt) == 3, (
        "Die alte Bedingung MUSS bei den drei leeren Formen danebengreifen - "
        "sonst misst dieser Riegel nichts. Danebengegriffen: %r"
        % [r["name"] for r in kaputt])
    for r in kaputt:
        assert r["gezeigt"] == "aufgeschoben", (
            "Fall '%s' haette %r gezeigt, erwartet war 'aufgeschoben'"
            % (r["name"], r["gezeigt"]))
