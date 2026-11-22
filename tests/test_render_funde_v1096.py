"""Render-Funde 1096 (Render-Audit von 1093, Belege C:/bau/logs/epk-render-1093/).

P2  Arbeitsscheine > Liste (breit, hell + dunkel): beim Querrollen malte der halbdurchsichtige Kopf
    DURCHZUFUEHRENDE ARBEITEN ueber den klebenden Kopf NUMMER - alle Koepfe kleben oben mit z-index 1
    (table thead th), die Klebekoepfe hatten ebenfalls 1, der spaetere gewinnt. Jetzt: Klebekoepfe
    (_asKopfKlebt) 3 > uebrige Koepfe (.epk-as-roll table thead th) 2 > klebende Zeilenzellen 1, alle
    klebenden Zellen deckend (Toenung ueber V.cd). mittel bleibt (eigene !important-Regeln).
P3  Kontraste >= 4,5:1 ueber die vorhandenen Helfer, Tippziele 44 px, deutsche Texte, Ganzzahlfelder
    (Fortschritt %, km) ohne parseInt je Tastendruck, Lade-/Leerzustaende mit EINEM Zustand.

Jeder Riegel mit Umkehrprobe. Weiss auf CI-Gruen #009640 bleibt (Entscheidung GF).
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet, _extract_fn

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


# ── WCAG ────────────────────────────────────────────────────────────────────
def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lum(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _k(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _misch(fg, bg, a):
    return tuple(round(f * a + g * (1 - a)) for f, g in zip(fg, bg))


def _thema(roh, name):
    m = re.search(r"\n  %s:\{(.*?)\}" % name, roh)
    assert m, name
    return dict(re.findall(r'(\w+):"(#[0-9A-Fa-f]{6})"', m.group(1)))


def _between(s, a, b):
    i = s.index(a)
    return s[i:s.index(b, i)]


def _lesbar_js(roh, dark, farben):
    js = ("var _dark=%s;var _lesbarMerk={};\n" % ("true" if dark else "false")
          + _extract_fn(roh, "_lesbar")
          + "\nprocess.stdout.write(JSON.stringify(%s.map(function(h){return _lesbar(h);})));" % json.dumps(farben))
    return js


def _lesbar(node_exe, roh, dark, farben):
    return json.loads(run_node_snippet(node_exe, _lesbar_js(roh, dark, farben)))


# ── P2: Klebekoepfe der AS-Liste ───────────────────────────────────────────
def _as_zeile(roh):
    return _between(roh, "const _asAktKlebt=", "\n")


def _as_werte(node_exe, zeile, dark, mittel):
    js = ("var V={cd:'#ffffff',bd:'BD'};var _dark=%s;var _asMittel=%s;\n" % ("true" if dark else "false", "true" if mittel else "false")
          + zeile + "\nvar T='rgba(239,68,68,.03)';process.stdout.write(JSON.stringify({"
          "kn:_asKopfKlebt(_asNrKlebt()),ka:_asKopfKlebt(_asAktSpalte()),zn:_asNrKlebt(T),za:_asAktSpalte(T),n0:_asNrKlebt(null)}));")
    return json.loads(run_node_snippet(node_exe, js))


def _css_z(roh, sel):
    m = re.search(re.escape(sel) + r"\s*\{\s*z-index:\s*(\d+)\s*;?\s*\}", roh)
    return int(m.group(1)) if m else None


def _deckend(bg):
    # nur Toenung ueber der Kartenflaeche (V.cd) oder V.cd selbst - nie eine nackte rgba-Flaeche
    return bg == "#ffffff" or (bg.startswith("linear-gradient(") and bg.endswith("),#ffffff"))


def _p2_ok(node_exe, roh, zeile):
    kopf_z = _css_z(roh, ".epk-as-roll table thead th")
    if kopf_z is None:
        return False
    for dark in (False, True):
        r = _as_werte(node_exe, zeile, dark, False)  # breit
        for k in ("kn", "ka"):
            if r[k].get("position") != "sticky" or not (r[k].get("zIndex", 0) > kopf_z):
                return False
            if not _deckend(r[k].get("background", "")):
                return False
        for z in ("zn", "za", "n0"):
            if not (0 < r[z].get("zIndex", 0) < kopf_z) or not _deckend(r[z].get("background", "")):
                return False
    return True


def test_p2_klebekopf_ueber_den_uebrigen_koepfen(roh, node_exe):
    z = _as_zeile(roh)
    assert _p2_ok(node_exe, roh, z)
    # die globale Regel bleibt 1, die Rollkasten-Regel hebt die uebrigen Koepfe nur auf 2
    assert "table thead th{position:sticky;top:0;z-index:1}" in roh
    assert _css_z(roh, ".epk-as-roll table thead th") == 2
    assert "className: \"epk-as-roll\"" in roh
    # mittel unveraendert: Ecke 3, uebrige 2 (beide !important)
    assert "table.epk-as-mittel thead th { z-index: 2 !important; }" in roh
    assert "table.epk-as-mittel thead th:first-child { z-index: 3 !important; }" in roh


@pytest.mark.parametrize("alt,neu,wo", [
    ("return {...k,zIndex:3,background:", "return {...k,background:", "zeile"),          # Klebekopf wieder 1
    (".epk-as-roll table thead th { z-index: 2; }", "", "roh"),                         # uebrige Koepfe wieder 1
    ('background:"linear-gradient("+_tn+","+_tn+"),"+V.cd,...(_ks', "background:_tn,...(_ks", "zeile"),  # halbdurchsichtig
])
def test_p2_umkehr(roh, node_exe, alt, neu, wo):
    z = _as_zeile(roh)
    if wo == "zeile":
        assert z.count(alt) == 1
        assert not _p2_ok(node_exe, roh, z.replace(alt, neu))
    else:
        assert roh.count(alt) == 1
        assert not _p2_ok(node_exe, roh.replace(alt, neu), z)


# ── P3 Kontraste ueber _lesbar ─────────────────────────────────────────────
HELL_FLAECHEN = [(255, 255, 255), (247, 247, 247), (242, 244, 242), (236, 243, 239), (251, 251, 251)]
DUNKEL_FLAECHEN = [(30, 35, 32), (35, 39, 36), (39, 44, 41)]  # gemessen 1093 (Zebra/heute)
LESBAR_FARBEN = ["#60a5fa", "#f59e0b", "#ef4444", "#06b6d4", "#f97316", "#3b82f6", "#fb923c"]


def test_p3_lesbar_haelt_4_5_auf_den_gemessenen_flaechen(roh, node_exe):
    for dark, flaechen in ((False, HELL_FLAECHEN), (True, DUNKEL_FLAECHEN)):
        aus = _lesbar(node_exe, roh, dark, LESBAR_FARBEN)
        for roh_f, f in zip(LESBAR_FARBEN, aus):
            for bg in flaechen:
                assert _k(_hex(f), bg) >= 4.5, (dark, roh_f, f, bg)


def test_p3_umkehr_rohe_farben_waren_rot():
    # gemessen 1093: 0 Grad blau 2,54 / 5 Grad Bernstein 2,01 / 15 Grad rot dunkel 3,78 / Cyan 2,20
    assert _k(_hex("#60a5fa"), (255, 255, 255)) < 4.5
    assert _k(_hex("#f59e0b"), (247, 247, 247)) < 4.5
    assert _k(_hex("#ef4444"), (39, 44, 41)) < 4.5
    assert _k(_hex("#06b6d4"), (242, 244, 242)) < 4.5
    assert _k(_hex("#f59e0b"), (236, 243, 239)) < 4.5


LESBAR_STELLEN = [
    'color:tMax<=0?_lesbar("#60a5fa"):tMax>=25?_lesbar(COLORS.ERROR):tMax>=15?_lesbar("#f59e0b"):V.tx}}, tMax, "°")',
    'color:w.h<=0?_lesbar("#60a5fa"):w.h>=25?_lesbar(COLORS.ERROR):w.h>=15?_lesbar("#f59e0b"):V.tx}}, w.h, "°")',
    '(w.tmax<=0?_lesbar("#60a5fa"):w.tmax<=5?V.tx:w.tmax<=15?_lesbar("#f59e0b"):_lesbar("#ef4444"))',
    '{...thS(),fontSize:UI.fMeta,color:_lesbar("#f59e0b")}}, "ÜS h")',
    'color:_lesbar("#06b6d4"),fontWeight:700,minWidth:40}}, jCode)',
    'color:isPull?_lesbar("#06b6d4"):isPush?_lesbar("#f97316"):V.tx}}',
    'color:_lesbar(_dark?COLORS.WARNING_DARK:COLORS.WARNING),marginBottom:8}}, "Offline-Modus"',
    'color:_lesbar(COLORS.INFO),marginBottom:8}}, "Polling (60s)"',
    'color:assigned?_okG("#22c55e"):_lesbar(COLORS.ERROR),minWidth:55,textAlign:"right"}}, assigned?"Aktiv":"Nicht")',
]
ALT_STELLEN = [
    'color:tMax<=0?"#60a5fa"', 'color:w.h<=0?"#60a5fa"', '(w.tmax<=0?"#60a5fa"',
    '{...thS(),fontSize:UI.fMeta,color:"#f59e0b"}}, "ÜS h")', 'color:"#06b6d4",fontWeight:700,minWidth:40',
    'color:isPull?"#06b6d4"', 'color:COLORS.INFO,marginBottom:8}}, "Polling (60s)"',
    'color:(_dark?COLORS.WARNING_DARK:COLORS.WARNING),marginBottom:8}}, "Offline-Modus"',
    ':COLORS.ERROR,minWidth:55,textAlign:"right"}}, assigned?"Aktiv":"Nicht")',
]


@pytest.mark.parametrize("anker", LESBAR_STELLEN)
def test_p3_stellen_nutzen_lesbar(roh, anker):
    assert roh.count(anker) == 1, anker


@pytest.mark.parametrize("anker", ALT_STELLEN)
def test_p3_alte_stellen_weg(roh, anker):
    assert anker not in roh


def test_p3_datum_im_gruenen_kopf(roh):
    neu1 = """React.createElement('span', { style: {fontWeight:400,fontSize:UI.fMeta,color:"#fff",background:"rgba(0,0,0,.22)",padding:"1px 6px",borderRadius:4}}, dateFmt(i))"""
    neu2 = """React.createElement('span',{style:{fontSize:UI.fMeta,color:"#fff",background:"rgba(0,0,0,.22)",padding:"1px 6px",borderRadius:4}},dateFmt(i))"""
    assert roh.count(neu1) == 1 and roh.count(neu2) == 1  # Planung > MA-Uebersicht, Zeiterfassung
    assert "opacity:.7}}, dateFmt(i))" not in roh and "opacity:.7}},dateFmt(i))" not in roh
    gruen = _hex("#009640")
    feld = _misch((0, 0, 0), gruen, .22)
    assert _k((255, 255, 255), feld) >= 4.5
    assert _k(_misch((255, 255, 255), gruen, .7), gruen) < 3  # Umkehr: gemessen 2,64


def test_p3_planung_ohne_zeilen_deckkraft(roh):
    seg = _between(roh, "const isEmpty=_isPaddingRow(r);", "DSHORT.map((d,dIdx)=>renderCell(r,d,dIdx))")
    assert "opacity:isEmpty&&!hasAnyContent?0.5:1" not in seg and "opacity:" not in seg.split("return (React.createElement('tr'")[1].split("}}")[0]
    assert 'color:isEmpty&&!hasAnyContent?V.mt:isEmpty?V.tx:"#009640"' in seg
    for name, flaechen in (("light", HELL_FLAECHEN), ("dark", DUNKEL_FLAECHEN)):
        mt = _hex(_thema(roh, name)["mt"])
        for bg in flaechen:
            assert _k(mt, bg) >= 4.5, (name, bg)
            assert _k(_misch(mt, bg, .5), bg) < 4.5  # Umkehr: mit Deckkraft .5 rot


def test_p3_flaechen_mit_weisser_schrift(roh):
    # Hinweise (window._showToast): dieselben Flaechen wie die React-Hinweise
    z = _between(roh, "  const colors={success:", "};")
    farben = dict(re.findall(r"(\w+):'(#[0-9A-Fa-f]{6})'", z))
    assert set(farben) == {"success", "error", "warning", "warn", "info"}
    for k, f in farben.items():
        assert _k((255, 255, 255), _hex(f)) >= 4.5, (k, f)
    assert _k((255, 255, 255), _hex("#ef4444")) < 4.5  # Umkehr: gemessen 3,76
    # Bauprovisorium Speichern: CI-Dunkelgruen, Haken als Linien-Ikone
    seg = _between(roh, "h('button',{onClick:_save,disabled:busy,", "));")
    assert "background:busy?V.dm:EP_GREEN_DARK" in seg and "#00a948" not in seg
    assert '_ik("abnahme",18),"Speichern"' in seg and "✓" not in seg
    m = re.search(r'const EP_GREEN_DARK="(#[0-9a-fA-F]{6})"', roh)
    assert _k((255, 255, 255), _hex(m.group(1))) >= 4.5
    assert _k((255, 255, 255), _hex("#00a948")) < 4.5  # Umkehr: gemessen 3,10


def test_p3_details_auf_orange(roh):
    seg = _between(roh, "_setEzDetail(function(v){return !v;});", "'Details'")
    assert "color:'#1a1a1a'" in seg
    orange = _hex("#f97316")
    assert _k(_hex("#1a1a1a"), orange) >= 4.5
    assert _k(_hex(_thema(roh, "dark")["tx"]), orange) < 4.5  # Umkehr: V.tx dunkel 2,46


def test_p3_keine_daten_und_datei_waehlen(roh):
    assert 'background:"#71717a18",color:V.dm,fontWeight:600}}, "Keine Daten")' in roh
    assert 'color:"#71717a",fontWeight:600}}, "Keine Daten")' not in roh
    seg = _between(roh, "'aria-disabled': selMA?undefined:\"true\"", '"Datei wählen"')
    assert "...(selMA?bpS:{...bsS(),color:V.mt" in seg and "opacity" not in seg
    for name, bgs in (("light", [(255, 255, 255)]), ("dark", [(38, 42, 40), (30, 35, 32)])):
        t = _thema(roh, name)
        for bg in bgs:
            assert _k(_hex(t["dm"]), bg) >= 4.5
            assert _k(_hex(t["mt"]), bg) >= 4.5
    assert _k(_hex("#71717a"), (38, 42, 40)) < 4.5  # Umkehr: gemessen 3,00


# ── P3 Tippziele ───────────────────────────────────────────────────────────
def test_p3_summary_44(roh):
    assert 'h(\'summary\',{style:{fontSize:UI.fMeta,color:V.dm,cursor:"pointer",minHeight:44,display:"flex",alignItems:"center"}},"Kunde nicht im Stamm? Manuell eingeben")' in roh
    assert "summary', { style: {cursor:\"pointer\",fontSize:UI.fMeta,color:V.dm,minHeight:44,display:\"flex\",alignItems:\"center\"}}, \"Details\")" in roh
    # Umkehr: die beiden gemessenen 24-px-summary sind weg
    assert '"pointer",minHeight:24,display:"flex",alignItems:"center"}},"Kunde nicht im Stamm?' not in roh
    assert 'color:V.dm,minHeight:24}}, "Details")' not in roh


# ── P3 Texte ───────────────────────────────────────────────────────────────
def test_p3_deutsche_texte(roh):
    for alt in ('"Erstellt (inkl. User)"', '"Geändert (inkl. User)"', '"Gelöscht (inkl. User)"', '"React-Error"',
                '{ value: "logout"}, "Logout")', "Keine Rollen in workers", "(DB nicht bereit? sql/STEMPEL_v1.sql)",
                '\\u26a0\\ufe0f Fehler beim Laden'):
        assert alt not in roh, alt
    for neu in ('{ value: "logout"}, "Abmeldung")', '{ value: "create"}, "Erstellt (inkl. Benutzer)")',
                '{ value: "react_error"}, "App-Fehler")', '"Keine Rollen gefunden – Mitarbeiterdaten noch nicht geladen."',
                '_bex4("Fehler beim Laden – Daten konnten nicht abgerufen werden","warn")'):
        assert neu in roh, neu
    # Werte (Filter auf die Aktivitaet) unveraendert
    for v in ('value: "logout"', 'value: "create"', 'value: "update"', 'value: "delete"', 'value: "react_error"'):
        assert v in roh


# ── P3 Ganzzahlfelder ──────────────────────────────────────────────────────
def _zahl_js(roh):
    return "\n".join(_extract_fn(roh, n) for n in ("_fzZahl", "_tankEinDE", "_ganzZahl", "_ganzText", "ZahlEingabe"))


def test_p3_ganztext(roh, node_exe):
    js = _zahl_js(roh) + r"""
process.stdout.write(JSON.stringify(["12,5","12.345","12","-3,9","","abc"," 7 ",null].map(_ganzText)));"""
    assert json.loads(run_node_snippet(node_exe, js)) == ["12", "12.345", "12", "-3", "", "abc", "7", None]


KM_BLUR = ["onBlur: e=>setQTankKm(_ganzText(e.target.value))", "onBlur: e=>setQKm(_ganzText(e.target.value))",
           "onBlur: e=>setBKm(_ganzText(e.target.value))", "onBlur: e=>setKmVal(_ganzText(e.target.value))",
           "onBlur: e=>setTankKm(_ganzText(e.target.value))",
           "onBlur: e=>{const _g=_ganzText(e.target.value);setNf(p=>({...p,kmStand:_g}));}",
           "onBlur:ev=>{const _g=_ganzText(ev.target.value);_setTankEdit(st=>({...st,km:_g}));}",
           "onBlur:e=>{const _g=_ganzText(e.target.value);setForm(p=>({...p,km_start:_g}));}",
           "onBlur:e=>{const _g=_ganzText(e.target.value);setForm(p=>({...p,km_ende:_g}));}"]


@pytest.mark.parametrize("anker", KM_BLUR)
def test_p3_km_felder_glaetten_beim_verlassen(roh, anker):
    assert roh.count(anker) == 1, anker


def _tippen(node_exe, roh, ausdruck, neu):
    """Tippt '1','2',',','5' in ein leeres Feld. neu=True: ZahlEingabe (Rohtext im Fokus); False: altes
    kontrolliertes Feld, das den gerechneten Wert sofort zurueckschreibt."""
    if neu:
        anz = "ZahlEingabe({value:form.fortschritt,inputMode:'numeric',onChange:onCh})"
    else:
        anz = "{value:form.fortschritt,onChange:onCh,onFocus:function(){},onBlur:function(){}}"
    js = _zahl_js(roh) + """
var ST=null;var React={useState:function(i){return [ST,function(v){ST=v;}];},createElement:function(t,p){return p;}};
var form={fortschritt:""};var setForm=function(f){form=f(form);};
var onCh=function(e){return %s;};
var anzeige=function(){return %s;};
var p=anzeige();p.onFocus({});
["1","2",",","5"].forEach(function(c){p=anzeige();p.onChange({target:{value:String(p.value)+c}});});
p=anzeige();var fokus=p.value;p.onBlur({});p=anzeige();
process.stdout.write(JSON.stringify({gespeichert:form.fortschritt,fokus:fokus,danach:p.value}));""" % (ausdruck, anz)
    return json.loads(run_node_snippet(node_exe, js))


def test_p3_fortschritt_tippt_komma(roh, node_exe):
    seg = _between(roh, '"Fortschritt %" ), React.createElement(ZahlEingabe, {', "style: II()} ))")
    m = re.search(r"onChange: e=>(setForm\(p=>\(\{\.\.\.p,fortschritt:Math\.min\(100,Math\.max\(0,_ganzZahl\(e\.target\.value\)\|\|0\)\)\}\)\))", seg)
    assert m, seg[:200]
    r = _tippen(node_exe, roh, m.group(1), True)
    assert r == {"gespeichert": 12, "fokus": "12,5", "danach": "12"}, r
    # Umkehr: das alte Feld (parseInt + Begrenzung je Tastendruck, Wert sofort zurueck) machte aus "12,5" 100
    alt = "setForm(p=>({...p,fortschritt:Math.min(100,Math.max(0,parseInt(e.target.value)||0))}))"
    assert _tippen(node_exe, roh, alt, False)["gespeichert"] == 100
    # Begrenzung 0..100 bleibt
    js = _zahl_js(roh) + "process.stdout.write(JSON.stringify(['150','-5','abc','100'].map(function(v){return Math.min(100,Math.max(0,_ganzZahl(v)||0));})));"
    assert json.loads(run_node_snippet(node_exe, js)) == [100, 0, 0, 100]


def test_p3_serviceheft_km_ueber_zahleingabe(roh):
    assert "React.createElement(ZahlEingabe, { type: \"text\", inputMode:\"numeric\", pattern:\"[0-9]*\", autoComplete:\"off\", value: s.km||\"\"," in roh
    assert "React.createElement('input', { type: \"text\", inputMode:\"numeric\", pattern:\"[0-9]*\", autoComplete:\"off\", value: s.km||\"\"," not in roh


# ── P3 Lade-/Leerzustaende ─────────────────────────────────────────────────
def test_p3_fuehrerschein_ein_zustand(roh, node_exe):
    seg = _between(roh, "    ,liste.length?h('div',{}", "'Halterpflicht")
    i = seg.index("\n    :(status==='laedt'")
    ausdruck = seg[i + len("\n    :"):seg.rindex("\n    ,h('div'")]
    js = ("var UI={fKlein:1};var V={dm:'x'};var h=function(t,p,c){return c;};var res={};"
          "['laedt','ok','fehler','offline','rechte'].forEach(function(status){res[status]=(%s);});"
          "process.stdout.write(JSON.stringify(res));") % ausdruck
    r = json.loads(run_node_snippet(node_exe, js))
    assert r == {"laedt": None, "ok": "Noch keine Kontrolle erfasst.", "fehler": None, "offline": None,
                 "rechte": "Kontrollen nicht lesbar."}, r
    # stHinweis traegt den Lade-/Fehlersatz weiterhin
    assert "status==='laedt'?'Kontrollen werden geladen …'" in roh
    # Umkehr: der alte Ausdruck sagte beim Laden "Noch keine Kontrolle erfasst."
    alt = "status==='rechte'?'Kontrollen nicht lesbar.':'Noch keine Kontrolle erfasst.'"
    js2 = "var status='laedt';process.stdout.write(JSON.stringify(%s));" % alt
    assert json.loads(run_node_snippet(node_exe, js2)) == "Noch keine Kontrolle erfasst."
    # Fristen-Karte: keine Entwarnung waehrend des Ladens
    assert "}):(tm.status==='laedt'?null" in roh


def test_p3_kompetenzen_lade_und_fehlerzustand(roh):
    seg = _extract_fn(roh, "WorkerKompetenzenPanel")
    assert "_Skeleton(3)" not in seg
    assert 'React.createElement(_LadeSkelett,{rows:3,was:"Kompetenzen",onReload:()=>{load();}})' in seg
    assert 'if(_ladeZustand(false,_kpFehl,komps.length)==="fehler")return React.createElement(_LadeFehler,' in seg
    assert "catch(e){if(_mnt.current){_setKpFehl(true);" in seg
    assert "if(_mnt.current){setLoading(true);_setKpFehl(false);}" in seg  # Erneut laden zeigt wieder den Ladezustand
    # Lesepfad unveraendert
    assert "await _api.get('worker_kompetenzen','worker_id=eq.'+encodeURIComponent(workerId))" in seg


def test_p3_kompetenzen_zustandsregel(roh, node_exe):
    js = _extract_fn(roh, "_ladeZustand") + "process.stdout.write(JSON.stringify([_ladeZustand(false,true,0),_ladeZustand(false,true,2),_ladeZustand(false,false,0),_ladeZustand(true,true,0)]));"
    assert json.loads(run_node_snippet(node_exe, js)) == ["fehler", "liste", "leer", "laden"]
