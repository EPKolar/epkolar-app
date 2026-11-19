# -*- coding: utf-8 -*-
"""v1058 Tablet-Geraetepruefung (Lenovo hoch/quer, 1055/1056) - Funde 1, 2, 3 und 5.

1 Flotte quer: _fzInfoModus liefert seit v1055 am Tablet quer 'sheet' (Karte < 420 px), das Blatt (_infoSheet)
  hing aber nur im Handy-Zweig der FlotteView. Quer erschien darum NUR der Verlauf, nie die Info-Karte.
  Beim Drehen mit offener Karte (hoch -> quer) blieb der Popup-Versatz stehen und der Marker lag am unteren Rand.
2 Glocke: v1055 markierte erledigte Ausfall-Meldungen nur als gelesen - gelistet (roter Rand, Dringend) blieben sie.
3 Glocke: Abwesenheits-Text endete nach einer Zeile bei "inzwis...".
5 Kleinkram: Planung-KW-Chip, Dispo-Pfeil, Material-Reiter, Plaene-Kopf, km-Tausenderpunkt, Spezialfahrzeuge leer.

Jeder Rechner laeuft echt aus index.html (Node), jede Gruppe hat eine Umkehrprobe.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn


def _fns(src, *names):
    out = []
    for n in names:
        f = _extract_fn(src, n)
        assert f, n + " nicht gefunden"
        out.append(f)
    return "\n".join(out) + "\n"


def _run(node_exe, code, expr):
    return json.loads(run_node_snippet(node_exe, code + "\nprocess.stdout.write(JSON.stringify(" + expr + "));"))


# ── 1 Flotte ─────────────────────────────────────────────────────────────────

def _flotte_desktop(src):
    i = src.index("/* Maximiert: Fahrtenbuch fuellt den ganzen Flotte-Tab, Dreifenster ausgeblendet. */")
    j = src.index("//@FLOTTE-AUSBAU-START", i)
    return src[i:j]


def _flotte_mobil(src):
    i = src.index("/* Mobile: kein Drag-Splitter (Sebastian).")
    j = src.index("/* Maximiert: Fahrtenbuch fuellt den ganzen Flotte-Tab", i)
    return src[i:j]


def test_flotte_quer_liefert_blatt(index_html, node_exe):
    code = re.search(r"var FZ_POPUP_MIN_KARTE_H=\d+;", index_html).group(0) + "\n" + _fns(index_html, "_fzInfoModus")
    # Lenovo quer: Karte ~313 CSS-px hoch, kein Handy -> Blatt
    assert _run(node_exe, code, "_fzInfoModus(false,true,313)") == "sheet"


def test_flotte_blatt_haengt_auch_im_tablet_zweig(index_html):
    assert ",_infoSheet" in _flotte_mobil(index_html)
    assert ",_infoSheet" in _flotte_desktop(index_html), "Tablet/Desktop-Zweig rendert das Blatt nicht"


def test_flotte_umkehrprobe_ohne_blatt_im_tablet_zweig(index_html):
    alt = index_html.replace("    ,_infoSheet/* v1058 Tablet quer (1)", "    /* v1058 Tablet quer (1)", 1)
    assert alt != index_html
    assert ",_infoSheet" not in _flotte_desktop(alt), "Umkehrprobe: der Riegel muss den alten Zustand (v1055) erkennen"


def test_flotte_marker_im_bild(index_html, node_exe):
    code = _fns(index_html, "_fzPunktImBild")
    r = _run(node_exe, code,
             "[_fzPunktImBild(380,391,760,313,30),_fzPunktImBild(380,156,760,313,30),_fzPunktImBild(380,300,760,313,30),"
             "_fzPunktImBild(10,156,760,313,30),_fzPunktImBild(null,1,760,313,30),_fzPunktImBild(1,1,0,0,30)]")
    # nach dem Drehen: Marker bei y 391 in 313 hoher Karte -> verschieben; Mitte -> nicht; Rand -> verschieben; Muell -> nichts tun
    assert r == [False, True, False, False, True, True]


def test_flotte_marker_wird_im_blatt_modus_zentriert(index_html):
    i = index_html.index("const _sheetPanRef=_react.useRef.call(void 0, '');")
    blk = index_html[i:i + 900]
    assert "if(_infoModus!=='sheet'||_selLat===null||!map){_sheetPanRef.current='';return;}" in blk
    assert "if(!_fzPunktImBild(pt.x,pt.y,sz.x,sz.y,30))map.panTo([la,lo],{animate:false});" in blk
    assert "},[selFid,_selLat,_selLon,_infoModus,popAnstoss]);" in blk
    # Marke erst im Zeitgeber: faellt der Lauf durch neue Abhaengigkeiten weg, versucht es der naechste
    assert "setTimeout(function(){_sheetPanRef.current=_k;" in blk


# ── 2 Glocke: erledigte Ausfall-Meldungen ────────────────────────────────────

def _esk(src):
    return (re.search(r"var ESK_NETZ_RUNDEN=[^;]+;", src).group(0) + "\n"
            "var ESK_AUSFALL_TITEL=" + re.search(r"var ESK_AUSFALL_TITEL=(\{[^}]*\});", src).group(1) + ";\n"
            "var ESK_AUSFALL_TYP=" + re.search(r"var ESK_AUSFALL_TYP=(\{[^}]*\});", src).group(1) + ";\n"
            "var _LS={};var localStorage={getItem:function(k){return _LS.hasOwnProperty(k)?_LS[k]:null;},setItem:function(k,v){_LS[k]=String(v);}};\n"
            + _fns(src, "_notifKeyId", "_eskAusfallSchritt", "_eskAusfallMelden", "_eskAusfallKeyVon",
                   "_eskAusfallStandLesen", "_eskAusfallStandSetzen", "_eskAusfallVeraltet"))


LISTE = [
    # die beiden vom Geraet (Di 17.11. 21:07), gelesen
    {"id": "a1", "type": "ticket_eskalation", "title": "Fristenprüfung unvollständig", "read": True, "user": "u1",
     "time": "2026-11-17T20:07:00.000Z"},
    {"id": "a2", "type": "material_eskalation", "title": "Material-Fristen NICHT geprüft", "read": True, "user": "u1",
     "time": "2026-11-17T20:07:00.000Z"},
    # echte Eskalation, keine Ausfall-Meldung
    {"id": "a3", "type": "ticket_eskalation", "title": "🔺 Ticket überfällig: Dach", "read": False, "user": "u1",
     "time": "2026-11-17T20:07:00.000Z"},
    # Altbestand mit Zeichen vor dem Titel
    {"id": "a4", "type": "ticket_eskalation", "title": "⚠️ Fristenprüfung unvollständig", "read": False, "user": "u1",
     "time": "2026-11-17T20:07:00.000Z"},
]


def test_glocke_erledigte_ausfaelle_verschwinden(index_html, node_exe):
    code = _esk(index_html) + "var L=" + json.dumps(LISTE, ensure_ascii=False) + ";\n"
    ok = "Date.UTC(2026,10,19,12,0,0)"
    r = _run(node_exe, code,
             "(function(){var out={};"
             "out.leer=L.filter(function(n){return !_eskAusfallVeraltet(n,_eskAusfallStandLesen());}).map(function(n){return n.id;});"
             "_eskAusfallStandSetzen('rls_frist','ok'," + ok + ");_eskAusfallStandSetzen('rls_material','ok'," + ok + ");"
             "var st=_eskAusfallStandLesen();"
             "out.nachOk=L.filter(function(n){return !_eskAusfallVeraltet(n,st);}).map(function(n){return n.id;});"
             "var neu={id:'a5',type:'ticket_eskalation',title:'Fristenprüfung unvollständig',user:'u1',time:new Date(" + ok + "+60000).toISOString()};"
             "out.neuer=_eskAusfallVeraltet(neu,st);"
             "out.keys=L.map(_eskAusfallKeyVon);"
             "out.perId=_eskAusfallKeyVon({id:_notifKeyId('u1','material_eskalation','rls_material'),type:'material_eskalation',title:'x',user:'u1'});"
             "return out;})()")
    assert r["leer"] == ["a1", "a2", "a3", "a4"], "ohne sauberen Lauf bleibt alles stehen"
    assert r["nachOk"] == ["a3"], "nach sauberem Lauf: beide Ausfall-Meldungen weg, echte Eskalation bleibt"
    assert r["neuer"] is False, "eine Meldung NACH dem sauberen Lauf bleibt sichtbar"
    assert r["keys"] == ["rls_frist", "rls_material", "", "rls_frist"]
    assert r["perId"] == "rls_material"


def test_glocke_neuer_ausfall_zeigt_wieder(index_html, node_exe):
    code = _esk(index_html) + "var L=" + json.dumps(LISTE, ensure_ascii=False) + ";\n"
    r = _run(node_exe, code,
             "(function(){_eskAusfallStandSetzen('rls_frist','ok',Date.UTC(2026,10,19,12,0,0));"
             "var vor=_eskAusfallVeraltet(L[0],_eskAusfallStandLesen());"
             "var m=_eskAusfallMelden('rls_frist','rechte');"
             "return [vor,m>0,_eskAusfallVeraltet(L[0],_eskAusfallStandLesen())];})()")
    assert r == [True, True, False], "ein spaeter gemeldeter Ausfall (fehl > ok) muss wieder sichtbar sein"


def test_glocke_verdrahtung(index_html):
    assert ("const _eskStand=_eskAusfallStandLesen();const myNotifs=curUser?notifications.filter("
            "n=>n.user===curUser.id&&!_eskAusfallVeraltet(n,_eskStand)):[];") in index_html
    i = index_html.index("const _ausfallErledigt=(key)=>{")
    blk = index_html[i:i + 700]
    assert '_eskAusfallStandSetzen(key,"ok",Date.now());};' in blk
    assert 'if(r.melden)_eskAusfallStandSetzen(key,"fehl",j);' in index_html
    # die v1055-Pins bleiben
    assert 'if(_fArt==="")_ausfallErledigt("rls_frist");}' in index_html
    assert 'if(_mArt==="")_ausfallErledigt("rls_material");}' in index_html


def test_glocke_umkehrprobe_nur_gelesen_reicht_nicht(index_html, node_exe):
    """v1055-Zustand: nur gelesen markiert, keine Ausblendung -> die gelesene Meldung bleibt in der Liste."""
    alt = index_html.replace("&&!_eskAusfallVeraltet(n,_eskStand)", "", 1)
    assert alt != index_html
    assert "_eskAusfallVeraltet(n,_eskStand)" not in alt
    # und ein kaputter Rechner (fehl/ok vertauscht) wuerde vom Test oben erkannt
    kaputt = index_html.replace("if(!(ok>0)||fehl>ok)return false;", "if(!(ok>0))return false;", 1)
    assert kaputt != index_html
    code = _esk(kaputt) + "var L=" + json.dumps(LISTE, ensure_ascii=False) + ";\n"
    r = _run(node_exe, code,
             "(function(){_eskAusfallStandSetzen('rls_frist','ok',Date.UTC(2026,10,19,12,0,0));"
             "_eskAusfallMelden('rls_frist','rechte');return _eskAusfallVeraltet(L[0],_eskAusfallStandLesen());})()")
    assert r is True, "Umkehrprobe: ohne fehl-Pruefung bliebe ein neuer Ausfall versteckt"


# ── 3 Glocke: zwei Zeilen ────────────────────────────────────────────────────

def _body_stil(src):
    i = src.index("title: _absNotifText(n,abs)}, _absNotifText(n,abs))")
    j = src.rindex("React.createElement('div', { style: {", 0, i)
    return src[j:i]


def test_glocke_text_zwei_zeilen(index_html):
    st = _body_stil(index_html)
    assert "WebkitLineClamp:2" in st and 'display:"-webkit-box"' in st and 'WebkitBoxOrient:"vertical"' in st
    assert 'whiteSpace:"nowrap"' not in st
    assert "fontSize:12" in st


def test_glocke_text_umkehrprobe(index_html):
    alt = index_html.replace(
        'overflow:"hidden",display:"-webkit-box",WebkitLineClamp:2,WebkitBoxOrient:"vertical",whiteSpace:"normal",overflowWrap:"anywhere"}',
        'overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}', 1)
    assert alt != index_html
    assert 'whiteSpace:"nowrap"' in _body_stil(alt)


# ── 5 Kleinkram ──────────────────────────────────────────────────────────────

def test_planung_kw_chip_grundbreite(index_html, node_exe):
    i = index_html.index("'data-wp-kwreihe': \"1\"")
    seg = index_html[i:i + 1400]
    m = re.search(r'flex:"1 1 "\+(Math\.min\(260,_ks\.length\*56\))\+"px"', seg)
    assert m, "KW-Reihe: Grundbreite nicht nach Chipzahl"
    r = _run(node_exe, "", "[1,2,26].map(function(n){var _ks=new Array(n);return " + m.group(1) + ";})")
    assert r == [56, 112, 260]
    assert 'flex:"1 1 260px"' not in seg, "Umkehrprobe: feste 260 px liessen einen Chip unter die Pfeile fallen"


def test_dispo_pfeile_bleiben_in_der_reihe(index_html):
    i = index_html.index("/* v3.9.725 #14: KW-Tabs (Wochenplanungs-Stil)")
    seg = index_html[i:i + 4500]
    assert "flexWrap:\"nowrap\"}}/* v1058 (5)" in seg
    assert "minWidth:44,flexShrink:0},'aria-label':\"Vorherige Woche\"" in seg
    assert "minWidth:44,flexShrink:0},'aria-label':\"Nächste Woche\"" in seg
    # AS Hochformat (GF 19.11.2026): die Wochen-Huelle bricht nicht mehr um (KW 50 stand allein in
    # Zeile 2, die Pfeile wurden hohe Seitenspalten) - EINE Reihe, die bei Platzmangel selbst rollt.
    assert "h('div',{'data-kw-leiste':\"1\",style:{display:\"flex\",gap:6,flexWrap:\"nowrap\",overflowX:\"auto\",scrollbarWidth:\"thin\",flex:\"1 1 0\",minWidth:0}}" in seg
    # Reihenfolge: Pfeil zurueck, Wochen-Huelle, Pfeil vor
    a = seg.index("Vorherige Woche")
    b = seg.index("wochen.map(")
    c = seg.index("Nächste Woche\"},_ik(")
    assert a < b < c


def test_material_reiter_tablet_padding(index_html):
    assert 'padding:isMob?"10px 14px":"10px 10px"' in index_html
    assert 'padding:isMob?"10px 14px":"10px 16px",border:"none",borderBottom:tab===t.id' not in index_html


def test_plaene_kopf_tablet_hoch(index_html):
    assert 'flex:isMob?"1 1 0":(ww<1000?"1 1 100%":"2 1 240px")' in index_html
    assert 'placeholder: ww<1000?"Pin-Nr / Titel suchen…":"Pin-Nr oder Titel suchen…"' in index_html


def _km_fmt(src):
    m = re.search(r'fmt: ch\.fmt\|\|(\(v=>\(typeof v==="number"&&isFinite\(v\)\)\?v\.toLocaleString\("de-[A-Z]{2}",\{maximumFractionDigits:1\}\):v\))', src)
    assert m, "Standard-Formatierer der Diagramme nicht gefunden"
    return m.group(1)


def test_auswertung_km_tausenderpunkt(index_html, node_exe):
    f = _km_fmt(index_html)
    r = _run(node_exe, "var F=" + f + ";", "[F(243848),F(5000),F(12.5),F('x')]")
    assert r == ["243.848", "5.000", "12,5", "x"]


def test_auswertung_km_umkehrprobe(index_html, node_exe):
    alt = index_html.replace('v.toLocaleString("de-DE",{maximumFractionDigits:1}):v)/* v1058', 'v.toLocaleString("de-AT",{maximumFractionDigits:1}):v)/* v1058', 1)
    assert alt != index_html
    r = _run(node_exe, "var F=" + _km_fmt(alt) + ";", "F(243848)")
    assert r != "243.848", "Umkehrprobe: de-AT gruppiert hier mit Leerzeichen"


def test_spezialfahrzeuge_leer(index_html, node_exe):
    code = _fns(index_html, "_wpSpezHatBuchung")
    r = _run(node_exe, code,
             "(function(){var T=['Mo','Di','Mi','Do','Fr','Sa'];var FZ=[{id:'f1'},{id:'f2'}];"
             "var leer=[{z:{Mo:{ma:['m1'],fz:[]},Di:{fz:['x9']}}},{z:null},{}];"
             "var voll=[{z:{Mi:{fz:['f2']}}}];"
             "return [_wpSpezHatBuchung(FZ,leer,T),_wpSpezHatBuchung(FZ,voll,T),_wpSpezHatBuchung([],voll,T),_wpSpezHatBuchung(FZ,null,T)];})()")
    assert r == [False, True, False, False]
    assert "const _wpSpezGebucht=_wpSpezHatBuchung(spezFz,rows,DSHORT);" in index_html
    assert ', !_wpSpezGebucht&&React.createElement(\'div\', { style: {padding:"2px 8px 4px "+(_WP_SP.nr+8)+"px",fontSize:UI.fMeta,color:V.dm}}, "Diese Woche ist kein Spezialfahrzeug eingeplant.")' in index_html


def test_spezialfahrzeuge_umkehrprobe(index_html, node_exe):
    kaputt = index_html.replace("return Array.isArray(l)&&l.some(function(id){return ids[id]===1;});", "return Array.isArray(l)&&l.length>0;", 1)
    assert kaputt != index_html
    r = _run(node_exe, _fns(kaputt, "_wpSpezHatBuchung"),
             "_wpSpezHatBuchung([{id:'f1'}],[{z:{Di:{fz:['x9']}}}],['Di'])")
    assert r is True, "Umkehrprobe: fremde Fahrzeug-ids duerfen nicht als Spezialfahrzeug-Buchung zaehlen"
