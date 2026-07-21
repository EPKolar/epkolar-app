# -*- coding: utf-8 -*-
"""v3.9.773 — Zulagen-Report.

v3.9.774: Montagezulage komplett aus der App entfernt (Sebastian-Entscheid). Die Vergabe-Kacheln
(_tagBtn) und der _mzWtag-Helper sind mit weggefallen — hier bleibt nur der Pin, dass der
Entfernungszulage-Rechenkern unberührt ist.
"""


def test_rechnung_unberuehrt(index_html):
    # v3.9.785: KV-Satz klein 11,94 (Alt 11,71 war der FALSCHE Wert; KV-Blatt gueltig ab 01.01.2026). Die
    # Rechenfunktionen selbst bleiben bestehen (nur die Entfernungszulage-Menge ist jetzt 3-stufig via _ezEffTage).
    assert "taggeldAb6h:11.94," in index_html  # war 11,71 (falsch)
    for fn in ("function _kvTaggeldTag(", "function _kvZulagenMonat(", "function _pzeTagRow("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
