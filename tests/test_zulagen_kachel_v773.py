# -*- coding: utf-8 -*-
"""v3.9.773 — Zulagen-Report.

v3.9.774: Montagezulage komplett aus der App entfernt (Sebastian-Entscheid). Die Vergabe-Kacheln
(_tagBtn) und der _mzWtag-Helper sind mit weggefallen — hier bleibt nur der Pin, dass der
Entfernungszulage-Rechenkern unberührt ist.
"""


def test_rechnung_unberuehrt(index_html):
    assert "taggeldAb6h:11.71," in index_html
    for fn in ("function _kvTaggeldTag(", "function _kvZulagenMonat(", "function _pzeTagRow("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
