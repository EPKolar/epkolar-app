# -*- coding: utf-8 -*-
"""v3.9.1006 CI EP: Kolar & Sohn - Riegel auf die EIGENSCHAFTEN, nicht die Schreibweise.

1. Kontrast: jede Text-Token-Paarung in Hell UND Dunkel >= 4,5:1, Knopfrand >= 3:1,
   Weiss auf dem Primaerknopf >= 4,5:1 - GERECHNET aus den Werten im Quelltext
   (WCAG 2.1 relative Leuchtdichte), mit Umkehrprobe: der alte Wert mt=#9ca3af faellt durch.
2. Knopf-Hierarchie: Exporte sind sekundaer (kein Rot/Lila/Orange in xBtn), Gefahr nur bdS.
3. color-scheme steht STATISCH im Kopf, vor dem ersten <script> (Samsung Internet
   entscheidet sein Zwangs-Dunkel beim Laden; per JS gesetzt ist zu spaet).
4. Suchfeld-Muster: der Selektor schlaegt die Handy-Regel
   input:not([type=checkbox]):not([type=radio]){padding:8px !important} - genau an ihr
   ist der v1004-Fix (paddingLeft:34) am Geraet gescheitert.
"""
import io
import os
import re

import pytest

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def kontrast(a, b):
    x, y = sorted([_lum(a), _lum(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def test_kontrastrechner_ist_geeicht():
    assert round(kontrast("#000000", "#ffffff"), 1) == 21.0
    assert round(kontrast("#ffffff", "#009640"), 2) == 3.86


def _thema(roh, name):
    m = re.search(name + r':\{(bg:"#[0-9A-Fa-f]{6}".*?)\}', roh)
    assert m, "THEMES.%s nicht gefunden" % name
    return dict(re.findall(r'(\w+):"(#[0-9A-Fa-f]{6})"', m.group(1)))


def _pruefe_thema(t):
    fehl = []
    for text in ("tx", "dm", "mt"):
        for grund in ("bg", "cd", "sb"):
            k = kontrast(t[text], t[grund])
            if k < 4.5:
                fehl.append("%s auf %s %.2f" % (text, grund, k))
    for grund in ("cd", "bg"):
        k = kontrast(t["bdK"], t[grund])
        if k < 3.0:
            fehl.append("bdK gegen %s %.2f" % (grund, k))
    return fehl


@pytest.mark.parametrize("name", ["dark", "light"])
def test_thementext_besteht_aa(roh, name):
    t = _thema(roh, name)
    fehl = _pruefe_thema(t)
    assert not fehl, "%s unter AA: %s" % (name, "; ".join(fehl))


def test_umkehrprobe_alter_hellwert_faellt_durch(roh):
    """Ohne diese Probe koennte der Riegel nie rot werden: der alte mt-Wert
    #9ca3af (2,54:1) muss scheitern."""
    t = _thema(roh, "light")
    t["mt"] = "#9ca3af"
    assert _pruefe_thema(t), "Riegel misst nichts - alter Wert besteht."


def test_ui_token_hell_und_dunkel(roh):
    m = re.search(r"const UI=\{(.*?)\};", roh, re.S)
    hell = dict(re.findall(r'(\w+):"(#[0-9A-Fa-f]{6})"', m.group(1)))
    md = re.search(r"const UI_DUNKEL=\{(.*?)\};", roh)
    assert md, "UI_DUNKEL fehlt - UI waere wieder nur hell (Projektliste im Dunkel unlesbar)."
    dunkel = dict(hell)
    dunkel.update(re.findall(r'(\w+):"(#[0-9A-Fa-f]{6})"', md.group(1)))
    assert kontrast("#ffffff", hell["knopf"]) >= 4.5
    for wert in (hell, dunkel):
        for text in ("tinte", "grau", "markeTxt", "fehler"):
            k = kontrast(wert[text], wert["grund"])
            assert k >= 4.5, "%s auf grund %.2f" % (text, k)
        assert kontrast(wert["tinte"], wert["flaeche"]) >= 4.5
    assert "Object.defineProperty(UI,k" in roh, "UI folgt dem Thema nicht."


def _block(roh, start):
    i = roh.index(start)
    return roh[i:roh.index("\r\n", i)]


def test_exporte_sind_sekundaer_und_nicht_rot(roh):
    x = _block(roh, "const xBtn=")
    for farbe in ("#ef4444", "#8b5cf6", "#f97316", "#3b82f6"):
        assert farbe not in x, "xBtn traegt wieder %s - ein Export ist keine Gefahr." % farbe
    assert "V.bdK" in x


def test_knopfstufen(roh):
    assert "linear-gradient" not in _block(roh, "const bpS=")
    assert "UI.knopf" in _block(roh, "const bpS=")
    assert "UI.fehler" in _block(roh, "const bdS=")
    assert "const btS=" in roh, "Tertiaerknopf fehlt."
    assert "minHeight:44" in _block(roh, "const _knB=")


def test_zahlen_ohne_schreibmaschine(roh):
    assert 'const mono="inherit";' in roh
    assert re.search(r"body\{[^}]*font-variant-numeric:tabular-nums", roh)


def test_color_scheme_statisch_vor_dem_ersten_script(roh):
    kopf = roh[:roh.index("</head>")] if "</head>" in roh else roh[:20000]
    i = kopf.find('<meta name="color-scheme" content="light dark">')
    assert i >= 0, "Statisches color-scheme-Meta fehlt im Kopf."
    assert i < roh.index("<script"), "Das Meta steht hinter dem ersten <script>."
    assert re.search(r":root \{[^}]*color-scheme: light dark;", roh), ":root color-scheme fehlt."


def test_suchfeld_selektor_schlaegt_die_handyregel(roh):
    assert 'input.epk-suche:not([type="checkbox"]):not([type="radio"]){padding-left:38px !important}' in roh


@pytest.mark.parametrize("anker", [
    "'aria-label': \"Projekte durchsuchen\"",
    "placeholder: \"Suche Nr, Kunde, Arbeit...\"",
    "placeholder: \"Benutzer suchen…\"",
    "placeholder:\"Suchen (Name, Lieferant, Notiz)…\"",
])
def test_die_vier_gemeldeten_suchfelder_tragen_das_muster(roh, anker):
    i = roh.index(anker)
    a = max(roh.rfind("createElement('input'", 0, i), roh.rfind("h('input'", 0, i))
    e = roh.index("}", i)
    assert "epk-suche" in roh[a:e + 200], "Suchfeld ohne Muster: %s" % anker


def test_keine_geschwister_lupe_mehr(roh):
    assert "marginRight:-26,marginLeft:8,zIndex:1,pointerEvents:\"none\"" not in roh
