# -*- coding: utf-8 -*-
"""v3.9.1016 - Navigation kompakt (Tablet/Rechner).

Befund am Tablet 1200x1920 (CSS ~800 px), gemessen: Kopf 172 px + Reiterleiste
194 px = 29 % der Hoehe (Firmentext in 4 Zeilen, 18 Reiter in 4 Zeilen); in der
Projektansicht lagen 1392 px Reiter in einer 559 px breiten, quer rollenden
Leiste - rechts abgeschnitten. Nachher: Kopf 57 px + Leiste 54 px.

Riegel (Eigenschaften, nicht Wortlaut):
  * Rechte-Logik unveraendert: die Reiterliste und ihr Filter sind
    byte-gleich zum Stand d3c4cc6 (md5 ueber den Block, Zeilenenden normiert).
  * Jeder Bereich, den eine Rolle sieht, steht entweder in der Zeile (1 Tipp)
    oder im Mehr (2 Tipps) - genau einmal, keiner geht verloren. Am
    ausgefuehrten _navTeilen (Node) fuer jede Rollen-Teilmenge.
  * Handy unveraendert: Fussleiste und mobiles Mehr-Menue rendern wie bisher,
    die obere Leiste nimmt auf dem Handy weiter die volle Liste.
  * Mehr-Knopf barrierefrei: aria-haspopup/expanded, aria-current wenn der
    aktive Bereich im Mehr liegt, jeder Eintrag mit aria-label und 44 px.
Umkehrprobe am Ende.
"""
import hashlib
import json
import re
import subprocess


def _n(s):
    return s.replace("\r\n", "\n")


def _block(src, a, b):
    i = src.index(a)
    return src[i:src.index(b, i)]


def _ohne_zeilen(block, marke):
    return "\n".join(z for z in block.split("\n") if marke not in z)


def test_rechte_logik_der_reiter_ist_byte_gleich(index_html):
    s = _n(index_html)
    reiter = _block(s, "const _allTabs=[", "\n  ];")
    filt = _block(s, "const tabs=curUser?_allTabs.filter(", "}):[];")
    # Kameras Phase 1 (v1055): je EINE Zeile dazu (Reiter nur mit Schalter _kamFlag, Filter
    # _kamFlag && Kamerarolle). Ohne genau diese Zeilen sind beide Bloecke weiter byte-gleich zum
    # Stand d3c4cc6 - die Rechte aller bestehenden Reiter sind also nachweislich unveraendert.
    assert hashlib.md5(_ohne_zeilen(reiter, 'perm:"kameras"').encode("utf-8")).hexdigest() == "7a6b4fdfffef09e288fa08c0c84265eb"
    assert hashlib.md5(_ohne_zeilen(filt, 't.perm==="kameras"').encode("utf-8")).hexdigest() == "0d494f2313403b9e6c66f4d56fb6d44a"
    assert hashlib.md5(reiter.encode("utf-8")).hexdigest() == "988b724d88e048a036b44a3f12ae3ee8"
    assert hashlib.md5(filt.encode("utf-8")).hexdigest() == "ed11b627ce024ace3515915f45929949"


def _teilen_js(src):
    i = src.index("const NAV_HAUPT=")
    j = src.index("if(typeof window!=='undefined')window._navTeilen=_navTeilen;", i)
    return src[i:j]


def _perms(src):
    return re.findall(r'perm:"([a-z_]+)"', _block(src, "const _allTabs=[", "\n  ];"))


def _lauf(teilen, perms):
    js = teilen + ";var P=%s;var out=[];" % json.dumps(perms) + (
        "for(var m=0;m<(1<<Math.min(P.length,12));m++){var l=P.filter(function(p,i){return i>=12||(m>>i)&1;}).map(function(p){return {perm:p};});"
        "var t=_navTeilen(l);out.push([l.map(function(x){return x.perm;}),t.haupt.map(function(x){return x.perm;}),t.mehr.map(function(x){return x.perm;})]);}"
        "console.log(JSON.stringify(out));")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _pruefe(faelle):
    for liste, haupt, mehr in faelle:
        assert sorted(haupt + mehr) == sorted(liste), "Bereich verloren/doppelt: %r" % liste
        assert [p for p in liste if p in haupt] == haupt, "Reihenfolge in der Zeile veraendert"
        assert [p for p in liste if p in mehr] == mehr, "Reihenfolge im Mehr veraendert"
        assert len(haupt) <= 6


def test_jeder_bereich_genau_einmal_zeile_oder_mehr(index_html):
    perms = _perms(index_html)
    assert len(perms) >= 18
    teilen = _teilen_js(index_html)
    faelle = _lauf(teilen, perms)
    assert len(faelle) == 4096
    _pruefe(faelle)
    voll = faelle[-1]
    assert voll[1] == ["_home", "projekte", "arbeitsscheine", "wochenplanung", "zeiterfassung", "urlaub"]


def test_platzmangel_schiebt_ins_mehr_statt_zu_verlieren(index_html):
    assert "const _navSicht=isMob?tabs:_navTeil.haupt.slice(0,_navN);" in index_html
    assert "const _navMehr=isMob?[]:_navTeil.haupt.slice(_navN).concat(_navTeil.mehr);" in index_html
    assert "const _pnSicht=isMob?(navTabs||[]):_pnTeil.haupt.slice(0,_pnN);" in index_html
    assert "const _pnMehr=isMob?[]:_pnTeil.haupt.slice(_pnN).concat(_pnTeil.mehr);" in index_html
    m = _block(index_html, "function NavPlatzMesser(", "\n}")
    assert "if((umbruch||quer)&&ist>0)setN(ist-1);" in m, "Messer darf nur bis 0 zaehlen"
    assert 'addEventListener("resize"' in m


def test_handy_bleibt_unveraendert(index_html):
    assert "moreOpen&&isMob&&React.createElement" in index_html
    assert '{ik:"raster",l:"Mehr",g:4,c:"#71717a"}' in index_html
    assert 'className: "tab-bar"+(isMob?" pf-hauptnav":"")' in index_html
    assert "const moreTabs=isMob?tabs:tabs.filter(t=>t.g>=4);" in index_html
    # NavMehr/Messer nur ab Tablet
    assert index_html.count("!isMob&&React.createElement(NavMehr,") == 2
    assert index_html.count("!isMob&&React.createElement(NavPlatzMesser,") == 2
    assert "const showSep=isMob&&i>0&&t.g!==prevG;" in index_html


def test_mehr_knopf_ist_barrierefrei(index_html):
    m = _block(index_html, "function NavMehr(", "\n}")
    for teil in ("'aria-haspopup': \"true\"", "'aria-expanded': offen?\"true\":\"false\"",
                 "'aria-current': akt?\"page\":undefined", "'aria-label': c.l",
                 "minHeight:44", 'e.key==="Escape"', "ReactDOM.createPortal(", "zu(false);onWahl(c);"):
        assert teil in m, teil
    assert "if(!liste.length)return null;" in m, "leeres Mehr darf nicht erscheinen"


def test_sync_hinweis_sitzt_im_kopf_nicht_in_der_leiste(index_html):
    leiste = _block(index_html, 'className: "top-tabs"', "/* v3.9.69 S49 Riedmann-Sidebar-Fix: Mehr-Button")
    assert "window._lastJuprowaSyncAt" not in leiste
    kopf = _block(index_html, "/* v3.9.1016 Juprowa-Sync-Hinweis", "/* Sync indicator */")
    assert "window._lastJuprowaSyncAt" in kopf and "minWidth:" in kopf and 'visibility:da?"visible":"hidden"' in kopf


def test_umkehrprobe(index_html):
    teilen = _teilen_js(index_html)
    kaputt = teilen.replace("(NAV_HAUPT.indexOf(t.perm)>=0?h:m).push(t);", "if(NAV_HAUPT.indexOf(t.perm)>=0)h.push(t);", 1)
    assert kaputt != teilen
    faelle = _lauf(kaputt, _perms(index_html))
    try:
        _pruefe(faelle)
    except AssertionError:
        pass
    else:
        raise AssertionError("Umkehrprobe: verlorene Bereiche wuerden nicht auffallen")
    s = _n(index_html).replace('{l:"Flotte",ik:"standort"', '{l:"Flotte2",ik:"standort"', 1)
    assert hashlib.md5(_block(s, "const _allTabs=[", "\n  ];").encode("utf-8")).hexdigest() != "7a6b4fdfffef09e288fa08c0c84265eb"
