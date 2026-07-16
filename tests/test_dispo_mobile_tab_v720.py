# -*- coding: utf-8 -*-
"""v3.9.720 — Dispo P1-d (Sebastian): Dispo-Tab am Handy auffindbar.

Die AS-Sub-Tab-Leiste blendete auf isMob ALLE Labels aus (isMob?"":t.l) -> das 🗓-Icon ohne Text
erkennt niemand als Dispo. Fix: auf isMob das Label KLEIN (9px) UNTER dem Icon (column-Flex), alle
Tabs gleich, Tap-Target >=44px. Struktur-Pins (React-JSX; Optik im Browser-Smoke).
"""
import re


def _as_view(index_html):
    s = re.search(r"function\s+ArbeitsscheinView\s*\(", index_html)
    e = re.search(r"\nfunction\s+[A-Z]\w*\s*\(", index_html[s.end():])
    return index_html[s.start(): s.end() + e.start()]


def _as_tabbar(index_html):
    block = _as_view(index_html)
    i = block.index('{id:"liste",i:"📋"')
    return block[i:i + 1400]


def test_labels_nicht_mehr_ausgeblendet(index_html):
    seg = _as_tabbar(index_html)
    assert 'isMob?"":t.l' not in seg, "AS-Sub-Tabs blenden Labels auf Mobile noch aus"


def test_label_immer_gerendert(index_html):
    seg = _as_tabbar(index_html)
    # t.l wird in einem span gerendert (Label sichtbar, auch mobil)
    assert re.search(r"createElement\(\s*['\"]span['\"][^)]*\}\s*,\s*t\.l\s*\)", seg), \
        "Label t.l wird nicht mehr als eigener span gerendert"


def test_spalten_layout_auf_mobile(index_html):
    seg = _as_tabbar(index_html)
    assert 'flexDirection:isMob?"column"' in seg, "Kein column-Flex (Label unter Icon) auf Mobile"


def test_taptarget_44(index_html):
    seg = _as_tabbar(index_html)
    assert "minHeight:44" in seg, "Tap-Target <44px"
