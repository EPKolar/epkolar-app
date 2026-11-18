# -*- coding: utf-8 -*-
"""v3.9.1038 Tablet-Funde (17.11.2026) - Riegel mit Umkehrprobe je Fund.

1 Materialkatalog: Wiederholung je Seite, Ende an leerer/kuerzerer Seite, 60 Seiten.
2 Schein-Formular: OFFA-Platzhalter 0001-01-01 / 00:00 leer ANZEIGEN (Formularwert bleibt).
3 Update-Banner offline: nichts loeschen, Hinweis zeigen.
4 Plaene hochkant: Blatt unter dem Plan, Plan behaelt Hoehe.
5 Dispo/MA-Uebersicht: kein Bruch mitten im Wort.
6 Kamera: neutrale Meldung, Linien-Ikone statt Emoji.
7 Stunden mit Dezimalkomma.
8 Sync-Text ohne "0 ausstehende".
"""
import json
import re
import shutil

import pytest

from conftest import run_node_snippet

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")


def _zeile(html, anfang):
    i = html.index(anfang)
    return html[i:html.index("\n", i)]


# ── 1 Materialkatalog ──────────────────────────────────────────────────────
def _katalog_js(html, server_max=1000, gesamt=25121, fehl_offsets=None):
    seiten = re.search(r"const _MAT_KAT_SEITEN=\d+;", html).group(0)
    a = html.index("const sa=[];let _saOff")
    b = html.index("setSuppLoad({n:sa.length", a)
    kern = html[a:b]
    fehl = json.dumps(fehl_offsets or {})
    return (
        seiten +
        "let a=true;const _saSel='s';const waits=[];let calls=0;const fehl=" + fehl + ";"
        "globalThis.setTimeout=(f,ms)=>{waits.push(ms);f();return 0;};"
        "async function _sbGet(t,f){calls++;const off=+f.split('offset=')[1];const lim=+/limit=(\\d+)/.exec(f)[1];"
        "if(fehl[off]>0){fehl[off]--;throw new Error('netz');}"
        "const n=Math.max(0,Math.min(lim," + str(server_max) + "," + str(gesamt) + "-off));"
        "return Array.from({length:n},(_,i)=>({id:off+i}));}"
        "(async()=>{" + kern +
        "console.log(JSON.stringify({n:sa.length,g:_saGekappt,f:_saFehler,calls,waits,uniq:new Set(sa.map(r=>r.id)).size}));})();"
    )


@needs_node
def test_1_katalog_ganz_trotz_1000er_kappe_und_wackelnetz(node_exe, index_html):
    # Seite bei Offset 3000 faellt zweimal aus, danach geht sie - der Katalog muss trotzdem ganz kommen.
    r = json.loads(run_node_snippet(node_exe, _katalog_js(index_html, fehl_offsets={"3000": 2})))
    assert r["n"] == 25121 and r["uniq"] == 25121, r
    assert r["f"] is False and r["g"] is False, r
    assert r["waits"] == [800, 2000], r


@needs_node
def test_1_dreimal_fehlgeschlagen_markiert_fehler(node_exe, index_html):
    r = json.loads(run_node_snippet(node_exe, _katalog_js(index_html, fehl_offsets={"2000": 3})))
    assert r["f"] is True and r["n"] == 2000, r


@needs_node
def test_1_umkehrprobe_ohne_wiederholung_und_alte_6_seiten(node_exe, index_html):
    ohne = index_html.replace("const _saWart=[800,2000];", "const _saWart=[];", 1)
    assert ohne != index_html
    r = json.loads(run_node_snippet(node_exe, _katalog_js(ohne, fehl_offsets={"3000": 2})))
    assert r["f"] is True, "Riegel blind: ohne Wiederholung haette der Fehler kommen muessen"
    sechs = re.sub(r"const _MAT_KAT_SEITEN=\d+;", "const _MAT_KAT_SEITEN=6;", index_html, count=1)
    r = json.loads(run_node_snippet(node_exe, _katalog_js(sechs)))
    assert r["g"] is True and r["n"] == 6000, "Riegel blind fuer 6 Seiten bei 1000er-Kappe: %r" % r


# ── 2 Schein-Formular Platzhalter ───────────────────────────────────────────
def pruef_termin_anzeige(src):
    b = []
    if 'type: "date", value: _hasTermin(form.terminBestaetigt)?form.terminBestaetigt:""' not in src:
        b.append("terminBestaetigt zeigt Platzhalter")
    if 'type: "date", value: _hasTermin(form.terminVorschlag)?form.terminVorschlag:""' not in src:
        b.append("terminVorschlag zeigt Platzhalter")
    if 'type: "time", value: _asZeitAnz(form.terminZeit)' not in src or 'type: "time", value: _asZeitAnz(form.terminVorschlagZeit)' not in src:
        b.append("Uhrzeit zeigt 00:00-Platzhalter")
    # Gespeichert wird weiter der Formularwert - onChange unveraendert
    if "onChange: e=>setForm(p=>({...p,terminBestaetigt:e.target.value}))" not in src:
        b.append("onChange terminBestaetigt veraendert")
    return b


@needs_node
def test_2_termin_platzhalter_leer(node_exe, index_html):
    assert pruef_termin_anzeige(index_html) == []
    js = (_zeile(index_html, "const _hasTermin = ") + "\n" + _zeile(index_html, "const _asZeitAnz = ") +
          "\nconsole.log(JSON.stringify([_hasTermin('0001-01-01'),_hasTermin('2026-11-17'),"
          "_asZeitAnz('00:00'),_asZeitAnz('00:00:00'),_asZeitAnz('08:30'),_asZeitAnz(null)]));")
    assert json.loads(run_node_snippet(node_exe, js)) == [False, True, "", "", "08:30", ""]


def test_2_umkehrprobe(index_html):
    kaputt = index_html.replace('value: _hasTermin(form.terminVorschlag)?form.terminVorschlag:""', "value: form.terminVorschlag", 1)
    assert pruef_termin_anzeige(kaputt)


# ── 3 Update offline ───────────────────────────────────────────────────────
def _update_js(html, online):
    zeile = _zeile(html, "  const doSwUpdate=async()=>{").strip()
    return (
        "const log=[];Object.defineProperty(globalThis,'navigator',{value:{onLine:" + ("true" if online else "false") + "},configurable:true,writable:true});"
        "globalThis.window={__toast:(m)=>log.push('toast:'+m),_forceCacheClear:async()=>log.push('clear')};"
        "const setSwUpdate=v=>log.push('banner:'+v);const swReg={current:null};"
        "const _optionalChain=()=>undefined;" + zeile +
        "doSwUpdate().then(()=>console.log(JSON.stringify(log)));"
    )


@needs_node
def test_3_update_offline_loescht_nichts(node_exe, index_html):
    log = json.loads(run_node_snippet(node_exe, _update_js(index_html, False)))
    assert "clear" not in log and not any(x.startswith("banner:") for x in log), log
    assert any(x.startswith("toast:Keine Verbindung") for x in log), log
    log = json.loads(run_node_snippet(node_exe, _update_js(index_html, True)))
    assert log == ["banner:false", "clear"], log


@needs_node
def test_3_umkehrprobe(node_exe, index_html):
    kaputt = index_html.replace('navigator.onLine===false)return void(window.__toast&&window.__toast("Keine Verbindung', 'navigator.onLine===null)return void(window.__toast&&window.__toast("Keine Verbindung', 1)
    assert kaputt != index_html
    log = json.loads(run_node_snippet(node_exe, _update_js(kaputt, False)))
    assert "clear" in log, "Riegel blind: ohne Sperre wird offline geloescht"


# ── 4 Plaene hochkant ──────────────────────────────────────────────────────
def pruef_hochkant(src):
    b = []
    if "const _hochkant=!isMob&&!_dauerListe&&typeof window!==\"undefined\"&&window.innerHeight>window.innerWidth;" not in src:
        b.append("keine Hochkant-Erkennung")
    if "const _gestapelt=_hochkant&&_rechts;" not in src or "Math.round(_stVh*0.45)" not in src:
        b.append("Plan behaelt keine Mindesthoehe")
    if 'gridTemplateColumns:(_rechts&&!_gestapelt)?"minmax(0,1fr) 380px":"minmax(0,1fr)"' not in src:
        b.append("Spalte bleibt hochkant neben dem Plan")
    if '...(_gestapelt?{hoehe:_stPlanH+"px"}:null)' not in src:
        b.append("Plan-Hoehe hochkant nicht gesetzt")
    if 'maxHeight:_gestapelt?_stBlattH+"px":' not in src:
        b.append("Blatt rollt nicht in sich")
    return b


def test_4_plaene_hochkant(index_html):
    assert pruef_hochkant(index_html) == []


def test_4_umkehrprobe(index_html):
    kaputt = index_html.replace('gridTemplateColumns:(_rechts&&!_gestapelt)?', 'gridTemplateColumns:_rechts?', 1)
    assert pruef_hochkant(kaputt)


# ── 5 Wortbruch ────────────────────────────────────────────────────────────
def pruef_wortbruch(src):
    b = []
    for anker in (",o.bvh?h('div',{lang:\"de\",style:{", ",o.arbeit?h('div',{lang:\"de\",style:{"):
        if anker not in src:
            b.append("Dispo-Kachel ohne lang=de: " + anker)
            continue
        z = src[src.index(anker):src.index("\n", src.index(anker))][:260]
        if 'hyphens:"auto"' not in z or "break-word" in z or "anywhere" in z:
            b.append("Dispo-Kachel bricht im Wort: " + z[:80])
    for anker in ("_wpNameLesbar(p.bvh))", "_wpNameLesbar(p.bvh));"):
        for m in re.finditer(re.escape(anker), src):
            vor = src[max(0, m.start() - 400):m.start()]
            if "WebkitLineClamp:2" not in vor:
                continue
            if "anywhere" in vor[vor.rindex("WebkitLineClamp:2"):] or "hyphens" not in vor[vor.rindex("WebkitLineClamp:2"):]:
                b.append("MA-Uebersicht bricht im Wort")
    return b


def test_5_kein_bruch_im_wort(index_html):
    assert pruef_wortbruch(index_html) == []


def test_5_umkehrprobe(index_html):
    kaputt = index_html.replace(
        "overflow:'hidden',overflowWrap:'normal',wordBreak:'normal',hyphens:'auto'},lang:'de'}",
        "overflow:'hidden',overflowWrap:'anywhere'}", 1)
    assert kaputt != index_html
    assert pruef_wortbruch(kaputt)


# ── 6 Kamera ───────────────────────────────────────────────────────────────
def pruef_kamera(src):
    b = []
    if '"📷 "+_kameraFehlerText' in src:
        b.append("Emoji vor der Kamera-Meldung")
    if "Kamera-Zugriff verweigert" in src:
        b.append("Meldung 'verweigert' noch da")
    if 'function _scanMsgInhalt(m){return /^(Kamera |Keine passende Kamera)/.test(String(m||""))?_ikVw("kamera",m):m;}' not in src:
        b.append("keine Linien-Ikone")
    if src.count("_scanMsgInhalt(") < 5:
        b.append("Scan-Meldungen nicht alle ueber _scanMsgInhalt")
    return b


@needs_node
def test_6_kamera_neutral(node_exe, index_html):
    assert pruef_kamera(index_html) == []
    js = _zeile(index_html, "function _kameraFehlerText(err){") + (
        "\nconsole.log(JSON.stringify(_kameraFehlerText({name:'NotAllowedError'})));")
    t = json.loads(run_node_snippet(node_exe, js))
    assert t.startswith("Kamera nicht freigegeben") and not re.search(r"[\U0001F300-\U0001FAFF]", t)


def test_6_umkehrprobe(index_html):
    kaputt = index_html.replace("setAsScanMsg(_kameraFehlerText(err))", 'setAsScanMsg("📷 "+_kameraFehlerText(err))', 1)
    assert pruef_kamera(kaputt)


# ── 7 Dezimalkomma ─────────────────────────────────────────────────────────
def pruef_komma(src):
    b = []
    # v1044 (Tablet-Pruefung 1041, Fund 9): Euro jetzt ueber _eurKachel ("€ 711", wie die Home-Kacheln) - der Riegel prueft weiter das Komma der Literzahl
    if 'v>0?(unit==="€"?_eurKachel(v):_projStdDE(v,1)):""' not in src:
        b.append("Balkenwerte mit Punkt")
    for k in ("Stunden gesamt", "Diese Woche", "Letzte Woche"):
        z = src[src.index('_statBox("%s",' % k):][:120]
        if 'toLocaleString("de-AT")' not in z:
            b.append(k + " mit Punkt")
    if '_statBox("Ø Woche",_wochenSchnitt.toLocaleString("de-AT")' not in src:
        b.append("Ø Woche mit Punkt")
    if '((Math.round((o.dauerMin||0)/60*10)/10).toLocaleString("de-AT")+"h")' not in src:
        b.append("Dispo-Dauer mit Punkt")
    return b


@needs_node
def test_7_dezimalkomma(node_exe, index_html):
    assert pruef_komma(index_html) == []
    js = _zeile(index_html, "function _projStdDE(v,d){") + (
        "\nconsole.log(JSON.stringify([_projStdDE(8.5,1),_projStdDE(165,1),(Math.round(8.46*10)/10).toLocaleString('de-AT')]));")
    assert json.loads(run_node_snippet(node_exe, js)) == ["8,5", "165,0", "8,5"]


def test_7_umkehrprobe(index_html):
    kaputt = index_html.replace('_projStdDE(v,1)):""', '_n(v,1)):""', 1)
    assert pruef_komma(kaputt)


# ── 8 Sync-Text ────────────────────────────────────────────────────────────
@needs_node
def test_8_sync_ohne_null(node_exe, index_html):
    i = index_html.index('syncing?(pendingCount>0?("Synchronisiere "')
    ausdruck = index_html[i + len("syncing?"):index_html.index("/* Tablet-Funde 17.11.: keine", i)]
    js = ("const f=pendingCount=>" + ausdruck + ";console.log(JSON.stringify([f(0),f(1),f(3)]));")
    assert json.loads(run_node_snippet(node_exe, js)) == [
        "Synchronisiere…", "Synchronisiere 1 ausstehende Änderung…", "Synchronisiere 3 ausstehende Änderungen…"]


def test_8_umkehrprobe(index_html):
    assert 'syncing?("Synchronisiere "+pendingCount+" ausstehende Änderungen…"):' not in index_html
