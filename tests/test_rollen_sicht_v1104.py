# -*- coding: utf-8 -*-
"""v3.9.1104 - Rollen-Sicht (GF-Entscheide 24.11.2026).

1. Startseite der Feldrollen: keine Firmen-Tankkosten (Kachel "Tankkosten Monat",
   Diagramme "Tankkosten 6 Monate" und "Tankkosten <Monat> pro Fahrzeug"), kein
   Team-Block; "Projekte aktiv" / "x gesamt" / "Aktive Projekte" zaehlen nur die
   zugewiesenen Projekte - mit DERSELBEN Regel wie der Reiter Projekte
   (_projSichtbarFuer, vorher inline in ProjList).
2. Arbeitsscheine fuer Feldrollen: kein "OFFA Excel"-Knopf samt Untertitel
   (canDo offa_export, das es schon gab), keine Monteur-Umbuchung je Schein,
   kein aenderbares Bestaetigt-Datum, kein Stornieren.
3. SV-Nr. und Reisepass im Mitarbeiter-Detail nur Admin und Buero
   (_maPersDatenRolle), nicht mehr der Projektleiter.
4. Monatsabrechnung (perm stunden) nicht mehr fuer den Projektleiter -
   aus seiner Modulliste genommen; Admin/Buero und die Feldrollen, die sie
   heute haben, unveraendert.
5. Service-Worker-Update-Takt: reg darf undefined sein.

Jeder Riegel hat eine Umkehrprobe: der Altstand (Quelltext vor 1104) muss
denselben Pruefer rot machen.
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
FELD = ["monteur", "helfer", "techniker", "obermonteur"]
STAFF = ["admin", "buero", "projektleiter"]


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _komp(src, name):
    a = src.index("\nfunction " + name + "(")
    # Ende = naechste Komponente (Grossbuchstabe). Ein schlichtes "\nfunction "
    # endet in ArbeitsscheinView schon bei der inneren Spalte-0-Funktion sharePdf.
    b = re.compile(r"\nfunction [A-Z]").search(src, a + 10).start()
    return src[a:b]


def _fn(src, name):
    """Top-level Funktion bis zur naechsten Zeile, die mit } beginnt."""
    a = src.index("\nfunction " + name + "(") + 1
    b = src.index("\n}\n", a)
    return src[a:b + 2]


def _const(src, name):
    a = src.index("\nconst " + name + "=") + 1
    b = src.index("\n};", a)
    return src[a:b + 3]


# ── 1. eine Projekt-Regel, in Node ausgefuehrt ───────────────────────────────
def _proj_probe(node_exe, fn_src):
    js = fn_src + """
const P=[{id:"p1"},{id:"p2"},{id:"p3"}];const MP={w1:["p2"]};
const out={};
for(const r of %s){out[r]=_projSichtbarFuer({role:r,monteurId:"w1"},P,MP).map(p=>p.id);}
out.ohneMid=_projSichtbarFuer({role:"monteur",monteurId:""},P,MP).map(p=>p.id);
console.log(JSON.stringify(out));
""" % json.dumps(FELD + STAFF)
    return json.loads(run_node_snippet(node_exe, js))


def _proj_fehler(out):
    f = []
    for r in FELD:
        if out[r] != ["p2"]:
            f.append(r)
    for r in STAFF:
        if out[r] != ["p1", "p2", "p3"]:
            f.append(r)
    if out["ohneMid"] != []:
        f.append("ohneMid")
    return f


def test_projektregel_in_node(node_exe, roh):
    assert _proj_fehler(_proj_probe(node_exe, _fn(roh, "_projSichtbarFuer"))) == []


def test_projektregel_umkehr_alle_projekte_waere_rot(node_exe):
    alt = "function _projSichtbarFuer(u,projects,mp){\n  return projects;\n}\n"
    assert _proj_fehler(_proj_probe(node_exe, alt)) != []


def _home_fehler(home):
    f = []
    if 'const aktivP=projects.filter(' in home or '()=>projects.filter(p=>p.status==="aktiv").slice(0,5)' in home:
        f.append("aktiv-Zaehlung ueber alle Projekte")
    if "_projSichtbarFuer(curUser,projects,monteurProjekte)" not in home:
        f.append("Home nutzt nicht die gemeinsame Regel")
    if "}}, projects.length, \" gesamt\" )" in home:
        f.append("gesamt ueber alle Projekte")
    karte = r"isOps&&React\.createElement\('div', \{ style: CC\(\)\}\n"
    zeile = r"[^\n]*\n"
    muster = {
        "Team": karte + r"[^\n]*\"Team\" \)",
        "Tankkosten 6 Monate": karte + zeile + r"[^\n]*\"Tankkosten 6 Monate\"",
        "pro Fahrzeug": karte + zeile + r"[^\n]*\" pro Fahrzeug\"",
        "Tankkosten Monat": r"isOps&&hasPerm\(curUser,\"fahrzeuge\"\)&&React\.createElement" + zeile + r"[^\n]*\"Tankkosten Monat\"",
    }
    for name, rx in muster.items():
        if not re.search(rx, home):
            f.append("nicht isOps-gesperrt: " + name)
    return f


def test_home_nur_eigene_projekte_und_keine_firmenkosten(roh):
    assert _home_fehler(_komp(roh, "HomeView")) == []


def test_home_umkehr_altstand_waere_rot(roh):
    home = _komp(roh, "HomeView")
    alt = home.replace("_hvProj.filter(", "projects.filter(").replace("_hvProj.length", "projects.length")
    alt = alt.replace("_projSichtbarFuer(curUser,projects,monteurProjekte)", "projects")
    alt = alt.replace("isOps&&", "")
    f = _home_fehler(alt)
    assert any("aktiv" in x for x in f)
    assert any("gemeinsame Regel" in x for x in f)
    assert any("Tankkosten 6" in x for x in f)
    assert any("Team" in x for x in f)


def test_projlist_nutzt_dieselbe_regel(roh):
    pl = _komp(roh, "ProjList")
    assert "projects=_projSichtbarFuer(curUser,projects,monteurProjekte);" in pl
    assert "_myProjIds" not in pl


def test_home_finkzeit_abruf_nur_mit_recht_stunden(roh):
    home = _komp(roh, "HomeView")
    i = home.index('const data=await _sbGet("finkzeit"')
    assert 'if(!hasPerm(curUser,"stunden"))return;' in home[i - 500:i]


# ── 2. Arbeitsscheine ────────────────────────────────────────────────────────
def _as_fehler(av):
    f = []
    if av.count('canDo("offa_export",curUser)&&React.createElement(\'div\', { style: {position:"relative",display:"inline-block"}}, React.createElement(\'button\', { onClick: ()=>setShowExportPicker(') != 1:
        f.append("OFFA-Excel-Knopf")
    if av.count("canDo(\"offa_export\",curUser)&&React.createElement('p'") != 1:
        f.append("Untertitel")
    # alle Storno-Knoepfe hinter isAdmin
    for m in re.finditer(r"storno\((a\.id|editId)\)", av):
        zeile = av[av.rfind("\n", 0, m.start()):m.start()]
        if not re.search(r",\s*isAdmin&&", zeile):
            f.append("Storno offen")
    if av.count("{...tdSt(),padding:2}}, !isAdmin?(_hasTermin(a.terminBestaetigt)?fdt(a.terminBestaetigt):") != 1:
        f.append("Bestaetigt Liste")
    if av.count("{...tdSt(),padding:2}}, !isAdmin?((((monteure||[]).find(_m=>_m.id===a.monteur)||{}).n)||") != 1:
        f.append("Monteur Liste")
    if "terminBestaetigt:e.target.value})), disabled:_asMtLocked||!isAdmin," not in av:
        f.append("Bestaetigt Formular")
    if "disabled: !isAdmin, title:" not in av:
        f.append("Monteur Formular")
    return f


def test_as_feldrollen_gesperrt(roh):
    av = _komp(roh, "ArbeitsscheinView")
    assert 'const isAdmin=curUser.role==="admin"||curUser.role==="projektleiter"||curUser.role==="buero";' in av
    assert _as_fehler(av) == []
    assert av.count("storno(a.id)") >= 2 and av.count("storno(editId)") == 1


def test_as_umkehr_altstand_waere_rot(roh):
    av = _komp(roh, "ArbeitsscheinView")
    alt = av.replace('canDo("offa_export",curUser)&&', "").replace(", isAdmin&&!isSt&&", ", !isSt&&")
    alt = alt.replace(", isAdmin&&editId&&", ", editId&&").replace("disabled:_asMtLocked||!isAdmin,", "disabled:_asMtLocked,")
    alt = alt.replace("disabled: !isAdmin, title:", "disabled: isMonteurRole&&!isAdmin, title:")
    alt = re.sub(r"!isAdmin\?\(_hasTermin\(a\.terminBestaetigt\)\?fdt\(a\.terminBestaetigt\):\"[^\"]*\"\):", "", alt)
    alt = alt.replace("!isAdmin?((((monteure||[]).find(_m=>_m.id===a.monteur)||{}).n)||\"—\"):", "")
    f = _as_fehler(alt)
    for teil in ("OFFA-Excel-Knopf", "Untertitel", "Storno offen", "Bestaetigt Liste", "Monteur Liste", "Bestaetigt Formular", "Monteur Formular"):
        assert teil in f, teil


def test_canDo_offa_export_rollen_in_node(node_exe, roh):
    js = _fn(roh, "canDo") + """
const out={};for(const r of %s){out[r]=canDo("offa_export",{role:r,monteurId:"w1"});}
console.log(JSON.stringify(out));
""" % json.dumps(FELD + STAFF)
    out = json.loads(run_node_snippet(node_exe, js))
    assert {r: out[r] for r in FELD} == {r: False for r in FELD}
    assert {r: out[r] for r in STAFF} == {r: True for r in STAFF}


# ── 3. SV-Nr. / Reisepass ───────────────────────────────────────────────────
def test_persdaten_rolle_in_node(node_exe, roh):
    js = _fn(roh, "_maPersDatenRolle") + _fn(roh, "_maStaffRolle") + """
const out={};for(const r of %s){out[r]=[_maPersDatenRolle({role:r}),_maStaffRolle({role:r})];}
console.log(JSON.stringify(out));
""" % json.dumps(FELD + STAFF)
    out = json.loads(run_node_snippet(node_exe, js))
    assert out["admin"] == [True, True]
    assert out["buero"] == [True, True]
    assert out["projektleiter"] == [False, True]
    for r in FELD:
        assert out[r] == [False, False]


def _ma_fehler(ma):
    f = []
    for feld in ("svnr", "reisepass"):
        if "_maPersDatenRolle(curUser)?React.createElement('input', { value: selM." + feld + "||\"\"" not in ma:
            f.append(feld + " Detail")
        if "_maPersDatenRolle(curUser)&&React.createElement('div', {}, React.createElement('label', { htmlFor:\"lbl_monteurNew_" + feld + "\"" not in ma:
            f.append(feld + " Neu")
    if "window._maskSVNR(selM.svnr,_maPersDatenRolle(curUser))" not in ma:
        f.append("svnr Maske")
    if "_maPersDatenRolle(curUser)?(selM.reisepass||" not in ma:
        f.append("reisepass Maske")
    if "updMonteur(selM.id,\"tel\"" not in ma or "isAdmin?React.createElement('input', { value: selM.tel||\"\"" not in ma:
        f.append("Telefon nicht mehr wie vorher")
    return f


def test_mitarbeiter_svnr_reisepass_nur_admin_buero(roh):
    assert _ma_fehler(_komp(roh, "MitarbeiterView")) == []


def test_mitarbeiter_umkehr_altstand_waere_rot(roh):
    ma = _komp(roh, "MitarbeiterView")
    alt = ma.replace("_maPersDatenRolle(curUser)&&", "").replace("_maPersDatenRolle(curUser)", "isAdmin")
    f = _ma_fehler(alt)
    for teil in ("svnr Detail", "reisepass Detail", "svnr Neu", "reisepass Neu", "svnr Maske", "reisepass Maske"):
        assert teil in f, teil


def test_kein_weiterer_svnr_reisepass_anzeigeort(roh):
    """Grep-Riegel: SV-Nr./Reisepass werden nur in MitarbeiterView angezeigt."""
    ma = _komp(roh, "MitarbeiterView")
    rest = roh.replace(ma, "")
    assert "selM.svnr" not in rest and "selM.reisepass" not in rest
    assert '"SV-Nr."' not in rest and '"Reisepass-Nr."' not in rest


# ── 4. Monatsabrechnung: perm stunden ───────────────────────────────────────
def _perm_probe(node_exe, roles_src, hasperm_src):
    js = "const COLORS={ERROR:'#f00'};" + roles_src + hasperm_src + """
const out={};for(const r of %s){out[r]=hasPerm({role:r},"stunden");}
console.log(JSON.stringify(out));
""" % json.dumps(FELD + STAFF)
    return json.loads(run_node_snippet(node_exe, js))


def _perm_fehler(out):
    soll = {"admin": True, "buero": True, "projektleiter": False,
            "monteur": False, "helfer": True, "techniker": True, "obermonteur": True}
    return [r for r in soll if out[r] != soll[r]]


def test_stunden_ohne_projektleiter_in_node(node_exe, roh):
    assert _perm_fehler(_perm_probe(node_exe, _const(roh, "ROLES"), _fn(roh, "hasPerm"))) == []


def test_stunden_umkehr_pl_mit_stunden_waere_rot(node_exe, roh):
    roles = _const(roh, "ROLES")
    alt = roles.replace('"offa","fahrzeuge","bautagebuch","material","bauprovisorien"]},/* v3.9.1104',
                        '"offa","stunden","fahrzeuge","bautagebuch","material","bauprovisorien"]},/* v3.9.1104', 1)
    assert alt != roles
    assert _perm_fehler(_perm_probe(node_exe, alt, _fn(roh, "hasPerm"))) == ["projektleiter"]


def test_monatsabrechnung_haengt_nur_am_recht(roh):
    """Reiter und Home-Kachel lesen perm stunden - kein zweiter Rollen-Schalter."""
    assert '{l:"Monatsabrechnung",ik:"dokument",c:"#f97316",perm:"stunden",g:2}' in roh
    assert 'FINKZEIT_ENABLED&&hasPerm(curUser,"stunden")&&React.createElement' in roh


# ── 5. Service-Worker-Update-Takt ───────────────────────────────────────────
def _sw_tick(roh):
    a = roh.index("swUpdateTimer.current=setInterval(") + len("swUpdateTimer.current=setInterval(")
    b = roh.index(",60000);", a)
    return roh[a:b]


def _sw_laeuft(node_exe, pfeil):
    js = "try{(function(reg){return (%s);})(undefined)();console.log('ok');}catch(e){console.log('wirft');}" % pfeil
    return run_node_snippet(node_exe, js)


def test_sw_tick_ohne_reg_wirft_nicht(node_exe, roh):
    assert _sw_laeuft(node_exe, _sw_tick(roh)) == "ok"


def test_sw_tick_umkehr_alter_aufruf_wirft(node_exe):
    assert _sw_laeuft(node_exe, "()=>reg.update().catch(()=>{})") == "wirft"
