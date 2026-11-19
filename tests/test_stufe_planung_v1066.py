# -*- coding: utf-8 -*-
"""Stufe Planung (v1066) - Owner-Vorgabe "EINE Oberflaeche, drei Breiten-Stufen",
zweite Seite nach den Arbeitsscheinen (v1065): Plaene & Tickets (VPlan).

Vorher entschied VPlan selbst an fuenf Stellen ueber die Breite: isMob=ww<BP_MOB,
isTab=ww<768, _dauerListe=ww>=900, zweimal ww<1000 und window.innerWidth<BP_MOB in
der Plan-Hoehenmessung. Die Ticket-Liste zeigte am Tablet hochkant (800 CSS-px)
die Rechner-Tabelle mit minWidth 700 und zehn Spalten; die Kacheln standen dort
in zwei hohen Reihen.

Was hier gesichert wird:
1. Alle Entscheidungen der Seite kommen aus _layoutStufe - mit echtem Code fuer
   384, 412, 800x1280 hochkant, 1280x800 quer und 1920x1080 ausgefuehrt.
2. breit: Tabelle unveraendert. mittel: Karten in zwei Spalten, schmal: eine.
   Karte und Tabelle haengen an derselben Entscheidung (_plTabelle).
3. Die Karte traegt alle Angaben der Tabellenzeile und dieselben Handlungen -
   gerendert mit echtem Code, Handlungen ausgeloest.
4. Kacheln: mittel kompakt in einer Reihe, schmal hinter einer Aufklappzeile,
   nie quer rollend (v3.9.930).
5. Abdeckung: VPlan vergleicht keine Breite selbst, fragt kein Geraet.
Jeder Riegel hat eine Umkehrprobe.
"""
import io
import json
import os
import re
import sys

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

DEKL = 'const _plStufe=_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0));'


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _vplan(src):
    a = src.index("function VPlan(")
    return src[a:src.index("\nfunction ", a)]


def _stufe_code(src):
    """BP_MOB + BP_BREIT/BP_QUER + _layoutStufe, so wie sie in index.html stehen."""
    i = src.index("const BP_BREIT=")
    j = src.index("function _layoutStufe(w,h){", i)
    k = src.index("function _grobZeiger(", j)
    return "const BP_MOB=600;\n" + src[i:k]


def _entscheidung(v):
    """Die Entscheidungszeile von VPlan: von _plStufe bis vor den Kachel-Zustand."""
    i = v.index(DEKL)
    j = v.index("const [_plKpiAuf,_plSetKpiAuf]=", i)
    return v[i:j]


def _ausdruck(v, anfang, ende):
    i = v.index(anfang) + len(anfang)
    return v[i:v.index(ende, i)]


def _karten_spalten(v):
    return _ausdruck(v, "'data-pl-karten': _plStufe, style: {display:\"grid\",gridTemplateColumns:", ",gap:8,")


def _kachel_klasse(v):
    return _ausdruck(v, "React.createElement('div', { className: \"kpi-grid\"+", ", style: {marginBottom:_plStufe")


# (Breite, Hoehe) -> erwartete Seite. A55 hochkant 384/412, Tablet hochkant 800x1280,
# Tablet quer 1280x800, Rechner 1920x1080.
GROESSEN = [
    ([384, 832], {"stufe": "schmal", "isMob": True, "dauer": False, "tabelle": False,
                  "spalten": "minmax(0,1fr)", "kachel": "kpi-grid epk-leiste epk-kachel-kompakt epk-kachel-zwei"}),
    ([412, 915], {"stufe": "schmal", "isMob": True, "dauer": False, "tabelle": False,
                  "spalten": "minmax(0,1fr)", "kachel": "kpi-grid epk-leiste epk-kachel-kompakt epk-kachel-zwei"}),
    ([800, 1280], {"stufe": "mittel", "isMob": False, "dauer": False, "tabelle": False,
                   "spalten": "repeat(2,minmax(0,1fr))", "kachel": "kpi-grid epk-leiste epk-kachel-kompakt epk-kachel-vier"}),
    ([1280, 800], {"stufe": "breit", "isMob": False, "dauer": True, "tabelle": True,
                   "spalten": "minmax(0,1fr)", "kachel": "kpi-grid"}),
    ([1920, 1080], {"stufe": "breit", "isMob": False, "dauer": True, "tabelle": True,
                    "spalten": "minmax(0,1fr)", "kachel": "kpi-grid"}),
]


def _seite(node_exe, src, faelle):
    v = _vplan(src)
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function lauf(ww,hh){window.innerWidth=ww;window.innerHeight=hh;\n"
          + _entscheidung(v) + "\n"
          "return {stufe:_plStufe,isMob:isMob,dauer:_dauerListe,tabelle:_plTabelle,"
          "spalten:(" + _karten_spalten(v) + "),kachel:\"kpi-grid\"+(" + _kachel_klasse(v) + ")};}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(faelle) + ".map(function(f){return lauf(f[0],f[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_seite_fuer_fuenf_groessen(roh, node_exe):
    r = _seite(node_exe, roh, [f for f, _ in GROESSEN])
    assert r == [e for _, e in GROESSEN], list(zip([f for f, _ in GROESSEN], r))


def test_umkehr_tabelle_an_der_handyschwelle_waere_rot(roh, node_exe):
    """Haengt die Tabelle wieder an 'nicht Handy', zeigt das Tablet hochkant die
    10-Spalten-Tabelle - der Befund. Der Riegel muss das sehen."""
    kaputt = roh.replace('const _plTabelle=_plStufe==="breit";', "const _plTabelle=!isMob;", 1)
    assert kaputt != roh
    assert _seite(node_exe, kaputt, [f for f, _ in GROESSEN]) != [e for _, e in GROESSEN]


def test_umkehr_eigene_schwelle_waere_rot(roh, node_exe):
    kaputt = roh.replace('const _dauerListe=_plStufe==="breit";', "const _dauerListe=window.innerWidth>=1300;", 1)
    assert kaputt != roh
    assert _seite(node_exe, kaputt, [f for f, _ in GROESSEN]) != [e for _, e in GROESSEN]


# ── Karte und Tabelle an derselben Entscheidung ────────────────────────────
TABELLE = ", _plTabelle&&React.createElement('div', { style: {...CC(),padding:0,overflow:\"hidden\"}}, React.createElement('div', { style: {overflowX:\"auto\"}}, React.createElement('table', { style: {width:\"100%\",borderCollapse:\"collapse\",minWidth:700,fontSize:12}}"
KARTE = ", !_plTabelle&&_vpFiltered.length>0&&React.createElement('div', { 'data-pl-karten': _plStufe"


def _zweige(v):
    t = v.index(TABELLE)
    k = v.index(KARTE, t)
    e = v.index(", !allTickets.length&&", k)
    return v[t:k], v[k + 2:e].rstrip()


def test_karte_und_tabelle_haengen_an_derselben_entscheidung(roh):
    v = _vplan(roh)
    assert v.count(TABELLE) == 1 and v.count(KARTE) == 1
    code = nur_code(v)
    assert "isMob&&_vpFiltered.length>0&&" not in code, "Karte haengt wieder nur am Handy"
    assert "!isMob&&React.createElement('div', { style: {...CC(),padding:0,overflow:\"hidden\"}}, React.createElement('div', { style: {overflowX:\"auto\"}}, React.createElement('table'" not in code


HANDLUNGEN = ["setSelPlan(plans.find(x=>x.id===t.planId)||null);setSubView(\"viewer\");_onTicketSelect(t);",
              "e.stopPropagation();deleteTicket(t.id);"]
ANGABEN = ["t.title", "tt.l", "ts.l", "tp.l", "l.name", "w.n", "pl.name", "fdt(t.dueDate)", "t.progress"]


def _karte_ok(v):
    tab, karte = _zweige(v)
    return all(h in tab and h in karte for h in HANDLUNGEN) and all(a in karte for a in ANGABEN)


def test_karte_traegt_alle_angaben_und_handlungen_der_zeile_quelltext(roh):
    assert _karte_ok(_vplan(roh))


def test_umkehr_karte_ohne_loeschen_waere_rot(roh):
    v = _vplan(roh)
    _, karte = _zweige(v)
    kaputt = v.replace(karte, karte.replace("deleteTicket(t.id);", "void 0;"), 1)
    assert kaputt != v and not _karte_ok(kaputt)


def _render_js(karte, stufe):
    stubs = r"""
var React={createElement:function(t,p){var c=[].slice.call(arguments,2);return {t:(typeof t==="string"?t:"K"),p:p||{},c:c};}};
var Badge="Badge";var CC=function(){return {padding:18,marginBottom:14};};var bsS=function(){return {};};
var V={dm:"dm",tx:"tx",bd:"bd",bg:"bg",ac:"ac"};var UI={fMeta:12,fKlein:13,fTitel:15,zahlen:{fontVariantNumeric:"tabular-nums"}};
var _ik=function(n){return {t:"ik",p:{},c:[]};};var _tkRot=function(){return "rot";};var fdt=function(d){return "F:"+d;};
var _dueIsPast=function(){return true;};
var TICKET_TYPES={mangel:{l:"TypMangel"}};var TICKET_STATUS={offen:{l:"StatusOffen",c:"#123456"}};var TICKET_PRIO={hoch:{l:"PrioHoch"}};
var layers=[{id:"el",name:"EbeneElektro"}];var monteure=[{id:"m1",n:"MonteurHuber"}];var MONT=[];var plans=[{id:"p1",name:"PlanEG"}];
var _ticketNr={t1:7};var log=[];
var setSelPlan=function(x){log.push("plan:"+(x&&x.id));};var setSubView=function(x){log.push("sub:"+x);};
var _onTicketSelect=function(t){log.push("sel:"+t.id);};var deleteTicket=function(id){log.push("del:"+id);};
var _vpFiltered=[{id:"t1",title:"TitelKabel",type:"mangel",status:"offen",priority:"hoch",gewerk:"el",assignee:"m1",planId:"p1",dueDate:"2026-11-01",progress:40}];
var _plTabelle=false;var _plStufe=""" + json.dumps(stufe) + r""";
var baum=(""" + karte + r""");
var texte=[],klicks=[],tasten=[],fonts=[];
(function lauf(n){if(n==null||n===false)return;if(Array.isArray(n)){n.forEach(lauf);return;}
 if(typeof n!=="object"){texte.push(String(n));return;}
 var p=n.p||{};if(p.text)texte.push(String(p.text));if(p["aria-label"])texte.push("ARIA:"+p["aria-label"]);
 if(p.onClick)klicks.push({t:n.t,label:p["aria-label"]||"",f:p.onClick,tab:p.tabIndex,key:p.onKeyDown,minH:(p.style||{}).minHeight,w:(p.style||{}).width});
 if(p.style&&p.style.fontSize!=null)fonts.push(p.style.fontSize);
 (n.c||[]).forEach(lauf);})(baum);
var gestoppt=0;var ev={stopPropagation:function(){gestoppt++;},preventDefault:function(){}};
var karte=klicks.filter(function(k){return k.t==="div";})[0];var loesch=klicks.filter(function(k){return k.t==="button";})[0];
var r={spalten:baum.p.style.gridTemplateColumns,texte:texte.join("|"),fonts:fonts,
 karteTab:karte&&karte.tab,karteTaste:!!(karte&&karte.key),loeschMinH:loesch&&loesch.minH,loeschW:loesch&&loesch.w,loeschLabel:loesch&&loesch.label};
log=[];karte.f(ev);r.oeffnen=log.slice();
log=[];karte.key({key:"Enter",target:1,currentTarget:1,preventDefault:function(){}});r.taste=log.slice();
log=[];karte.key({key:"Enter",target:2,currentTarget:1,preventDefault:function(){}});r.tasteKind=log.slice();
log=[];loesch.f(ev);r.loeschen=log.slice();r.gestoppt=gestoppt;
process.stdout.write(JSON.stringify(r));
"""
    return stubs


def _render(node_exe, v, stufe):
    _, karte = _zweige(v)
    ausdruck = karte[len("!_plTabelle&&_vpFiltered.length>0&&"):]
    return json.loads(run_node_snippet(node_exe, _render_js(ausdruck, stufe)))


def test_karte_gerendert_zeigt_alles_und_handelt_wie_die_zeile(roh, node_exe):
    r = _render(node_exe, _vplan(roh), "mittel")
    assert r["spalten"] == "repeat(2,minmax(0,1fr))"
    for t in ("TitelKabel", "TypMangel", "StatusOffen", "PrioHoch", "EbeneElektro", "MonteurHuber",
              "PlanEG", "F:2026-11-01", "40", "7", "überfällig", "Ebene", "Verantw.", "Plan", "Frist"):
        assert t in r["texte"], (t, r["texte"])
    # Antippen = dieselbe Handlung wie die Tabellenzeile (Plan waehlen, Viewer, Unterblatt am Pin)
    assert r["oeffnen"] == ["plan:p1", "sub:viewer", "sel:t1"]
    # Tastatur: Enter auf der Karte oeffnet, Enter auf dem Loeschknopf in ihr nicht
    assert r["karteTab"] == 0 and r["karteTaste"]
    assert r["taste"] == ["plan:p1", "sub:viewer", "sel:t1"] and r["tasteKind"] == []
    # Loeschen: dieselbe Funktion, oeffnet die Karte nicht mit
    assert r["loeschen"] == ["del:t1"] and r["gestoppt"] == 1
    assert r["loeschMinH"] == 44 and r["loeschW"] == 44 and r["loeschLabel"] == "Ticket löschen"
    # Schrift nie unter 12
    assert r["fonts"] and min(r["fonts"]) >= 12, r["fonts"]
    r1 = _render(node_exe, _vplan(roh), "schmal")
    assert r1["spalten"] == "minmax(0,1fr)"


def test_umkehr_karte_ohne_pin_oeffnen_waere_rot(roh, node_exe):
    v = _vplan(roh)
    kaputt = v.replace('setSubView("viewer");_onTicketSelect(t);};const _fld=', 'setSubView("viewer");};const _fld=', 1)
    assert kaputt != v
    r = _render(node_exe, kaputt, "mittel")
    assert r["oeffnen"] != ["plan:p1", "sub:viewer", "sel:t1"]


def test_karte_ci(roh):
    """CI EP Kolar: Tokens, tabular-nums statt Monospace, keine Schrift unter 12, keine Emoji,
    keine neue Fremdfarbe (nur Weiss auf der Status-Plakette wie in der Tabelle)."""
    _, karte = _zweige(_vplan(roh))
    assert _karte_ci_ok(karte), _karte_ci_ok(karte, grund=True)


def _karte_ci_ok(karte, grund=False):
    fehler = []
    if "fontFamily:mono" in karte:
        fehler.append("Monospace")
    if "...UI.zahlen" not in karte:
        fehler.append("keine tabular-nums")
    for m in re.finditer(r"fontSize:(\d+)", karte):
        if int(m.group(1)) < 12:
            fehler.append("Schrift " + m.group(1))
    farben = set(re.findall(r"#[0-9a-fA-F]{3,6}\b", karte))
    if farben - {"#fff"}:
        fehler.append("Farben " + str(sorted(farben)))
    if re.search(u"[☀-➿\U0001F300-\U0001FAFF]", karte):
        fehler.append("Emoji")
    return fehler if grund else not fehler


def test_umkehr_karte_ci_waere_rot(roh):
    _, karte = _zweige(_vplan(roh))
    assert not _karte_ci_ok(karte.replace("fontSize:UI.fMeta", "fontSize:10", 1))
    assert not _karte_ci_ok(karte.replace("...UI.zahlen", "fontFamily:mono", 1).replace("...UI.zahlen", "fontFamily:mono"))
    assert not _karte_ci_ok(karte.replace("color:V.dm", "color:\"#e11d48\"", 1))


# ── Kacheln ────────────────────────────────────────────────────────────────
def test_kacheln_kompakt_und_aufklappbar(roh):
    v = _vplan(roh)
    assert "subView!==\"viewer\"&&isMob&&React.createElement('button', { type: \"button\", onClick: ()=>_plSetKpiAuf(v=>!v), 'aria-expanded': _plKpiAuf?\"true\":\"false\"" in v
    i = v.index("onClick: ()=>_plSetKpiAuf(v=>!v)")
    zeile = v[i:v.index("\n", i)]
    assert "minHeight:44" in zeile and "...UI.zahlen" in zeile and "_klappIk(_plKpiAuf,16)" in zeile
    assert "subView!==\"viewer\"&&(!isMob||_plKpiAuf)&&React.createElement('div', { className: \"kpi-grid\"+" in v
    for kl in ("epk-kachel-vier", "epk-kachel-zwei"):
        css = re.findall(r"\.kpi-grid\.epk-leiste\.epk-kachel-kompakt\." + kl + r"\s*\{[^}]*\}", roh)
        assert len(css) == 1, kl
        assert "overflow-x" not in css[0] and "display: none" not in css[0]
        assert "!important" in css[0]
    assert "repeat(4,minmax(0,1fr))" in re.findall(r"\.epk-kachel-vier\s*\{[^}]*\}", roh)[0]
    assert "repeat(2,minmax(0,1fr))" in re.findall(r"\.epk-kachel-zwei\s*\{[^}]*\}", roh)[0]


def test_umkehr_kacheln_querrollend_waere_rot(roh):
    kaputt = roh.replace(".kpi-grid.epk-leiste.epk-kachel-kompakt.epk-kachel-zwei { grid-template-columns: repeat(2,minmax(0,1fr)) !important; }",
                         ".kpi-grid.epk-leiste.epk-kachel-kompakt.epk-kachel-zwei { display: flex !important; overflow-x: auto; }", 1)
    assert kaputt != roh
    with pytest.raises(AssertionError):
        test_kacheln_kompakt_und_aufklappbar(kaputt)


# ── ABDECKUNG ─────────────────────────────────────────────────────────────
# VPlan fragt _layoutStufe und vergleicht keine Breite selbst. Ausnahmen mit Grund:
AUSNAHMEN = {
    # Seitentitel: dasselbe Muster an vielen Stellen der App, gepinnt von
    # test_d9_seitenueberschriften_v956 / test_seitentitel_v1007 (wie im AS-Riegel).
    "fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite",
    # Lage, keine Breitenschwelle: in der Stufe mittel steht der Plan hochkant ueber
    # der Liste. Dieselbe Frage (Hoehe > Breite), die _layoutStufe selbst fuer quer
    # stellt; gepinnt von test_tablet_funde_v1038 (Plaene hochkant).
    "window.innerHeight>window.innerWidth",
}
BREITEN_MUSTER = re.compile(
    r"\bww\s*[<>]=?|[<>]=?\s*ww\b|innerWidth\s*[<>]=?|[<>]=?\s*(?:window\.)?innerWidth\b"
    r"|matchMedia|userAgent|navigator\.platform|maxTouchPoints|\bisTab\b")


def _fremde_breiten(src):
    code = nur_code(_vplan(src))
    for aus in AUSNAHMEN:
        code = code.replace(aus, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


def test_abdeckung_keine_eigenen_breitenvergleiche(roh):
    funde = _fremde_breiten(roh)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)


def test_abdeckung_ausnahmen_gibt_es_wirklich(roh):
    """Eine Ausnahme, die nicht mehr im Code steht, waere eine stille Erlaubnis."""
    code = nur_code(_vplan(roh))
    for aus in AUSNAHMEN:
        assert aus in code, aus


def test_abdeckung_vplan_fragt_die_stufe(roh):
    v = _vplan(roh)
    assert v.count(DEKL) == 1
    for s in ('const isMob=_plStufe==="schmal";', 'const _dauerListe=_plStufe==="breit";',
              'const _plTabelle=_plStufe==="breit";', 'if(_layoutStufe()==="schmal"){let _bh=58;',
              'const _hochkant=_plStufe==="mittel"&&'):
        assert s in v, s


@pytest.mark.parametrize("alt,neu", [
    ('const _plTabelle=_plStufe==="breit";', "const _plTabelle=ww>=1100;"),
    ('if(_layoutStufe()==="schmal"){let _bh=58;', "if(window.innerWidth<BP_MOB){let _bh=58;"),
    ('placeholder: _plStufe==="mittel"?', "placeholder: 1000>ww?"),
    ('const _plTabelle=_plStufe==="breit";', "const _plTabelle=!window.matchMedia(\"(max-width:1099px)\").matches;"),
    ('const _plTabelle=_plStufe==="breit";', "const _plTabelle=!/Android/.test(navigator.userAgent);"),
    ('gridTemplateColumns:_plStufe!=="breit"?"1fr":"1fr 1fr"', 'gridTemplateColumns:isTab?"1fr":"1fr 1fr"'),
])
def test_umkehr_abdeckung_findet_jeden_eigenen_vergleich(roh, alt, neu):
    assert roh.count(alt) == 1, alt
    kaputt = roh.replace(alt, neu, 1)
    assert _fremde_breiten(kaputt), "Abdeckungsriegel blind fuer: " + neu


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def test_stufe_steht_im_block_von_vplan(roh):
    """node_check parst nur - eine Funktion im falschen Block waere gruen und zur
    Laufzeit ein ReferenceError."""
    bl = _bloecke(roh)

    def blk(pos):
        # erster Treffer wie im AS-Riegel: '<script' in Zeichenketten erzeugt ueberlappende Scheinbloecke
        return [n for n, (a, b) in enumerate(bl) if a <= pos < b][:1]
    assert blk(roh.index("function _layoutStufe(w,h){")) == blk(roh.index("function VPlan("))
    assert blk(roh.index("function _klappIk(")) == blk(roh.index("function VPlan("))


def test_abtaster_zaehlt_die_deklaration_als_code(roh):
    """Die Eichprobe von code_scan zaehlt const _xyStufe=_layoutStufe( mit - die
    Deklaration von VPlan muss als Code erkannt werden, sonst schrumpft die Probe."""
    ok, gefunden, erwartet = code_scan.eichen(roh)
    assert ok and erwartet >= 20, (ok, gefunden, erwartet)
    feld = code_scan.ist_code(roh)
    assert feld[roh.index(DEKL)]
