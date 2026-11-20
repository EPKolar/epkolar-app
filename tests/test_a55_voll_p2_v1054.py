# -*- coding: utf-8 -*-
"""A55-Vollpruefung 19.11.2026 (v3.9.1049-1051), P2-Funde.

1  Monteur-Auswahl im AS-Formular zeigte bei leerem Monteur den ERSTEN Monteur (Barger).
2  AS-Formular oeffnete unter der aufgeklappten Uebersicht ausserhalb des Bildes.
3  Dispo: Neu berechnen rechts abgeschnitten, Monteur-Zeilen mit leerem Riesenraum.
4  Chef KV-Zuschlaege: Dezimalpunkt und keine Einheit.
5  Fussleiste: Zeiterfassung ueber Mehr markierte Mehr.
6  Zeiterfassung: Umschaltknopf Einzelansicht wirkte tot.
7  Abwesenheiten: unbeschrifteter Ruecknahme-Knopf ohne Rueckfrage.
8  Klapp-Glyphen statt Linien-Ikone.
9  5 000 Artikel statt 5.000.
10 color-scheme fuer Samsung-Zwangsdunkel (nur geprueft, unveraendert).
Jede Pruefung mit Umkehrprobe.
"""
import json
import re

from conftest import run_node_snippet

FORM_KIDS_START = '_optLeer("\\u2014 ohne Monteur \\u2014")'
FORM_KIDS_END = "_maWaehlbar(monteure,form.monteur).map(m=>React.createElement('option', { key: m.id, value: m.id}, m.n))"
OLD_KIDS = FORM_KIDS_END


def _one_liner(html, name):
    m = re.search(r"function " + re.escape(name) + r"\(.*?\n", html)
    assert m, name
    return m.group(0)


def _form_kids(html):
    a = html.index(FORM_KIDS_START)
    b = html.index(FORM_KIDS_END, a) + len(FORM_KIDS_END)
    return html[a:b]


_SELECT_JS = r"""
var React={createElement:function(t,p){var c=[].slice.call(arguments,2);return {t:t,p:p||{},c:c};}};
%s
function _maWaehlbar(l,a){return l;}
function flat(a,o){o=o||[];a.forEach(function(x){if(Array.isArray(x))flat(x,o);else if(x&&x.t==='option')o.push(x);});return o;}
function txt(o){return o.c.join('');}
/* Browser-Regel: Wert ohne passende Option -> erste Option wird angezeigt */
function zeigt(kids,wert){var os=flat(kids);var t=os.filter(function(o){return String(o.p.value)===String(wert);})[0]||os[0];return {text:txt(t),value:String(t.p.value)};}
var monteure=[{id:'m1',n:'Barger'},{id:'m2',n:'Schmid'}];
var out=[];
['', 'm2', 'weg'].forEach(function(w){var form={monteur:w};out.push(zeigt([%s],w));});
console.log(JSON.stringify(out));
"""


def _run_select(node_exe, html, kids):
    helpers = "".join(_one_liner(html, n) for n in ("_optFremd", "_optNeutral", "_optLeer"))
    return json.loads(run_node_snippet(node_exe, _SELECT_JS % (helpers, kids)))


# ---------- 1 ----------
def test_1_leerer_monteur_zeigt_leer(index_html, node_exe):
    r = _run_select(node_exe, index_html, _form_kids(index_html))
    assert r[0] == {"text": "— ohne Monteur —", "value": ""}
    assert r[1] == {"text": "Schmid", "value": "m2"}
    assert r[2]["value"] == "weg" and "unbekannt" in r[2]["text"]


def test_1_umkehr_alte_auswahl_zeigt_barger(index_html, node_exe):
    r = _run_select(node_exe, index_html, OLD_KIDS)
    assert r[0] == {"text": "Barger", "value": "m1"}, "Umkehrprobe greift nicht"


def test_1_wert_und_speichern_unveraendert(index_html):
    i = index_html.index(FORM_KIDS_START)
    sel = index_html[index_html.rindex("React.createElement('select'", 0, i):i]
    assert "value: form.monteur, onChange: e=>{if(isMonteurRole&&!isAdmin)return;setForm(p=>({...p,monteur:e.target.value}));}" in sel
    # Zeilen-Auswahl der Liste: Rueckfrage-Tor und leere Option bleiben
    assert "value: a.monteur||\"\", title:" in index_html
    assert "_asZeileRueckfrage(a,\"prioritaet\",_np)" in index_html
    # Fahrzeug-Typ ohne Wert zeigte den ersten Typ - jetzt neutrale Option wie bei den Tickets
    assert "{...II(),fontSize:12}}, _optFremd(FZ_TYPEN,selFz.typ)&&_optNeutral(selFz.typ)" in index_html


# ---------- 2 ----------
def test_2_formular_rollt_ins_bild(index_html):
    assert "key: \"as-form\", 'data-as-form': \"1\", style: {scrollMarginTop:8} }" in index_html
    eff = "const _af=document.querySelector('[data-as-form=\"1\"]');if(_af&&_af.scrollIntoView){_af.scrollIntoView({block:\"start\"});}"
    assert eff in index_html


def test_2_umkehr(index_html):
    k = index_html.replace("'data-as-form': \"1\", ", "", 1)
    assert "key: \"as-form\", 'data-as-form'" not in k


# ---------- 3 ----------
def test_3_dispo_kopf_bricht_um_und_zeilen(index_html):
    assert ",h('div',{style:{display:\"flex\",gap:10,alignItems:\"center\",flexWrap:\"wrap\",minWidth:0}}" in index_html
    assert "verticalAlign:\"top\",minWidth:_dpKlebt?120:180," in index_html
    assert "fontWeight:700,whiteSpace:\"nowrap\",verticalAlign:\"top\"},_dpKlebt?{}:{position:\"sticky\",left:0,zIndex:2,background:V.cd})},m.n||\"\")" in index_html
    assert ",h('div',{style:{display:\"flex\",gap:10,alignItems:\"center\"}}\r\n" not in index_html


# ---------- 4 ----------
def test_4_kv_deutsch_mit_einheit(index_html, node_exe):
    a = index_html.index("function KVZuschlagReport")
    b = index_html.index("function AuswertungView", a)
    kv = index_html[a:b]
    assert "v>0.001?_fzDE(v,1)+' h':'—'" in kv and "_fzDE(r.zuschlagStd,1)+' h'" in kv
    assert "_n(v,1)" not in kv and "_n(r.zuschlagStd,1)" not in kv
    fz = _one_liner(index_html, "_fzDE")
    out = run_node_snippet(node_exe, fz + "console.log(JSON.stringify([_fzDE(72,1)+' h',_fzDE(783.8,1)+' h',_fzDE(1234.5,1)]));")
    assert json.loads(out) == ["72,0 h", "783,8 h", "1.234,5"]


# ---------- 5 ----------
_NAV_JS = r"""
var tabs=[{perm:'_home',g:0},{perm:'projekte',g:1},{perm:'wochenplanung',g:2},{perm:'zeiterfassung',g:2},{perm:'_chef',g:0},{perm:'flotte',g:3}];
var _fussG=function(t){return t.perm==="_chef"?4:t.g;};
var out={};
tabs.forEach(function(sh,safeKat){
  var akt=[];
  [0,1,2,3,4].forEach(function(g){var gr={g:g};var grTabs=tabs.filter(function(t){return _fussG(t)===gr.g;});
    %s
    if(isActive)akt.push(g);});
  out[sh.perm]=akt;});
console.log(JSON.stringify(out));
"""


def test_5_fussleiste_gruppe_unabhaengig_vom_weg(index_html, node_exe):
    m = re.search(r"const isActive=grTabs\.some\(t=>tabs\.indexOf\(t\)===safeKat\);", index_html)
    assert m
    assert "_fussMehrKat" not in index_html and "_viaMehr" not in index_html
    out = json.loads(run_node_snippet(node_exe, _NAV_JS % m.group(0)))
    assert out == {"_home": [0], "projekte": [1], "wochenplanung": [2], "zeiterfassung": [2], "_chef": [4], "flotte": [3]}


def test_5_umkehr_alte_regel_markiert_mehr(node_exe):
    alt = ("var _fussMehrKat=3;var _viaMehr=_fussMehrKat!==null&&_fussMehrKat===safeKat;"
           "var isActive=gr.g===4?(_viaMehr||grTabs.some(t=>tabs.indexOf(t)===safeKat)):(!_viaMehr&&grTabs.some(t=>tabs.indexOf(t)===safeKat));")
    out = json.loads(run_node_snippet(node_exe, _NAV_JS % alt))
    assert out["zeiterfassung"] == [4], "Umkehrprobe greift nicht"


# ---------- 6 ----------
def _ze_knoepfe(html):
    a = html.index("isAdmin&&React.createElement('div',{role:\"group\",'aria-label':\"Ansicht\"")
    return html[a:html.index("_zpIk(\"person\",\"Einzelansicht\")))", a)]


_ZE_JS = r"""
var viewAll=true,gemerkt=[];function setViewAll(v){viewAll=v;}function _zeAnsichtMerken(v){gemerkt.push(v);}
var bgS='G',bsS=function(){return 'S';};function _zpIk(i,t){return t;}
var React={createElement:function(t,p){var c=[].slice.call(arguments,2);return {t:t,p:p||{},c:c};}};
var isAdmin=true;
function knoepfe(){var g=__KNOEPFE__;return g.c;}
var st=[];
function tipp(i){knoepfe()[i].p.onClick();st.push(viewAll);}
tipp(1);tipp(1);tipp(0);tipp(0);
var k=knoepfe();
console.log(JSON.stringify({st:st,gemerkt:gemerkt,pressed:[k[0].p['aria-pressed'],k[1].p['aria-pressed']]}));
"""


def test_6_zwei_feste_knoepfe(index_html, node_exe):
    src = _ze_knoepfe(index_html)
    js = _ZE_JS.replace("__KNOEPFE__", src + '_zpIk("person","Einzelansicht")))')
    out = json.loads(run_node_snippet(node_exe, js))
    # zweimal Einzelansicht -> bleibt Einzelansicht (vorher hob der zweite Tipp den ersten auf)
    assert out["st"] == [False, False, True, True]
    assert out["gemerkt"] == [False, True]
    assert out["pressed"] == ["true", "false"]


def test_6_umkehr_alter_umschalter(index_html):
    assert "onClick:()=>{const _nv=!viewAll;setViewAll(_nv);_zeAnsichtMerken(_nv);}" not in index_html


# ---------- 7 ----------
def test_7_ruecknahme_beschriftet_mit_rueckfrage(index_html):
    a = index_html.index("showActions&&isAdmin&&e.approval!==\"ausstehend\"&&(React.createElement('button'")
    b = index_html.index("_zpIk(\"drehen\",\"Zurücknehmen\",16)))", a)
    k = index_html[a:b]
    i_conf = k.index("if(!(await window._confirmModal(")
    i_push = k.index("SQ.push({url:\"/api/absences/\"+encodeURIComponent(k),method:\"PUT\",body:{status:\"ausstehend\",approved_by:\"\"}});")
    assert i_conf < i_push
    assert "'aria-label': (e.approval===\"genehmigt\"?\"Genehmigung\":\"Ablehnung\")+\" zurücknehmen: \"" in k
    assert "_ik(\"drehen\",16)))" not in index_html[a:a + 2000]


# ---------- 8 ----------
ALT_GLYPHEN = [
    '_kachelAuf?"▾":"▸"', '"▲ Kompakt":"▼ Details"', '"▾ Weniger":"▸ Weitere…"', '"▼ Zeitabgleich":"▶ Zeitabgleich"',
    "(ohneOpen?'▾ ':'▸ ')", "(listOpen?'▾ ':'▸ ')", "transform:_secOpen(id)?'rotate(90deg)':'none'}},'▸')",
    'transform:isOpen?"rotate(90deg)":"rotate(0deg)"}}, "▸")', 'transform:sysOpen?"rotate(180deg)":"rotate(0)",color:V.dm}}, "▼")',
    'transform:isDetail?"rotate(180deg)":"rotate(0)",transition:"transform .2s"}}, "▼")',
    'transform:isOpen?"rotate(180deg)":"rotate(0)",transition:"transform .2s"}}, "▼")',
    'transform:isOpen?"rotate(180deg)":"rotate(0)"}}, "▼")',
]


def test_8_keine_klapp_glyphen(index_html):
    for g in ALT_GLYPHEN:
        assert g not in index_html, g
    for neu in ("_klappIk(_kachelAuf,16)", "_klappIk(kontExpanded,16)", "_klappIk(showMoreTyp,16)", "_klappIk(expandedZ===z.id,16)",
                "_klappIk(ohneOpen,14)", "_klappIk(listOpen,16)", "_klappIk(!!_secOpen(id),16)", "_klappIk(sysOpen,16)",
                "_klappIk(isDetail,16)"):
        assert neu in index_html, neu
    assert index_html.count("'aria-expanded': isDetail") == 2
    assert "'aria-expanded':!!_secOpen(id)" in index_html


def test_8_umkehr(index_html):
    k = index_html.replace("_klappIk(kontExpanded,16), kontExpanded?\"Kompakt\":\"Details\"", "kontExpanded?\"▲ Kompakt\":\"▼ Details\"")
    assert any(g in k for g in ALT_GLYPHEN)


# ---------- 9 ----------
def test_9_tausender_punkt(index_html, node_exe):
    assert 'toLocaleString("de-AT")+" Artikel' not in index_html
    assert '_fzDE(suppLoad.n,0)+" Artikel) – Verbindung' in index_html
    assert '_fzDE(sysItemCount,0)+" Art."' in index_html
    out = run_node_snippet(node_exe, _one_liner(index_html, "_fzDE") + "console.log(_fzDE(5000,0));")
    assert out == "5.000"


# ---------- 10 ----------
def test_10_color_scheme_folgt_app_wahl(index_html, node_exe):
    m = re.search(r"<script>/\* v3\.9\.1006 Sebastian: color-scheme.*?\*/(\(function\(\)\{.*?\}\)\(\);)</script>", index_html, re.S)
    assert m
    js = ("var out=[];[null,'light','dark','system'].forEach(function(v){"
          "var localStorage={getItem:function(){return v;}};var at={};"
          "var document={documentElement:{style:{},setAttribute:function(k,w){at[k]=w;}}};"
          "(function(localStorage,document){" + m.group(1) + "})(localStorage,document);"
          "out.push([document.documentElement.style.colorScheme,at['data-epk-thema']]);});console.log(JSON.stringify(out));")
    out = json.loads(run_node_snippet(node_exe, js))
    assert out == [["only light", "hell"], ["only light", "hell"], ["only dark", "dunkel"], ["only light", "hell"]]
    # v3.9.1079 Samsung-Hell 3: das statische Meta steht auf der Grundwahl "only light" (vorher "light dark",
    # am A55 ohne Wirkung); das Kopfskript zieht es auf die App-Wahl (test_samsung_hell_v1079.py).
    assert '<meta name="color-scheme" content="only light">' in index_html
    assert ':root[data-epk-thema="hell"] { color-scheme: only light;' in index_html
    assert 'document.documentElement.style.colorScheme=dark?"only dark":"only light"' in index_html


# ---------- P3 ----------
def test_p3_kleinkram(index_html):
    assert "(absences)" not in index_html
    assert "tage+(tage===1?' Tag':' Tage')" in index_html and "tage+'d')" not in index_html
    # UI-Runde 1072: die Dauer steht als "2 h" statt "02:00" (las sich wie eine Endzeit); der
    # Kern dieses Riegels - kein Trenner am Zeilenanfang, leere Teile gefiltert - bleibt.
    assert '[a.terminZeit||"", _dauerKurzDE(a.dauer), _kurz(a.arbeitsanweisungen,60)].filter(Boolean).join(" · ")' in index_html
