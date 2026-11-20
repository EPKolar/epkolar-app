# -*- coding: utf-8 -*-
"""Stufe 8 Projekte (GF 19.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: neun Ansichten des Projektbereichs entschieden selbst ueber die Breite
(isMob=ww<BP_MOB, dazu isTab=ww<768 in ProjectShell und VFotos und ww<768 im
Projekt-Dashboard). Am Tablet hochkant (600-1099 px) hiess das:
  - Projektakte: die Seitenleiste war ab 769 px 236 px breit (Ikonenleiste nur
    per CSS bis 768 px) - der Akte fehlten 180 px;
  - Projektliste: sieben fr-Spalten wurden auf 600 px gequetscht, Koepfe
    brachen um;
  - Dashboard: Gewerk und Letzte Eintraege erst ab 768 px nebeneinander;
  - Dokumente: neben dem 240-px-Baum passte keine 280-px-Kachel - Querrollen.

Jetzt (nur Darstellung):
  schmal  = Handy, unveraendert (isMob = Stufe "schmal" = n<BP_MOB).
  mittel  = Tablet hochkant: Ikonenleiste (Klasse sb-rail), Projektliste
            bleibt Liste (Owner-Vorgabe) mit Mindestspalten und nicht
            umbrechenden Koepfen, Dashboard zweispaltig, Dokumentbaum 200 px
            und Kacheln ab 240 px.
  breit   = quer/PC: wie bisher.

Was hier gesichert wird (jeder Riegel mit Umkehrprobe):
1. Stufe NUR ueber _layoutStufe - die ECHTEN Ausdruecke fuer 384, 599, 600,
   800x1280, 1280x800, 1920x1080 in Node ausgefuehrt; Handy-Grenze 599/600
   identisch mit vorher.
2. Abdeckung: in keiner der neun Ansichten steht noch eine eigene
   Breitenabfrage ausser zwei benannten, gezaehlten Ausnahmen.
3. Nur Darstellung: jede Ansicht ist nach Rueckbau der aufgezaehlten
   Darstellungs-Ersetzungen BYTE-GLEICH mit origin/main v3.9.1077 (md5
   gepinnt) - Handler, Schreibwege, Abrufe unberuehrt.
4. Die Ikonenleiste haengt an einer Klasse, nicht an einer Breitenabfrage.
"""
import hashlib
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
H = '_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0));'

KOMP = ["ProjList", "ProjectShell", "VDash", "VForm", "VCheck", "VFotos", "VDoku", "VBautag", "VGefahrstoff"]
# Praefix der Stufen-Variable je Ansicht
PRAEFIX = {"ProjList": "_pj", "ProjectShell": "_ps", "VDash": "_ds", "VForm": "_f", "VCheck": "_vc",
           "VFotos": "_vf", "VDoku": "_vd", "VBautag": "_bt", "VGefahrstoff": "_gs"}


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _k(src, name):
    a = src.index("\nfunction %s(" % name)
    return src[a:src.index("\nfunction ", a + 5)]


def _dekl(name):
    p = PRAEFIX[name]
    d = "const %sStufe=%sconst isMob=%sStufe===\"schmal\";" % (p, H, p)
    if name in ("ProjList", "ProjectShell", "VDoku"):
        d += "const %sMittel=%sStufe===\"mittel\";" % (p, p)
    return d


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return src[i:i + len("const BP_MOB=600;")] + "\n" + src[j:k]


# ── 1. Entscheidung mit echtem Code ─────────────────────────────────────────
# Ausdruecke, die woertlich in der Ansicht stehen und hier ausgefuehrt werden.
AUSDRUCK = {
    "ProjList": [
        'isMob?"1fr":_pjMittel?"repeat(auto-fill,minmax(260px,1fr))":"repeat(auto-fill,minmax(320px,1fr))"',
        '(isMob||_pjMittel)?{overflowX:"auto"}:{overflow:"hidden"}',
        '_pjMittel?{whiteSpace:"nowrap"}:{}',
    ],
    "ProjectShell": ['(_psMittel ? " sb-rail" : "")', '_psMittel?"6px 2px":"9px 12px"'],  # 1084 P3: Leiste mit Namen unter der Ikone - Knopf-Innenabstand 10px -> 6px 2px (Riegel in test_p3_funde_v1084.py)
    "VDash": ['isMob?"repeat(2,1fr)":"repeat(4,1fr)"',
              'isMob?"1fr":_dsStufe==="mittel"?"minmax(0,1fr) minmax(0,1fr)":"1fr 1fr"'],
    "VFotos": ['isMob?"repeat(2,1fr)":_vfStufe==="mittel"?"repeat(3,1fr)":"repeat(4,1fr)"'],
    "VDoku": ['isMob?"100%":_vdMittel?"200px":"240px"',
              'isMob?"1fr":_vdMittel?"repeat(auto-fill,minmax(min(100%,240px),1fr))":"repeat(auto-fill,minmax(280px,1fr))"'],
}
GROESSEN = [[384, 832], [599, 900], [600, 900], [800, 1280], [1280, 800], [1920, 1080]]
STUFEN = ["schmal", "schmal", "mittel", "mittel", "breit", "breit"]
LISTE_M = "minmax(180px,2.4fr) minmax(130px,1.3fr) minmax(90px,1fr) 80px 110px 90px 60px"
LISTE_S = "150px 130px 80px 70px 90px 54px 52px"
LISTE_B = "2.4fr 1.3fr 1fr 80px 110px 90px 60px"
ERWARTET = {
    "ProjList": lambda s: [s, s == "schmal",
                           {"schmal": "1fr", "mittel": "repeat(auto-fill,minmax(260px,1fr))"}.get(s, "repeat(auto-fill,minmax(320px,1fr))"),
                           {"overflowX": "auto"} if s != "breit" else {"overflow": "hidden"},
                           {"whiteSpace": "nowrap"} if s == "mittel" else {},
                           {"schmal": LISTE_S, "mittel": LISTE_M, "breit": LISTE_B}[s]],
    "ProjectShell": lambda s: [s, s == "schmal", " sb-rail" if s == "mittel" else "", "6px 2px" if s == "mittel" else "9px 12px"],
    "VDash": lambda s: [s, s == "schmal", "repeat(2,1fr)" if s == "schmal" else "repeat(4,1fr)",
                        {"schmal": "1fr", "mittel": "minmax(0,1fr) minmax(0,1fr)"}.get(s, "1fr 1fr")],
    "VFotos": lambda s: [s, s == "schmal", {"schmal": "repeat(2,1fr)", "mittel": "repeat(3,1fr)"}.get(s, "repeat(4,1fr)")],
    "VDoku": lambda s: [s, s == "schmal", {"schmal": "100%", "mittel": "200px"}.get(s, "240px"),
                        {"schmal": "1fr", "mittel": "repeat(auto-fill,minmax(min(100%,240px),1fr))"}.get(s, "repeat(auto-fill,minmax(280px,1fr))")],
}


def _gridcols(v):
    m = re.search(r"const _gridCols=.*?;(?=/\*|\r?\n)", v)
    assert m, "_gridCols nicht gefunden"
    return m.group(0)


def _entscheidung(node_exe, src, name, groessen):
    v = _k(src, name)
    d = _dekl(name)
    assert nur_code(v).count(d) == 1, name
    aus = list(AUSDRUCK.get(name, []))
    for a in aus:
        assert a in v, (name, a)
    vorspann = ""
    if name == "ProjList":
        vorspann = "var _seeBetrag=true,isAdmin=true;" + _gridcols(v)
        aus.append("_gridCols")
    p = PRAEFIX[name]
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;" + d + vorspann
          + "var r=[" + ",".join([p + "Stufe", "isMob"] + ["(" + a + ")" for a in aus]) + "];return r;}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(groessen)
          + ".map(function(x){return f(x[0],x[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


@pytest.mark.parametrize("name", KOMP)
def test_entscheidung_je_ansicht(roh, node_exe, name):
    r = _entscheidung(node_exe, roh, name, GROESSEN)
    if name in ERWARTET:
        assert r == [ERWARTET[name](s) for s in STUFEN], list(zip(GROESSEN, r))
    else:
        assert [x[:2] for x in r] == [[s, s == "schmal"] for s in STUFEN], r


def test_dieselbe_handy_grenze_wie_vorher(roh, node_exe):
    """schmal == alte isMob (ww<BP_MOB): 599 Handy, 600 nicht - in allen neun Ansichten."""
    for name in KOMP:
        r = _entscheidung(node_exe, roh, name, [[599, 900], [600, 900]])
        assert [x[1] for x in r] == [True, False], name


def test_umkehr_breite_grenze_auf_handy_waere_rot(roh, node_exe):
    kaputt = roh.replace("const BP_BREIT=1100;", "const BP_BREIT=600;", 1)
    assert kaputt != roh
    r = _entscheidung(node_exe, kaputt, "ProjectShell", GROESSEN)
    assert r != [ERWARTET["ProjectShell"](s) for s in STUFEN]


def test_projektliste_bleibt_liste_im_mittel(roh, node_exe):
    """Owner-Vorgabe: Listen bleiben am Tablet Listen - sieben Spalten, keine Karte."""
    r = _entscheidung(node_exe, roh, "ProjList", [[800, 1280]])
    assert r[0][-1] == LISTE_M and len(r[0][-1].split(" ")) == 7


# ── 2. Abdeckung ────────────────────────────────────────────────────────────
TITEL = "fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite"   # gemeinsamer, gepinnter Seitentitel
KOPF_1200 = "!isMob&&ww<1200"   # Kopfzeilen-Umbruch der Projektakte an der Rechner-Schwelle (v3.9.389-Muster)
AUSNAHMEN = {"ProjectShell": {KOPF_1200: 3}, "VDash": {TITEL: 1}, "VForm": {TITEL: 1}, "VCheck": {TITEL: 1},
             "VFotos": {TITEL: 1}, "VDoku": {TITEL: 1}, "VBautag": {TITEL: 2}}
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|\(ww\|\|0\)\s*[<>]|innerWidth\s*[<>]=?|matchMedia|userAgent|\bisTab\b")


def _fremde_breiten(src, name):
    code = nur_code(_k(src, name))
    for a, n in AUSNAHMEN.get(name, {}).items():
        assert code.count(a) == n, (name, a, code.count(a))
        code = code.replace(a, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


@pytest.mark.parametrize("name", KOMP)
def test_abdeckung_keine_eigenen_breitenvergleiche(roh, name):
    funde = _fremde_breiten(roh, name)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe in %s:\n%s" % (name, "\n".join(funde))
    assert "ww<BP_MOB" not in nur_code(_k(roh, name))


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    alt = 'const isMob=_vdStufe==="schmal";'
    assert _fremde_breiten(roh.replace(alt, "const isMob=ww<BP_MOB;", 1), "VDoku")
    v = _k(roh, "VBautag")
    alt2 = 'gridTemplateColumns:isMob?"1fr":"1fr 1fr 1fr"'
    assert v.count(alt2) == 1
    kaputt = roh.replace(v, v.replace(alt2, alt2.replace("isMob", "ww<768")), 1)
    assert _fremde_breiten(kaputt, "VBautag")


def test_pin_zaehlt_elf(roh):  # 1078: zusammen mit Stufe 9 (Flotte, -3) sind es 11
    # 1079: Stufe 10 (-3) und Stufe 11 (-7) zusammen -> nur App main-pad bleibt
    assert roh.count("ww<BP_MOB") == 1


# ── 3. Nur Darstellung: Rueckbau ergibt origin/main byte-gleich ────────────
def _md5(t):
    # CRLF-Arbeitskopie und LF-Blob gleich behandeln (die Ansicht endet vor "\nfunction", ein einzelnes \r bliebe stehen)
    return hashlib.md5(t.replace("\r\n", "\n").rstrip("\r").encode("utf-8")).hexdigest()


# (neu, alt) - die einzigen Ersetzungen; alles andere ist byte-gleich mit vorher.
RUECKBAU = {
    "ProjList": [
        (':_pjMittel?("minmax(180px,2.4fr) minmax(130px,1.3fr) minmax(90px,1fr) 80px"+(_seeBetrag?" 110px":"")+" 90px"+(isAdmin?" 60px":"")):("2.4fr', ':("2.4fr'),
        ('...((isMob||_pjMittel)?{overflowX:"auto"}:{overflow:"hidden"})', '...(isMob?{overflowX:"auto"}:{overflow:"hidden"})'),
        ('color:UI.grau,...(_pjMittel?{whiteSpace:"nowrap"}:{})}', 'color:UI.grau}'),
        ('isMob?"1fr":_pjMittel?"repeat(auto-fill,minmax(260px,1fr))":', 'isMob?"1fr":'),
    ],
    "ProjectShell": [
        ('_psMittel?', 'isTab&&!isMob?'),
        (' + (_psMittel ? " sb-rail" : "")', ''),
    ],
    "VDash": [
        ('isMob?"1fr":_dsStufe==="mittel"?"minmax(0,1fr) minmax(0,1fr)":"1fr 1fr"', 'ww<768?"1fr":"1fr 1fr"'),
        ('gridTemplateColumns:isMob?"repeat(2,1fr)"', 'gridTemplateColumns:ww<BP_MOB?"repeat(2,1fr)"'),
        ('"repeat("+(isMob?2:4)', '"repeat("+(ww<BP_MOB?2:4)'),
    ],
    "VFotos": [
        ('_vfStufe==="mittel"?"repeat(3,1fr)"', 'isTab?"repeat(3,1fr)"'),
    ],
    "VDoku": [
        ('isMob?"100%":_vdMittel?"200px":"240px"', 'isMob?"100%":"240px"'),
        ('minWidth:isMob?"auto":_vdMittel?180:200,', 'minWidth:isMob?"auto":200,'),
        ('isMob?"1fr":_vdMittel?"repeat(auto-fill,minmax(min(100%,240px),1fr))":', 'isMob?"1fr":'),
    ],
}
# Deklaration samt Stufe-8-Kommentar -> alte Zeile(n)
ALT_DEKL = {
    "ProjList": "const isMob=ww<BP_MOB;",
    "ProjectShell": "const isTab=ww<768;\n  const isMob=ww<BP_MOB;",
    "VDash": None,   # neue Zeile, vorher nicht vorhanden
    "VForm": None,   # isMob stand vor _fStufe - Sonderfall unten
    "VCheck": "const isMob=ww<BP_MOB;",
    "VFotos": "const isMob=ww<BP_MOB;\n  const isTab=ww<768;",
    "VDoku": "const isMob=ww<BP_MOB;",
    "VBautag": "const isMob=ww<BP_MOB;",
    "VGefahrstoff": "const isMob=ww<BP_MOB;",
}
# origin/main v3.9.1077 (9eab816), Ansicht von "\nfunction X(" bis zur naechsten "\nfunction ", LF-normalisiert.
VORHER_MD5 = {
    "ProjList": "009a9a30a3da611e8d20af6f42d6f85c",  # 1084 P3 (4): mgOffen zaehlt ueber _mgIstOffen (offen + in Behebung, Altwerte ueber _mgStSicht) - einzige Abweichung, Diff gegen 24eca7f geprueft, bewusste Aenderung (Riegel in test_p3_funde_v1084.py); vorher 66ba75f5967323f9de6b086b32166543. Davor: 1080 A55 (5): Suchfeld am Handy fuellt die Zeile (flex 1 1 200px, min 200 px statt max 160) - bewusste Aenderung, Pruefsumme nachgezogen (Riegel in test_a55_funde_v1080.py)
    "ProjectShell": "34e67b860edbe44d1112e24745802d10",  # 1084 P3 (1)+(4): Ikonenleiste in mittel mit sichtbarem Namen unter der Ikone (Spalte, 12 px, zwei Zeilen, _psRailL) und Reiterzaehler _pfMgOffen ueber _mgIstOffen - einzige Abweichungen, Diff gegen 24eca7f geprueft, bewusste Aenderung (Riegel in test_p3_funde_v1084.py); vorher 105f63f457076ab247862198e9aca48a. Davor: 1081 Render-Fund P3b: Seitenleiste "Dashboard" -> "Übersicht" (einzige Abweichung, Diff gegen 9ccd9ed) - bewusste Aenderung, Pruefsumme nachgezogen (Riegel in test_render_funde_v1081.py); vorher a7c3fc48b6eafd9b067a82fc784dbcb1
    "VDash": "987e68311725a0598ddcc8963ecc308d",  # 1084 P3 (4): "Maengel behoben" zaehlt ueber _mgStSicht (Altwert "erledigt" = behoben) - einzige Abweichung, Diff gegen 24eca7f geprueft, bewusste Aenderung (Riegel in test_p3_funde_v1084.py); vorher 1535894ef6da1b54a5f4ace1ef146a09
    "VForm": "911d2045f9db2d517980527e2eb9c7c4",
    "VCheck": "ccbec7ed48801b845c5652027c17b4cc",  # 1079: Samsung-Zweig setzt colorScheme "only light/only dark" am Eingabefeld - bewusste Aenderung, Pruefsumme nachgezogen
    "VFotos": "c501370f6173b37f745ff49a1a3f8e34",
    "VDoku": "42b03a16097e9a268407e49ed1faa835",
    "VBautag": "b46f143b897badedcccc69775c880fbe",
    "VGefahrstoff": "1ef705749e386acde2c4936ed917506d",
}


def _zurueck(src, name):
    v = _k(src, name).replace("\r\n", "\n")
    d = re.escape(_dekl(name)) + r"/\* Stufe 8 Projekte[^*]*\*/"
    if name == "VDash":
        v, n = re.subn(r"\n  " + d, "", v)
    elif name == "VForm":
        v, n = re.subn(re.escape("const _fStufe=" + H) + r'const isMob=_fStufe==="schmal";/\* Stufe 8 Projekte[^*]*\*/',
                       lambda m: "const isMob=ww<BP_MOB;\n  const _fStufe=" + H, v)
    else:
        v, n = re.subn(d, lambda m: ALT_DEKL[name], v)
    assert n == 1, (name, "Deklaration nicht gefunden")
    for neu, alt in RUECKBAU.get(name, []):
        assert neu in v, (name, neu)
        v = v.replace(neu, alt)
    return v


@pytest.mark.parametrize("name", KOMP)
def test_nur_darstellung_rueckbau_ist_byte_gleich(roh, name):
    v = _zurueck(roh, name)
    assert not re.search(r"\b%s(?:Stufe|Mittel)\b" % PRAEFIX[name], v) or name == "VForm", name
    assert _md5(v) == VORHER_MD5[name], name


def test_umkehr_handler_aenderung_waere_rot(roh):
    alt = "onClick: ()=>onOpen(p),"
    assert alt in _k(roh, "ProjList")
    kaputt = roh.replace(alt, "onClick: ()=>{onOpen(p);},", 1)
    assert _md5(_zurueck(kaputt, "ProjList")) != VORHER_MD5["ProjList"]


def test_umkehr_handlung_nur_breit_waere_rot(roh):
    """Ein Knopf, der nur in einer Stufe erscheint, ist keine Darstellung mehr."""
    v = _k(roh, "ProjectShell")
    alt = "isMob&&React.createElement('button', { onClick: () => setMobNav(true)"
    assert v.count(alt) == 1
    kaputt = roh.replace(alt, "(isMob||_psMittel)&&React.createElement('button', { onClick: () => setMobNav(true)", 1)
    assert _md5(_zurueck(kaputt, "ProjectShell")) != VORHER_MD5["ProjectShell"]


# ── 4. Ikonenleiste per Klasse ──────────────────────────────────────────────
def _css(roh):
    a = roh.index("<style")
    return roh[a:roh.index("</style>", a)]


CSS_PFLICHT = [".sidebar.sb-rail { width: 76px; }",  # 1084 P3 (1): 56 -> 76 px, damit der Name unter der Ikone steht (Riegel in test_p3_funde_v1084.py)
               ".sidebar.sb-rail .sb-text, .sidebar.sb-rail .sb-logo-text { display: none; }"]


def test_ikonenleiste_css_ohne_breitenabfrage(roh):
    css = _css(roh)
    for z in CSS_PFLICHT:
        assert z in css, z
    for r in re.findall(r"[^\n{}]*sb-rail[^{]*\{[^}]*\}", css):
        assert "@media" not in r, r


def test_umkehr_fehlende_klasse_waere_rot(roh):
    kaputt = _css(roh.replace(CSS_PFLICHT[0], "", 1))
    assert CSS_PFLICHT[0] not in kaputt
