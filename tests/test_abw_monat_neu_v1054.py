# -*- coding: utf-8 -*-
"""v3.9.1054 - Abwesenheiten, Monat "ALLE" neu (Sebastian-Spezifikation 19.11.2026).

Reine Anzeige: eine Zeile je Mitarbeiter, Tage als Spalten. Gemessen wird mit
Node an den ECHTEN Helfern, die aus index.html GESCHNITTEN werden (Zaehl-Assert
auf jeden Anker) - nicht an einer Abschrift:

  * Typtafel ABW_MON_TYP: genau die Schluessel aus AT_T (Wahrheit = App, nicht
    die U/K/Z/S der Vorlage), Buchstabe und Farbe je Typ eindeutig, kein
    Signalrot, weisse Schrift >= 4,5:1 auf jeder Flaeche.
  * Laufzerlegung: gleicher Typ + gleicher Status an Folgetagen = EIN Balken,
    runde Enden nur an Anfang/Ende.
  * Zusammenfassung "Heute abwesend" / "Diese Woche (KW nn)" samt Leerfall.
  * Summe = Abwesenheits-ARBEITSTAGE (Sa/So/Feiertag zaehlen nicht, wie
    _stdVonTagK); keine halben Tage - das Modell kennt kein Vormittag/Nachmittag.
  * "Nur Abwesende", abgelehnt nie sichtbar, Heute-Spalte.
  * Ausgetretene: die v3.9.1049-Zeitraumregel (_absImMonat) bleibt woertlich.

Jede Zusicherung hat eine Gegenprobe, die zeigt, dass der Melder anschlaegt.
"""
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
INDEX = WURZEL / "index.html"


def _q():
    return io.open(INDEX, encoding="utf-8", newline="").read()


def _schnitt(q, a, e):
    assert q.count(a) == 1, "Anker %d-mal: %r" % (q.count(a), a)
    i = q.index(a)
    return q[i:q.index(e, i) + len(e)]


def _block(q):
    a = "const ABW_MON_TYP={"
    e = 'Abwesenheitstage (Arbeitstage)")));\r\n}'  # schliessende Klammer auf eigener Zeile (Riegel test_hook_order_static)
    return _schnitt(q, a, e)


STUBS = r"""
"use strict";
var TIME_HOUR=3600000, TIME_DAY=24*TIME_HOUR;
var COLORS={ERROR:"#ef4444"};
var _dark=false;
var UI={fMeta:12,fKlein:13,rKnopf:10,marke:"#009640",markeBg:"#E8F4EC"};
var V={cd:"#fff",bd:"#ddd",tx:"#111",dm:"#555",weBg:"rgba(0,0,0,.04)"};
var MO_DE=["Jänner","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"];
function _pad(n){return String(n).padStart(2,"0");}
function dk(d){return d.getFullYear()+"-"+_pad(d.getMonth()+1)+"-"+_pad(d.getDate());}
function fdt(s){return s;}
function bsS(){return {};}
function _ik(n){return {t:"svg",p:{ik:n},c:[]};}
function _okG(h){return h;}
var _stateOverride=null;
var React={createElement:function(t,p){var c=Array.prototype.slice.call(arguments,2);return {t:t,p:p||{},c:c};}};
var _react={useState:function(v){return [_stateOverride===null?v:_stateOverride,function(){}];},useRef:function(){return {current:null};},useEffect:function(){}};
"""


def _programm(q, rumpf):
    teile = [
        STUBS,
        _schnitt(q, "const AT_T={", "\r\n};"),
        _schnitt(q, "function _easterSunday(y){", "\r\n}"),
        _schnitt(q, "function _isATFeiertag(d){", "\r\n}"),
        _schnitt(q, "function _lesbar(h,chip){", "_lesbarMerk[k]=r;return r;}"),
        "var _lesbarMerk={};",
        _schnitt(q, "function _resolveApprK(abs,approvals,key){", "return _av||\"ausstehend\";}"),
        _block(q),
        r"""
function texte(n){var o=[];(function w(x){if(x==null||x===false)return;if(typeof x==="string"||typeof x==="number"){o.push(String(x));return;}if(Array.isArray(x)){x.forEach(w);return;}if(x.c)x.c.forEach(w);})(n);return o;}
function knoten(n,pred){var o=[];(function w(x){if(!x||typeof x!=="object")return;if(Array.isArray(x)){x.forEach(w);return;}if(pred(x))o.push(x);if(x.c)x.c.forEach(w);})(n);return o;}
var A={};
""",
        rumpf,
        "\nprocess.stdout.write(JSON.stringify(A));\n",
    ]
    return "\n".join(teile)


def _node(js):
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def q():
    return _q()


# ---------------------------------------------------------------- Typtafel
def _lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2]


def _kontrast_weiss(h):
    return 1.05 / (_lum(h) + 0.05)


def _ist_rot(h):
    import colorsys
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, lig, sat = colorsys.rgb_to_hls(r, g, b)
    deg = hue * 360
    return sat > 0.4 and (deg >= 345 or deg <= 15)


def test_typtafel_wahrheit_app_eindeutig_lesbar_kein_rot(q):
    A = _node(_programm(q, r"""
A.typ=ABW_MON_TYP; A.at=Object.keys(AT_T); A.atc=Object.keys(AT_T).map(function(k){return AT_T[k].c;});
A.krank=_abwMonTyp("krank"); A.unbek=_abwMonTyp("gibtsnicht");
"""))
    typ = A["typ"]
    assert sorted(typ) == sorted(A["at"]), "Typtafel != AT_T-Schluessel"
    codes = [v["k"] for v in typ.values()]
    farben = [v["c"].lower() for v in typ.values()]
    assert all(len(k) == 1 and k.isalpha() for k in codes), codes
    assert len(set(codes)) == len(codes), "Buchstabe doppelt"
    assert len(set(farben)) == len(farben), "Farbe doppelt"
    for k, v in typ.items():
        assert _kontrast_weiss(v["c"]) >= 4.5, (k, v["c"], _kontrast_weiss(v["c"]))
        assert not _ist_rot(v["c"]), (k, v["c"])
    assert typ["urlaub"]["k"] == "U" and typ["krankenstand"]["k"] == "K" and typ["zeitausgleich"]["k"] == "Z"
    assert A["krank"] == "krankenstand" and A["unbek"] == "sonstiges"
    # Gegenprobe: der Rot-Melder schlaegt an der alten AT_T-Farbe (Krankenstand = COLORS.ERROR) an,
    # der Kontrast-Melder an der alten Urlaubsflaeche #3b82f6 (3,68:1).
    assert any(_ist_rot(c) for c in A["atc"])
    assert _kontrast_weiss("#3b82f6") < 4.5


# ---------------------------------------------------------- Laufzerlegung
def test_balken_laufzerlegung_runde_enden(q):
    A = _node(_programm(q, r"""
var abs={}, appr={};
["2026-11-02","2026-11-03","2026-11-04"].forEach(function(d){abs["Anna_"+d]={type:"urlaub",status:"genehmigt"};});
abs["Anna_2026-11-05"]={type:"urlaub",status:"beantragt"};
abs["Anna_2026-11-06"]={type:"krankenstand",status:"genehmigt"};
abs["Anna_2026-11-10"]={type:"zeitausgleich",status:"genehmigt"};
var z=_abwMonZeile(abs,appr,"Anna",2026,10);
A.len=z.length;
A.f=z.slice(0,10).map(function(c){return c?[c.t,c.gen,c.anf,c.end]:null;});
A.rad=[1,2,3,4,9].map(function(i){return _abwLaufStil(z[i]).borderRadius;});
A.offenStil=_abwLaufStil(z[4]);
A.genStil=_abwLaufStil(z[1]);
"""))
    assert A["len"] == 30
    f = A["f"]
    assert f[0] is None
    assert f[1] == ["urlaub", True, True, False]
    assert f[2] == ["urlaub", True, False, False]
    assert f[3] == ["urlaub", True, False, True]
    # beantragt ist ein EIGENER Lauf (Status wechselt) - Gegenprobe zur Typgleichheit
    assert f[4] == ["urlaub", False, True, True]
    assert f[5] == ["krankenstand", True, True, True]
    assert f[9] == ["zeitausgleich", True, True, True]
    assert A["rad"] == ["6px 0px 0px 6px", "0px 0px 0px 0px", "0px 6px 6px 0px",
                        "6px 6px 6px 6px", "6px 6px 6px 6px"]
    assert A["genStil"]["color"] == "#fff" and A["genStil"]["background"] == "#1d4ed8"
    assert "dashed" in A["offenStil"]["borderTop"] and "repeating-linear-gradient" in A["offenStil"]["background"]


# ------------------------------------------------------ abgelehnt nie sichtbar
def test_abgelehnt_nie_als_abwesenheit(q):
    A = _node(_programm(q, r"""
var abs={"B_2026-11-02":{type:"urlaub",status:"abgelehnt"},"B_2026-11-03":{type:"urlaub",status:"beantragt"},"B_2026-11-04":{type:"urlaub",status:"genehmigt"}};
var appr={"B_2026-11-03":"abgelehnt"};
var z=_abwMonZeile(abs,appr,"B",2026,10);
A.z=z.slice(0,4).map(function(c){return c?c.gen:null;});
A.sum=_abwMonSumme(z,2026,10);
/* Gegenprobe: ohne Ablehnung waeren beide sichtbar */
var z2=_abwMonZeile(abs,{},"B",2026,10);
A.z2=z2.slice(0,4).map(function(c){return c?c.gen:null;});
"""))
    assert A["z"] == [None, None, None, True]
    assert A["sum"] == {"tage": 1, "offen": 0}
    assert A["z2"] == [None, None, False, True]


# ------------------------------------------------------------------- Summe
def test_summe_arbeitstage_keine_halben_tage(q):
    A = _node(_programm(q, r"""
var abs={};
/* Fr 04.12. bis Di 08.12.2026: Sa/So und der 08.12. (Maria Empfaengnis) zaehlen nicht */
["2026-12-04","2026-12-05","2026-12-06","2026-12-07","2026-12-08"].forEach(function(d){abs["C_"+d]={type:"urlaub",status:"genehmigt"};});
abs["C_2026-12-10"]={type:"sonder_arzt",status:"beantragt",hours:"2"};
var z=_abwMonZeile(abs,{},"C",2026,11);
A.s=_abwMonSumme(z,2026,11);
A.zellen=z.filter(Boolean).length;
"""))
    # 6 Zellen sichtbar (Datenwahrheit), gezaehlt 3 Arbeitstage: Fr 04., Mo 07., Do 10. (2 h Arzt = 1 Tag, kein 0,5)
    assert A["zellen"] == 6
    assert A["s"] == {"tage": 3, "offen": 1}
    assert isinstance(A["s"]["tage"], int)


def test_modell_kennt_keinen_halbtag(q):
    """Belegt die Entscheidung 'keine halben Zellen': der Abwesenheits-Schreibweg traegt kein VM/NM-Feld."""
    i = q.index("function AbsView(")
    absview = q[i:q.index("\r\nfunction ", i + 10)]
    assert len(absview) > 50000 and "status:\"beantragt\"" in absview  # der Schreibweg liegt im Schnitt
    for w in ("vormittag", "nachmittag", "halbtag", "half_day", "halfDay"):
        assert w not in absview.lower(), w
    assert "0.5" not in _block(q)


# ------------------------------------------------------- Zusammenfassung
def test_zusammenfassung_heute_und_woche_mit_leerfall(q):
    A = _node(_programm(q, r"""
var abs={"Zora_2026-11-18":{type:"krankenstand",status:"genehmigt"},
         "Anton_2026-11-16":{type:"urlaub",status:"genehmigt"},"Anton_2026-11-17":{type:"zeitausgleich",status:"beantragt"},
         "Berta_2026-11-23":{type:"urlaub",status:"genehmigt"},
         "Carl_2026-11-18":{type:"urlaub",status:"abgelehnt"}};
var w=_abwMonWer(abs,{},["Zora","Anton","Berta","Carl"],"2026-11-18");
A.w=w;
A.txt=texte(_abwWerWegKarte(w,false)).join("|");
var leer=_abwMonWer({},{},["Zora","Anton"],"2026-11-18");
A.leer=leer; A.leertxt=texte(_abwWerWegKarte(leer,true)).join("|");
A.kw=[_abwKW(new Date(2026,0,1)),_abwKW(new Date(2026,11,28)),_abwKW(new Date(2027,0,1)),_abwKW(new Date(2025,11,29)),_abwKW(new Date(2026,10,18))];
"""))
    w = A["w"]
    assert w["kw"] == 47 and w["von"] == "2026-11-16" and w["bis"] == "2026-11-22"
    assert w["heute"] == [{"nm": "Zora", "t": "krankenstand", "gen": True}]
    assert [x["nm"] for x in w["woche"]] == ["Anton", "Zora"]  # Berta = naechste Woche, Carl abgelehnt
    anton = w["woche"][0]
    assert anton["n"] == 2 and anton["typen"] == ["urlaub", "zeitausgleich"] and anton["gen"] is False
    assert "Heute abwesend:" in A["txt"] and "Diese Woche (KW 47):" in A["txt"]
    assert "niemand abwesend" not in A["txt"]
    assert A["leer"]["heute"] == [] and A["leer"]["woche"] == []
    assert A["leertxt"].count("niemand abwesend") == 2
    assert A["kw"] == [1, 53, 53, 1, 47]


# ------------------------------------------------------ Nur Abwesende
def test_nur_abwesende_filter_und_sortierung(q):
    A = _node(_programm(q, r"""
var abs={"Zora_2026-11-03":{type:"urlaub",status:"genehmigt"}};
var zs=_abwMonZeilen(abs,{},["Zora","anton","Berta"],2026,10);
A.alle=_abwMonFilter(zs,false).map(function(r){return r.nm;});
A.nur=_abwMonFilter(zs,true).map(function(r){return r.nm;});
A.typen=_abwMonTypen(zs);
"""))
    assert A["alle"] == ["anton", "Berta", "Zora"]
    assert A["nur"] == ["Zora"]
    assert A["typen"] == {"typen": ["urlaub"], "offen": False}


# --------------------------------------------- Raster: Heute, Legende, Filter
_RENDER = r"""
var heute=new Date(), Y=heute.getFullYear(), M=heute.getMonth(), T=heute.getDate();
var abs={}; abs["Anna_"+dk(heute)]={type:"urlaub",status:"genehmigt"};
function rend(mo,nur){_stateOverride=nur?true:null;var b=AbwMonatAlle({abs:abs,approvals:{},namen:["Anna","Bert"],alleNamen:["Anna","Bert"],yr:Y,mo:mo,setMo:function(){},sel:"",setSel:function(){},isMob:false});_stateOverride=null;return b;}
var b=rend(M,false);
var hz=knoten(b,function(n){return n.p&&n.p["aria-current"]==="date";});
A.heute=hz.map(function(n){return [n.p.style.gridColumn,n.p.style.background,texte(n).join("")];});
A.T=T;
A.bodyHeute=knoten(b,function(n){return n.p&&n.p.key==="c_Bert_"+(T-1);})[0].p.style.background;
var weI=-1;for(var i=0;i<28;i++){var d=new Date(Y,M,i+1);if(d.getDay()===6&&i!==T-1){weI=i;break;}}
A.bodyWE=knoten(b,function(n){return n.p&&n.p.key==="c_Bert_"+weI;})[0].p.style.background;
var tab=knoten(b,function(n){return n.p&&n.p.role==="table";})[0];
A.raster=tab.p.style.gridTemplateColumns;
var scroll=knoten(b,function(n){return n.p&&n.p.style&&n.p.style.overflowX==="auto";});
A.scroll=scroll.length;
A.kleb=knoten(b,function(n){return n.p&&n.p.style&&n.p.style.position==="sticky"&&n.p.style.left===0;}).length;
A.txt=texte(b).join("|");
A.nurTxt=texte(rend(M,true)).join("|");
var anders=rend((M+6)%12,false);
A.heuteAnders=knoten(anders,function(n){return n.p&&n.p["aria-current"]==="date";}).length;
A.legAnders=texte(anders).join("|");
"""


def test_raster_heute_legende_filter(q):
    A = _node(_programm(q, _RENDER))
    assert len(A["heute"]) == 1
    col, bg, txt = A["heute"][0]
    assert col == str(A["T"] + 1) and bg == "#009640" and txt == str(A["T"])
    # Tagesspalte durchgehend: Heute gruen getoent, Wochenende schattiert, Werktag frei
    assert A["bodyHeute"] == "rgba(0,150,64,.10)"
    assert A["bodyWE"] == "rgba(0,0,0,.04)"
    assert A["raster"].startswith("150px repeat(") and A["raster"].endswith(",28px) 48px")
    assert A["scroll"] == 1 and A["kleb"] >= 3
    t = A["txt"]
    for s in ("Mitarbeiter", "Nur Abwesende", "Heute abwesend:", "Urlaub", "Heute",
              "Wochenende / Feiertag", "Anna", "Bert", "KW "):
        assert s in t, s
    assert "Mo" in t.split("|") and "So" in t.split("|")
    # Nur Abwesende: Bert (ohne Abwesenheit) faellt weg; Gegenprobe oben zeigt ihn
    assert "Bert" not in A["nurTxt"].split("|") and "Bert" in t.split("|")
    # anderer Monat: keine Heute-Spalte, Legende ohne Typ
    assert A["heuteAnders"] == 0
    assert "Keine Abwesenheiten im" in A["legAnders"]


# ----------------------------------------------- Ausgetretene (v1049 bleibt)
def test_ausgetretene_regel_unveraendert(q):
    regel = ('const _absMonAb=yr+"-"+String(mo+1).padStart(2,"0");const _absImMonat=nm=>_absAb(nm,_absMonAb+"-01")'
             '||Object.keys(abs||{}).some(k=>k.startsWith(nm+"_"+_absMonAb));')
    assert q.count(regel) == 1
    assert q.count("names.filter(m=>_absImMonat(m))") == 1
    assert q.count("namen: names.filter(m=>_absImMonat(m)), alleNamen: names,") == 1
    ab = 'const _absAb=(nm,ab)=>{const o=(monteure||[]).find(x=>x.n===nm);return !(o&&_maIstEhemalig(o,ab));};'
    assert q.count(ab) == 1
    js = "\n".join([
        STUBS,
        _schnitt(q, "function _maIstEhemalig(m,heute){", "\r\n}"),
        r"""
var A={};
function liste(yr,mo,abs,monteure){var names=monteure.map(function(m){return m.n;});
""" + ab + regel + r"""
return names.filter(m=>_absImMonat(m));}
var mt=[{n:"Aktiv"},{n:"Weg",austritt:"2026-07-22"}];
A.nach=liste(2026,9,{},mt);
A.mitDaten=liste(2026,9,{"Weg_2026-10-05":{type:"urlaub"}},mt);
A.vor=liste(2026,6,{},mt);
process.stdout.write(JSON.stringify(A));
"""])
    A = _node(js)
    assert A["nach"] == ["Aktiv"]
    assert A["mitDaten"] == ["Aktiv", "Weg"]
    assert A["vor"] == ["Aktiv", "Weg"]


# --------------------------------------------------------- Bauvorschriften
def test_bauvorschriften(q):
    b = _block(q)
    assert "86400000" not in b
    assert not re.search("[\U0001F300-\U0001FAFF☀-➿]", b), "Emoji im neuen Block"
    for m in re.finditer(r"fontSize\s*:\s*([^,}]+)", b):
        v = m.group(1).strip()
        assert v.startswith("UI.f"), v
    assert "fontVariantNumeric:\"tabular-nums\"" in b
    assert "#009640" in b
    assert "minHeight:44" in b and "minWidth:44" in b
    # altes Raster (ohne Status, zeigte auch abgelehnt) ist weg; Handy-Sperre !isMob entfaellt
    assert "V.empty}} ));})))))))" not in q
    assert q.count("isAdmin&&React.createElement(AbwMonatAlle,") == 1
    assert q.count("isAdmin&&isMob&&_abwWerWegKarte(") == 1
