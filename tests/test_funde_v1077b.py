"""Funde 1077b - restliche Funde aus der Uebergabe 19.11.2026.

Der echte Code aus index.html laeuft in Node (keine Abschrift). Zu jedem Riegel eine Umkehrprobe:
der Rueckbau muss den Test rot machen.

1  Holter-Artikelzahlen: _sbGet schickte IMMER den Range-Kopf 0-4999. PostgREST schneidet ihn mit
   limit/offset - der Lieferantenkatalog (limit=10000&offset=...) bekam 5000 Zeilen, die zweite
   Seite (offset=5000) 416, und seit v1055 gilt 416 als Ende. Ergebnis: 5000 von 25.121 Artikeln,
   ohne Warnung. Dazu zaehlte die Haendlerliste die Artikel als Laenge einer bei 5000 gekappten
   Liste. Jetzt: eigene Grenze = kein Range-Kopf; Zaehlung ueber Content-Range (count=exact).
2  Scheine pro Monteur: Balken summierten 228, gezaehlt werden 233 Scheine - die 5 ohne Monteur
   fielen still heraus. Jetzt Balken "Ohne Monteur" / "Monteur nicht in der Liste" (je nur > 0).
"""
import json

from conftest import run_node_snippet, _extract_fn


def _fn(src, name):
    f = _extract_fn(src, name)
    assert f, name + " nicht gefunden"
    return f + "\n"


def _run(node_exe, code, expr):
    out = run_node_snippet(node_exe, code + "\nprocess.stdout.write(JSON.stringify(" + expr + "));")
    return json.loads(out)


def _run_async(node_exe, code, expr):
    out = run_node_snippet(
        node_exe,
        code + "\n(async()=>{const __r=await (" + expr + ");process.stdout.write(JSON.stringify(__r));})();")
    return json.loads(out)


# ── 1 Holter: Range-Kopf nur zur Helfer-Grenze ────────────────────────────

_STUBS = r"""
var SB_REST="https://x/rest/v1";var _calls=[];
function _sbSelFuer(t){return "";}
function _sbH(extra){var h={apikey:"k"};if(extra)Object.assign(h,extra);return h;}
async function _authRetry(fn){return fn();}
async function _netzLesen(fn){return fn();}
function _fT(o,ms){return o;}
function _netzLeseMs(){return 1000;}
function _isAuthErr(){return false;}
function _onAuthFail(){}
function _sbGrenzeMelden(t,f,rows){return rows;}
async function fetch(url,o){_calls.push({url:url,range:(o&&o.headers&&o.headers.Range)||null});return {ok:true,status:200,json:async()=>[],headers:{get:()=>null}};}
"""


def _sbget_code(src, kaputt=False):
    s = src
    if kaputt:
        s = s.replace("headers:hatGrenze?_sbH():_sbRH()", "headers:_sbRH()")
    return _STUBS + _fn(s, "_sbRH") + "async " + _fn(s, "_sbGet") + "async " + _fn(s, "_sbGetOrder")


def _probe(node_exe, code):
    return _run_async(node_exe, code,
                      '(async()=>{await _sbGet("supplier_articles_safe","select=id&limit=10000&offset=5000");'
                      'await _sbGet("projects","select=id");'
                      'await _sbGetOrder("time_entries","date.desc","select=id&limit=20");'
                      'await _sbGetOrder("time_entries","date.desc","select=id");return _calls;})()')


def test_eigene_grenze_ohne_range_kopf(index_html, node_exe):
    c = _probe(node_exe, _sbget_code(index_html))
    assert c[0]["range"] is None and "limit=10000&offset=5000" in c[0]["url"], c[0]
    assert c[1]["range"] == "0-4999" and c[1]["url"].endswith("limit=5000"), c[1]
    assert c[2]["range"] is None and "limit=5000" not in c[2]["url"], c[2]
    assert c[3]["range"] == "0-4999" and c[3]["url"].endswith("limit=5000"), c[3]


def test_umkehr_range_kopf_immer(index_html, node_exe):
    c = _probe(node_exe, _sbget_code(index_html, kaputt=True))
    assert c[0]["range"] == "0-4999", "Umkehrprobe stumm: der Rueckbau schickt keinen Range-Kopf"


def test_content_range_gesamt(index_html, node_exe):
    code = _fn(index_html, "_crGesamt")
    r = _run(node_exe, code, '[_crGesamt("0-0/25118"),_crGesamt("*/0"),_crGesamt("0-0/*"),_crGesamt(null),_crGesamt(""),_crGesamt("0-4999/25121")]')
    assert r[0] == 25118 and r[1] == 0 and r[5] == 25121
    assert r[2] is None and r[3] is None and r[4] is None  # NaN -> null in JSON


def test_haendlerzaehlung_ueber_content_range(index_html, node_exe):
    i = index_html.index("const fetchSuppliers=async()=>{")
    block = index_html[i:i + 2500]
    assert "await _saAnzahlExakt(s.id)" in block
    assert block.index("_saAnzahlExakt(s.id)") < block.index('_sbGet("supplier_articles_safe","select=id&supplier_id=eq."+s.id)')
    code = (_STUBS.replace("async function fetch", "async function _altFetch")
            + 'async function fetch(url,o){_calls.push({url:url,prefer:o.headers.Prefer||null});'
              'return {ok:true,status:206,headers:{get:(k)=>k==="content-range"?"0-0/25118":null}};}\n'
            + _fn(index_html, "_crGesamt") + "async " + _fn(index_html, "_saAnzahlExakt"))
    r = _run_async(node_exe, code, '(async()=>{const n=await _saAnzahlExakt("b1");return [n,_calls];})()')
    assert r[0] == 25118
    assert r[1][0]["prefer"] == "count=exact" and "supplier_id=eq.b1" in r[1][0]["url"] and "limit=1" in r[1][0]["url"]


# ── 2 Scheine pro Monteur: Summe der Balken = Anzahl Scheine ─────────────

def test_scheine_pro_monteur_summe(index_html, node_exe):
    code = _fn(index_html, "_asMontRest")
    expr = ('(function(){var mon=[{id:"w1",n:"A"},{id:"w2",n:"B"}];'
            'var sch=[{monteur:"w1"},{monteur:"w1"},{monteur:"w2"},{monteur:""},{monteur:null},{},{monteur:"w9"}];'
            'var rows=[{l:"A",v:2},{l:"B",v:1}];return _asMontRest(rows,mon,sch);})()')
    r = _run(node_exe, code, expr)
    assert sum(x["v"] for x in r) == 7
    assert {"l": "Ohne Monteur", "v": 3} == {k: r[2][k] for k in ("l", "v")}
    assert {"l": "Monteur nicht in der Liste", "v": 1} == {k: r[3][k] for k in ("l", "v")}
    # nichts zu ergaenzen -> keine Zusatzbalken
    r2 = _run(node_exe, code, '_asMontRest([{l:"A",v:1}],[{id:"w1"}],[{monteur:"w1"}])')
    assert len(r2) == 1


def test_scheine_pro_monteur_haengt_am_diagramm(index_html):
    i = index_html.index("const asMont=_react.useMemo.call")
    block = index_html[i:i + 400]
    assert block.startswith("const asMont=_react.useMemo.call(void 0, ()=>_asMontRest(")
    assert ",monteure,arbeitsscheine),[monteure,arbeitsscheine]);" in block


def test_umkehr_ohne_zusatzbalken(index_html, node_exe):
    kaputt = index_html.replace('if(leer>0)out.push({l:"Ohne Monteur"', 'if(false)out.push({l:"Ohne Monteur"', 1)
    assert kaputt != index_html
    r = _run(node_exe, _fn(kaputt, "_asMontRest"), '_asMontRest([],[{id:"w1"}],[{monteur:""}])')
    assert sum(x["v"] for x in r) != 1, "Umkehrprobe stumm"
