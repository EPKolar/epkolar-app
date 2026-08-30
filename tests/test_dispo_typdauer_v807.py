# -*- coding: utf-8 -*-
"""v3.9.807 — Dispo 3B: Auftragstyp als Dauer-Signal in die _dispoDauer-Quellenkette (Sebastian).

Reihung: gesetzte Dauer > Klassen-Median(n>=8, v751) > Typ-Median(n>=8) > Typ-Fallback > Text-Keyword > Default.
Typ-Signal nur bei uebergebenem typMedian (Wiring-Stellen); ohne typMedian = altes Verhalten.
'kein'/leer/'stoerung' tragen KEIN Typ-Signal (nicht in DISPO_TYP_DAUER_FALLBACK; stoerung laeuft ueber Topf 0).

node-eval mit den ECHTEN _dispoDauer/_dispoMedianJeTyp + Konstanten aus index.html; die schwer extrahierbaren
Text-Regel-Deps (_dispoParseDauer/_dispoMengeFaktor/DISPO_DAUER_REGELN) werden minimal gestubbt.
"""
from _hilfen import nur_code
from conftest import run_node_snippet


def _line(index_html, marker):
    a = index_html.index(marker)
    return index_html[a:index_html.index("\n", a)]


def _fn(index_html, name):
    a = index_html.index("function " + name + "(")
    return index_html[a:index_html.index("\n}", a) + 2]


def _bundle(index_html):
    stubs = (
        # Parse "HH:MM:SS" / dezimal -> Minuten; leer -> null.
        "function _dispoParseDauer(d){if(!d)return null;var p=String(d).split(':');"
        "if(p.length>=2)return (+p[0])*60+(+p[1]);var f=parseFloat(String(d).replace(',','.'));"
        "return isNaN(f)?null:Math.round(f*60);}\n"
        "function _dispoMengeFaktor(t,o){return 1;}\n"
        # Eine Test-Regel: Keyword 'kwtest' -> Klasse 'testklasse', min 200.
        "var DISPO_DAUER_REGELN=[{re:/kwtest/,klasse:'testklasse',min:200,obj:null}];\n"
    )
    return (stubs
            + _line(index_html, "var DISPO_DAUER_DEFAULT=") + "\n"
            + _line(index_html, "var DISPO_TYP_DAUER_FALLBACK=") + "\n"
            + _fn(index_html, "_dispoMedianJeTyp") + "\n"
            + _fn(index_html, "_dispoDauer") + "\n")


def _eval(index_html, node_exe, expr):
    return run_node_snippet(node_exe, _bundle(index_html) + ";process.stdout.write(String(" + expr + "))")


# ── _dispoMedianJeTyp ────────────────────────────────────────────────────────
def test_median_je_typ(node_exe, index_html):
    sch = ("[{scheinstatus:'erledigt',scheinart:'reparatur',dauer:'02:00:00'},"
           "{scheinstatus:'abgerechnet',scheinart:'reparatur',dauer:'01:00:00'},"   # abgerechnet zaehlt NICHT
           "{scheinstatus:'fertig',scheinart:'reparatur',dauer:'03:00:00'},"
           "{scheinstatus:'erledigt',scheinart:'kein',dauer:'01:00:00'},"           # kein -> nichts
           "{scheinstatus:'erledigt',scheinart:'stoerung',dauer:'01:00:00'},"       # stoerung -> nichts
           "{scheinstatus:'aufgenommen',scheinart:'reparatur',dauer:'05:00:00'}]")  # offen zaehlt NICHT
    # reparatur: erledigt 120 + fertig 180 -> Median 150, n=2. (abgerechnet/aufgenommen ignoriert.)
    out = _eval(index_html, node_exe, f"JSON.stringify(_dispoMedianJeTyp({sch}))")
    import json
    m = json.loads(out)
    assert m.get("reparatur") == {"median": 150, "n": 2}, m
    assert "kein" not in m and "stoerung" not in m, m


# ── _dispoDauer-Reihung ──────────────────────────────────────────────────────
def _dauer(node_exe, index_html, schein, extra=""):
    return _eval(index_html, node_exe, f"JSON.stringify(_dispoDauer({schein}{extra}))")


def test_gesetzt_schlaegt_alles(node_exe, index_html):
    import json
    o = json.loads(_dauer(node_exe, index_html,
        "{dauer:'02:00:00',scheinart:'reparatur',arbeitsanweisungen:'kwtest'}",
        ",null,{testklasse:{median:200,n:8}},{reparatur:{median:150,n:8}}"))
    assert o == {"min": 120, "geschaetzt": False}, o


def test_klassenmedian_schlaegt_typ(node_exe, index_html):
    import json
    o = json.loads(_dauer(node_exe, index_html,
        "{scheinart:'reparatur',arbeitsanweisungen:'kwtest'}",
        ",null,{testklasse:{median:200,n:8}},{reparatur:{median:150,n:8}}"))
    assert o == {"min": 200, "geschaetzt": True}, o  # Klassen-Median 200 > Typ 150


def test_typmedian_schlaegt_fallback(node_exe, index_html):
    import json
    o = json.loads(_dauer(node_exe, index_html,
        "{scheinart:'reparatur'}", ",null,null,{reparatur:{median:150,n:8}}"))
    assert o == {"min": 150, "geschaetzt": True}, o  # Typ-Median 150 > Fallback 120


def test_fallback_schlaegt_textkeyword(node_exe, index_html):
    import json
    o = json.loads(_dauer(node_exe, index_html,
        "{scheinart:'reparatur',arbeitsanweisungen:'kwtest'}", ",null,null,{}"))
    assert o == {"min": 120, "geschaetzt": True}, o  # Typ-Fallback 120 > Text-Keyword 200


def test_kein_typ_signal_faellt_auf_keyword(node_exe, index_html):
    import json
    o = json.loads(_dauer(node_exe, index_html,
        "{scheinart:'kein',arbeitsanweisungen:'kwtest'}", ",null,null,{}"))
    assert o == {"min": 200, "geschaetzt": True}, o  # 'kein' -> kein Typ-Signal -> Text-Keyword 200


def test_ohne_typmedian_identisch_zu_vorher(node_exe, index_html):
    import json
    # 3-arg-Aufruf (kein typMedian): reparatur mit Keyword -> Text-Keyword 200 (KEIN Fallback).
    o = json.loads(_dauer(node_exe, index_html,
        "{scheinart:'reparatur',arbeitsanweisungen:'kwtest'}", ",null,null"))
    assert o == {"min": 200, "geschaetzt": True}, o
    # reparatur ohne Keyword, ohne typMedian -> Default 90 (KEIN Fallback ohne typMedian).
    o2 = json.loads(_dauer(node_exe, index_html, "{scheinart:'reparatur'}", ",null,null"))
    assert o2 == {"min": 90, "geschaetzt": True}, o2


def test_verdrahtung_und_kerne(index_html):
    assert "var DISPO_TYP_DAUER_FALLBACK={reparatur:120,montage:180,mangelbehebung:90,garantie:90,lieferung:30};" in index_html
    assert "function _dispoDauer(schein,regeln,gelernt,typMedian){" in index_html
    assert "var _typMed=_dispoMedianJeTyp(scheine);" in index_html
    # v3.9.886: gezaehlt wurde OHNE Kommentare. Der Riegel war rot, weil ein
    # erklaerender Kommentar und der APP_VERSION-Changelog den Aufruf woertlich
    # nennen - er mass also die Prosa mit (dateiweit 4 statt 2).
    #
    # v3.9.913 - ZWEI Umbauten:
    # 1. Die eigene Strippregel ist weg; sie war die zweite Kopie von nur_code()
    #    und die schwaechere (sie kannte den image/*-Falschoeffner nicht).
    # 2. DIE ZAHL IST WEG. "Beide Planner-Aufrufe" heisst: die Kapazitaets-
    #    Schleife UND die Plan-Abbildung. Beide haben einen Namen (_ddf/_dd).
    #    Die Summe 2 haette auch gestimmt, wenn eine Stelle doppelt und die
    #    andere gar nicht verdrahtet waere - und sie musste bei jeder neuen
    #    Aufrufstelle nachgezogen werden. Benannt sagt der Riegel, WELCHE fehlt.
    _code = nur_code(index_html)
    for wo, ruf in (
        ("die Kapazitaets-Schleife (kapAbzug je Monteur/Tag)",
         "var _ddf=_dispoDauer(s,null,_gelernt,_typMed);"),
        ("die Plan-Abbildung (Chip-Datensatz)",
         "var _dd=_dispoDauer(s,null,_gelernt,_typMed);"),
    ):
        assert ruf in _code, (
            "%s reicht die gelernten Mediane nicht durch (%r fehlt) - dort rechnet "
            "der Plan dann wieder mit dem Typ-Fallback statt mit dem Gelernten."
            % (wo, ruf)
        )
    # Kerne unberuehrt.
    for k in ("function _dispoMedianJeKlasse(", "function _dispoParseDauer(", "function _dispoMengeFaktor("):
        assert k in index_html, "Kern veraendert/entfernt: " + k
