# -*- coding: utf-8 -*-
"""v1016 Bedienung - Fixe aus dem 3-Lauf-Tablettest (Lenovo 1200x1920, CSS ~800 px).

GF: "vor allem muss es einfach in der bedienung sein", "design professionell, nicht verspielt".

Jeder Riegel hat eine Umkehrprobe: die alte Form (Stand d3c4cc6) wird eingesetzt und
der Pruefer muss sie melden - sonst waere die Abwesenheit trivial wahr.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn
from _hilfen import nur_code


def _fn(src, name):
    i = src.index("function " + name + "(")
    j = src.find("\nfunction ", i + 10)
    return src[i:j]


# ── 1. "Alle Projekte" fuehrt fest zur Projektliste ─────────────────────────

ALT_ONBACK = "onBack: ()=>{if(history.state&&history.length>1){history.back();}"


def _onback(src):
    i = src.index("React.createElement(ProjectShell, { key: openP.id")
    j = src.index(", onHome:", i)
    return src[i:j]


def _onback_ok(seg):
    return ("history.back()" not in seg) and ('tabs.findIndex(t=>t.perm==="projekte")' in seg)


def test_alle_projekte_springt_zur_liste(index_html):
    seg = nur_code(_onback(index_html))
    assert _onback_ok(seg), "onBack springt nicht fest zur Projektliste"
    # Zaehler = Zahl der feuernden Effekte (openP immer, kat nur bei Wechsel)
    assert "_skipPush.current=1+(_zk!==kat?1:0)" in seg


def test_alle_projekte_umkehrprobe():
    assert not _onback_ok(ALT_ONBACK + "...}")


# ── 2. Dialoge: fuer wen, gleiche Knoepfe, gleiche Pause ────────────────────

def test_ze_dialog_nennt_mitarbeiter_im_kopf(index_html):
    ze = _fn(index_html, "ZeiterfassungView")
    assert "'data-dialog-wer':\"ze\"" in ze
    assert 'dayLabel+(workerName?" · "+workerName:"")' in ze
    assert '"+ Neuer Eintrag"' not in ze


def test_projekt_dialog_gleich_aufgebaut(index_html):
    vz = _fn(index_html, "VZeit")
    assert "'data-dialog-wer':\"projekt\"" in vz
    assert 'editEntryId?"Änderungen speichern":"Eintrag speichern"' in vz
    assert '"✓ Speichern"' not in vz
    assert '"📅 "+dayLabel' not in vz


PAUSE_NEU = "React.createElement('option',{value:1},\"1 h\")"


def test_pause_beschriftung_gleich(index_html):
    assert index_html.count(PAUSE_NEU) == 2
    for alt in ('"1h (Standard)"', "\"30min\"", "React.createElement('option',{value:1},\"1h\")"):
        assert alt not in index_html, alt


def test_pause_umkehrprobe(index_html):
    kaputt = index_html.replace(PAUSE_NEU, "React.createElement('option',{value:1},\"1h\")", 1)
    assert kaputt.count(PAUSE_NEU) == 1


# ── 3. Stundenfeld sieht berechnet aus; Karte ohne Eingabe ─────────────────

def test_stundenfeld_berechnet_gestaltet(index_html):
    assert index_html.count("..._zeitStdStil(addVon,addBis,addPause)}}),_zeitStdHinweis(addVon,addBis,addPause)") == 2
    # die v885-Bedingung fuer die Sperre bleibt (Hintertuer bei leerem Von/Bis)
    assert index_html.count("readOnly:_zeitEffektiveStunden(addVon,addBis,addPause)!=null") == 2


def test_stundenfeld_stil_folgt_der_sperre(node_exe, index_html):
    teile = [_extract_fn(index_html, n) for n in ("_zeitParse", "_zeitFmt", "_zeitRundVon", "_zeitRundBis",
                                                     "_wrapHrs", "_zeitEffektiveStunden", "_zeitStdStil")]
    assert all(teile)
    js = ("var ZEIT_RASTER_MIN=5;var V={dm:'#555'};\n" + "\n".join(teile) +
          "\nprocess.stdout.write(JSON.stringify([_zeitStdStil('07:00','16:00',1),_zeitStdStil('','16:00',1)]));")
    a, b = json.loads(run_node_snippet(node_exe, js))
    assert a.get("cursor") == "default" and a.get("borderStyle") == "dashed", a
    assert b == {}, "bei leerem Von/Bis ist das Feld beschreibbar und darf nicht grau sein"


def _karte(ze):
    i = ze.index("/* Hours input */")
    return ze[i:ze.index("/* Add entry button */", i)]


def test_karte_hat_keine_stunden_eingabe(index_html):
    k = _karte(_fn(index_html, "ZeiterfassungView"))
    m = re.search(r"React\.createElement\('input',\{([^}]*)", k)
    assert m, "Anzeigefeld nicht gefunden"
    assert "readOnly:true" in m.group(1) and "tabIndex:-1" in m.group(1), m.group(1)
    assert 'type:"number"' not in m.group(1)
    # Leer-/Komma-Schutz (Riegel v885) bleibt im Code
    assert 'if(_roh==="")return;' in k


def test_karte_umkehrprobe(index_html):
    k = _karte(_fn(index_html, "ZeiterfassungView")).replace("readOnly:true,", "", 1)
    m = re.search(r"React\.createElement\('input',\{([^}]*)", k)
    assert "readOnly:true" not in m.group(1)


def test_karte_zeigt_pause_und_zwei_nachkommastellen(index_html):
    ze = _fn(index_html, "ZeiterfassungView")
    k = _karte(ze)
    assert "_zeitPauseText(entry.pause)" in k and "_hK(entry.hours,2)" in k
    render = ze[ze.index("/* Header */"):]
    assert not re.search(r"_hK\([^)]*,1\)", render), re.findall(r"_hK\([^)]*,1\)", render)


def test_pause_und_loeschname_rechnen(node_exe, index_html):
    js = (_extract_fn(index_html, "_zeitPauseText") + "\n" + _extract_fn(index_html, "_zeitEintragName") +
          "\nprocess.stdout.write(JSON.stringify([_zeitPauseText(1),_zeitPauseText(0.5),_zeitPauseText(0),_zeitPauseText(null),"
          "_zeitEintragName('2026-11-16',8,'BVH Test'),_zeitEintragName('2026-11-17',8.75,'')]));")
    r = json.loads(run_node_snippet(node_exe, js))
    assert r == ["1 h Pause", "30 Min Pause", "ohne Pause", "",
                 "Mo 16.11. · 8,00 h · BVH Test", "Di 17.11. · 8,75 h"], r


# ── 5. MA-Uebersicht ohne Doppelbelegung, Kopf CI ──────────────────────────

def _ma_uebersicht(src):
    wp = _fn(src, "WeekPlan")
    i = wp.index("const maData=fieldMA.map(")
    return wp[i:wp.index("})()", wp.index("Projekte:", i))]


def _ma_funde(seg):
    return [b for b in ("Doppelbelegung", "isConflict", "hasConflict", "#f97316,#ea580c") if b in seg]


def test_ma_uebersicht_ohne_doppelbelegung(index_html):
    seg = nur_code(_ma_uebersicht(index_html))
    assert _ma_funde(seg) == [], _ma_funde(seg)
    assert "linear-gradient(135deg,#009640,#006e30)" in seg


def test_ma_uebersicht_umkehrprobe(index_html):
    seg = nur_code(_ma_uebersicht(index_html)) + '_zpWarn("Doppelbelegung")'
    assert _ma_funde(seg)


# ── 6. Zahlen-Konsistenz Fahrzeuge ─────────────────────────────────────────

def test_home_und_fahrzeugseite_dasselbe_praedikat(index_html):
    """Die Fahrzeug-Seite behaelt ihre Zeilen (test_fuhrpark_kacheln_v898 schneidet sie
    woertlich aus) - der gemeinsame Helfer muss zeichengleich dasselbe Praedikat tragen."""
    pk = "const _pkSt=window._pickerlStatus(f.pickerl);return _pkSt==='warn'||_pkSt==='overdue';"
    sv = 'if(!f.naechstService)return false;const d=new Date(f.naechstService+"T00:00:00");return d<=new Date();'
    assert "function _fzPickerlFaellig(f){" + pk + "}" in index_html
    assert "function _fzServiceFaellig(f){" + sv + "}" in index_html
    assert "const pickerFaellig=visibleFz.filter(f=>{" + pk + "}).length;" in index_html
    assert "const serviceFaellig=visibleFz.filter(f=>{" + sv + "}).length;" in index_html
    hv = _fn(index_html, "HomeView")
    assert "const _fzFk=_fzFaelligkeit(_alertFz);" in hv and "TIME_DAY>-365" not in hv


def test_faelligkeit_rechnet(node_exe, index_html):
    m = re.search(r"window\._pickerlStatus=\(datum,warnDays\)=>\{.*?\};", index_html)
    assert m
    js = ("const TIME_HOUR=3600000;const TIME_DAY=86400000;const window={};" + m.group(0) + "\n" +
          "\n".join(_extract_fn(index_html, n) for n in ("_fzPickerlFaellig", "_fzServiceFaellig", "_fzFaelligkeit")) +
          "\nconst d=n=>{const x=new Date();x.setDate(x.getDate()+n);return x.toISOString().slice(0,10);};"
          "const F=[{id:'a',pickerl:d(-596)},{id:'b',pickerl:d(400),naechstService:d(-3)},"
          "{id:'c',status:'stillgelegt',pickerl:d(-5),naechstService:d(-5)},{id:'e',pickerl:d(-5),naechstService:d(-1)}];"
          "const r=_fzFaelligkeit(F);process.stdout.write(JSON.stringify([r.pickerl.length,r.service.length,r.fahrzeuge]));")
    assert json.loads(run_node_snippet(node_exe, js)) == [2, 2, 3]


def test_kennzahlen_ehrlich_beschriftet(index_html):
    code = nur_code(index_html)
    alt = [b for b in ("'Service/Pickerl 14T'", "'Service/Reparatur'", "{l:'Monteure heute'", "\"Team aktiv\" )") if b in code]
    assert alt == [], alt
    assert "_metric('Neu fällig in 14 Tagen',fzFaellig" in index_html
    # Stufe 4 (19.11.2026): dieselbe Zahl heisst ueberall "Kalibrierung fällig" (Kachel + Filter der Werkzeug-Seite);
    # gesichert bleibt: die Kachel liest wzKalibFaellig.
    assert "_metric('Kalibrierung fällig',wzKalibFaellig" in index_html


# ── 7. Buero-Portal ────────────────────────────────────────────────────────

def test_buero_stunden_aufgeteilt(index_html):
    assert 'label: "Stunden total"' not in index_html
    assert 'label: "Stunden auf Projekten"' in index_html and '" h Scheine/Freitext"' in index_html


# ── 8. Kalender: Alle Monteure ─────────────────────────────────────────────

def test_kalender_alle_monteure_fuer_buero(index_html):
    assert 'isAdmin?"__alle__":(curUser.monteurId' in index_html
    assert 'if(calMonteur==="__alle__")return isAdmin;' in index_html
    # v3.9.1049: die Liste fuehrt Ausgetretene nur noch mit eigenen Scheinen (_maFilterliste)
    assert '"Alle Monteure"), _maFilterliste(monteure,calMonteur,m=>arbeitsscheine.some(a=>a.monteur===m.id)).map(m=>React.createElement(\'option\', { key: m.id, value: m.id}, m.n))' in index_html


# ── 9. Plan-Viewer-Legende ─────────────────────────────────────────────────

def test_legende_nicht_mehr_oben_links(index_html):
    i = index_html.index("v3.9.184 PlanRadar-Status-Legende")
    blk = index_html[i:i + 1200]
    assert 'bottom: 48, left: 10' in blk and 'top: 10, left: 10' not in blk


# ── 10. Querschnitt ────────────────────────────────────────────────────────

def test_mahlzeit_erst_ab_elf(index_html):
    assert 'const greet=hour<11?"Guten Morgen":hour<14?"Mahlzeit"' in index_html


def test_wochentrend_vergleicht_gleichen_zeitraum(index_html):
    hv = _fn(index_html, "HomeView")
    assert "lastWeekHBisTag>0&&weekH>0&&" in hv
    assert 'color:diff>0?_okG("#22c55e"):V.dm' in hv and '"weniger", " als letzte Woche"' not in hv
    assert 'color:diff>0?_okG("#22c55e"):"#f97316"' not in hv


def test_kamera_meldung_deutsch(node_exe, index_html):
    assert "Kamera-Zugriff verweigert: \"+err" not in index_html
    js = _extract_fn(index_html, "_kameraFehlerText") + (
        "\nprocess.stdout.write(JSON.stringify([_kameraFehlerText({name:'NotAllowedError',message:'Permission denied'}),"
        "_kameraFehlerText({name:'X'})]));")
    a, b = json.loads(run_node_snippet(node_exe, js))
    # Tablet-Funde 17.11. (v1038): neutral "nicht freigegeben" statt "verweigert" - wer die Abfrage nur schliesst, hat nichts verweigert.
    assert "nicht freigegeben" in a and "verweigert" not in a and "Permission" not in a and b == "Kamera nicht verfügbar"


def test_datum_deutsch(node_exe, index_html):
    m = re.search(r"const _datumDE=v=>\{.*?\};", index_html)
    assert m
    js = m.group(0) + "\nprocess.stdout.write(JSON.stringify([_datumDE('2026-11-16 10:11'),_datumDE('2026-09-18'),_datumDE('x')]));"
    assert json.loads(run_node_snippet(node_exe, js)) == ["16.11.2026 10:11", "18.09.2026", "x"]
    assert "sub:_datumDE(k.split(\"_\")" in index_html


def test_diagramm_schalter_ist_tippflaeche(index_html):
    f = _fn(index_html, "ChartBox")
    assert 'role: "switch"' in f and "width:44,height:44,padding:0" in f


def test_svgpie_vollkreis(index_html):
    assert "if(pct>=0.9999){" in _fn(index_html, "SvgPie")


def test_systemkonfiguration_ohne_roh_json(index_html):
    f = _fn(index_html, "SystemConfigPanel")
    assert "_sysCfgIstJson(row.value)?" in f and "fontFamily:mono,color:V.acTx}},row.key)" not in f


def test_esc_nur_mit_maus(index_html):
    i = index_html.index('fontWeight:600,minHeight:24}}, "ESC")')
    assert 'matchMedia("(pointer:fine)")' in index_html[i - 400:i]
