# -*- coding: utf-8 -*-
"""v3.9.786 — Konflikt-Warnung Abwesenheit <-> Projektzeit (Sebastian 21.07.2026).

WARNEN, nicht blockieren. Beide Richtungen. Loesen-Zugang nur isStaff (Buero/Admin/PL). Kein DDL, absences
read-only in der Pruefung, EZ-Kern (_ezSet/_ezEffTage/_ezDayEff) byte-identisch (v785).
"""
import re


def test_a_addentry_guard(index_html):
    """(a) Projektzeit-Erfassung: addEntry (async) warnt bei genehmigter Abwesenheit am Buchungstag; bestaetigt -> durch."""
    # ZeiterfassungView bekommt abs/approvals (App-Ebene, kein neuer Fetch)
    assert "function ZeiterfassungView({curUser,monteure,projects,arbeitsscheine,entries,setEntries,ww,abs,approvals}){" in index_html
    assert "React.createElement(ZeiterfassungView, { curUser: curUser, monteure: monteure, projects: projects, arbeitsscheine: arbeitsscheine, entries: entries, setEntries: setEntries, ww: ww, abs: abs, approvals: absApprovals}" in index_html
    # addEntry ist async und prueft via _ezAbsSet (read-only) + _confirmModal
    assert "const addEntry=async()=>{" in index_html
    assert "var _kwSet=_ezAbsSet(abs||{},approvals,_kwName);" in index_html, "addEntry nutzt die v783-Authority _ezAbsSet (read-only)"
    assert "'⚠ An diesem Tag ist '+_kwTyp+' hinterlegt. Trotzdem Zeit buchen?'" in index_html
    assert "confirmLabel:'Trotzdem buchen',cancelLabel:'Abbrechen'" in index_html
    # nicht-blockierend: nur bei Abbruch return (mit Guard-Reset), sonst laeuft der Eintrag normal durch
    assert "if(!_kwOk){_addEntryInFlightRef.current=0;return;}" in index_html, "Abbruch bricht ab; Bestaetigung schreibt durch"


def test_b_absence_guard(index_html):
    """(b) Abwesenheits-Erfassung/-Genehmigung: warnt, wenn am/an den Tag(en) Projektzeit (h>0) erfasst ist."""
    # AbsView bekommt entries (App-Ebene) + _teAmTag-Helfer (read-only Summe)
    assert "function AbsView({abs,setAbs,approvals,setApprovals,files,setFiles,ww,curUser,pushNotif,monteure,entries}){" in index_html
    assert "React.createElement(AbsView, { abs: abs, setAbs: setAbs, approvals: absApprovals, setApprovals: setAbsApprovals, files: mFiles, setFiles: setMFiles, ww: ww, curUser: curUser, pushNotif: pushNotif, monteure: monteure, entries: entries}" in index_html
    assert "const _teAmTag=(who,iso)=>{" in index_html
    # tog (Einzeltag) + submitRequest (Bereich) sind async und warnen; approve haengt Konflikt-Hinweis an
    assert "const tog=async d=>{" in index_html
    assert "const submitRequest=async()=>{" in index_html
    assert "'⚠ An diesem Tag ist bereits Projektzeit erfasst ('+_n(_teH,1)+' h). Abwesenheit trotzdem eintragen?'" in index_html
    # Mehrtages listet die betroffenen Tage
    assert "'⚠ An diesen Tagen ist bereits Projektzeit erfasst: '+_konflTage.join(', ')" in index_html
    assert "_konflTage.push(fdt(dk(_cd))+' ('+_n(_cth,1)+'h)')" in index_html
    # Genehmigung: Konflikt-Hinweis in der Bestaetigung
    assert "⚠ Konflikt: an diesem Tag sind bereits \"+_n(_apTeH,1)+\" h Projektzeit erfasst." in index_html


def test_c_loesen_nur_isstaff(index_html):
    """(c) "Konflikt lösen"-Zugang am v783-Marker NUR isStaff; verlinkt bestehende Pfade, KEINE neue Mutation."""
    # isStaff-Definition (admin/PL/buero) + Handler + onNav durchgereicht
    assert "const _isStaff=curUser.role==='admin'||curUser.role==='projektleiter'||curUser.role==='buero';" in index_html
    assert "const _konfliktLoesen=async()=>{if(!_isStaff)return;" in index_html
    assert "props.onNav('zeiterfassung')" in index_html, "Zugang navigiert in bestehenden Editier-Tab"
    assert "onNav: onNav}" in index_html, "PZEView bekommt onNav (aus VBueroExport)"
    # Loesen-Button an Desktop-Marker UND Mobile-Card, je isStaff-gegated
    assert "if(_isStaff)bits.push(h('button',{key:'kfl',onClick:_konfliktLoesen" in index_html
    assert "_isStaff?h('button',{onClick:_konfliktLoesen" in index_html
    # KEINE neue Mutation aus dem Marker heraus: kein DELETE/PUT im Loesen-Handler
    loes = index_html[index_html.index("const _konfliktLoesen="):index_html.index("const _p2=(n)=>", index_html.index("const _konfliktLoesen="))]
    assert "method:'DELETE'" not in loes and "method:'PUT'" not in loes and "SQ.push" not in loes, "Loesen-Zugang darf nichts mutieren"


def test_rollen_gate_semantik(index_html):
    """Rollen-Pin: der Loesen-Zugang haengt an isStaff (admin/PL/buero); Monteur/lager_display sind NICHT enthalten.

    (Die WARNUNGEN a/b sehen alle Rollen; nur der Loesen-Button ist isStaff-gegated. PZEView ist zudem
    bueroexport-gegated, d.h. der Monteur sieht das Panel gar nicht.)
    """
    m = re.search(r"const _isStaff=([^;]+);", index_html)
    assert m, "_isStaff-Definition nicht gefunden"
    bed = m.group(1)
    assert "'admin'" in bed and "'projektleiter'" in bed and "'buero'" in bed
    assert "monteur" not in bed and "lager_display" not in bed, "Field-/Kiosk-Rollen duerfen nicht isStaff sein"


def test_ez_kern_unberuehrt(index_html):
    """GRENZE: der v785-EZ-Kern bleibt byte-identisch (kein _ezSet/_ezEffTage/_ezDayEff angefasst)."""
    assert "function _ezDayEff(std,flagEntry,absGenehmigt){" in index_html
    assert "(((parseFloat(std)||0)>6)&&!absGenehmigt)?'klein':''" in index_html
    assert "return {tageKlein:tK,tageMittel:tM,tageGross:tG,sum:tK*sK+tM*sM+tG*sG};" in index_html
    assert "async function _ezSet(wid,datum,stufe,von){" in index_html
    assert "taggeldAb6h:11.94," in index_html
