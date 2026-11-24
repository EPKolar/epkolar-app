"""3.9.1117 (GF-Entscheidung 24.11.2026): Monatsfreigabe ohne Stempelzeiten.

1. Buero-Portal, Reiter Monatsfreigabe: hat der Monats-Schnappschuss 0 Stempel-Minuten, steht in der Karte
   "Keine Stempelzeiten in diesem Monat"; "Fertig – zur Admin-Freigabe" verlangt eine ausdrueckliche Bestaetigung
   im App-Dialog (_confirmModal, kein confirm()). Ohne Bestaetigung wird NICHTS geschrieben (kein _mfPatch, keine Meldung).
2. Chef-Portal "Monatsabrechnungen zur Freigabe": derselbe Hinweis in der Listenzeile und in der geoeffneten Abrechnung.
3. Keine Vertretung fuer die Admin-Freigabe: das Buero sieht bei zur_admin_freigabe
   "wartet auf Freigabe durch Admin seit <Datum Uhrzeit>" - Zeitpunkt aus finkzeit_verlauf
   (akt='status', neu='zur_admin_freigabe', juengster Eintrag); nicht lesbar -> ohne Datum.

Keine Aenderung an Stempel-/Zulagen-Rechnung, keine DB-Aenderung. Umkehrprobe: gegen 3.9.1116 rot.
"""
import json
import re
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


def _fn(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n}", i) + 2]


def _zeile(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n", i)]


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return r.stdout


def _buero(src):
    i = src.index("function MonatsfreigabeBuero(")
    return src[i:src.index("\nfunction ", i + 10)]


def _chef(src):
    i = src.index("function MonatsfreigabeChef(")
    return src[i:src.index("\nfunction ", i + 10)]


def _helfer_js(src):
    i = src.index("var MF_OHNE_STEMPEL_TXT=")
    return ("var MF_ZULAGEN_KEYS=['a','b'];\n" + _fn(src, "function _mfZaehlen(liste){") + "\n"
            + src[i:src.index("\n", i)] + "\n" + _zeile(src, "function _mfOhneStempel(snap){") + "\n")


# ── 1 Erkennung ─────────────────────────────────────────────────────────────
@needs_node
def test_ohne_stempel_erkennung(index_html):
    js = _helfer_js(index_html) + r"""
const f=_mfOhneStempel;
console.log(JSON.stringify([
  f({summe:{min:0,arbeitstage:0,z:{}},tage:[]}),
  f({summe:{min:480,arbeitstage:1,z:{}},tage:[{d:"2026-10-01",min:480}]}),
  f({tage:[{d:"2026-10-01",min:0,st:"a"}]}),
  f({tage:[{d:"2026-10-01",min:30}]}),
  f(null), f(undefined), f("x"), MF_OHNE_STEMPEL_TXT]));"""
    assert json.loads(_node(js)) == [True, False, True, False, False, False, False,
                                     "Keine Stempelzeiten in diesem Monat"]


# ── 2 Buero: Bestaetigung vor dem Senden, ohne Ja nichts geschrieben ────────
def _fertig_js(src, antwort, minuten):
    b = _buero(src)
    i = b.index("    var fertig=function(){")
    j = b.index("    var fristSpeichern=", i)
    fertig = b[i:j]
    return (_helfer_js(src) + r"""
var calls=[],toasts=[];var window={__toast:function(t,a){toasts.push([t,a||""]);}};
var heute="2026-11-24",fr="2026-12-10",m={id:"w1",n:"Test A"},ym="2026-10",row={id:"mf_w1_2026-10"},abs={},approvals={},users=[],pushNotif=function(){};
function _mfTageBis(a,b){return 16;}
function _zeMonatName(x){return "Oktober 2026";}
async function _mfBaueSnapshot(){return {v:1,ym:ym,tage:[{d:"2026-10-01",min:""" + str(minuten) + r"""}],summe:{min:""" + str(minuten) + r""",arbeitstage:0,z:{}}};}
async function _confirmModal(msg,opts){calls.push(["dialog",msg,opts&&opts.confirmLabel]);return """ + antwort + r""";}
function confirm(){calls.push(["confirm()"]);return true;}
async function _mfPatch(id,body){calls.push(["patch",id,body.status]);return true;}
function _mfMelden(){calls.push(["melden"]);}
function _mfZahlAnstossen(){}
var neu=0;function setNeu(){} var busy="";function setBusy(){}
""" + _zeile(src, "function _mfOhneStempelBestaetigen(name,ym){") + "\n"
            + b[b.index("  var tun=async function"):b.index("\n", b.index("  var tun=async function"))] + "\n"
            + fertig + "\nPromise.resolve(fertig()).then(function(){console.log(JSON.stringify({calls:calls,toasts:toasts}));});")


@needs_node
def test_ohne_stempel_abbrechen_schreibt_nichts(index_html):
    r = json.loads(_node(_fertig_js(index_html, "false", 0)))
    arten = [c[0] for c in r["calls"]]
    assert arten == ["dialog"], r
    assert "Keine Stempelzeiten in diesem Monat" in r["calls"][0][1]
    assert r["toasts"] and "Nicht gesendet" in r["toasts"][0][0] and r["toasts"][0][1] == "warn"


@needs_node
def test_ohne_stempel_bestaetigt_sendet(index_html):
    r = json.loads(_node(_fertig_js(index_html, "true", 0)))
    assert [c[0] for c in r["calls"]] == ["dialog", "patch", "melden"], r
    assert r["calls"][1][2] == "zur_admin_freigabe"


@needs_node
def test_mit_stempel_kein_dialog(index_html):
    r = json.loads(_node(_fertig_js(index_html, "false", 480)))
    assert [c[0] for c in r["calls"]] == ["patch", "melden"], r


def test_buero_karte_zeigt_hinweis_und_kein_confirm(index_html):
    b = _buero(index_html)
    assert 'row&&st!=="freigegeben"?_mfOhneStempelHinweis(row.snapshot):null' in b
    assert not re.search(r"(?<![\w.])confirm\(", b), "kein Browser-confirm()"
    assert "_confirmModal(MF_OHNE_STEMPEL_TXT" in index_html


# ── 3 Chef-Portal ───────────────────────────────────────────────────────────
def test_chef_liste_und_geoeffnet_zeigen_hinweis(index_html):
    c = _chef(index_html)
    assert '_mfOhneStempel(r.snapshot)?h("span",{"data-mf-ohne-stempel-zeile":r.id' in c
    assert "MF_OHNE_STEMPEL_TXT):null" in c
    assert ",_mfOhneStempelHinweis(r.snapshot),h(MfKacheln,{sum:s})" in c


# ── 4 Wartet auf Admin seit ─────────────────────────────────────────────────
@needs_node
def test_wartet_seit_aus_verlauf(index_html):
    js = (_fn(index_html, "async function _mfAdminWartetSeit(ids){") + "\n" + _zeile(index_html, "function _mfAdminWartetText(am){") + r"""
var SB_REST="https://x/rest/v1",urls=[];function _sbH(){return {};}function _fT(o){return o;}
async function _authRetry(f){return f();}
function _mfZeit(iso){return "Z("+iso+")";}
var antwort=[{finkzeit_id:"mf_a_2026-10",am:"2026-11-20T10:00:00Z"},{finkzeit_id:"mf_a_2026-10",am:"2026-11-02T08:00:00Z"},{finkzeit_id:"mf_b_2026-10",am:"2026-11-21T09:30:00Z"}];
async function fetch(u){urls.push(u);return {ok:true,json:async function(){return antwort;}};}
(async function(){
  var o=await _mfAdminWartetSeit(["mf_a_2026-10","mf_b_2026-10"]);
  var leer=await _mfAdminWartetSeit([]);
  fetch=async function(){return {ok:false,json:async function(){return [];}};};
  var nichtLesbar=await _mfAdminWartetSeit(["mf_a_2026-10"]);
  console.log(JSON.stringify({o:o,leer:leer,nl:nichtLesbar,u:urls,t1:_mfAdminWartetText(o["mf_a_2026-10"]),t0:_mfAdminWartetText(undefined)}));
})();""")
    r = json.loads(_node(js))
    assert r["o"] == {"mf_a_2026-10": "2026-11-20T10:00:00Z", "mf_b_2026-10": "2026-11-21T09:30:00Z"}
    assert r["leer"] == {} and r["nl"] == {}
    assert len(r["u"]) == 1
    u = r["u"][0]
    assert "/finkzeit_verlauf?" in u and "akt=eq.status" in u and "neu=eq.zur_admin_freigabe" in u and "order=am.desc" in u
    assert 'finkzeit_id=in.("mf_a_2026-10","mf_b_2026-10")' in u
    assert r["t1"] == "wartet auf Freigabe durch Admin seit Z(2026-11-20T10:00:00Z)"
    assert r["t0"] == "wartet auf Freigabe durch Admin"


def test_buero_zeigt_wartet_seit(index_html):
    b = _buero(index_html)
    assert 'st==="zur_admin_freigabe"?h("div",{"data-mf-wartet-admin":row.id' in b
    assert "_mfAdminWartetText(wartetSeit[row.id])" in b
    assert 'x.status==="zur_admin_freigabe";}).map(function(x){return x.id;})).then(function(o){if(lebt)setWartetSeit(o);})' in b


def test_rechnung_unberuehrt(index_html):
    """Keine Aenderung an Stempel-/Zulagen-Rechnung: _mfBaueSnapshot und _mfSnapshot rufen die neuen Helfer nicht."""
    for kopf in ("async function _mfBaueSnapshot(", "function _mfSnapshot("):
        f = _fn(index_html, kopf)
        assert "_mfOhneStempel" not in f and "_mfAdminWartet" not in f
