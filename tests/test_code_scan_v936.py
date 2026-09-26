# -*- coding: utf-8 -*-
"""v3.9.936 - ein Abtaster, der zu wenig findet, meldet ein gruenes Ergebnis.

WAS PASSIERT IST
────────────────
Ich habe Sebastian zweimal berichtet, im Code stehe kein `ww<600` mehr. Beide
Male falsch. Gefunden hat es er, indem er eine dieser Zeilen hereinkopiert:

    function WerkzeugView(...){ const isMob=ww<600; ...

Die Ursache war nicht der Code, sondern mein Zaehler. Er suchte
Blockkommentare mit

    re.finditer(r"/\\*[\\s\\S]*?\\*/", text)

und hielt damit JEDES `/*` fuer einen Kommentaranfang - auch das in

    accept:"application/pdf,image/*"

Dieses Sternchen wird nie geschlossen. Alles dahinter galt als Kommentar:
die letzten rund 80 kB der Datei, WerkzeugView mitten darin. Der Zaehler
meldete 0 statt 1.

Vorher hatten mir schon drei Verfahren drei verschiedene Zahlen geliefert
(31 roh, 28, 13). Dass keine davon stimmte, haette mir das Auseinanderlaufen
sagen muessen - stattdessen habe ich das plausibelste genommen.

WAS DIESER RIEGEL SICHERT
─────────────────────────
1. Ein `/*` in einer Zeichenkette eroeffnet keinen Kommentar.
2. Ein Anfuehrungszeichen in einem regulaeren Ausdruck eroeffnet keine
   Zeichenkette (daran ist die ZWEITE Fassung gescheitert: 7 von 22).
3. Die EICHPROBE besteht - und sie KANN scheitern (Koeder).
4. Bei gescheiterter Eichung wird GEWORFEN, nicht gezaehlt. Eine Zahl aus
   einem nachweislich irrenden Abtaster ist schlimmer als keine.
"""
import io

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(WURZEL / "scripts"))
from code_scan import ist_code, eichen, nur_code_stellen, alle_stellen  # noqa: E402


# ── Die zwei Fallen, die mich getroffen haben ─────────────────────────────

def test_ein_sternchen_in_einer_zeichenkette_ist_kein_kommentar():
    """DIE Falle. accept:"application/pdf,image/*" hat 80 kB verschluckt."""
    t = 'var a=1;var b="application/pdf,image/*";var isMob=ww<600;'
    feld = ist_code(t)
    i = t.index("ww<600")
    assert feld[i], (
        "Das Sternchen in der Zeichenkette hat einen Kommentar eroeffnet - "
        "genau der Fehler, der WerkzeugView 80 kB weit unsichtbar machte.")


def test_ein_anfuehrungszeichen_im_regex_ist_keine_zeichenkette():
    """Die Falle der ZWEITEN Fassung: 7 von 22 statt 22 von 22."""
    t = 'var r=/[\'"]/g;var isMob=ww<600;'
    feld = ist_code(t)
    i = t.index("ww<600")
    assert feld[i], (
        "Das Anfuehrungszeichen im regulaeren Ausdruck hat eine Zeichenkette "
        "eroeffnet, die nie geschlossen wird.")


def test_ein_echter_blockkommentar_wird_erkannt():
    """Gegenprobe: der Abtaster darf nicht einfach alles Code nennen."""
    t = 'var a=1;/* hier steht ww<600 im Kommentar */var b=2;'
    feld = ist_code(t)
    i = t.index("ww<600")
    assert not feld[i], "Ein echter Blockkommentar wurde als Code gelesen."


def test_ein_zeilenkommentar_wird_erkannt():
    t = 'var a=1;// ww<600 stand hier mal\nvar b=2;'
    feld = ist_code(t)
    assert not feld[t.index("ww<600")]
    assert feld[t.index("var b")]


def test_eine_division_bleibt_code():
    """Ein / ist nicht immer ein Regex-Anfang.

    Wer jedes / als Regex liest, verschluckt den Rest der Zeile.
    """
    t = 'var x=a/b;var isMob=ww<600;'
    feld = ist_code(t)
    assert feld[t.index("ww<600")], "Eine Division wurde als Regex gelesen."


def test_ein_vorlagenliteral_mit_ausdruck_ist_innen_code():
    t = 'var s=`farbe:${V.bg}`;var isMob=ww<600;'
    feld = ist_code(t)
    assert feld[t.index("V.bg")], "Der Ausdruck im Vorlagenliteral ist Code."
    assert not feld[t.index("farbe")], "Der Text davor ist keine Anweisung."
    assert feld[t.index("ww<600")]


# ── Die Eichprobe ─────────────────────────────────────────────────────────

def test_die_eichprobe_besteht_am_echten_bestand():
    s = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    ok, gefunden, erwartet = eichen(s)
    assert ok, (
        "Die Eichung ist gescheitert: %d von %d isMob-Deklarationen als Code "
        "erkannt. Solange das so ist, darf keine Zahl aus diesem Abtaster "
        "berichtet werden." % (gefunden, erwartet))
    assert erwartet >= 20, (
        "Nur %d Deklarationen als Grundgesamtheit - zu wenig, um etwas zu "
        "belegen. Eine leere Probe besteht immer." % erwartet)


def test_die_eichprobe_kann_scheitern(monkeypatch):
    """KOEDER. Eine Probe, die nie scheitert, belegt nichts.

    Der Abtaster wird absichtlich blind gemacht; die Eichung MUSS das
    melden, und die Auskunft MUSS verweigert werden.
    """
    import code_scan
    monkeypatch.setattr(code_scan, "ist_code",
                        lambda t: bytearray(len(t)))     # alles "kein Code"
    t = "var isMob=ww<600;{}\nvar isMob=ww<600;"
    ok, gefunden, _erwartet = code_scan.eichen(t)
    assert not ok, "Ein blinder Abtaster hat die Eichung bestanden."
    assert gefunden == 0
    with pytest.raises(SystemExit) as e:
        code_scan.nur_code_stellen(t, "ww<600")
    assert "EICHUNG GESCHEITERT" in str(e.value)
    with pytest.raises(SystemExit):
        code_scan.alle_stellen(t, "ww<600")


# ── Die Zahl, um die es ging ──────────────────────────────────────────────

def test_im_code_steht_keine_nackte_600er_schwelle_mehr():
    """Jetzt mit einem Abtaster, der sich vorher ausweisen muss."""
    s = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    treffer = nur_code_stellen(s, "ww<600")
    assert not treffer, (
        "%d nackte ww<600 im Code: %s" % (len(treffer), treffer))
    alle = alle_stellen(s, "ww<600")
    assert alle, (
        "Kein einziges ww<600 gefunden - auch nicht in Kommentaren. Dann "
        "misst dieser Riegel nichts: die drei Changelog-Nennungen muessen da "
        "sein.")
