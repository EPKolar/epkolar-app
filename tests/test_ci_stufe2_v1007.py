# -*- coding: utf-8 -*-
"""v3.9.1007 - CI Stufe 2: Farbe nur bei Status, Satzschreibung, ruhige Karte.

Riegel auf die EIGENSCHAFT: in den genannten Bereichen steht keine
Zierfarbe mehr (Hex-Bunt ohne Statusbedeutung), keine Versalien-Beschriftung,
kein Verlauf. Statusfarben laufen ueber UI.fehler / UI.achtungTxt (AA).
"""
import re

ZIER = ("#3b82f6", "#0ea5e9", "#6366f1", "#8b5cf6", "#a855f7", "#ec4899",
        "#14b8a6", "#d97706", "COLORS.INFO")


def _bereich(html, a, e):
    i = html.find(a)
    j = html.find(e, i)
    assert i != -1 and j > i, (a, e)
    return html[i:j]


def test_home_kennzahlen_ohne_zierfarbe_und_versalien(index_html):
    b = _bereich(index_html, "/* ═══ KPIs ═══ */", "dv('kpis')&&lastRefresh")
    code = re.sub(r"/\*[\s\S]*?\*/", "", b)
    for f in ZIER:
        assert f not in code, "Zierfarbe %s in den Home-Kennzahlen" % f
    assert 'textTransform:"uppercase"' not in code


def test_home_baustellenkarten_ohne_zierfarbe(index_html):
    b = _bereich(index_html, "/* ═══ MEINE BAUSTELLEN", "/* ═══ MEIN FAHRZEUG")
    code = re.sub(r"/\*[\s\S]*?\*/", "", b)
    for f in ZIER + ("#f97316", "#22c55e"):
        assert f not in code, "Zierfarbe %s auf den Baustellenkarten" % f
    assert "background:UI.marke" in code, "Fortschrittsbalken nicht Markengruen"


def test_begruessung_ohne_verlauf(index_html):
    b = _bereich(index_html, "/* ═══ HERO GREETING ═══ */", "/* Weather Strip")
    code = re.sub(r"/\*[\s\S]*?\*/", "", b)
    assert "linear-gradient" not in code
    assert "...CC()" in code


def test_kpi_beschriftung_in_satzschreibung(index_html):
    i = index_html.find("function Kpi({label,value,sub,color,onClick,i,title,trend}){")
    rumpf = index_html[i:index_html.find("\n}", i)]
    zeile = [z for z in rumpf.split("\n") if "}}, label)" in z]
    assert len(zeile) == 1
    assert "uppercase" not in zeile[0]
    assert "fontSize:UI.fMeta" in zeile[0], "Beschriftung unter 12 px?"


def test_planung_ma_zaehler_nicht_blau(index_html):
    for z in ("const mc=maPerDay[d]||0;", "const maC=maPerDay[d]||0;"):
        i = index_html.find(z)
        assert i != -1
        assert "#3b82f6" not in index_html[i:i + 2200], z


def test_umkehrprobe(index_html):
    kaputt = index_html.replace('width:pct+"%",background:UI.marke}}', 'width:pct+"%",background:"#3b82f6"}}', 1)
    assert kaputt != index_html
    try:
        test_home_baustellenkarten_ohne_zierfarbe(kaputt)
    except AssertionError:
        return
    raise AssertionError("Umkehrprobe: Riegel schlaegt nicht an")
