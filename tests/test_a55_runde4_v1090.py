# -*- coding: utf-8 -*-
r"""A55 Handy-Runde 4 (App 3.9.1088, 384x752) - P3-Funde, Riegel mit Umkehrproben.

1 Tankprotokoll: Liter roh mit Dezimalpunkt ("72.77 L"), Monatsauswertung deutsch ("72,8 L");
  Zahlenspalten teils monospace, teils normal (am Handy auch die Feldnamen).
2 Offline-/Server-Streifen doppelt (Kopf UND ueber der Fussleiste, zusammen ~150 px).
3 Projekt-Uebersicht "· Fortschritt" mit Streupunkt; Checkliste "5.6.2026 · · 0/0 erledigt";
  Dokumente-Leerzustand am Handy mit Rechner-Text "Klicken oder Dateien hierher ziehen".
4 Projekt-Reiterzeile 390 > 379 px, "Mehr" am Rand; Schublade "Zeiterfassung" vs. Reiter "Zeiten".
5 Fahrzeug-Serviceheft: Dateinamen auf 50 px abgeschnitten.

Jeder Riegel ist eine Pruefung, die eine Liste von Problemen liefert: am neuen Stand leer,
am Stand vor dem Fix (release/v1090, 34a2e56) nicht leer.
"""
import io
import os
import re
import subprocess

import pytest

WURZEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ALT_REV = "34a2e56"


def _norm(s):
    return s.replace("\r\n", "\n")


@pytest.fixture(scope="module")
def neu():
    return _norm(io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8", newline="").read())


@pytest.fixture(scope="module")
def alt():
    r = subprocess.run(["git", "show", ALT_REV + ":index.html"], cwd=WURZEL, capture_output=True)
    s = r.stdout.decode("utf-8", "replace")
    if not s:
        pytest.skip("alter Stand nicht lesbar")
    return _norm(s)


def _node():
    for k in ("node", "node.exe"):
        try:
            subprocess.run([k, "-v"], capture_output=True, check=True)
            return k
        except Exception:
            continue
    pytest.skip("node fehlt")


def _fn_quelle(src, name):
    a = src.index("function %s(" % name)
    tiefe, i = 0, src.index("{", a)
    while True:
        c = src[i]
        if c == "{":
            tiefe += 1
        elif c == "}":
            tiefe -= 1
            if tiefe == 0:
                return src[a:i + 1]
        i += 1


# ── 1 Tankprotokoll ─────────────────────────────────────────────────────────

LITER_ANFANG = "React.createElement('td', { 'data-l': \"Liter\", style: {"
LITER_ENDE = ", React.createElement('td', { 'data-l': \"Gesamt \\u20ac\""


def _liter_ausdruck(src):
    a = src.index(LITER_ANFANG)
    e = src.index(LITER_ENDE, a)
    zelle = src[a:e]
    k = zelle.index("}}, ") + 4
    kinder = zelle[k:].rstrip()
    assert kinder.endswith(")")
    return kinder[:-1]


def _liter_ausgaben(src):
    js = (_fn_quelle(src, "_fzZahl") + "\n" + _fn_quelle(src, "_fzDE") + "\n"
          "var out=[];[72.77,'72.77','52,3',55,29.1].forEach(function(v){var t={liter:v};"
          "out.push([" + _liter_ausdruck(src) + "].join(''));});"
          "process.stdout.write(JSON.stringify(out));")
    r = subprocess.run([_node(), "-e", js], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr[:400]
    import json
    return json.loads(r.stdout)


def probleme_liter(src):
    raus = []
    for o in _liter_ausgaben(src):
        if re.search(r"\d\.\d", o):
            raus.append("Dezimalpunkt in %r" % o)
    return raus


def test_liter_deutsch(neu):
    aus = _liter_ausgaben(neu)
    assert aus == ["72,77 L", "72,77 L", "52,30 L", "55,00 L", "29,10 L"], aus
    assert probleme_liter(neu) == []


def test_umkehr_liter_mit_punkt_wird_rot(neu, alt):
    assert probleme_liter(alt), "alter Stand zeigte 72.77 L - die Pruefung muss das sehen"
    kaputt = neu.replace(_liter_ausdruck(neu), "t.liter, \" L\" ", 1)
    assert probleme_liter(kaputt)


def _tabelle(src, name, ende):
    i = src.index("'data-fv-tabelle': \"%s\"" % name)
    return src[i:src.index(ende, i)]


def probleme_schrift(src):
    raus = []
    for name, ende in (("tank", "(selFz.tankLog||[]).length>1&&"), ("monate", "(()=>{const totalL=")):
        t = re.sub(r"/\*.*?\*/", "", _tabelle(src, name, ende), flags=re.S)
        if "monospace" in t or "fontFamily:mono" in t:
            raus.append("%s: monospace in der Tabelle" % name)
    return raus


def test_tank_eine_schrift(neu, alt):
    assert probleme_schrift(neu) == []
    assert probleme_schrift(alt)
    t = _tabelle(neu, "tank", "(selFz.tankLog||[]).length>1&&")
    assert t.count('fontVariantNumeric:"tabular-nums"') >= 4


# ── 2 Ein Netz-Streifen ─────────────────────────────────────────────────────

def probleme_streifen(src):
    raus = []
    if "'data-epk': \"netz-streifen\"" in src:
        raus.append("zweiter Streifen ueber der Fussleiste")
    if "isMob?(!syncStatus.connected?\" Offline – lokal gespeichert\":\" Server nicht erreichbar\")" not in src:
        raus.append("Kopf-Streifen am Handy nicht einzeilig")
    return raus


def test_ein_streifen(neu, alt):
    assert probleme_streifen(neu) == []
    assert len(probleme_streifen(alt)) == 2
    # der Kopf-Streifen bleibt mit Sync-Fenster und Zaehler
    a = neu.index("isMob?(!syncStatus.connected?\" Offline")
    kopf = neu[neu.rfind("(!syncStatus.connected||!syncStatus.serverOk)&&React.createElement('div'", 0, a):a]
    assert "setShowSyncPanel(true)" in kopf
    assert "pendingCount, \" ausstehend\"" in neu[a:a + 900]


# ── 3 Projekt: Punkte und Wortlaut ──────────────────────────────────────────

def probleme_punkte(src):
    raus = []
    if "\"· Fortschritt: \"" in src:
        raus.append("Uebersicht: Streupunkt vor Fortschritt")
    if "fdt(c.date), \" · \"  , (c.by" in src:
        raus.append("Checkliste: feste Trenner auch bei leerem Feld")
    return raus


def test_keine_streupunkte(neu, alt):
    assert probleme_punkte(neu) == []
    assert len(probleme_punkte(alt)) == 2
    assert "done+\"/\"+tot+\" erledigt\"].filter(Boolean).join(\" · \")" in neu


def test_checkliste_kopfzeile_ohne_leerfeld(neu):
    a = neu.index("[c.date?fdt(c.date):\"\", ")
    e = neu.index(".join(\" · \")", a) + len(".join(\" · \")")
    ausdruck = re.sub(r"/\*.*?\*/", "", neu[a:e], flags=re.S)
    js = ("var fdt=function(d){return '5.6.2026';};var ww=[];var done=0,tot=0;"
          "var r=[];[{date:'2026-06-05',by:''},{date:'2026-06-05',by:'Pinger'},{date:'',by:''}].forEach(function(c){r.push(" + ausdruck + ");});"
          "process.stdout.write(JSON.stringify(r));")
    out = subprocess.run([_node(), "-e", js], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[:300]
    import json
    r = json.loads(out.stdout)
    assert r == ["5.6.2026 · 0/0 erledigt", "5.6.2026 · Pinger · 0/0 erledigt", "0/0 erledigt"], r
    assert not any("· ·" in x for x in r)


def probleme_doku_text(src):
    if "_ikVw(\"hochladen\",\"Klicken oder Dateien hierher ziehen\")" in src:
        return ["Rechner-Text auch am Handy"]
    if "(_layoutStufe()===\"schmal\"||!_canHover)?\"Tippen, um Dateien hinzuzufügen\":\"Klicken oder Dateien hierher ziehen\"" not in src:
        return ["Touch-Wortlaut fehlt"]
    return []


def test_doku_touch_wortlaut(neu, alt):
    assert probleme_doku_text(neu) == []
    assert probleme_doku_text(alt)


# ── 4 Projekt-Reiterzeile ───────────────────────────────────────────────────

def _reiterzeile(src):
    a = src.index("_pfHaupt.map(n=>React.createElement('button'")
    return src[a:src.index("isMob&&pfMehrAuf&&React.createElement('div', { role: \"menu\"", a)]


def probleme_reiter(src):
    z = _reiterzeile(src)
    raus = []
    if "padding:\"0 12px\"" in z or "padding:\"0 10px\"" in z or "padding:\"0 8px\"" not in z:
        raus.append("Reiter breiter als 0 8px - Zeile 416 > 384 px (Geraet 390 > 379)")
    if "position:\"sticky\",right:0" not in z:
        raus.append("Mehr klebt nicht rechts")
    if "setPfMehrAuf(v=>!v)" not in z:
        raus.append("Mehr ohne Funktions-Umschalter")
    if "title: n.voll&&n.voll!==n.l?n.voll:undefined" not in z:
        raus.append("Kurzname ohne vollen Namen im title")
    return raus


def test_reiterzeile(neu, alt):
    assert probleme_reiter(neu) == []
    assert len(probleme_reiter(alt)) == 4
    assert "return n?{...n,l:l,voll:n.l}:null;" in neu
    assert "[\"zeit\",\"Zeiten\"]]" in neu and "zeit:\"Zeiten\"" in neu


def test_schublade_kurzname_am_handy(neu, alt):
    s = "React.createElement('span', { className: \"sb-text\"}, (isMob&&(_pfReiter.find(r=>r[0]===n.id)||[])[1])||n.l"
    assert s in neu and s not in alt
    # voller Name bleibt im title der Schublade
    assert "onClick: ()=>doNav(n.id), title: n.l," in neu


# ── 5 Fahrzeug-Dokumente ────────────────────────────────────────────────────

def _svc_liste(src):
    a = src.index("_svcDocList(s).map((d,di)=>")
    return src[a:src.index("'data-svc-del': \"1\"", a)]


def probleme_svc_name(src):
    z = _svc_liste(src)
    raus = []
    if "maxWidth:50" in z or "width:50}" in z:
        raus.append("Name/Kachel auf 50 px")
    if "title: d.name||undefined, style: {fontSize:UI.fMeta,color:V.dm,flex:\"1 1 auto\",minWidth:0,overflow:\"hidden\",textOverflow:\"ellipsis\"" not in z:
        raus.append("Name ohne freie Breite/title")
    return raus


def test_svc_name_volle_breite(neu, alt):
    assert probleme_svc_name(neu) == []
    assert len(probleme_svc_name(alt)) == 2
