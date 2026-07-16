# -*- coding: utf-8 -*-
"""v3.9.726 — Register #15: Vorab-Optik beruhigen — Hinweis darf nicht wie ein Vorschlag aussehen.

Sebastian: NUR echte Vorschlags-Chips bekommen Rahmen/Chip-Optik.
a) Baustellen-Tag ohne Vorschlag: KEIN Kasten, kein "(Vorab möglich)"-Suffix -> dezent getoenter
   Zellhintergrund + kleine graue Zeile "🏗 <BVH>", Tooltip "Störung vorher möglich, bis <min> min".
b) Harte Blocker (🏖️/🤒/⏰/🚫) kompakt: Icon + ein Wort, ohne Box.
c) EINE Legenden-Zeile unter dem Panel-Kopf.
d) Echter Vorab-Vorschlag-Chip traegt weiter "vor 🏗 <BVH>" (Info am Vorschlag, nicht an der leeren Zelle).
"""


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


def test_legende(index_html):
    body = _panel(index_html)
    assert "⚡ Störungsdienst · 🏗 auf Baustelle (Störung vorher möglich) · 🏖️ Urlaub · 🚫 gesperrt" in body


def test_vorab_tooltip_und_kein_suffix(index_html):
    body = _panel(index_html)
    # Tooltip erklaert das Vorab-Fenster (mit DISPO_VORAB_MIN)
    assert 'Störung vorher möglich, bis "+DISPO_VORAB_MIN+" min' in body
    # Zelle zeigt nur "🏗 <BVH>" (aus tagArt), kein "(Vorab möglich)"-Suffix an der leeren Zelle
    assert '"🏗 "+_bvh' in body


def test_vorab_zelle_getoent_kein_kasten(index_html):
    body = _panel(index_html)
    assert "_cellBg" in body, "Vorab-Zelle nicht dezent getoent"


def test_echter_vorab_chip_traegt_vor_bau(index_html):
    # Der Vorschlag-Chip traegt "vor 🏗" (in _dispoPlan begruendung) — bleibt am Chip.
    assert "vor 🏗 " in index_html
