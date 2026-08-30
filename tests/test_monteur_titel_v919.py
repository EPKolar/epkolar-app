# -*- coding: utf-8 -*-
"""v3.9.919 - Ein abgeschnittener Monteursname sah aus wie ein vollstaendiger.

IM BROWSER GESEHEN (30.08.2026, 1440 px, echte oesterreichische Namensformen)
-----------------------------------------------------------------------------
    Maximilian Gruber-Wallner  ->  "Maximilian G"
    Alexander Steinberger      ->  "Alexander St"
    Sebastian Guenther         ->  "Sebastian Gu"
    Michael Hofbauer           ->  "Michael Hofb"
    Franz Huber                ->  "Franz Huber"   (passt)
    Ali                        ->  "Ali"           (passt)

Vier von sechs abgeschnitten - und OHNE jedes Zeichen dafuer. Kein
Auslassungszeichen, kein Titel. Zwei Monteure, deren Namen sich erst spaet
unterscheiden, waren in der Liste nicht auseinanderzuhalten: die Saat mit zwei
Testmonteuren las sich in beiden Zeilen als "Testmonteur".

**Eine abgeschnittene Lesung sah aus wie eine vollstaendige** - dieselbe
Krankheit wie die Nullen dieser Woche, nur in der Anzeige statt in der Zahl.

WARUM AUSGERECHNET DIESES FELD
------------------------------
Der Monteur ist eines der ZWEI Felder, die v3.9.918 bewusst laut gelassen hat,
weil das Dispo-Brett Termin und Monteur in EINEM updAs-Aufruf schreibt. Ein
Feld laut zu lassen, das man nicht lesen kann, waere die falsche Haelfte.

WAS NICHT GEHT (beides gemessen, nicht vermutet)
------------------------------------------------
* BREITER: die Tabelle misst bei 1440 px Fenster bereits 1430 px.
* AUSLASSUNGSZEICHEN: `text-overflow: ellipsis` wird auf einem select als
  berechneter Stil gemeldet, aber NICHT gezeichnet. Im Bild nachgesehen - die
  Zeile mit der Regel bricht genauso stumm ab wie die ohne.

Deshalb ein `title`: kostet keine Breite, macht den Wert WIEDERHERSTELLBAR.

WAS DIESER RIEGEL MISST
-----------------------
Nicht, dass irgendwo das Wort title steht, sondern dass der Ausdruck den
richtigen Namen LIEFERT. Er wird woertlich aus index.html geschnitten und mit
Node ausgefuehrt - auch fuer die beiden Faelle, in denen es keinen Namen gibt.
"""
import json
import subprocess

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"

ANFANG = 'title: (((monteure||[]).find(_m=>_m.id===a.monteur)||{}).n)||"kein Monteur"'

MONTEURE = [
    {"id": "M1", "n": "Michael Hofbauer"},
    {"id": "M2", "n": "Maximilian Gruber-Wallner"},
    {"id": "M3", "n": ""},
]

FAELLE = [
    ("zugewiesen", "M1", "Michael Hofbauer"),
    ("langer Name", "M2", "Maximilian Gruber-Wallner"),
    ("kein Monteur", "", "kein Monteur"),
    ("unbekannte Kennung", "M9", "kein Monteur"),
    ("Name leer", "M3", "kein Monteur"),
]


def _ausdruck(quelle):
    i = quelle.index(ANFANG)
    return quelle[i + len("title: "):i + len(ANFANG)]


def test_der_titel_nennt_den_vollen_namen(tmp_path):
    quelle = INDEX.read_text(encoding="utf-8")
    assert quelle.count(ANFANG) == 1, (
        "Der Titel am Monteur-Feld ist nicht mehr eindeutig zu finden - "
        "dieser Riegel misst dann nichts. Treffer: %d" % quelle.count(ANFANG))

    ausdruck = _ausdruck(quelle)
    programm = (
        "const monteure = " + json.dumps(MONTEURE) + ";" + chr(10)
        + "const faelle = JSON.parse(process.argv[2]);" + chr(10)
        + "console.log(JSON.stringify(faelle.map(function(f){" + chr(10)
        + "  const a = {monteur: f.monteur};" + chr(10)
        + "  return {name: f.name, titel: (" + ausdruck + ")};" + chr(10)
        + "})));" + chr(10))

    p = tmp_path / "titel.js"
    p.write_text(programm, encoding="utf-8")
    r = subprocess.run(
        ["node", str(p), json.dumps([{"name": n, "monteur": m} for n, m, _ in FAELLE])],
        capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    aus = {z["name"]: z["titel"] for z in json.loads(r.stdout)}

    for name, _, erwartet in FAELLE:
        assert aus[name] == erwartet, (
            "Fall '%s': Titel ist %r, erwartet %r" % (name, aus[name], erwartet))

    # Der Titel darf NIE leer sein - ein leerer Titel ist genau der Zustand,
    # den dieser Riegel abschaffen soll: der Name waere unwiederbringlich.
    assert all(aus.values()), (
        "Ein leerer Titel ist kein Titel - dann ist der abgeschnittene Name "
        "wieder unwiederbringlich. %r" % aus)


def test_gegenprobe_ohne_titel_ist_der_name_verloren(tmp_path):
    """Belegt, dass dieser Riegel den Zustand VOR v3.9.919 ueberhaupt sieht."""
    quelle = INDEX.read_text(encoding="utf-8")
    ohne = quelle.replace(ANFANG + ", ", "", 1)
    assert ohne != quelle, "Die Umkehr hat nichts entfernt - der Riegel misst nichts"
    assert ANFANG not in ohne, "Der Titel steht noch da - die Umkehr griff nicht"
