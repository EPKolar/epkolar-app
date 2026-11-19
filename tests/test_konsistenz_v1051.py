# -*- coding: utf-8 -*-
"""v1051 Konsistenz-Durchgang (Zweig fix/konsistenz-1051).

1. EINE Fahrzeug-Zeichnung: _fzBusSvg ist die einzige Geometrie; die Flotten-Karte
   (_fzVanSvg/_fzVanMarkerHtml) und die Flotten-Liste (_fzVanEl) delegieren dorthin.
   Laeuft in Node mit dem ECHTEN Helfer und dem ECHTEN Flotten-Block aus index.html.
2. Buero-Portal: Bearbeiten-Dialoge mit Linien-Ikone (titleIk "stift") statt Emoji,
   keine Bild-Emoji mehr in der Oberflaeche (ausgenommen: Tank-Handler eines anderen
   Zweigs und Excel-Dateititel).
3. Werkzeuge Ein/Aus: App-Rueckfrage (_confirmModal) statt nativem alert/confirm.
   Verhalten AUSGEFUEHRT: Abbrechen schreibt nichts, Bestaetigen schreibt genau den
   bisherigen PUT-Koerper. Umkehrprobe: ein Koeder ohne return nach der Rueckfrage
   muss rot werden.
4. Sammel-Tanken in CI-Farben (kein Orange mehr im Block).
"""
import json
import os
import re
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from conftest import _extract_fn, EPK_TEST_TIMEOUT  # noqa: E402
from test_flotte_karte_busse_v1049 import _consts, _block, _DEPS, _OUT  # noqa: E402


def _node(node_exe, tmp_path, code, name):
    p = tmp_path / name
    p.write_text(code, encoding="utf-8")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, "node: " + (r.stderr or "")[:1500]
    assert r.stdout.strip(), "node lieferte nichts - ein leerer Lauf ist kein gruener Lauf"
    return json.loads(r.stdout.strip().splitlines()[-1])


def _zeile(html, anfang):
    treffer = [z for z in html.split("\n") if z.startswith(anfang)]
    assert len(treffer) == 1, "%d Zeilen beginnen mit %r" % (len(treffer), anfang)
    return treffer[0].rstrip("\r")


# ── 1. EINE Fahrzeug-Zeichnung ──────────────────────────────────────────────
GEO = r"""
var pfad=function(t){var m=/<path d="([^"]+)"/.exec(t);return m?m[1]:null;};
var arten=["bus","lkw","anhaenger","pkw","stapler"];
_out({
  busStrich:_fzBusSvg({art:"bus"}), vanFaehrt:_fzVanSvg("faehrt",36,false), vanSpiegel:_fzVanSvg("faehrt",36,true),
  vanAlt:_fzVanSvg("veraltet",36,false), vanKein:_fzVanSvg("kein_tracker",36,false),
  pfadBus:pfad(_fzBusSvg({art:"bus"})), pfadVan:pfad(_fzVanSvg("steht",36,false)),
  pfadArten:arten.map(function(a){return pfad(_fzVanSvg("steht",36,false,a));}),
  artAttr:arten.map(function(a){return /data-fz-art="([a-z]+)"/.exec(_fzVanSvg("steht",36,false,a))[1];}),
  marker:_fzVanMarkerHtml({zustand:"faehrt",heading:270,kennzeichen:"TU-1",art:"pkw"}),
  inj:_fzBusSvg({karte:{fill:'red" onload="x',stroke:"url(#a)",dash:'1" onclick="y',fenster:"#fff;x",opacity:"9"}})
});
"""


def _geo(index_html, node_exe, tmp_path, name, ersetze=None):
    teile = [_consts(index_html), _OUT]
    for n in _DEPS:
        fn = _extract_fn(index_html, n)
        assert fn, n + " nicht gefunden"
        teile.append(fn + "\n")
    code = "".join(teile)
    if ersetze:
        alt, neu = ersetze
        assert alt in code, "Koeder-Anker fehlt: %r" % alt
        code = code.replace(alt, neu, 1)
    return _node(node_exe, tmp_path, code + _block(index_html) + GEO, name)


def test_eine_geometrie_quelle(index_html):
    assert "_fzBusSvg" in _DEPS, "der Marker-Lauf muss den echten _fzBusSvg mitnehmen"
    for alt in ("FZ_VAN_KAROSSE", "FZ_VAN_FENSTER", "FZ_VAN_RAEDER", "FZ_VAN_VIEWBOX"):
        assert alt not in index_html, "zweite Fahrzeug-Geometrie wieder da: " + alt
    # die Transporter-Karosse steht genau einmal in der Datei
    assert index_html.count('M5 24.5V9.5A3.5 3.5 0 0 1 8.5 6H30.5L37.5 14H41') == 1
    blk = _block(index_html)
    assert "return _fzBusSvg({art:art,gr:Number(breite)||36,karte:_fzVanStil(zustand),spiegeln:!!spiegeln});" in blk
    el = _extract_fn(index_html, "_fzVanEl")
    assert el and "_fzBusSvg({art:art," in el and "<path" not in el and "'path'" not in el


def test_karte_und_fahrzeuge_zeichnen_dasselbe(index_html, node_exe, tmp_path):
    m = _geo(index_html, node_exe, tmp_path, "geo.js")
    assert m["pfadBus"] and m["pfadBus"] == m["pfadVan"], "Karte und Seite Fahrzeuge zeichnen verschiedene Transporter"
    assert m["artAttr"] == ["bus", "lkw", "anhaenger", "pkw", "stapler"]
    assert len(set(m["pfadArten"])) == 5, "fuenf verschiedene Zeichnungen erwartet"
    # Kartenstil: Flaeche in Zustandsfarbe, weisser Rand, Spiegelung, Strichelung nur bei veraltet
    assert 'fill="#009640"' in m["vanFaehrt"] and 'stroke="#ffffff"' in m["vanFaehrt"]
    assert "scaleX(-1)" in m["vanSpiegel"] and "scaleX(-1)" not in m["vanFaehrt"]
    assert "stroke-dasharray" in m["vanAlt"] and "stroke-dasharray" not in m["vanFaehrt"]
    assert 'fill="none"' in m["vanKein"]
    assert 'aria-hidden="true"' in m["vanFaehrt"] and "color:" not in m["vanFaehrt"]
    # Strichstil der Seite Fahrzeuge bleibt wie in v1049
    assert "color:#009640" in m["busStrich"] and 'fill="currentColor"' in m["busStrich"]
    mk = m["marker"]
    assert 'data-fz-art="pkw"' in mk and "rotate(270deg)" in mk and "scaleX(-1)" in mk and "width:44px" in mk


def test_kartenstil_nimmt_keine_fremden_werte_auf(index_html, node_exe, tmp_path):
    q = _geo(index_html, node_exe, tmp_path, "geo_inj.js")["inj"]
    assert "onload" not in q and "onclick" not in q and "url(" not in q and "#fff;x" not in q
    assert 'fill="#94a3b8"' in q and "opacity:1" in q


def test_koeder_ungeprueftes_kartenfeld_wird_erkannt(index_html, node_exe, tmp_path):
    q = _geo(index_html, node_exe, tmp_path, "geo_koeder.js",
             ('var fa=function(x,d){x=String(x==null?"":x);', 'var fa=function(x,d){return String(x);x=String(x==null?"":x);'))["inj"]
    assert "onload" in q, "KOEDER STUMM: ein ungepruefter Kartenwert bliebe unbemerkt"


# ── 2. Buero-Portal ohne Emoji ──────────────────────────────────────────────
_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-⛿✏✅❌➕⏰-⏺]")
# Ausnahmen mit Grund: Tank-Kontrolle/-Korrektur gehoeren dem Zweig feature/tanklog-atomar;
# genXls-Titel sind Dateiinhalt (Export), keine Oberflaeche.
_AUSNAHMEN = ("Fahrzeug nicht gefunden", "Beleg nicht mehr vorhanden", "tank_log", "Beleg als kontrolliert",
              "[tank-", "Tank-Korrektur", "genXls(")


def _buero(index_html):
    a = index_html.index("/* ═══ v3.9.775 EZKalender")
    b = index_html.index("\nfunction AdminPanel(", a)
    return re.sub(r"/\*[\s\S]*?\*/", "", index_html[a:b])


def test_buero_bearbeiten_dialoge_mit_linien_ikone(index_html):
    c = _buero(index_html)
    assert "✏️" not in c
    assert c.count('titleIk:"stift"') == 2
    assert 'title:"Berichte bearbeiten — "' in c and 'title:"Einzelbuchungen — "' in c
    m = index_html[index_html.index("window._exportReviewModal=function(opts){"):]
    m = m[:m.index("\n};")]
    assert "opts.titleIk" in m and "createElementNS(NS,'svg')" in m and "IKON[opts.titleIk]" in m
    assert "titleTx.textContent=title;" in m, "Titel weiter als Text (nicht innerHTML)"


def test_buero_portal_ohne_bild_emoji(index_html):
    rest = [z.strip()[:120] for z in _buero(index_html).split("\n")
            if _EMOJI.search(z) and not any(x in z for x in _AUSNAHMEN)]
    assert rest == [], rest


# ── 3. Werkzeuge Ein/Aus: App-Rueckfrage statt alert/confirm ────────────────
GRUND_WZ = ("const COLORS=", "const _ymd=d=>", "const td2=()=>", "function _isValidKalibDate(",
            "function _wzKalibFaellig(")


def _ausgeben_onclick(index_html):
    z = [x for x in index_html.split("\n") if 'document.getElementById("co_"+w.id)' in x]
    assert len(z) == 1, len(z)
    z = z[0]
    a = z.index("onClick: async ()=>{")
    b = z.index("}, style: {...bpS", a)
    return z[a + len("onClick: "):b + 1]


WZ_LAUF = r"""
var canDo=function(){return true;},curUser={},werkzeuge=[],monteure=[{id:"M1",n:"Max"}];
var setWerkzeuge=function(){},pushNotif=function(){};
var LOG=null;
var SQ={push:function(x){LOG.writes.push(JSON.parse(JSON.stringify(x)));}};
var document={getElementById:function(id){return id===LOG.selId?{value:LOG.sel}:null;}};
function alert(){LOG.nativ++;}
function confirm(){LOG.nativ++;return true;}
%(checkout)s
async function lauf(w,sel,antwort){
  LOG={writes:[],asked:[],toasts:[],nativ:0,sel:sel,selId:"co_"+w.id};werkzeuge=[w];
  window.__toast=function(m,t){LOG.toasts.push([m,t||""]);};
  window._confirmModal=function(m,o){LOG.asked.push([m,(o&&o.confirmLabel)||""]);return Promise.resolve(antwort);};
  var h=%(onclick)s;
  await h();
  return LOG;
}
(async function(){
  var faellig={id:"W1",name:"Fluke 1664",status:"verfuegbar",naechsteKalib:"2020-01-15"};
  var frei={id:"W2",name:"Hilti TE 30",status:"verfuegbar"};
  console.log(JSON.stringify({
    abbrechen:await lauf(faellig,"M1",false),
    bestaetigen:await lauf(faellig,"M1",true),
    frei:await lauf(frei,"M1",false),
    ohneMonteur:await lauf(faellig,"",true)
  }));
})();
"""


def _wz(index_html, node_exe, tmp_path, name, ersetze=None):
    onclick = _ausgeben_onclick(index_html)
    if ersetze:
        alt, neu = ersetze
        assert alt in onclick, "Koeder-Anker fehlt: %r" % alt
        onclick = onclick.replace(alt, neu, 1)
    checkout = _zeile(index_html, "  const checkout=(id,monteurId,projektId)=>")
    code = ("var window={};\n" + "\n".join(_zeile(index_html, a) for a in GRUND_WZ) + "\n"
            + _extract_fn(index_html, "_optionalChain") + "\n"
            + WZ_LAUF % {"checkout": checkout, "onclick": onclick})
    return _node(node_exe, tmp_path, code, name)


# Der PUT-Koerper, den checkout() vor v1051 schrieb (test_werkzeuge_ux_v1049 haelt den Quelltext fest)
ERWARTET = [{"url": "/api/werkzeuge/W1", "method": "PUT",
             "body": {"status": "ausgegeben", "zugewiesen": "M1", "projekt": "", "standort": "Baustelle"}}]


def test_ausgeben_rueckfrage_verhalten(index_html, node_exe, tmp_path):
    m = _wz(index_html, node_exe, tmp_path, "wz.js")
    ab, ja, fr, oh = m["abbrechen"], m["bestaetigen"], m["frei"], m["ohneMonteur"]
    for r in (ab, ja, fr, oh):
        assert r["nativ"] == 0, "natives alert/confirm aufgerufen"
    assert len(ab["asked"]) == 1 and "Fluke 1664 ist zur Kalibrierung fällig" in ab["asked"][0][0]
    assert ab["asked"][0][1] == "Trotzdem ausgeben"
    assert ab["writes"] == [], "Abbrechen hat geschrieben"
    assert ja["writes"] == ERWARTET, ja["writes"]
    assert fr["asked"] == [] and fr["writes"] == [{"url": "/api/werkzeuge/W2", "method": "PUT",
                                                    "body": ERWARTET[0]["body"]}]
    assert oh["writes"] == [] and oh["asked"] == [] and oh["toasts"] and oh["toasts"][0][1] == "warn"


def test_koeder_abbrechen_schreibt_wird_erkannt(index_html, node_exe, tmp_path):
    m = _wz(index_html, node_exe, tmp_path, "wz_koeder.js",
            ('{confirmLabel:"Trotzdem ausgeben"})))return;', '{confirmLabel:"Trotzdem ausgeben"})));'))
    assert m["abbrechen"]["writes"] != [], "KOEDER STUMM: Schreiben trotz Abbrechen bliebe unbemerkt"


def test_kein_natives_alert_confirm_im_ausgeben(index_html):
    oc = _ausgeben_onclick(index_html)
    assert not re.search(r"(?<![\w.])(alert|confirm)\(", oc), oc


# ── 4. Sammel-Tanken in CI-Farben ───────────────────────────────────────────
def test_sammel_tanken_ohne_orange(index_html):
    a = index_html.index(", batchMode&&!sel&&(React.createElement('div', { className: \"fade-in\"}")
    b = index_html.index("\n      , !sel&&!batchMode&&visibleFz.length===0", a)
    t = index_html[a:b]
    assert "#f97316" not in t and "249,115,22" not in t and "#ea580c" not in t
    assert '"2px solid "+COLORS.EP_GREEN' in t and "_lesbar(COLORS.EP_GREEN)" in t
    assert '"Sammel-Tanken"' in t and "Batch-Tanken" not in t
    assert "onClick: batchSave" in t and "onClick: ()=>batchDel(r.id)" in t, "Schreibwege unveraendert verdrahtet"
