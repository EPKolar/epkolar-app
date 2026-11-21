# -*- coding: utf-8 -*-
"""Stufe 11, die letzte Stufe der Breitenstufen (GF 20.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher entschieden App (Kopf/Navigation), HomeView, WeekPlan, ChartBox,
ChefDashboard, AuswertungView und KameraView selbst ueber die Breite
(isMob=ww<BP_MOB). Jetzt fragen alle die gemeinsame Stufe _layoutStufe(w,h).

Nur Darstellung - und in dieser Stufe bewusst OHNE sichtbare Aenderung:
  schmal  = genau die alte Handygrenze (599 Handy, 600 nicht)
  mittel  = wie bisher breit: an keiner der sieben Stellen bringt ein eigener
            Tablet-Zweig klar etwas (Kennzahlen 4/5 Spalten, Zweispalter und
            das 330-px-Diagrammraster passen bei 800 px hochkant bereits;
            die Planung ist eine Tabelle mit Direkt-Aendern und bleibt Tabelle;
            die Navigation hat mit _isTabletNav (600-1199) schon ihren
            Tablet-Zweig).
  breit   = wie bisher.

Benannte Ausnahmen (bleiben eigene Vergleiche, gepinnt):
  App        main-pad scrollPaddingBottom `ww<BP_MOB?` - wortgleich gepinnt in
             tests/test_scan1051_funde_v1053.py (_SP); _isTabletNav=ww>=600&&ww<1200
             ist die Navigationsgrenze (Desktop-Leiste ab 1200), keine Mobilschwelle.
  WeekPlan   _wpEng=ww<760, _wpZeile1 ww>=1200, Klebekopf ww<1200 - Spaltengrenzen
             der Planungstabelle (v3.9.944: dort fest vermessen).
  Auswertung gemeinsamer Seitentitel fontSize:window.innerWidth<BP_MOB?... (gepinnt
             in test_d9_seitenueberschriften_v956 u. a.).

Jeder Riegel mit Umkehrprobe. Rueckbau der Deklaration ergibt origin/main
(v3.9.1078, d1cbd11) byte-gleich - je ganze Komponente.
"""
import hashlib
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
HOEHE = '(typeof window!=="undefined"?window.innerHeight:0)'
KOMM = r"/\* Stufe 11 \(GF 20\.11\.2026\):.*?\*/"

KURZ = {"App": "ap", "HomeView": "hv", "WeekPlan": "wp", "ChartBox": "cb",
        "ChefDashboard": "cd", "AuswertungView": "av"}
NAMEN = list(KURZ) + ["KameraView"]


def _dekl(k):
    return 'const _%sStufe=_layoutStufe(ww,%s);const isMob=_%sStufe==="schmal";' % (k, HOEHE, k)


KA_STUFE = 'const _kaStufe=_layoutStufe(ww,' + HOEHE + ');var stufe=_kaStufe;'
KA_MOB = 'const isMob=_kaStufe==="schmal";'


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _teil(src, n):
    if n == "App":
        i = src.index("\n function App(){")
        return src[i:src.index("\n} exports.default = App;", i)]
    i = src.index("\nfunction " + n + "(")
    return src[i:src.index("\nfunction ", i + 5)]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


# ── Entscheidung: die ECHTEN Deklarationen ausgefuehrt ──────────────────────
def _entscheidung(node_exe, src, faelle):
    fns = []
    for n in NAMEN:
        v = _teil(src, n)
        if n == "KameraView":
            assert v.count(KA_STUFE) == 1 and v.count(KA_MOB) == 1
            fns.append("function KameraView(ww){" + KA_STUFE + KA_MOB + "return [stufe,isMob];}")
        else:
            d = _dekl(KURZ[n])
            assert v.count(d) == 1, n
            fns.append("function %s(ww){%sreturn [_%sStufe,isMob];}" % (n, d, KURZ[n]))
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n" + "\n".join(fns) + "\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;return ["
          + ",".join(n + "(ww)" for n in NAMEN) + "];}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(faelle)
          + ".map(function(x){return f(x[0],x[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


FAELLE = [
    ([384, 832], "schmal", True),
    ([412, 915], "schmal", True),
    ([599, 900], "schmal", True),
    ([600, 900], "mittel", False),
    ([800, 1280], "mittel", False),
    ([1280, 800], "breit", False),
    ([1920, 1080], "breit", False),
]


def test_entscheidung_alle_sieben_gleich_und_wie_vorher(roh, node_exe):
    r = _entscheidung(node_exe, roh, [f for f, _, _ in FAELLE])
    for (f, stufe, mob), zeile in zip(FAELLE, r):
        assert zeile == [[stufe, mob]] * len(NAMEN), (f, zeile)
        # isMob == alte Bedingung ww<BP_MOB
        assert all(z[1] == (f[0] < 600) for z in zeile), f


def test_umkehr_verschobene_handygrenze_waere_rot(roh, node_exe):
    kaputt = roh.replace('if(n<BP_MOB)return "schmal";', 'if(n<=BP_MOB)return "schmal";', 1)
    assert kaputt != roh
    r = _entscheidung(node_exe, kaputt, [[599, 900], [600, 900]])
    assert r != [[["schmal", True]] * len(NAMEN), [["mittel", False]] * len(NAMEN)]


# ── Rueckbau: ganze Komponente byte-gleich mit origin/main ──────────────────
MD5 = {
    "App": "0945c5465a40b3151f9661e127252869",  # 1087 Kameras Produktion: nur der Kommentar am Kamera-Schalter (KAMERAS_PROD=true, Team-Freigabe) geaendert; vorher 5d66679c1460949e9f258826c1d9d575
    "HomeView": "c86ca7b03e675361a1d9456b7f24ce52",  # 1079: Samsung-Zweig zeigt die Version ueber _verAnzeige (ohne -supabase) - bewusste Aenderung, Pruefsumme nachgezogen
    "WeekPlan": "33b42034306b2785f38e426cfc688679",  # 1085: beide Zweige zusammen - P3 (Chip bricht in mittel um) + A55 Runde 3 (Kennzeichen am Handy umbrechend, Kopf "Mo .. – Sa .."); einzeln 0aab4acb.. bzw. 41fe6254.., ohne beide aee55d9dc37dda2d1c26ccae5970eb0c
    "ChartBox": "0c795027cde4f0d474bc7d4f710eeaef",
    "ChefDashboard": "91da847b0545367d5f82b752b9ab2469",  # 1080 A55 (4): topOver ohne Kappung auf 8, Titel 'Kritisch überfällig' ohne 'die ältesten N' - bewusste Aenderung, Pruefsumme nachgezogen (Riegel in test_a55_funde_v1080.py)
    "AuswertungView": "01ec1e729f29416681c33602bfb3365c",
    "KameraView": "473255e66bb76536993ded5fa0b74cb8",  # 1088 LNA-Diagnose: Erneut pruefen stoesst den Abruf in der Nutzergeste an (_kamLnaAnstoss), Kachel-Grund lna/lna_frage (Riegel test_kamera_lna_v1088); vorher 2ccebbe69990b2c9c900567a72f7a866
}


def _md5(t):
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def _zurueck(src, n):
    v = _teil(src, n)
    if n == "KameraView":
        assert v.count(KA_STUFE) == 1
        v = v.replace(KA_STUFE, "var stufe=_layoutStufe(ww);", 1)
        m = re.search(re.escape(KA_MOB) + KOMM, v)
        assert m
        return v[:m.start()] + "var isMob=ww<BP_MOB;" + v[m.end():]
    m = re.search(re.escape(_dekl(KURZ[n])) + KOMM, v)
    assert m, "Stufen-Deklaration samt Kommentar nicht gefunden: " + n
    return v[:m.start()] + "const isMob=ww<BP_MOB;" + v[m.end():]


@pytest.mark.parametrize("n", NAMEN)
def test_rueckbau_ergibt_vorher(roh, n):
    assert _md5(_zurueck(roh, n)) == MD5[n]


@pytest.mark.parametrize("n,alt,neu", [
    ("App", "const _isTabletNav=ww>=600&&ww<1200;", "const _isTabletNav=ww>=600&&ww<1100;"),
    ("App", "const _navSicht=isMob?tabs:", "const _navSicht=_apStufe!==\"breit\"?tabs:"),
    ("HomeView", 'gridTemplateColumns:isMob?"repeat(2,1fr)":"repeat(4,1fr)"', 'gridTemplateColumns:isMob?"repeat(2,1fr)":"repeat(3,1fr)"'),
    ("WeekPlan", "const _wpEng=ww<760;", "const _wpEng=ww<800;"),
    ("ChartBox", 'maxWidth:isMob?"none":520', 'maxWidth:isMob?"none":560'),
    ("ChefDashboard", "gridTemplateColumns:isMob?'repeat(2,1fr)':'repeat(5,1fr)'", "gridTemplateColumns:isMob?'repeat(2,1fr)':'repeat(3,1fr)'"),
    ("AuswertungView", 'minmax(330px,1fr)', 'minmax(300px,1fr)'),
    ("KameraView", "var r=_kamRaster(ansicht,aktive.length,isMob);", "var r=_kamRaster(ansicht,aktive.length,stufe!==\"breit\");"),
])
def test_umkehr_jede_aenderung_waere_rot(roh, n, alt, neu):
    v = _teil(roh, n)
    assert v.count(alt) >= 1, (n, alt)
    kaputt = roh.replace(v, v.replace(alt, neu, 1), 1)
    assert _md5(_zurueck(kaputt, n)) != MD5[n]


# ── Abdeckung: keine eigenen Mobilvergleiche mehr, Ausnahmen namentlich ─────
BREITEN = re.compile(r"\bww\s*[<>]=?\s*\w+|\(ww\|\|0\)\s*[<>]|innerWidth\s*[<>]=?\s*\w+|matchMedia\([^)]*\)|userAgent")
AUSNAHMEN = {
    "App": ["ww>=600", "ww<1200", 'matchMedia("(pointer:fine)', "ww<BP_MOB"],
    "HomeView": [],
    "WeekPlan": ["matchMedia(q)", "ww<760", "ww>=1200", "ww<1200"],
    "ChartBox": [],
    "ChefDashboard": [],
    "AuswertungView": ["innerWidth<BP_MOB"],
    "KameraView": ["matchMedia('(pointer: fine)"],
}
SP_MAIN = ("React.createElement('main', { className: \"main-pad\", ...mainSwipe, style: ww<BP_MOB?{scrollPaddingBottom:"
           "\"calc(var(--epk-bar-h,58px) + var(--epk-bar-warn,24px) + env(safe-area-inset-bottom,0px))\"}:undefined}")
TITEL = "fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite"


def _breiten(src, n):
    return [m.group(0) for m in BREITEN.finditer(nur_code(_teil(src, n)))]


@pytest.mark.parametrize("n", NAMEN)
def test_abdeckung_nur_benannte_ausnahmen(roh, n):
    assert _breiten(roh, n) == AUSNAHMEN[n]


def test_ausnahmen_sind_die_gepinnten_ausdruecke(roh):
    assert _teil(roh, "App").count(SP_MAIN) == 1
    assert nur_code(_teil(roh, "App")).count("ww<BP_MOB") == 1
    assert _teil(roh, "AuswertungView").count(TITEL) == 1


@pytest.mark.parametrize("n,alt", [
    ("HomeView", 'const isMob=_hvStufe==="schmal";'),
    ("ChartBox", 'const isMob=_cbStufe==="schmal";'),
    ("KameraView", KA_MOB),
])
def test_umkehr_abdeckung_findet_alten_vergleich(roh, n, alt):
    v = _teil(roh, n)
    kaputt = roh.replace(v, v.replace(alt, "const isMob=ww<BP_MOB;", 1), 1)
    assert _breiten(kaputt, n) != AUSNAHMEN[n]


def test_umkehr_abdeckung_findet_useragent(roh):
    v = _teil(roh, "ChefDashboard")
    alt = 'const isMob=_cdStufe==="schmal";'
    kaputt = roh.replace(v, v.replace(alt, alt + "const _ua=navigator.userAgent;", 1), 1)
    assert _breiten(kaputt, "ChefDashboard") != AUSNAHMEN["ChefDashboard"]


# ── Geltungsbereich ─────────────────────────────────────────────────────────
def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


@pytest.mark.parametrize("n", NAMEN)
def test_stufe_steht_im_selben_block(roh, n):
    bl = _bloecke(roh)
    p1 = roh.index("function _layoutStufe(w,h){")
    p2 = roh.index(_teil(roh, n))
    n1 = [i for i, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [i for i, (a, b) in enumerate(bl) if a <= p2 < b]
    assert n1 and n2 and n1[0] == n2[0]


def test_isMob_vor_erster_verwendung_deklariert(roh):
    """const statt var in KameraView: keine Verwendung vor der Deklaration (TDZ)."""
    for n in NAMEN:
        code = nur_code(_teil(roh, n))
        erste = re.search(r"\bisMob\b", code)
        assert erste and code[erste.start() - 6:erste.start()] == "const ", n
