# -*- coding: utf-8 -*-
"""PWA-Navigation (Owner 24.11.2026): Buero-Portal, Flotte, Kameras als eigene Reiter am Rechner.

Am Rechner (ab 1200 px, dieselbe Grenze wie _isTabletNav) stehen die drei Bereiche
gleich hinter Abwesenheiten in der Reiterleiste und NICHT mehr im Mehr. Handy und
Tablet bleiben wie bisher. Passt die erweiterte Zeile nicht ganz, gehen die drei als
Gruppe zurueck ins Mehr. Rollen unveraendert: die Aufteilung arbeitet auf der bereits
gefilterten Reiterliste.

Ausgefuehrt in Node: die ECHTE Reiterliste (_allTabs), der ECHTE Rollenfilter,
hasPerm/canDo/ROLES/_kamRolle, _layoutStufe und die drei ECHTEN App-Zeilen
_navTeil/_navSicht/_navMehr. Jeder Riegel mit Umkehrprobe.
"""
import io
import json
import os

import pytest

from conftest import run_node_snippet

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
DREI = ["bueroexport", "flotte", "kameras"]
BASIS = ["_home", "projekte", "arbeitsscheine", "wochenplanung", "zeiterfassung", "urlaub"]

Z_TEIL = "const _navTeil=_navTeilBreit(tabs,ww,_navN);"
Z_SICHT = "const _navSicht=isMob?tabs:_navTeil.haupt.slice(0,_navN);"
Z_MEHR = "const _navMehr=isMob?[]:_navTeil.haupt.slice(_navN).concat(_navTeil.mehr);"
Z_PN = "const _pnTeil=_navTeilBreit(navTabsAlle||navTabs||[],ww,_pnN);"
FILTER_KAM = 'if(t.perm==="kameras")return _kamFlag&&!!_kamRolle(curUser);'


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _ab(src, a, b, mit_b=False):
    i = src.index(a)
    j = src.index(b, i)
    return src[i:j + (len(b) if mit_b else 0)]


def _harness(src):
    teile = [
        "var window={innerWidth:0,innerHeight:0};",
        "var COLORS={ERROR:'#e'};var V={ac:'#a'};var FINKZEIT_ENABLED=true;var _bauproOffenCount=0;",
        _ab(src, "const ROLES={", "\n};", True),
        _ab(src, "function hasPerm(user,mod){", "\nfunction canDo("),
        _ab(src, "function canDo(action,user,ownerId){", "\n\n// "),
        _ab(src, "var KAMERA_ROLLEN=", "\n", True),
        _ab(src, "function _kamRolle(user){", "\n}", True),
        _ab(src, "const BP_MOB=600;", "const BP_MOB=600;", True),
        _ab(src, "const BP_BREIT=", "function _grobZeiger("),
        _ab(src, "const NAV_HAUPT=", "if(typeof window!=='undefined')window._navTeilBreit=_navTeilBreit;"),
    ]
    app = _ab(src, "\n function App(){", "\n} exports.default = App;")
    for z in (Z_TEIL, Z_SICHT, Z_MEHR, FILTER_KAM):
        assert app.count(z) == 1, z
    reiter = _ab(app, "const _allTabs=[", "\n  ];", True)
    filt = _ab(app, "const tabs=curUser?_allTabs.filter(", "}):[];", True)
    teile.append(
        "function lauf(curUser,_kamFlag,ww,_navN,aktivPerm){" + reiter + "\n" + filt + "\n"
        "var isMob=_layoutStufe(ww,800)===\"schmal\";\n"
        + Z_TEIL + Z_SICHT + Z_MEHR +
        "var safeKat=tabs.findIndex(function(t){return t.perm===aktivPerm;});"
        "var p=function(l){return l.map(function(t){return t.perm;});};"
        "var aktivOben=_navSicht.filter(function(c){return tabs.indexOf(c)===safeKat;});"
        "var aktivMehr=_navMehr.filter(function(t){return tabs.indexOf(t)===safeKat;});"
        "return {tabs:p(tabs),sicht:p(_navSicht),mehr:p(_navMehr),aktivOben:p(aktivOben),aktivMehr:p(aktivMehr)};}"
    )
    return "\n".join(teile)


def _lauf(node_exe, src, faelle):
    js = _harness(src) + "\nprocess.stdout.write(JSON.stringify(" + json.dumps(faelle) + \
        ".map(function(f){return lauf(f[0],f[1],f[2],f[3],f[4]);})));"
    return json.loads(run_node_snippet(node_exe, js))


ADMIN = {"id": "a", "role": "admin", "rolle": "Geschaeftsfuehrer"}
BUERO = {"id": "b", "role": "buero"}
PL = {"id": "p", "role": "projektleiter"}
MONTEUR = {"id": "m", "role": "monteur"}
HELFER = {"id": "h", "role": "helfer"}


def _pruefe_breit_admin(r):
    assert r["sicht"] == BASIS + DREI, r["sicht"]
    for p in DREI:
        assert p not in r["mehr"], ("doppelt im Mehr", p)
    assert sorted(r["sicht"] + r["mehr"]) == sorted(r["tabs"]), "Bereich verloren/doppelt"


def test_breit_admin_drei_oben_nicht_im_mehr(roh, node_exe):
    r = _lauf(node_exe, roh, [[ADMIN, True, 1440, 99, "_home"], [ADMIN, True, 1200, 99, "_home"]])
    for x in r:
        _pruefe_breit_admin(x)
        assert "_chef" in x["mehr"] and "admin" in x["mehr"] and "fahrzeuge" in x["mehr"]


def test_breit_rollen_wie_im_mehr(roh, node_exe):
    """Jede Rolle sieht oben genau die der drei, die sie heute im Mehr sah."""
    rollen = [ADMIN, BUERO, PL, MONTEUR, HELFER]
    for flag in (True, False):
        heute = _lauf(node_exe, roh, [[u, flag, 1000, 99, "_home"] for u in rollen])  # Tablet = Stand heute
        breit = _lauf(node_exe, roh, [[u, flag, 1440, 99, "_home"] for u in rollen])
        for u, h, b in zip(rollen, heute, breit):
            assert h["tabs"] == b["tabs"], u
            erwartet = [p for p in DREI if p in h["mehr"]]
            assert [p for p in b["sicht"] if p in DREI] == erwartet, (u, flag)
            assert not [p for p in b["mehr"] if p in DREI], (u, flag)
            assert sorted(b["sicht"] + b["mehr"]) == sorted(b["tabs"]), u


def test_monteur_sieht_kameras_und_buero_portal_nirgends(roh, node_exe):
    r = _lauf(node_exe, roh, [[u, True, w, 99, "_home"] for u in (MONTEUR, HELFER) for w in (390, 1000, 1440)])
    for x in r:
        for p in ("kameras", "bueroexport", "flotte"):
            assert p not in x["tabs"] and p not in x["sicht"] and p not in x["mehr"], (p, x)


def test_schmal_und_tablet_unveraendert(roh, node_exe):
    r = _lauf(node_exe, roh, [[ADMIN, True, 390, 99, "_home"], [ADMIN, True, 599, 99, "_home"],
                              [ADMIN, True, 800, 99, "_home"], [ADMIN, True, 1199, 99, "_home"]])
    handy, handy2, tab, tab2 = r
    for h in (handy, handy2):  # Handy: obere Leiste traegt die volle Liste (per CSS aus), Mehr leer - wie bisher
        assert h["sicht"] == h["tabs"] and h["mehr"] == []
    for t in (tab, tab2):
        assert t["sicht"] == BASIS
        for p in DREI:
            assert p in t["mehr"]


def test_kein_platz_drei_gehen_als_gruppe_ins_mehr(roh, node_exe):
    """Platzmesser senkt n unter die Laenge der erweiterten Zeile: keine Teilmenge der drei oben."""
    r = _lauf(node_exe, roh, [[ADMIN, True, 1440, n, "_home"] for n in (8, 7, 6, 5)])
    for n, x in zip((8, 7, 6, 5), r):
        assert not [p for p in x["sicht"] if p in DREI], (n, x["sicht"])
        assert x["sicht"] == BASIS[:min(n, 6)]
        for p in DREI:
            assert x["mehr"].count(p) == 1
        assert sorted(x["sicht"] + x["mehr"]) == sorted(x["tabs"])


def test_aktiv_markiert_den_oberen_reiter(roh, node_exe):
    r = _lauf(node_exe, roh, [[ADMIN, True, 1440, 99, p] for p in DREI])
    for p, x in zip(DREI, r):
        assert x["aktivOben"] == [p] and x["aktivMehr"] == [], (p, x)
    # dieselbe Markierung wie jeder Hauptreiter: safeKat===ri -> UI.marke-Unterstrich, aria-current
    app = _ab(roh, "\n function App(){", "\n} exports.default = App;")
    leiste = _ab(app, "_navSicht.map((c,mi)=>{", "!isMob&&React.createElement(NavMehr,")
    for teil in ("const _isActive=safeKat===ri;", "onClick: ()=>{setKat(ri);setMoreOpen(false);}",
                 "'aria-current': _isActive?\"page\":undefined", "borderBottom:\"3px solid \"+(_isActive?UI.marke:\"transparent\")",
                 "_ik(c.ik,16), c.l"):
        assert leiste.count(teil) == 1, teil


def test_projektakte_nutzt_dieselbe_aufteilung(roh):
    i = roh.index("\nfunction ProjectShell(")
    ps = roh[i:roh.index("\nfunction ", i + 5)]
    assert ps.count(Z_PN) == 1
    assert ps.count("const _pnSicht=isMob?(navTabs||[]):_pnTeil.haupt.slice(0,_pnN);") == 1
    assert ps.index("const [_pnN,_setPnN]=") < ps.index(Z_PN)


def test_schwelle_gleich_isTabletNav(roh):
    assert roh.count("const NAV_BREIT_AB=1200;") == 1
    assert roh.count("const _isTabletNav=ww>=600&&ww<1200;") == 1
    assert roh.count('const NAV_BREIT_DAZU=["bueroexport","flotte","kameras"];') == 1


# ── Umkehrproben ────────────────────────────────────────────────────────────
def _kaputt(roh, alt, neu):
    assert roh.count(alt) == 1, alt
    return roh.replace(alt, neu, 1)


def test_umkehr_doppelt_im_mehr_faellt_auf(roh, node_exe):
    k = _kaputt(roh, "mehr:t.mehr.filter(function(e){return dazu.indexOf(e)<0;})", "mehr:t.mehr")
    r = _lauf(node_exe, k, [[ADMIN, True, 1440, 99, "_home"]])[0]
    with pytest.raises(AssertionError):
        _pruefe_breit_admin(r)


def test_umkehr_ohne_breiten_grenze_aendert_tablet(roh, node_exe):
    k = _kaputt(roh, "const NAV_BREIT_AB=1200;", "const NAV_BREIT_AB=600;")
    with pytest.raises(AssertionError):
        test_schmal_und_tablet_unveraendert(k, node_exe)


def test_umkehr_teilmenge_bei_platzmangel_faellt_auf(roh, node_exe):
    k = _kaputt(roh, "return n>=b.haupt.length?b:t;", "return b;")
    with pytest.raises(AssertionError):
        test_kein_platz_drei_gehen_als_gruppe_ins_mehr(k, node_exe)


def test_umkehr_kameras_ohne_rollentor_faellt_auf(roh, node_exe):
    k = _kaputt(roh, FILTER_KAM, 'if(t.perm==="kameras")return _kamFlag;')
    with pytest.raises(AssertionError):
        test_monteur_sieht_kameras_und_buero_portal_nirgends(k, node_exe)


def test_umkehr_alte_teilung_waere_rot(roh, node_exe):
    """Stand vor der Aenderung (alles ausser den sechs Hauptbereichen im Mehr) muss rot sein."""
    k = _kaputt(roh, "  if(!(ww>=NAV_BREIT_AB))return t;", "  return t;")
    with pytest.raises(AssertionError):
        test_breit_admin_drei_oben_nicht_im_mehr(k, node_exe)
    # und die App-Zeile selbst ist gepinnt: wer zur alten Teilung zurueckbaut, faellt im Harness auf
    k2 = _kaputt(roh, Z_TEIL, "const _navTeil=_navTeilen(tabs);")
    with pytest.raises(AssertionError):
        _harness(k2)


def test_umkehr_aktiv_markierung(roh, node_exe):
    k = _kaputt(roh, "const _isActive=safeKat===ri;", "const _isActive=false;")
    with pytest.raises(AssertionError):
        test_aktiv_markiert_den_oberen_reiter(k, node_exe)
