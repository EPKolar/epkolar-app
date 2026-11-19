# -*- coding: utf-8 -*-
"""v3.9.1050 A55-Pruefung (Samsung A55, dunkel, 390 px, v3.9.1048) - Restbefunde.

1  Glocke: jeden Morgen 07:01 "Fristenpruefung unvollstaendig" + "Material-Fristen NICHT geprueft" beim Admin.
   Die Fristen-Lesungen markierten JEDEN Wurf (auch ein kurzes Netzloch beim Aufwachen) wie einen Rechtefehler.
   Node fuehrt die ECHTEN Helfer und die ECHTEN Meldezeilen aus index.html aus:
     * Netzfehler: Runde 1 und 2 schweigen, Runde 3 meldet; Lesen gelingt -> Zaehler zurueck
     * Runden mit grossem Abstand (> Fenster) zaehlen nicht als "in Folge"
     * 403 / 401 (Marke aus _sbGet) und ein unbekannter Wurf melden SOFORT (Absicht v3.9.914 bleibt)
2  Darstellung: die Markierung im Mehr-Menue folgt derselben Wahl wie die Anzeige (resolveTheme == _themeMode)
3  Buero-Portal Abwesenheiten: Einheit "h" + Markierung "Standard" fuer fehlendes Kontingent
4  Linien-Chevrons statt Dreiecke (Stempelzeiten, Zulagen, Krankenstand-Zeilen)
5  Zulagen-Monatsnavigation als Einheit, Buero-Reiter ohne Umbruch
6  Auswertungen: "kein" heisst "Ohne Art"
Umkehrproben: jeder Rueckbau muss mindestens einen Befund liefern.
"""
import json
import re

import pytest

from conftest import run_node_snippet, _extract_fn
from _hilfen import nur_code


def _fns(src, namen):
    teile = []
    for n in namen:
        f = _extract_fn(src, n, rf"(?:async\s+)?function\s+{re.escape(n)}\s*\(")
        assert f, n
        teile.append(f)
    return "\n".join(teile)


def _zeile_ab(src, anfang):
    i = src.index(anfang)
    return src[i:src.index("\n", i)].rstrip("\r")


def _block(src, anfang, ende):
    i = src.index(anfang)
    j = src.index(ende, i) + len(ende)
    return src[i:j]


# ── 1 Glocke ──────────────────────────────────────────────────────────────

ESK_FNS = ("_rlsLeer", "_netzFehlerArt", "_netzOnline", "_eskLeseMarke", "_eskAusfallArt",
           "_eskAusfallSchritt", "_eskAusfallMelden", "_eskAusfallText",
           # v1058 (2): _eskAusfallMelden merkt sich den gemeldeten Ausfall (fehl) fuer die Glocken-Ausblendung
           "_eskAusfallStandLesen", "_eskAusfallStandSetzen")


def _esk(src, node_exe):
    code = _fns(src, ESK_FNS)
    konst = _zeile_ab(src, "var ESK_NETZ_RUNDEN=")
    # v1055 Tablet-Vollpruefung (2): Titel/Typ kommen aus ESK_AUSFALL_*, eine gelesene Runde ruft _ausfallErledigt
    # (markiert alte Ausfall-Meldungen als gelesen) - der Block endet darum hinter diesem Aufruf.
    konst += "\n" + _zeile_ab(src, "var ESK_AUSFALL_TITEL=") + "\n" + _zeile_ab(src, "var ESK_AUSFALL_TYP=") + "\nfunction _ausfallErledigt(k){}"
    mat = _block(src, '{const _mArt=_eskAusfallArt(openMat);', '_ausfallErledigt("rls_material");}')
    frist = _block(src, '{const _fArt=_eskAusfallArt(ovT,ovD);', '_ausfallErledigt("rls_frist");}')
    js = r"""
var _ls={};var localStorage={getItem:function(k){return k in _ls?_ls[k]:null;},setItem:function(k,v){_ls[k]=String(v);}};
var navigator={onLine:true};var _jetzt=1000000000000;var _DN=Date.now;Date.now=function(){return _jetzt;};
var window=undefined;
""" + konst + "\n" + code + r"""
var gefeuert=[],letzte="";function fire(k,t,ti,b){gefeuert.push({k:k,b:b});letzte=b;}
var admins=["a"],_pmU=["a"];
function netz(){return Promise.reject(new TypeError("Failed to fetch"));}
function zeit(){var e=new Error("signal timed out");e.name="TimeoutError";return Promise.reject(e);}
function wurf400(){return Promise.reject(new Error("HTTP400 bad"));}
function rls(st){return Promise.resolve().then(function(){var l=[];l.__rlsFehler=st;return l;});}
function ok(){return Promise.resolve([]);}
async function matRunde(q){gefeuert=[];const openMat=await q().catch(_eskLeseMarke);
""" + mat + r"""
return gefeuert.length;}
async function fristRunde(qt,qd){gefeuert=[];const ovT=await qt().catch(_eskLeseMarke);const ovD=await qd().catch(_eskLeseMarke);
""" + frist + r"""
return gefeuert.length?gefeuert[0].b:"";}
(async function(){var R={};
 _ls={};R.netz=[];for(var i=0;i<4;i++){R.netz.push(await matRunde(netz));_jetzt+=300000;}
 _ls={};R.zeitMitOk=[await matRunde(zeit),await matRunde(zeit),await matRunde(ok),await matRunde(zeit),await matRunde(zeit)];
 _ls={};R.abstand=[];for(var j=0;j<3;j++){R.abstand.push(await matRunde(netz));_jetzt+=3600000;}
 _ls={};letzte="";R.r403=await matRunde(function(){return rls(403);});R.r403b=letzte;
 _ls={};letzte="";R.r401=await matRunde(function(){return rls(401);});R.r401b=letzte;
 _ls={};letzte="";R.w400=await matRunde(wurf400);R.w400b=letzte;
 _ls={};letzte="";R.netz3=[];for(var k=0;k<3;k++){R.netz3.push(await matRunde(netz));_jetzt+=300000;}R.netz3b=letzte;
 _ls={};navigator.onLine=false;R.offline=[await matRunde(netz),await matRunde(netz),await matRunde(netz)];navigator.onLine=true;
 _ls={};R.ok=await matRunde(ok);
 _ls={};R.frist=[await fristRunde(netz,ok),await fristRunde(ok,netz),await fristRunde(netz,netz),await fristRunde(netz,netz),await fristRunde(netz,netz)];
 _ls={};R.frist403=await fristRunde(ok,function(){return rls(403);});
 _ls={};R.fristMix=await fristRunde(netz,function(){return rls(403);});
 console.log(JSON.stringify(R));})();
"""
    return json.loads(run_node_snippet(node_exe, js))


def _esk_befunde(r):
    b = []
    if r["netz"][:2] != [0, 0]:
        b.append("Netzfehler meldet schon in Runde 1/2: %r" % r["netz"])
    if r["netz"][2] != 1:
        b.append("Netzfehler meldet nach 3 Runden NICHT: %r" % r["netz"])
    if r["zeitMitOk"] != [0, 0, 0, 0, 0]:
        b.append("Gelesene Runde setzt den Zaehler nicht zurueck: %r" % r["zeitMitOk"])
    if r["abstand"] != [0, 0, 0]:
        b.append("Runden mit Stunden Abstand gelten als 'in Folge': %r" % r["abstand"])
    if r["r403"] != 1 or "Keine Leserechte für Materialanforderungen" not in r["r403b"]:
        b.append("403 meldet nicht sofort mit Rechte-Text: %r" % r.get("r403b"))
    if r["r401"] != 1 or "Keine Leserechte" not in r["r401b"]:
        b.append("401 meldet nicht sofort mit Rechte-Text: %r" % r.get("r401b"))
    if r["w400"] != 1 or "Leserechte" in r["w400b"] or "Verbindung" in r["w400b"]:
        b.append("Unbekannter Wurf (HTTP400) meldet nicht sofort / falscher Text: %r" % r.get("w400b"))
    if "keine Verbindung" not in r["netz3b"] or " seit " not in r["netz3b"] or "Leserechte" in r["netz3b"]:
        b.append("Netz-Meldung nach 3 Runden ohne eigenen Netz-Text: %r" % r["netz3b"])
    for k in ("r403b", "r401b", "w400b", "netz3b"):
        if "Rechte oder Netz" in r[k]:
            b.append("gemischter Text 'Rechte oder Netz' ist zurueck")
    if r["offline"][:2] != [0, 0] or r["offline"][2] != 1:
        b.append("Offline wird nicht wie Netz behandelt: %r" % r["offline"])
    if r["ok"] != 0:
        b.append("Gelesene leere Liste meldet")
    f = r["frist"]
    # drei Runden in Folge mit Netzausfall (gleich welche der beiden Lesungen) -> Meldung in Runde 3
    if f[0] or f[1] or not f[2]:
        b.append("Fristen (zwei Lesungen) zaehlen falsch: %r" % f)
    if f[2] and ("NICHT gemeldet" not in f[2] or "keine Verbindung" not in f[2] or "Leserechte" in f[2]):
        b.append("Netz-Meldung nennt Ursache/Folge nicht: %r" % f[2])
    if "Keine Leserechte für Mängel" not in r["frist403"]:
        b.append("403 auf Maengel meldet nicht sofort mit Rechte-Text: %r" % r["frist403"])
    if "Keine Leserechte für Mängel" not in r["fristMix"]:
        b.append("Netz + 403 gemischt: der Rechtefehler wird verdeckt/falsch benannt: %r" % r["fristMix"])
    return b


def test_glocke_netzausfall_erst_nach_drei_runden_rechte_sofort(index_html, node_exe):
    assert _esk_befunde(_esk(index_html, node_exe)) == []


def test_glocke_umkehrproben(index_html, node_exe):
    faelle = [
        # alter Einmal-Zustand (v3.9.914): jede markierte Liste meldet sofort - auch das Netzloch beim Aufwachen
        ('const _mSeit=_eskAusfallMelden("rls_material",_mArt);', 'const _mSeit=_rlsLeer(openMat)?1:0;'),
        ("var ESK_NETZ_RUNDEN=3,", "var ESK_NETZ_RUNDEN=1,"),
        ('if(art==="rechte"||art==="fehler")return {n:0,ts:0,ab:0,melden:true};', 'if(art==="rechte"||art==="fehler")return {n:0,ts:0,ab:0,melden:false};'),
        ('if(!(ts>0)||(+jetzt-ts)>ESK_NETZ_FENSTER_MS){n=0;ab=0;}', ''),
        ('if(art!=="netz")return {n:0,ts:0,ab:0,melden:false};', ''),
        ('if(st===401||st===403)return "rechte";', ''),
        ('{if(!art)art="netz";}else art="fehler";', '{art="fehler";}else art="fehler";'),
        ('if(art==="rechte")return "Keine Leserechte für "+was+', 'if(art==="rechte")return "Rechte oder Netz: "+was+'),
        ('_eskAusfallArt(ovT)===_fArt?"Tickets":"Mängel"', '_rlsLeer(ovT)?"Tickets":"Mängel"'),
    ]
    for alt, neu in faelle:
        assert index_html.count(alt) == 1, alt
        kaputt = index_html.replace(alt, neu, 1)
        assert _esk_befunde(_esk(kaputt, node_exe)) != [], "Rueckbau bleibt gruen: " + alt[:70]


def test_glocke_verdrahtung(index_html):
    code = nur_code(index_html)
    assert code.count(".catch(_eskLeseMarke);") == 3
    # die Lesungen laufen weiter ueber _sbGet (das selbst _netzLesen nutzt) - keine neue Lesestelle
    assert len([z for z in code.split("\n") if "_netzLesen(()=>" in z]) == 6
    sb = _extract_fn(index_html, "_sbGet", r"async\s+function\s+_sbGet\s*\(")
    assert sb and "_authRetry(()=>_netzLesen(()=>fetch(" in sb, "Fristen-Lesung laeuft nicht ueber den Wiederholungsweg"
    # Fusszeile: kein Produktname, Technikzeile nur fuer Admin
    assert '" Supabase: "' not in code and "Polling: Alle 60s" not in code
    assert 'curUser&&curUser.role==="admin"&&React.createElement(\'div\', { style: {display:"flex",alignItems:"center",gap:4}}, React.createElement(\'span\', { \'aria-hidden\': "true", style: {display:"inline-flex"}}, _ik("verbindung",14)), " Neue Meldungen werden jede Minute abgerufen"' in code
    # Titel stoesst nicht mehr an den Papierkorb
    assert 'alignItems:"center",gap:12}}' in code
    assert '_ikVw("glocke","Benachrichtigungen")' in code


# ── 2 Darstellung ─────────────────────────────────────────────────────────

def _thema(src, node_exe):
    code = _fns(src, ("resolveTheme", "_themeMode"))
    js = r"""
var _v=null;var localStorage={getItem:function(){return _v;}};
""" + code + r"""
var R=[];[null,"light","dark","system","",undefined].forEach(function(v){_v=v;R.push([String(v),resolveTheme(v),_themeMode()]);});
console.log(JSON.stringify(R));
"""
    return json.loads(run_node_snippet(node_exe, js))


def _thema_befunde(r):
    b = []
    for v, dunkel, wahl in r:
        if dunkel != (wahl == "dark"):
            b.append("Anzeige %s, Markierung %s bei gespeichert %s" % (dunkel, wahl, v))
    return b


def test_darstellung_markierung_folgt_der_anzeige(index_html, node_exe):
    assert _thema_befunde(_thema(index_html, node_exe)) == []
    code = nur_code(index_html)
    # Mehr-Menue liest die Wahl, die setThemeMode zusammen mit der Anzeige setzt
    assert "var _akt=themeWahl===o[0];" in code
    assert "d=resolveTheme(mode);setIsDark(d);applyTheme(d);setThemeWahl(mode);" in code


def test_darstellung_umkehrprobe(index_html, node_exe):
    alt = 'function _themeMode(){try{return localStorage.getItem("epk_theme")==="dark"?"dark":"light";}'
    assert index_html.count(alt) == 1
    kaputt = index_html.replace(alt, 'function _themeMode(){try{return "light";}', 1)
    assert _thema_befunde(_thema(kaputt, node_exe)) != []


# ── 3 Abwesenheiten ───────────────────────────────────────────────────────

def test_buero_abwesenheiten_einheit_und_standard(index_html):
    code = nur_code(index_html)
    assert ',fontSize:15}},_projStdDE(r.rest,1)+" h"),r.std?_abStdHinweis():null)),' in code
    assert 'UI.markeTxt}},_projStdDE(r.rest,1)+" h",r.std?_abStdHinweis():null)' in code
    assert 'pp[1]>0?_projStdDE(pp[1],1)+" h":"—"' in code
    assert 'v>0?_projStdDE(v,1)+" h":"\\u2014"' in code
    assert "std:!!(_abKontEcht&&!_abKontEcht[m.n])" in code
    # Kontingent vom Server; Lesefehler -> keine Markierung (unbekannt), nicht 'Standard'
    assert 'const d=await _sbGet("urlaubskontingent","jahr=eq."+_abYr);if(!a||_rlsLeer(d)||!Array.isArray(d))return;' in code
    assert '"Standard")' in code and "192,5 h (25 Tage)" in code
    # die Excel-Spalten trugen die Einheit schon
    assert '"Rest Urlaub (h)"' in code


# ── 4 Linien-Chevrons ─────────────────────────────────────────────────────

def _komp(src, name):
    f = _extract_fn(src, name)
    assert f, name
    return f


def test_buero_keine_dreiecke_mehr(index_html):
    for n in ("KVZulagenReport", "PZEView"):
        f = _komp(index_html, n)
        for g in ("▲", "▼", "⏱"):
            assert g not in f, (n, g)
    b = _komp(index_html, "VBueroExport")
    assert '_op?"▼":"▶"' not in b and '_ik(_op?"runter":"rechts",12))' in b
    assert ",_klappIk(open,16),_zpIk('uhr','Stempelzeiten',16))" in index_html
    assert "'Details',_klappIk(_ezDetail,14))" in index_html
    assert "function _klappIk(offen,gr){" in index_html


# ── 5 Zulagen-Navigation + Buero-Reiter ───────────────────────────────────

def test_zulagen_monatsnavigation_ist_eine_einheit(index_html):
    f = _komp(index_html, "KVZulagenReport")
    i = f.index("'data-monat-nav':'1'")
    gruppe = f[i:f.index("_ezHeute", i)]
    assert "flexWrap:'nowrap'" in gruppe
    for teil in ("_ezNav(-1)", "_ezTitel()", "_ezNav(1)"):
        assert teil in gruppe, teil


def test_buero_reiter_ohne_umbruch(index_html):
    b = _komp(index_html, "VBueroExport")
    leiste = b[b.index('{display:"flex",gap:6,flexWrap:"nowrap",overflowX:"auto"'):]
    leiste = leiste[:leiste.index(";})),")]
    assert "BX_TABS.map" in leiste
    assert "fontWeight:600," in leiste and "_act?700:500" not in leiste


# ── 6 Auswertungen ────────────────────────────────────────────────────────

def _asart(src, node_exe):
    asart = _zeile_ab(src, "const AS_ART=")
    farbe = _zeile_ab(src, "const _AS_ART_FARBE=")
    memo = _zeile_ab(src, "const asArt=")
    js = r"""
var _react={useMemo:{call:function(t,f){return f();}}};
var arbeitsscheine=[{scheinart:"kein"},{scheinart:"kein"},{scheinart:""},{},{scheinart:"montage"}];
""" + asart + "\n" + farbe.split("/*")[0] + "\n" + memo.split("/*")[0] + r"""
console.log(JSON.stringify(asArt));
"""
    return json.loads(run_node_snippet(node_exe, js))


def test_auswertung_ohne_art(index_html, node_exe):
    r = _asart(index_html, node_exe)
    namen = [x["l"] for x in r]
    assert "kein" not in namen
    ohne = [x for x in r if x["l"] == "Ohne Art"]
    assert len(ohne) == 1 and ohne[0]["v"] == 4, r
    assert sum(x["v"] for x in r) == 5


def test_auswertung_umkehrprobe(index_html, node_exe):
    alt = 'l:k==="kein"?"Ohne Art":v.l'
    assert index_html.count(alt) == 1
    r = _asart(index_html.replace(alt, "l:v.l", 1), node_exe)
    assert "kein" in [x["l"] for x in r]
