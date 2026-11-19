# -*- coding: utf-8 -*-
"""A55-2 (Samsung A55, Bericht 3 vom 16.11.2026 + Zusatzfund Bericht 6) - Riegel je Fund, je mit Umkehrprobe.

Jeder Riegel ist eine Pruefung pruefe_X(src) -> bool. Sie muss auf dem echten Quelltext gruen sein
UND auf einem gezielt zurueckgebauten Quelltext rot - sonst schlaegt der Riegel nie an.

 6  Formulare: Wischen ueber das Unterschriftenfeld zeichnete eine Unterschrift.
 7  Projektakte: Fussleiste mit allen Reitern quer (rechts 'Zeiter...' abgeschnitten); Menueknopf fix
    ueber Kopfzeile 1 (verdeckte 'Alle Projekte'), Kopfzeile 1 brach um.
 8  Arbeitsschein-Karte: roter Storno-Knopf links direkt neben 'Bearbeiten'.
 9  Arbeitsscheine: Schnellfilter 'Alle' aktiv, obwohl der Status-Filter wirkte.
10  Chef -> Projekte: Auftragssumme/Budget/Fortschritt ohne Beschriftung.
12  Emoji in Formulare, Material, Einstellungen, KV-Zuschlaege, Update-Banner.
13/14  technische Schluessel als Text (stempel pause rules, projects.betrag, created_at, time_entries).
16  Chef -> Personal: Monteurnamen auf 90 px gekuerzt.
18  Ebenen/Tickets: rote Loeschknoepfe.
19  Projekt -> Zeiten: Tageskoepfe abgeschnitten (minWidth:700 vom globalen min-width:0 gekappt).
22  Material: '1 Anforderungen'.
23  Projektakte: Unterseite oeffnete mit der alten Rollposition.
25  Arbeitsscheine ueber Mehr geoeffnet -> Fussleiste markierte 'Baustelle'.
Z   Wisch-Navigation: keine Seite wechseln, solange Mehr-Liste offen ist oder die Geste in einem Dialog beginnt.
"""
import io
import os
import re
import subprocess
import tempfile

import pytest

from _hilfen import nur_code

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")


def _fn(src, name, ende="\nfunction "):
    i = src.index("function " + name + "(")
    j = src.find(ende, i + 10)
    return src[i:j]


def _umkehr(pruefe, src, alt, neu):
    assert pruefe(src), "Riegel ist auf dem echten Stand rot"
    kaputt = src.replace(alt, neu, 1)
    assert kaputt != src, "Rueckbau griff nicht: " + alt[:80]
    assert not pruefe(kaputt), "Umkehrprobe: Riegel schlaegt beim Rueckbau nicht an"


# ── 6 Unterschrift ──────────────────────────────────────────────────────────
def _sig_ok(src):
    f = _fn(src, "SignaturePad")
    return ("const startDraw=(e)=>{if(!aktiv)return;" in f
            and "if(!aktiv||!drawing)return;" in f
            and 'touchAction:aktiv?"none":"pan-y"' in f
            and "onClick: ()=>setAktiv(true)" in f
            and "✍" not in f and "✅" not in f)


def test_6_unterschrift_erst_nach_tipp(index_html):
    _umkehr(_sig_ok, index_html, "const startDraw=(e)=>{if(!aktiv)return;", "const startDraw=(e)=>{")
    _umkehr(_sig_ok, index_html, 'touchAction:aktiv?"none":"pan-y"', 'touchAction:"none"')


# ── 7 Projektakte Kopf + Fussleiste ────────────────────────────────────────
def _pf_ok(src):
    f = _fn(src, "ProjectShell")
    return ("isMob&&_pfFussLeiste, (isMob?[]:_pnSicht).map(" in f
            and 'position:"fixed",top:8,left:8,zIndex:89' not in f
            and "gap:6,minWidth:0,flex:1}}, isMob&&React.createElement('button', { onClick: () => setMobNav(true)" in f
            and 'flexShrink:0,gap:6,flexWrap:isMob?"nowrap":"wrap"' in f
            and "_pfGruppen.map(" in f)


def test_7_projektakte_fussleiste_fuenf_gruppen(index_html):
    _umkehr(_pf_ok, index_html, "isMob&&_pfFussLeiste, (isMob?[]:_pnSicht).map(", "_pnSicht.map(")
    _umkehr(_pf_ok, index_html, 'flexShrink:0,gap:6,flexWrap:isMob?"nowrap":"wrap"', 'flexShrink:0,gap:6,flexWrap:"wrap"')


def test_7_fussleiste_in_der_akte_nennt_dieselben_gruppen_wie_die_app(index_html):
    f = _fn(index_html, "ProjectShell")
    for gr in ('l:"Home",g:0', 'l:"Baustelle",g:1', 'l:"Zeit",g:2', 'l:"Fuhrpark",g:3', 'l:"Mehr",g:4'):
        assert gr in f, gr
    assert 'const _pfG=t=>t.perm==="_chef"?4:t.g;' in f, "Chef haengt am Mehr wie in der App"


# ── 8 Storno abgesetzt ─────────────────────────────────────────────────────
def _storno_ok(src):
    return ('fontSize:UI.fMeta,cursor:"pointer",fontWeight:600,minHeight:44,marginLeft:"auto"}' in src
            and 'minHeight:44,order:-1,marginRight:"auto"}, title: "Stornieren"' not in src)


def test_8_storno_rechts_abgesetzt(index_html):
    _umkehr(_storno_ok, index_html, 'fontSize:UI.fMeta,cursor:"pointer",fontWeight:600,minHeight:44,marginLeft:"auto"}',
            'fontSize:12,cursor:"pointer",fontWeight:600,minHeight:44,order:-1,marginRight:"auto"}')
    assert "storno(a.id);" in index_html and 'confirmModal("Arbeitsschein wirklich stornieren?"' in index_html


# ── 9 'Alle' ehrlich ───────────────────────────────────────────────────────
def _alle_ok(src):
    return 'const act=chip.key===""?(!quickFilter&&filterStatus==="alle"):quickFilter===chip.key;' in src


def test_9_alle_nur_aktiv_wenn_nichts_filtert(index_html):
    _umkehr(_alle_ok, index_html, 'const act=chip.key===""?(!quickFilter&&filterStatus==="alle"):quickFilter===chip.key;',
            "const act=quickFilter===chip.key;")
    assert "onClick:()=>setQuickFilter(chip.key)" in index_html, "Klickweg unveraendert"


# ── 10/14 Beschriftungen Chef ──────────────────────────────────────────────
def _chef_ok(src):
    return ("'Budget verbr.'" in src and "'kalk. Kosten / Kostenbudget'" in src
            and "' · Baufortschritt '" in src and "projects.betrag" not in code_ohne_kommentar(src)
            and "erfasste time_entries" not in src and "(created_at)" not in src
            and '"Fortschritt ", (p.fortschritt||0), " %"' in src)


def code_ohne_kommentar(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


def test_10_14_budget_klar_beschriftet(index_html):
    _umkehr(_chef_ok, index_html, "'Budget verbr.'", "'Budget %'")
    _umkehr(_chef_ok, index_html, "Auftragssummen der Projekte nach Anlagedatum",
            "Auftragssummen (projects.betrag) nach Anlagedatum (created_at)")
    # Rechnung unveraendert
    assert "ePct:be>0?Math.round(kalk/be*100):null" in index_html


# ── 12 Emoji ───────────────────────────────────────────────────────────────
def _ohne_toast(t):
    return re.sub(r"__toast[^;]*;|_showToast[^;]*;|__pushNotif\([^;]*;", "", t)


def test_12_emoji_frei_formulare(index_html):
    i = index_html.index("function VForm(")
    j = index_html.index("\nfunction ", index_html.index("function FRegie(") + 5)
    teil = code_ohne_kommentar(_ohne_toast(index_html[i:j]))
    assert EMOJI.findall(teil) == [], EMOJI.findall(teil)


def test_12_emoji_material_reiter_und_knoepfe(index_html):
    i = index_html.index("function VMaterial(")
    teil = index_html[i:index_html.index("\nfunction VOffa(")]
    for alt in ('"🛒 Warenkorb"', '"📋 Verlauf"', '"📦 Lager"', '"🏪 Bestellungen"', '"⚙ Katalog"',
                '"🖨 Drucken"', '"📦 Ans Lager senden"', '"📊 Bestellung vorbereiten"', '"🛒 Bestellt"',
                '"✅ Erledigt"', '"❌ Storno"', '"🗑 Löschen"', '"📍 Lieferadresse"'):
        assert alt not in teil, alt
    assert "}, _ik(t.ik,16), t.l, t.badge>0&&" in teil


def test_12_emoji_einstellungen_kv_update(index_html):
    for alt in ("'⚙️ System-Konfiguration'", '"\U0001F52C Smoke-Tests', '"✓ Smoke-Tests"', '"\U0001F50D Integrit',
                "'\U0001F4B6 KV-Zuschl", '"\U0001F504 Neue Version verf', "'✏ '+row.updated_by"):
        assert alt not in index_html, alt
    assert '_ikVw("regler","System-Konfiguration")' in index_html


def test_12_umkehrprobe(index_html):
    f = lambda s: '"\U0001F504 Neue Version verf' not in s
    _umkehr(f, index_html, '_ik("drehen",18), "Neue Version verf', '"\U0001F504 Neue Version verf')


# ── 13 Schluesselname ──────────────────────────────────────────────────────
def test_13_sysconfig_deutscher_name(index_html):
    js = index_html[index_html.index("const _SYSCFG_NAMEN="):index_html.index("\n", index_html.index("function _sysCfgLabel("))]
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    probe = js + "\nconsole.log(_sysCfgLabel({key:'stempel_pause_rules'}),'|',_sysCfgLabel({key:'x_y'}),'|',_sysCfgLabel({key:'km',description:'TÜV'}));"
    out = _node(probe)
    assert out.strip() == "Stempel-Pausenregeln | x y | Pickerl", out


# ── 16 Personal ────────────────────────────────────────────────────────────
def test_16_personal_name_volle_breite(index_html):
    f = lambda s: "flex:isMob?'1 1 0':'0 0 130px',minWidth:0" in s and "width:isMob?90:130" not in s
    _umkehr(f, index_html, "flex:isMob?'1 1 0':'0 0 130px',minWidth:0", "width:isMob?90:130")


# ── 18 Loeschknoepfe neutral ───────────────────────────────────────────────
def test_18_loeschen_neutral(index_html):
    f = lambda s: s.count("Ticket löschen\", onClick: e=>{e.stopPropagation();deleteTicket(t.id);}, style: {...bsS(),color:V.dm") == 1 and \
        "onClick: ()=>deleteLayer(l.id), style: {...bsS(),color:V.dm" in s
    _umkehr(f, index_html, "onClick: ()=>deleteLayer(l.id), style: {...bsS(),color:V.dm", "onClick: ()=>deleteLayer(l.id), style: {...bdS")


# ── 19 Zeiten ──────────────────────────────────────────────────────────────
def test_19_zeiten_drei_spalten_am_handy(index_html):
    # UI-Runde 1072: die Spaltenwahl steht jetzt in _zeWochenSpalten(_layoutStufe(...)) - am Handy
    # weiter drei Tage je Reihe (repeat(3,minmax(0,1fr))), Tablet hochkant ebenfalls drei mit 150 px
    # Mindestbreite, quer/PC sechs mit 120 px. Der Kern dieses Riegels (kein minWidth:700 am Raster,
    # das die globale Regel ohnehin kappt) bleibt unveraendert.
    f = lambda s: 'gridTemplateColumns:_zeWochenSpalten(_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0))),gap:6}}' in s and \
        'stufe==="schmal"?"repeat(3,minmax(0,1fr))"' in s and \
        'gridTemplateColumns:"repeat(6,1fr)",gap:6,minWidth:isMob?700:0' not in s
    _umkehr(f, index_html, 'gridTemplateColumns:_zeWochenSpalten(_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0))),gap:6}}',
            'gridTemplateColumns:"repeat(6,1fr)",gap:6,minWidth:isMob?700:0}}')


# ── 22 Grammatik ───────────────────────────────────────────────────────────
def test_22_eine_anforderung(index_html):
    f = lambda s: 'orders.length===1?" Anforderung":" Anforderungen"' in s
    _umkehr(f, index_html, 'orders.length===1?" Anforderung":" Anforderungen"', '" Anforderungen"')


# ── 23 Rollposition ────────────────────────────────────────────────────────
def test_23_unterseite_oeffnet_oben(index_html):
    f = lambda s: 'const _m=document.querySelector(".proj-main");if(_m)_m.scrollTop=0;}catch(_e){}},[view]);' in _fn(s, "ProjectShell")
    _umkehr(f, index_html, ",[view]);", ",[]);")


# ── 25 Mehr markiert ───────────────────────────────────────────────────────
# A55-Vollpruefung 19.11.: Fund 25 umgekehrt - Zeiterfassung ueber Mehr markierte Mehr statt Zeit.
# Markiert ist jetzt immer die Gruppe des gezeigten Reiters, egal ueber welchen Weg (Verhalten: test_a55_voll_p2_v1054).
def test_25_markierung_haengt_nicht_am_weg(index_html):
    f = lambda s: "const isActive=grTabs.some(t=>tabs.indexOf(t)===safeKat);" in s and "_fussMehrKat" not in s \
        and "setKat(ri);setMoreOpen(false);}" in s
    _umkehr(f, index_html, "const isActive=grTabs.some(t=>tabs.indexOf(t)===safeKat);",
            "const _viaMehr=_fussMehrKat!==null&&_fussMehrKat===safeKat;const isActive=!_viaMehr&&grTabs.some(t=>tabs.indexOf(t)===safeKat);")


# ── Z Wisch-Navigation ─────────────────────────────────────────────────────
def _node(js):
    fn = os.path.join(tempfile.gettempdir(), "a55f2_probe_%d.js" % os.getpid())
    io.open(fn, "w", encoding="utf-8").write(js)
    r = subprocess.run(["node", fn], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return r.stdout


_PROBE = r"""
var _react={useRef:{call:function(_,v){return {current:v};}}};
var SPERRE=false;
var document={body:{},querySelector:function(sel){return (SPERRE&&sel.indexOf('data-swipe-sperre')>=0)?{}:null;}};
function getComputedStyle(){return {overflowX:'visible'};}
%s
function el(treffer){return {nodeType:1,scrollWidth:0,clientWidth:0,parentElement:null,style:{},
  closest:function(sel){return (treffer||[]).some(function(t){return sel.indexOf(t)>=0;})?{style:{}}:null;}};}
function lauf(punkte,treffer){var g=[];var h=useSwipe(function(){g.push('L');},function(){g.push('R');});
  var mv=null;h.ref({addEventListener:function(t,f){if(t==='touchmove')mv=f;},removeEventListener:function(){}});
  h.onTouchStart({touches:[{clientX:punkte[0][0],clientY:punkte[0][1]}],target:el(treffer),currentTarget:{}});
  for(var i=1;i<punkte.length;i++)mv({touches:[{clientX:punkte[i][0],clientY:punkte[i][1]}],cancelable:true,preventDefault:function(){}});
  var e=punkte[punkte.length-1];h.onTouchEnd({changedTouches:[{clientX:e[0],clientY:e[1]}],stopPropagation:function(){}});return g.join('');}
function linie(a,b,c,d,n){var r=[];for(var i=0;i<=n;i++)r.push([a+(c-a)*i/n,b+(d-b)*i/n]);return r;}
var o={};
o.senkrecht=lauf(linie(300,600,370,300,20));
o.senkrecht_x_fest=lauf(linie(1010,1500,1010,700,20));
o.waagrecht=lauf(linie(300,400,180,405,10));
o.bogen=lauf(linie(300,400,170,490,10));
o.dialog=lauf(linie(300,400,180,405,10),['[role=dialog]']);
SPERRE=true;o.mehr_offen=lauf(linie(300,400,180,405,10));
console.log(JSON.stringify(o));
"""


def _swipe(src):
    a = src.index("function _swScrollableX(")
    b = src.index("// v3.9.75 Sprint-54.2 FIX-5: useSwipeDown")
    import json
    return json.loads(_node(_PROBE % src[a:b]).strip())


def _swipe_ok(src):
    o = _swipe(src)
    return o == {"senkrecht": "", "senkrecht_x_fest": "", "waagrecht": "L", "bogen": "L", "dialog": "", "mehr_offen": ""}


def test_z_wisch_senkrecht_nie_waagrecht_ja_overlay_nein(index_html):
    _umkehr(_swipe_ok, index_html, '||el.closest("[role=dialog],[aria-modal=true]")||_swSperre());', ");")


def test_z_mehr_listen_tragen_die_sperre(index_html):
    assert "moreOpen&&isMob&&React.createElement('div', { 'data-swipe-sperre': \"1\"" in index_html
    assert "'aria-label': \"Weitere Bereiche\", 'data-swipe-sperre': \"1\"" in index_html
