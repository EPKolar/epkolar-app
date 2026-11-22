"""v1052 Bug-Hunt-Fixes (Befunde aus dem Bug-Hunt v3.9.1051 vom 19.11.2026).

H1  Stammdaten-Karte: Entwurf aus fin={} (Finanzen laden noch) -> beim Speichern nach dem Laden gingen alle 7 Finanzspalten
    als null an fz_finanzen (Upsert loescht Leasing/Versicherung). Jetzt: nur angefasste Felder in den Rumpf.
M1  Kundenportal: submitMangel ersetzte nm.photos mit dem Schnappschuss -> waehrend des Hochladens hinzugefuegte Fotos weg.
N1  401/403 beim Lesen (leeres Array mit __rlsFehler) galt als "keine Daten".
N2  Flotten-Karte: Marker-Klick mit veraltetem trailFid -> _showTrail uebersprungen; spaete Spur-Antwort ueberschrieb die aktuelle.
N3  Betrag knapp unter 1e8 rundete auf 1e8 -> numeric(10,2)-Ueberlauf.
F   _fzFristen: erledigt "0"/"false" (Text) galt als erledigt.

Jeder Test laeuft VERHALTENSBASIERT in Node mit den ECHTEN Funktionen aus index.html - und als Umkehrprobe gegen den
Stand v3.9.1051 (6df5e0e, aus git): dort MUSS der Fehler auftreten, sonst misst der Test nichts.
"""
import json
import re
import subprocess

import pytest

from conftest import _extract_fn, REPO_ROOT, EPK_TEST_TIMEOUT
from test_flotte_stammdaten_v1050 import _harness, STAMM

ALT_REV = "6df5e0e"


@pytest.fixture(scope="module")
def alt_html():
    try:
        r = subprocess.run(["git", "-C", REPO_ROOT, "show", ALT_REV + ":index.html"], capture_output=True,
                           timeout=EPK_TEST_TIMEOUT)
    except Exception:  # noqa: BLE001
        r = None
    if r is None or r.returncode != 0 or len(r.stdout) < 1000000:
        pytest.skip("Altstand " + ALT_REV + " nicht im git - Umkehrprobe nicht moeglich")
    return r.stdout.decode("utf-8")


def _node(node_exe, tmp_path, name, snip):
    f = tmp_path / (name + ".js")
    f.write_text(snip, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


# Mini-React: Zustand/Refs/Effekte bleiben ueber mehrere Renders erhalten (Index-basiert wie React selbst).
_MINI_REACT = r"""
var __S={},__D={},__i=0,__pend=[];
var _react={
  useState:{call:function(_x,init){var k=__i++;if(!(k in __S))__S[k]=(typeof init==='function')?init():init;return [__S[k],function(v){__S[k]=(typeof v==='function')?v(__S[k]):v;}];}},
  useRef:{call:function(_x,init){var k=__i++;if(!(k in __S))__S[k]={current:init};return __S[k];}},
  useEffect:{call:function(_x,fn,deps){var k=__i++;var alt=__D[k];var neu=!alt||!deps||deps.some(function(d,j){return d!==alt[j];});if(neu){__D[k]=deps;__pend.push(fn);}}},
  useMemo:{call:function(_x,fn){return fn();}}
};
var React={createElement:function(t,p){var c=Array.prototype.slice.call(arguments,2);return {t:t,p:p||{},c:c};},Fragment:'frag'};
function __render(K,props){var tree;for(var r=0;r<4;r++){__i=0;__pend=[];tree=K(props);var p=__pend;__pend=[];if(!p.length&&r>0)break;p.forEach(function(fn){fn();});}return tree;}
function __alle(n,out){out=out||[];if(!n||typeof n!=='object')return out;if(Array.isArray(n)){n.forEach(function(x){__alle(x,out);});return out;}out.push(n);(n.c||[]).forEach(function(x){__alle(x,out);});return out;}
function __tx(n){if(n===null||n===undefined||n===false||n===true)return '';if(typeof n==='string'||typeof n==='number')return String(n);if(Array.isArray(n))return n.map(__tx).join(' ');return (n.c||[]).map(__tx).join(' ');}
function __find(tree,pred){return __alle(tree).filter(pred)[0]||null;}
var V={bg:'#fff',cd:'#fff',bd:'#ddd',tx:'#111',dm:'#555',mt:'#888'};var mono='monospace';
var UI={fMeta:12,fKlein:13,fText:14,fTitel:16,rChip:6,rKnopf:8,markeTxt:'#060',grau:'#666'};
var COLORS={ERROR:'#e00',ERROR_FILL:'#b00',WARNING_FILL:'#a50',INFO_FILL:'#048',EP_GREEN:'#009640'};
function CC(){return {};}function II(){return {};}function LL(){return {};}function bsS(){return {};}var bpS={};
function _ik(n){return {t:'svg',p:{n:n},c:[]};}function _ikVw(n,t){return {t:'ik',p:{n:n},c:[t]};}
function fmt$(x){return String(x);}
var __toasts=[];var window={__toast:function(m){__toasts.push(String(m));}};var navigator={onLine:true};
"""

F1 = {"id": "fz1", "kennzeichen": "TU-1", "reifen_saison": "winter", "reifen_lager": "", "service_km_intervall": 30000,
      "naechst_service_km": 150000}
FIN = {"fahrzeug_id": "fz1", "leasing_geber": "Porsche Bank", "leasing_ende": "2028-05-31", "leasing_rate": 489.9,
       "leasing_km_limit": 120000, "versicherung_polizze": "AB-123", "versicherung_ablauf": "2027-01-01",
       "versicherung_praemie": 1450}
FIN7 = ["leasing_geber", "leasing_ende", "leasing_rate", "leasing_km_limit", "versicherung_polizze",
        "versicherung_ablauf", "versicherung_praemie"]


def _stamm_snip(src, szenario):
    # v3.9.1095: FahrzeugStammKarte ruft _fzStammRest (Zusammenfassung aller Felder); im Altstand gibt es sie nicht
    rest = ("_fzStammRest",) if "_fzStammRest=" in src or "function _fzStammRest" in src else ()
    return (_harness(src, *STAMM, *rest, "FahrzeugStammKarte") + _MINI_REACT
            + "var FZ_REIFEN_TXT=FZ_REIFEN_TXT||{};function _fzDatumAnz(x){return String(x);}\n"
            + "var F=" + json.dumps(F1) + ",FIN=" + json.dumps(FIN) + ";var sent={fz:[],fi:[]};\n"
            + "function P(o){return Object.assign({f:F,fin:null,darfFinanz:true,finDa:false,finStatus:'laedt',spaltenDa:true,"
              "darfReifen:true,offenStart:true,isMob:false,onSpeichern:function(b){sent.fz.push(b);},"
              "onSpeichernFin:function(b){sent.fi.push(b);}},o||{});}\n"
            + "function tippe(props,id,wert){var t=__render(FahrzeugStammKarte,props);var e=__find(t,function(n){return n.p&&n.p.id===id;});"
              "if(!e)throw new Error('kein Feld '+id);e.p.onChange({target:{value:wert}});return __render(FahrzeugStammKarte,props);}\n"
            + "function speichere(props){var t=__render(FahrzeugStammKarte,props);var b=__find(t,function(n){return n.t==='button'&&(n.c||[]).indexOf('Speichern')>=0;});"
              "b.p.onClick();__render(FahrzeugStammKarte,props);}\n"
            + szenario + "\n")


def _stamm(node_exe, tmp_path, src, name, szenario):
    return _node(node_exe, tmp_path, name, _stamm_snip(src, szenario))


H1_SZENARIO = r"""
var p1=P();var t0=__render(FahrzeugStammKarte,p1);
var finInputDa=!!__find(t0,function(n){return n.t==='input'&&n.p&&n.p.id==='fzst_leasing_rate';});
var ladeTxt=__tx(t0).indexOf('werden geladen')>=0;
tippe(p1,'fzst_reifen_lager','Reifen Huber');
var p2=P({fin:Object.assign({},FIN),finDa:true,finStatus:'ok'});
__render(FahrzeugStammKarte,p2);
speichere(p2);
process.stdout.write(JSON.stringify({sent:sent,finInputDa:finInputDa,ladeTxt:ladeTxt}));
"""


def test_h1_finanzen_laden_waehrend_edit_loescht_nichts(node_exe, index_html, tmp_path):
    r = _stamm(node_exe, tmp_path, index_html, "h1neu", H1_SZENARIO)
    assert r["finInputDa"] is False and r["ladeTxt"] is True, "solange Finanzen laden: kein Finanz-Eingabefeld, Hinweis sichtbar"
    assert r["sent"]["fi"] == [], "kein fz_finanzen-Rumpf - niemand hat ein Finanzfeld angefasst: " + json.dumps(r["sent"])
    assert r["sent"]["fz"] == [{"reifen_lager": "Reifen Huber"}], r["sent"]


def test_h1_umkehrprobe_altstand_loescht_7_finanzspalten(node_exe, alt_html, tmp_path):
    r = _stamm(node_exe, tmp_path, alt_html, "h1alt", H1_SZENARIO)
    assert len(r["sent"]["fi"]) == 1, r
    assert r["sent"]["fi"][0] == {k: None for k in FIN7}, "Altstand muss den Fehler zeigen: " + json.dumps(r["sent"])


H1B_SZENARIO = r"""
var p1=P({fin:Object.assign({},FIN),finDa:true,finStatus:'ok'});
tippe(p1,'fzst_leasing_rate','500');
var fin2=Object.assign({},FIN,{versicherung_praemie:1600,leasing_geber:'VW Leasing'});
var f2=Object.assign({},F,{naechst_service_km:180000});
var p2=P({f:f2,fin:fin2,finDa:true,finStatus:'ok'});
__render(FahrzeugStammKarte,p2);
var t=__render(FahrzeugStammKarte,p2);
var praemieFeld=__find(t,function(n){return n.p&&n.p.id==='fzst_versicherung_praemie';});
speichere(p2);
process.stdout.write(JSON.stringify({sent:sent,praemieAnzeige:praemieFeld?praemieFeld.p.value:null}));
"""


def test_h1_fremde_aenderung_waehrend_edit_bleibt(node_exe, index_html, tmp_path):
    """Zweiter Weg derselben Ursache: ein anderes Geraet aendert Praemie/Leasinggeber/Service-km, waehrend hier die Rate
    bearbeitet wird. Gesendet wird NUR die Rate; die nicht angefassten Felder zeigen den neuen Serverstand."""
    r = _stamm(node_exe, tmp_path, index_html, "h1bneu", H1B_SZENARIO)
    assert r["sent"]["fi"] == [{"leasing_rate": 500}], r
    assert r["sent"]["fz"] == [], r
    assert r["praemieAnzeige"] == "1600", "nicht angefasstes Feld folgt dem Server"


def test_h1_umkehrprobe_fremde_aenderung(node_exe, alt_html, tmp_path):
    r = _stamm(node_exe, tmp_path, alt_html, "h1balt", H1B_SZENARIO)
    fi = r["sent"]["fi"][0]
    assert fi.get("versicherung_praemie") == 1450 and fi.get("leasing_geber") == "Porsche Bank", \
        "Altstand schreibt die alten Werte zurueck: " + json.dumps(r)
    assert r["sent"]["fz"] == [{"naechst_service_km": 150000}], r


def test_h1_rechte_status_text_und_nicht_editierbar(node_exe, index_html, tmp_path):
    r = _stamm(node_exe, tmp_path, index_html, "h1r",
               "var t=__render(FahrzeugStammKarte,P({finStatus:'rechte'}));"
               "process.stdout.write(JSON.stringify({tx:__tx(t),inp:!!__find(t,function(n){return n.t==='input'&&n.p.id==='fzst_leasing_rate';})}));")
    assert "nicht lesbar" in r["tx"] and r["inp"] is False


# ── N3 ──────────────────────────────────────────────────────────────────────

N3_EXPR = ("process.stdout.write(JSON.stringify({a:_fzStammWert('versicherung_praemie',' 99999999.995'),"
           "b:_fzStammWert('versicherung_praemie','99999999,99'),c:_fzStammWert('leasing_rate','99999999,994'),"
           "d:_fzStammWert('leasing_rate','100000000'),e:_fzStammWert('leasing_rate','450,555')}));")


def test_n3_erst_runden_dann_pruefen(node_exe, index_html, tmp_path):
    r = _node(node_exe, tmp_path, "n3", _harness(index_html, *STAMM) + N3_EXPR)
    assert r["a"]["ok"] is False and r["a"]["wert"] is None and r["a"]["fehler"] == "Zahl zu groß", r["a"]
    assert r["b"] == {"ok": True, "wert": 99999999.99, "fehler": ""}
    assert r["c"]["ok"] is True and r["c"]["wert"] == 99999999.99
    assert r["d"]["ok"] is False
    assert r["e"]["wert"] == 450.56


def test_n3_umkehrprobe(node_exe, alt_html, tmp_path):
    r = _node(node_exe, tmp_path, "n3alt", _harness(alt_html, *STAMM) + N3_EXPR)
    assert r["a"] == {"ok": True, "wert": 100000000, "fehler": ""}, "Altstand liess 1e8 durch: " + json.dumps(r["a"])


# ── F: _fzFristen erledigt als Text ──────────────────────────────────────────

F_EXPR = ("var fz=[{id:'F',kennzeichen:'X',termine:[{datum:'2026-11-25',erledigt:'0',beschreibung:'T0'},"
          "{datum:'2026-11-26',erledigt:'false',beschreibung:'T1'},{datum:'2026-11-27',erledigt:'1',beschreibung:'T2'},"
          "{datum:'2026-11-28',erledigt:true,beschreibung:'T3'},{datum:'2026-11-29',erledigt:0,beschreibung:'T4'}]}];"
          "var r=_fzFristen(fz,new Date(2026,10,19,10).getTime(),[],null).filter(function(x){return x.art==='termin';})"
          ".map(function(x){return x.hinweis;});process.stdout.write(JSON.stringify(r));")


def _fristen_snip(src):
    return _harness(src, "_fzPickerlStufe", "_fzTerminErledigt", "_fzFristen", "_fzTageTxt") + F_EXPR


def test_fristen_erledigt_text_null_ist_offen(node_exe, index_html, tmp_path):
    r = _node(node_exe, tmp_path, "fneu", _fristen_snip(index_html))
    assert sorted(r) == ["T0", "T1", "T4"], r


def test_fristen_umkehrprobe(node_exe, alt_html, tmp_path):
    r = _node(node_exe, tmp_path, "falt", _fristen_snip(alt_html))
    assert "T0" not in r and "T1" not in r, "Altstand verschluckte '0'/'false': " + json.dumps(r)


# ── N1: 401/403 ist kein leerer Bestand ─────────────────────────────────────

def _n1_snip(src):
    teile = [_MINI_REACT, _extract_fn(src, "_rlsLeer"), _extract_fn(src, "_fzFinLaden"),
             re.search(r"^var _fzFin=.*$", src, re.M).group(0).rstrip("\r"),
             re.search(r"^var _fsKtrCache=.*$", src, re.M).group(0).rstrip("\r")]
    for n in ("_fsKtrMerken", "_fsKtrAusCache", "_fsKtrChip", "FsKontrolleFristenKarte"):
        teile.append(_extract_fn(src, n))
    h = _harness(src, "_maIstEhemalig", "_fsPlusMonate", "_fsKtrSortiert", "_fsKtrStatus", "_fsKtrFaellig")
    return h + "\n".join(teile) + r"""
function _maStaffRolle(){return true;}
function __rls(){var l=[];l.__rlsFehler=403;return Promise.resolve(l);}
var _sbGet=function(){return __rls();};
(async function(){
  await _fzFinLaden({role:'buero'});
  var fin=_fzFin.status;
  var mon=[{id:'m1',n:'Anna',fs:'B'}],fz=[{id:'F',kennzeichen:'X',fahrer:'m1',status:'aktiv'}];
  __render(FsKontrolleFristenKarte,{monteure:mon,fahrzeuge:fz});
  await new Promise(function(r){setTimeout(r,5);});
  var t=__render(FsKontrolleFristenKarte,{monteure:mon,fahrzeuge:fz});
  process.stdout.write(JSON.stringify({fin:fin,tx:__tx(t)}));
})();
"""


def test_n1_rechtefehler_ist_kein_leerer_bestand(node_exe, index_html, tmp_path):
    r = _node(node_exe, tmp_path, "n1neu", _n1_snip(index_html))
    assert r["fin"] == "rechte", "Finanzen: 403 -> Status rechte (nicht ok, also nicht editierbar)"
    assert "nicht lesbar" in r["tx"] and "nie kontrolliert" not in r["tx"], r["tx"]


def test_n1_umkehrprobe(node_exe, alt_html, tmp_path):
    r = _node(node_exe, tmp_path, "n1alt", _n1_snip(alt_html))
    assert r["fin"] == "ok" and "nie kontrolliert" in r["tx"], "Altstand: 403 sah aus wie leer: " + json.dumps(r)


def test_n1_quelle_alle_vier_stellen(index_html):
    """Die vier Leser pruefen _rlsLeer (FsKontrolleSection laesst sich ohne ganze App nicht rendern)."""
    for fn in ("_fzFinLaden", "FsKontrolleSection", "FsKontrolleFristenKarte", "FlotteFristenPanel"):
        assert "_rlsLeer(d)" in _extract_fn(index_html, fn), fn
    assert "finStatus: _darfFin?_fzFin.status" in index_html, "Fristen bekommen den Finanzstatus"


# ── M1: Portal-Fotos waehrend des Hochladens ────────────────────────────────

def _m1_snip(src, szenario):
    a = src.index("const submitMangel=async()=>{")
    b = src.index("const kundeAbnahme", a)
    sub = src[a:b].rstrip()
    merge = _extract_fn(src, "_portalFotosMerge") if "function _portalFotosMerge" in src else ""
    return (merge + "\n" + r"""
function _optionalChain(ops){var v=ops[0];for(var i=1;i<ops.length;i+=2){if(v==null)return undefined;v=ops[i+1](v);}return v;}
var __toasts=[];var window={__toast:function(m){__toasts.push(String(m));}};
var A={thumb:'ta',full:'fa'},B={thumb:'tb',full:'fb'},C={thumb:'tc',full:'fc'};
var state={nm:{name:'Steckdose defekt',beschreibung:'',ort:'',photos:[A,B]}};
var newMangel=state.nm,submittingMangel=false,p={portalCode:'X',id:'P1'};
function setNewMangel(v){state.nm=(typeof v==='function')?v(state.nm):v;}
function setSubmittingMangel(){}function setPortalFotoUrls(){}function setForms(){}function td2(){return '2026-11-19';}
function uid(){return 'M1';}
var _mFotoLaeuft={current:0};var hochCalls=0;
async function _portalMangelFotosHoch(code,mid,fotos){hochCalls++;
  /* waehrend des Hochladens: Vorschau von C wird fertig (Foto kam nach dem Tipp) */
  state.nm=Object.assign({},state.nm,{photos:state.nm.photos.concat([C])});
  return {je:fotos.map(function(f,i){return 'pfad'+i;}),pfade:fotos.map(function(f,i){return 'pfad'+i;}),urls:{},fehl:[]};}
async function _portalRpcCall(){throw new Error('netz weg');}
async function _confirmModal(){return true;}
""" + sub + "\n" + szenario)


M1_SZENARIO = r"""
(async function(){
  await submitMangel();
  var ph=(state.nm&&state.nm.photos)||[];
  process.stdout.write(JSON.stringify({n:ph.length,full:ph.map(function(x){return x.full;}),pfad:ph.map(function(x){return x.pfad||'';}),hoch:hochCalls}));
})();
"""


def test_m1_foto_waehrend_hochladen_bleibt(node_exe, index_html, tmp_path):
    r = _node(node_exe, tmp_path, "m1neu", _m1_snip(index_html, M1_SZENARIO))
    assert r["full"] == ["fa", "fb", "fc"], "C (kam waehrend des Hochladens) muss bleiben: " + json.dumps(r)
    assert r["pfad"] == ["pfad0", "pfad1", ""], "A/B tragen ihren Pfad (kein Doppel-Upload beim zweiten Versuch)"


def test_m1_umkehrprobe(node_exe, alt_html, tmp_path):
    r = _node(node_exe, tmp_path, "m1alt", _m1_snip(alt_html, M1_SZENARIO))
    assert r["full"] == ["fa", "fb"], "Altstand verlor C: " + json.dumps(r)


def test_m1_absenden_wartet_auf_fotoaufbereitung(node_exe, index_html, tmp_path):
    r = _node(node_exe, tmp_path, "m1warte", _m1_snip(index_html, r"""
_mFotoLaeuft.current=1;
(async function(){await submitMangel();process.stdout.write(JSON.stringify({hoch:hochCalls,toast:__toasts.join('|')}));})();
"""))
    assert r["hoch"] == 0 and "vorbereitet" in r["toast"], r


def test_m1_merge_entfernt_bleibt_entfernt(node_exe, index_html, tmp_path):
    r = _node(node_exe, tmp_path, "m1merge", _extract_fn(index_html, "_portalFotosMerge") + r"""
var A={full:'a'},B={full:'b'},K={full:'k',key:'kk'};
var fotos=[{full:'a',key:'x0'},{full:'b',key:'x1'},{full:'k',key:'kk'}];
var r=_portalFotosMerge([A,K],[A,B,K],fotos,['p0','p1','']);
process.stdout.write(JSON.stringify(r));
""")
    assert r == [{"full": "a", "key": "x0", "pfad": "p0"}, {"full": "k", "key": "kk"}], r


def test_m1_fotowahl_gesperrt_beim_senden(index_html):
    a = index_html.index('"Fotos (empfohlen)"')
    portal = index_html[a:a + 4000]
    ok1 = 'multiple: true, disabled: submittingMangel' in portal
    ok2 = 'onClick: ()=>{if(submittingMangel)return;setNewMangel(m=>({...m,photos:m.photos.filter' in portal
    assert ok1, "Fotowahl waehrend des Sendens gesperrt"
    assert ok2, "Foto entfernen waehrend des Sendens gesperrt"


# ── N2: Flotten-Karte Marker-Klick / spaete Spur ────────────────────────────

def _n2_snip(src):
    def zeile(muster):
        m = re.search(r"^[ \t]*" + muster + r".*$", src, re.M)
        return m.group(0).rstrip("\r") if m else ""
    show = zeile(r"var _showTrail=function\(fid\)")
    clear = zeile(r"var _clearTrail=function\(\)")
    waehle = zeile(r"var _waehle=function\(fid\)")
    refs = zeile(r"const _trailFidRef=")
    sync = zeile(r"_trailFidRef\.current=trailFid;")
    mk = zeile(r"m\.on\('click',function\(\)")
    assert show and clear and waehle and mk
    body = ("var trailFid=S.trailFid,followId=S.followId;\n" + refs + "\n" + sync + "\n" + show + "\n" + clear + "\n"
            + waehle + "\nfunction mk(f){var m={on:function(e,cb){m.cb=cb;}};\n" + mk + "\nreturn m.cb;}\n"
            + "return {showTrail:_showTrail,mk:mk};")
    return _MINI_REACT + r"""
var S={trailFid:null,followId:null,track:null};
var _map={current:{removeLayer:function(){}}},_trail={current:null};
var L={polyline:function(){return {addTo:function(){return this;}};}};
var calls=[],offen=[];
function _holeTrack(fid){calls.push(fid);return new Promise(function(res){offen.push({fid:fid,res:res});});}
function setTrailFid(v){S.trailFid=v;}function setTrailSeit(){}function setTrackRows(v){S.track=v;}
function setSelFid(){}function setPopAnstoss(){}function setFollowId(v){S.followId=(typeof v==='function')?v(S.followId):v;}
function setFahrtTrail(){}function _clearFahrtMk(){}function _fzStatusSeit(){return NaN;}
var __R=new Function('S','_react','_map','_trail','L','_holeTrack','setTrailFid','setTrailSeit','setTrackRows','setSelFid','setPopAnstoss','setFollowId','setFahrtTrail','_clearFahrtMk','_fzStatusSeit',""" + json.dumps(body) + r""");
function render(){__i=0;return __R(S,_react,_map,_trail,L,_holeTrack,setTrailFid,setTrailSeit,setTrackRows,setSelFid,setPopAnstoss,setFollowId,setFahrtTrail,_clearFahrtMk,_fzStatusSeit);}
(async function(){
  var r1=render();var klickA=r1.mk({id:'A'});
  klickA();                       /* Marker A -> Spur A */
  var r2=render();var klickA2=r2.mk({id:'A'});   /* Poll baut die Marker neu (trailFid=A) */
  r2.showTrail('B');              /* Liste: Fahrzeug B */
  render();                       /* KEIN Marker-Neuaufbau (innerhalb 10 s) */
  klickA2();                      /* Marker A erneut */
  var nachKlick=calls.slice();
  /* Spaete Antwort fuer B kommt NACH der neuen Anfrage fuer A */
  var b=offen.filter(function(x){return x.fid==='B';})[0];if(b)b.res([{lat:1,lon:1,ts:'2026-11-19T10:00:00Z'}]);
  await new Promise(function(r){setTimeout(r,5);});
  var nachB=S.track?S.track.fid:null;
  process.stdout.write(JSON.stringify({calls:nachKlick,trailFid:S.trailFid,trackNachB:nachB}));
})();
"""


def test_n2_marker_klick_nach_listenauswahl_zeigt_spur(node_exe, index_html, tmp_path):
    r = _node(node_exe, tmp_path, "n2neu", _n2_snip(index_html))
    assert r["calls"] == ["A", "B", "A"], "Marker A nach Auswahl B muss die Spur A laden: " + json.dumps(r)
    assert r["trailFid"] == "A"
    assert r["trackNachB"] is None, "spaete Antwort fuer B darf die Spur von A nicht ersetzen"


def test_n2_umkehrprobe(node_exe, alt_html, tmp_path):
    r = _node(node_exe, tmp_path, "n2alt", _n2_snip(alt_html))
    assert r["calls"] == ["A", "B"], "Altstand ueberspringt _showTrail(A): " + json.dumps(r)
    assert r["trackNachB"] == "B"
