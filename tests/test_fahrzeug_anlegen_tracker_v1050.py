# -*- coding: utf-8 -*-
"""19.11.: "+ Fahrzeug" - das Anlege-Formular zeigte den GPS-Tracker-Block (v3.9.689), der selFz.tracker_imei
liest. Beim Anlegen gibt es kein selFz -> TypeError, die Fahrzeug-Ansicht brach. Der Block steht jetzt nur bei
einem bestehenden Fahrzeug (selFz&&...)."""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


def _tracker_block_geschuetzt(src):
    i = src.index('"GPS-Tracker")')
    vor = src[max(0, i - 700):i]
    j = vor.rfind("React.createElement('div', { style: {marginBottom:10,padding:10")
    assert j >= 0
    return bool(re.search(r"selFz&&(/\*.*?\*/)?$", vor[:j], re.S))


def test_tracker_block_nur_mit_fahrzeug():
    src = io.open(PFAD, encoding="utf-8", newline="").read()
    assert _tracker_block_geschuetzt(src)


def test_umkehrprobe_ohne_schutz():
    src = io.open(PFAD, encoding="utf-8", newline="").read()
    kaputt = re.sub(r"selFz&&/\*[^*]*?\*/(React\.createElement\('div', \{ style: \{marginBottom:10,padding:10)", r"\1", src, count=1)
    assert kaputt != src
    assert not _tracker_block_geschuetzt(kaputt)
