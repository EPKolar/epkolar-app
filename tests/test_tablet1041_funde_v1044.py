# -*- coding: utf-8 -*-
"""v1044 - Funde der Tablet-Pruefung v3.9.1041 (Lenovo 1200x1920, 18.11.2026).

Je Fund ein Pruefer (gibt eine Liste von Befunden zurueck, leer = gut) und eine
Umkehrprobe: der Pruefer muss gegen den kuenstlichen Rueckbau ANSCHLAGEN.
Ein Riegel, der nie ausgeloest wurde, ist kein Riegel.

1  Emoji -> Linien-Ikonen (Checklisten, Export, Abwesenheiten, Admin > System,
   Buero Tank, Zeiterfassung, Dispo-Legende ausserhalb _dispoPlan, Anmeldemaske)
2  Glocke: Heute/Gestern nach Kalendertag, Tabellennamen deutsch, Titel ohne Emoji
3  Material offline: "nicht geladen" statt Leerzustand
4  AS-Monatskalender: feste Spalten
5  Dispo: Telefon eigene Zeile, Tageskopf klebt, "Hält"
6  Zahlen/Waehrung deutsch in der Anzeige
7  Kleinkram (SB-Name, hh:mm-Feld, Optionsfelder, Maengel-Filter, Projekt-Leerzustand,
   Tastenkuerzel, Logo-Glyphe, Planung-Zeilenhoehe, Werkzeuge, Urlaubskontingent)
"""
import json
import re
import shutil

import pytest

from conftest import run_node_snippet

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")

# Haken/Kreuz (U+2713/U+2715) sind Schriftzeichen, kein Bild-Emoji - wie in test_ci_stufe3_zeit_planung_v1012
EMOJI = re.compile("[🌀-🫿☀-✒✔✖-➿⭐⏰⏱⏳⏮]")


def _teil(html, a, e):
    i = html.index(a)
    return html[i:html.index(e, i)]


def _ohne_kommentare(t):
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)


def _sichtbare_emoji(teil, erlaubt=("__toast", "genXls(", "_showToast", "pushNotif", "_confirmModal", "console.", "var titel=")):
    """Emoji im Code-Abschnitt, ausser in Zeilen mit Toast/Export/Rueckfrage (bewusste Restmenge)."""
    b = []
    for zeile in _ohne_kommentare(teil).split("\n"):
        for m in EMOJI.finditer(zeile):
            vor = zeile[:m.start()]
            seg = vor[max(vor.rfind(";"), vor.rfind("{"), vor.rfind(",") - 120, 0):]
            if any(x in seg[-200:] for x in erlaubt):
                continue
            b.append(zeile[max(0, m.start() - 40):m.end() + 10].strip())
    return b


# ── 1 Emoji ────────────────────────────────────────────────────────────────
BEREICHE_EMOJI = {
    "Export": ("function VExport(", "\nfunction VZeit("),
    "Checklisten": ("function VCheck(", "\n// Mangel auf Plan"),
    "Urlaubsantraege": ("function UrlaubsantragPanel(", "\nfunction ChefDashboard("),
}


def pruef_emoji(html):
    b = []
    for name, (a, e) in BEREICHE_EMOJI.items():
        if a not in html:
            b.append(name + ": Anfang fehlt")
            continue
        i = html.index(a)
        j = html.find(e, i)
        if j == -1:
            j = i + 40000
        for t in _sichtbare_emoji(html[i:j]):
            b.append(name + ": " + t)
    for alt in ('"\\u26fd Tank-Kontrolle"', '"\\ud83d\\udc41 Beleg"', '"🔒 Du buchst Zeit nur für dich selbst"',
                '"✏️"),_canDelZ', "cv.i, \" \" , cv.l", "title: tv.desc}, tv.i)", "_241 => _241.i]))",
                "_572 => _572.i]))", 'at2&&which==="gen"?at2.i:""', 'v.i," ",v.l', '"↩️"))',
                '"🗓 Dispo · "', '"🖐 Ziehen speichert', '"🏗 "+_bvh', 'g[0].icon+" "+g[0].label',
                '\\u2600\\ufe0f Hell', '\\ud83c\\udf19 Dunkel', '\\uD83D\\uDCF1 Baustellenmanagement-App', '"🔐 Anmelden"'):
        if alt in html:
            b.append("Emoji zurueck: " + alt)
    for neu in ('_ikVw("tank","Tank-Kontrolle")', '_ik(_NOTIF_TYP_IK[tk]||"glocke",16)', '_ik(_ROLE_IK[u.role]||"person",16)',
                "_dpIkTxt(g[0].icon,g[0].label+extra)", '_ikT("kalender","Dispo · "+_built.kwLabel)',
                '[["light","Hell",false,"sonne"],["dark","Dunkel",true,"mond"]]', '_ikVw("monitor","Baustellenmanagement-App")',
                '_ik("schloss",18),"Anmelden"'):
        if neu not in html:
            b.append("Ikone fehlt: " + neu)
    return b


def test_1_emoji(index_html):
    assert pruef_emoji(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ('_ik(x.warn?"schloss":"download",16), x.primary?"Exportieren"', '"📥 "+(x.primary?"Exportieren"'),
    ('_ik(pc===100?"abnahme":"checkliste",22)', 'pc===100?"🏁":"📋"'),
    ("_ik(STAT_IK[a.status]||'uhr',18)", "'⏳'"),
    ('_ikVw("tank","Tank-Kontrolle")', '"\\u26fd Tank-Kontrolle"'),
    ('_ik(_ROLE_IK[u.role]||"person",16)', "_optionalChain([rl, 'optionalAccess', _241 => _241.i])"),
    ('_ikVw("monitor","Baustellenmanagement-App")', '"\\uD83D\\uDCF1 Baustellenmanagement-App"'),
    ('React.createElement(_react.Fragment,null,_ik("schloss",18),"Anmelden")', '"🔐 Anmelden"'),
])
def test_1_umkehrprobe(index_html, alt, neu):
    assert alt in index_html
    assert pruef_emoji(index_html.replace(alt, neu, 1)) != []


def test_1_md5_funktion_traegt_ihre_emoji_weiter(index_html):
    """_dispoPlan bleibt byte-gleich: die Emoji stehen dort weiter als DATEN, das Panel uebersetzt sie."""
    assert 'return {icon:"🤒",label:"Krankenstand"};' in index_html
    tafel = _teil(index_html, "const _DP_IK={", "};")
    for ic in ("🤒", "🏖️", "⏰", "🚫", "⏮", "🎉", "🏗", "⚡"):
        assert '"%s":' % ic in tafel, ic


# ── 2 Glocke ───────────────────────────────────────────────────────────────
def _glocke_js(html):
    a = html.index("const _NOTIF_TAB_DE=")
    e = html.index("window._fmtTimeAgo=_fmtTimeAgo;")
    return html[a:e].replace("window._notifAnzeige=_notifAnzeige;", "")


def pruef_glocke_quelle(html):
    b = []
    body = _teil(html, "function _fmtTimeAgo(ts){", "\nwindow._fmtTimeAgo")
    if "if(hrs<24)" in body:
        b.append("24-h-Fenster statt Kalendertag")
    if "_tag0(now)-_tag0(t)" not in body:
        b.append("kein Kalendertag-Vergleich")
    if "color:n.read?V.dm:V.tx}}, _notifAnzeige(n.title))" not in html:
        b.append("Titel wird roh gezeichnet")
    if "_notifAnzeige(n.body))" not in html:
        b.append("Text wird roh gezeichnet")
    if '"material_orders war nicht lesbar' in html or '"tickets":"defects")+" war nicht lesbar' in html:
        b.append("Tabellenname in der Meldung")
    return b


def test_2_glocke_quelle(index_html):
    assert pruef_glocke_quelle(index_html) == []


def test_2_umkehrprobe(index_html):
    assert pruef_glocke_quelle(index_html.replace("_notifAnzeige(n.title))", "n.title)", 1)) != []
    assert pruef_glocke_quelle(index_html.replace("_tag0(now)-_tag0(t)", "now-t", 1)) != []


@needs_node
def test_2_glocke_verhalten(node_exe, index_html):
    js = _glocke_js(index_html) + r"""
var n=new Date();
var gestern=new Date(n.getFullYear(),n.getMonth(),n.getDate()-1,21,7).getTime();
var vorgestern=new Date(n.getFullYear(),n.getMonth(),n.getDate()-2,9,0).getTime();
console.log(JSON.stringify([_fmtTimeAgo(gestern),_fmtTimeAgo(vorgestern).indexOf("Gestern"),_fmtTimeAgo(Date.now()-5*60*1000),
 _notifAnzeige("⚠️ Fristenprüfung unvollständig"),_notifAnzeige("tickets war nicht lesbar (Rechte oder Netz)."),
 _notifAnzeige("material_orders war nicht lesbar"),_notifAnzeige("Neuer Mangel")]));"""
    r = json.loads(run_node_snippet(node_exe, js))
    stunden = __import__("datetime").datetime.now().hour
    if stunden >= 6 or True:
        assert r[0].startswith("Gestern, 21:07") or r[0].startswith("vor "), r[0]
    assert not r[0].startswith("Heute"), "gestern 21:07 darf nie 'Heute' heissen: " + r[0]
    assert r[1] == -1
    assert r[2] == "vor 5 min"
    assert r[3] == "Fristenprüfung unvollständig"
    assert r[4] == "Tickets waren nicht lesbar (Rechte oder Netz)."
    assert r[5] == "Materialanforderungen waren nicht lesbar"
    assert r[6] == "Neuer Mangel"


# ── 3 Material offline ─────────────────────────────────────────────────────
def pruef_material(html):
    b = []
    for t in ('_ordFehl?_nlTxt():matTokensLg.length>0?', '_soFehl?_nlTxt():suppOrdFilter==="offen"?',
              '_katFehl?(_nlTxt()+" – gespeicherte Kataloge unbekannt.', "myOrders.length===0&&_ordFehl&&",
              "myOrders.length===0&&!_ordFehl&&", "_setSoFehl(!so||!!so.__rlsFehler);",
              "if(a)_setKatFehl(!cats||!!cats.__rlsFehler);", '"Offline – nicht geladen"'):
        if t not in html:
            b.append("fehlt: " + t)
    return b


def test_3_material(index_html):
    assert pruef_material(index_html) == []


def test_3_umkehrprobe(index_html):
    assert pruef_material(index_html.replace("_ordFehl?_nlTxt():matTokensLg.length>0?", "matTokensLg.length>0?", 1)) != []
    assert pruef_material(index_html.replace("myOrders.length===0&&!_ordFehl&&", "myOrders.length===0&&", 1)) != []


# ── 4 Kalender ─────────────────────────────────────────────────────────────
def pruef_kalender(html):
    m = _teil(html, 'calView==="monat"&&React.createElement(', "/* ═══ WOCHENANSICHT ═══ */")
    b = []
    if 'repeat(7,1fr)' in m:
        b.append("1fr-Spalten (wachsen mit dem Inhalt je Woche)")
    if m.count('repeat(7,minmax(0,1fr))') != 2:
        b.append("Kopf und Wochen teilen nicht dieselben festen Spalten")
    if 'cursor:"pointer",minWidth:0,overflow:"hidden"}}' not in m:
        b.append("Tageszelle ohne minWidth:0")
    return b


def test_4_kalender(index_html):
    assert pruef_kalender(index_html) == []


def test_4_umkehrprobe(index_html):
    k = index_html.replace('gridTemplateColumns:"repeat(7,minmax(0,1fr))"}}\r\n            , wk.map', 'gridTemplateColumns:"repeat(7,1fr)"}}\r\n            , wk.map', 1)
    if k == index_html:
        k = index_html.replace("calDays.map((wk,wi)=>React.createElement('div', { key: wi, style: {display:\"grid\",gridTemplateColumns:\"repeat(7,minmax(0,1fr))\"}}",
                               "calDays.map((wk,wi)=>React.createElement('div', { key: wi, style: {display:\"grid\",gridTemplateColumns:\"repeat(7,1fr)\"}}", 1)
    assert k != index_html
    assert pruef_kalender(k) != []


# ── 5 Dispo ────────────────────────────────────────────────────────────────
def pruef_dispo(html):
    p = _teil(html, "function DispoPanel({", "\nfunction ArbeitsscheinView(")
    b = []
    if 'style:{display:"block",maxWidth:"100%",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",marginTop:1' not in p:
        b.append("Telefon nicht in eigener Zeile")
    if "position:\"sticky\"" not in p or "_dpTh({textAlign:\"left\"" not in p:
        b.append("Tageskopf klebt nicht")
    if 'overflowX:_dpKlebt?"clip":"auto"' not in p:
        b.append("Rollbehaelter faengt den klebenden Kopf ein")
    if "Haelt Tagesnorm" in p or "Hält Tagesnorm" not in p:
        b.append("Haelt statt Hält")
    return b


def test_5_dispo(index_html):
    assert pruef_dispo(index_html) == []


def test_5_umkehrprobe(index_html):
    assert pruef_dispo(index_html.replace("Hält Tagesnorm", "Haelt Tagesnorm", 1)) != []
    assert pruef_dispo(index_html.replace('overflowX:_dpKlebt?"clip":"auto"', 'overflowX:"auto"', 1)) != []


# ── 6 Zahlen ───────────────────────────────────────────────────────────────
def pruef_zahlen(html):
    b = []
    ber = _teil(html, "function BerCell({h})", "\nfunction printForm(")
    if re.search(r"[^A-Za-z_.]_n\((h|sum|totalH),", ber):
        b.append("Wochenbericht zeigt Punkt-Zahlen")
    if '_projStdDE(_mySummary.ist,1)+" h"' not in html:
        b.append("Monatsabrechnung Ist-Stunden mit Punkt")
    if '"€"+Math.round(v)' in html or '_n(it.value,0)+" €"' in html or 'Math.round(moData.reduce((a,b)=>a+b,0)), " €"' in html:
        b.append("Home-Tankkosten: Euro uneinheitlich")
    if "fmt: ch.fmt||" not in html or "fmt:_eur0}" not in html:
        b.append("Auswertungen ohne Tausenderpunkt/Euro")
    return b


def test_6_zahlen(index_html):
    assert pruef_zahlen(index_html) == []


def test_6_umkehrprobe(index_html):
    assert pruef_zahlen(index_html.replace("_projStdDE(totalH,1))))", "_n(totalH,1))))", 1)) != []
    assert pruef_zahlen(index_html.replace('unit==="€"?_eurKachel(v)', 'unit==="€"?"€"+Math.round(v)', 1)) != []


def test_6_exporte_bleiben(index_html):
    """Druck und Excel behalten _n - nur die Anzeige ist deutsch."""
    assert "${_n(totalStd,1)}" in index_html
    assert '"eventuelle Mehrstunden: "+_n(diff,1)+"h"' in index_html or '"eventuelle Mehrstunden: "+_n(diff,2)+"h"' in index_html


# ── 7 Kleinkram ────────────────────────────────────────────────────────────
def pruef_klein(html):
    b = []
    if "maxWidth:104,textOverflow:\"ellipsis\"" not in html or 'title: a.sachbearbeiter||"kein Sachbearbeiter"' not in html:
        b.append("SB-Name abgeschnitten ohne title")
    if 'gridTemplateColumns:isMob?"1fr":"1fr 1fr 1fr",gap:6}}' in html or html.count('minWidth:64,textAlign:"center"') != 2:
        b.append("hh:mm-Feld zu schmal (00:)")
    if "html input[type=radio]{-webkit-appearance:none !important" not in html:
        b.append("Optionsfeld ohne 22-px-Kur")
    if "'data-epk': \"mg-filter\"" not in html or 'flexWrap:isMob?"wrap":"nowrap",overflowX:isMob?"visible":"auto"' not in html:
        b.append("Maengel-Filter bricht um")
    if 'fil.length===0?null/*' not in html:
        b.append("leerer Tabellenkopf unter dem Projekt-Leerzustand")
    if '"⌘K")' in html or "matchMedia(\"(pointer: coarse)\").matches)return \"\";" not in html:
        b.append("Tastenkuerzel am Touchgeraet")
    if 'flexDirection:_isTabletNav?"column":"row"' not in html:
        b.append("Version neben dem Logo wird gekappt")
    if "const _wpZeile1=_wpGrob&&ww>=1200;" not in html or 'gridTemplateColumns:"repeat(4,44px)",width:188' not in html:
        b.append("Planung-Zeilenknoepfe zweistoeckig")
    if "minWidth:ww<1000?Math.max(640,ww-80):800" not in html:
        b.append("Werkzeug-Tabelle hoch abgeschnitten")
    for t in ('kontUnlesbar?"– (nicht gemessen)"', 'kontUnlesbar?"–":(_n(rest,1)', 'kontUnlesbar?"–":(_absH(mRest,0)+"h")',
              'sub: kontUnlesbar?"nicht gemessen":"von "+'):
        if t not in html:
            b.append("Kontingent zeigt Zahl trotz 'nicht gemessen': " + t)
    return b


def test_7_klein(index_html):
    assert pruef_klein(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ('fil.length===0?null/*', '/*'),
    ("const _wpZeile1=_wpGrob&&ww>=1200;", "const _wpZeile1=false;"),
    ('kontUnlesbar?"–":(_absH(mRest,0)+"h")', '_absH(mRest,0)+"h"'),
    ("html input[type=radio]{-webkit-appearance:none !important", "html input[type=radio]{"),
])
def test_7_umkehrprobe(index_html, alt, neu):
    assert alt in index_html
    assert pruef_klein(index_html.replace(alt, neu, 1)) != []


def test_7_planung_riegel_v1040_bleibt(index_html):
    """Das 2x2-Raster (v1040) steht unveraendert - die Reihe ist eine Ergaenzung ab 1200 px."""
    assert '...(_wpGrob?{gridTemplateColumns:"44px 44px",gap:4,width:92}:null)' in index_html
    assert "_wpGrob?React.createElement('col', { style: {width:100}}):React.createElement('col', { style: {width:54}})" in index_html
