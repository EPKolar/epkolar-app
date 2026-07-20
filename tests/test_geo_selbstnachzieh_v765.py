# -*- coding: utf-8 -*-
"""v3.9.765 — Register #19b: Geo-Selbstnachzieh (Nominatim + OSRM -> plz_geo/plz_distanz).

Fehlende Geo/Matrix im Hintergrund nachziehen, damit #28 (Fahrminuten) echte Daten bekommt.
Nominatim (max 1/s, nur Misses) -> plz_geo INSERT; OSRM /table (Firma 3470 + offene-Scheine-PLZ mit geo,
<=50 Koordinaten/Lauf, unter OSRM-<=80-Limit) -> plz_distanz INSERT. CSP connect-src += OSRM-Host
(Nominatim war schon drin). Rate-limitiert, inflight-/timeout-geguardet -> nie haengen. Nur Misses
(keine Netz-Last fuer bekannte PLZ). Kein arbeitsscheine-Write (Whitelist bleibt 5), kein Push/OFFA.
"""
import re
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


# ---------------------------------------------------------------- static

def test_csp_hosts(index_html):
    m = re.search(r"connect-src[^;\"]*", index_html)
    assert m, "connect-src nicht gefunden"
    cs = m.group(0)
    assert "https://nominatim.openstreetmap.org" in cs, "Nominatim-Host fehlt in connect-src"
    assert "https://router.project-osrm.org" in cs, "OSRM-Host fehlt in connect-src (#19b)"


def test_helfer_und_export(index_html):
    for fn in ("function _geoMisses(", "function _distPairMisses(", "function _osrmParse(",
               "function _geoPlzOk(", "async function _geoSelbstnachzieh("):
        assert fn in index_html, "%s fehlt" % fn
    assert "window._geoMisses=_geoMisses" in index_html, "kein window-Export der Geo-Helfer"


def test_selbstnachzieh_guards(index_html):
    m = re.search(r"async function _geoSelbstnachzieh\([\s\S]+?\n\}", index_html)
    assert m, "_geoSelbstnachzieh-Koerper nicht gefunden"
    body = m.group(0)
    assert "if(_geoNachziehLaeuft)return" in body, "kein Inflight-Guard (nie doppelt)"
    assert "navigator.onLine===false" in body, "kein Offline-Guard"
    assert "1100" in body, "keine 1/s-Rate-Limit-Pause (Nominatim-Policy)"
    assert "_fT(" in body and "8000" in body and "15000" in body, "keine Timeouts (nie haengen)"
    assert "_geoMisses(scheinePlz,geoMap)" in body, "geocodet nicht nur Misses"
    assert ".slice(0,50)" in body, "OSRM-Koordinaten nicht auf <=50/Lauf begrenzt"
    assert '_sbPost("plz_geo"' in body and '_sbPost("plz_distanz"' in body, "schreibt nicht plz_geo/plz_distanz"
    assert "arbeitsscheine" not in body, "beruehrt arbeitsscheine (verboten — Whitelist)"
    assert "juprowa" not in body.lower(), "beruehrt Juprowa/OFFA (verboten)"


# ---------------------------------------------------------------- node-eval

_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout, (r.stdout or "") + (r.stderr or "")


def test_pure_helfer(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
// _geoPlzOk: nur 4-stellige PLZ:
ok(_geoPlzOk('3470')===true && _geoPlzOk('347')===false && _geoPlzOk('')===false && _geoPlzOk(3470)===false,'PLZ-Format');

// _geoMisses: offene-PLZ ohne geo, dedupliziert, nur gueltige:
var geo={'3470':{lat:1,lon:2}};
var miss=_geoMisses(['3470','3001','3001','abc','','3002'],geo);
ok(miss.length===2 && miss.indexOf('3001')>=0 && miss.indexOf('3002')>=0,'Misses = 3001,3002 (3470 hat geo, dupe+invalid raus): '+JSON.stringify(miss));
ok(_geoMisses(['3470'],geo).length===0,'keine Misses wenn alles geo hat');

// _distPairMisses: nur PLZ MIT geo, fehlende Paare, max-Cap:
var geo2={'3470':{},'3001':{},'3002':{}};
var dm={'3001|3470':{km:5,min:8}};  // ein Paar bekannt
var pm=_distPairMisses('3470',['3001','3002'],geo2,dm);
// Paare: 3470-3001(bekannt), 3470-3002(fehlt), 3001-3002(fehlt) -> 2 Misses
ok(pm.length===2,'2 fehlende Paare, war '+pm.length);
ok(_distPairMisses('3470',['3001','3002'],geo2,dm,1).length===1,'max-Cap greift');
// PLZ ohne geo werden ignoriert:
ok(_distPairMisses('3470',['9999'],geo2,{}).length===0,'9999 ohne geo raus -> nur 3470 -> 0 Paare');

// _osrmParse: durations(s)/distances(m) -> Zeilen, min>=1, nur i<j:
var resp={durations:[[0,600,1200],[600,0,300],[1200,300,0]], distances:[[0,10000,20000],[10000,0,5000],[20000,5000,0]]};
var rows=_osrmParse(resp,['3470','3001','3002']);
ok(rows.length===3,'3 Paare (i<j) aus 3x3-Matrix, war '+rows.length);
var r01=rows.filter(function(r){return r.plz_a==='3470'&&r.plz_b==='3001';})[0];
ok(r01 && r01.min===10 && r01.km===10,'3470-3001: 600s->10min, 10000m->10km: '+JSON.stringify(r01));
ok(_osrmParse(null,['a']).length===0 && _osrmParse({durations:[[0]]},null).length===0,'robust gegen leer');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "geo765.js")
