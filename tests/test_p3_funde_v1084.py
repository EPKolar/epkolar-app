# -*- coding: utf-8 -*-
"""v3.9.1084 - restliche P3-Funde der Render-Pruefung 1080 (Playwright, Offline-Anmeldung, Supabase gesperrt).

(1) Projektakte in "mittel" (Tablet hochkant): die 13 Ikonen der Seitenleiste hatten nur einen
    title - am Finger unsichtbar. Jetzt steht der Name (12 px, hoechstens zwei Zeilen, weiche
    Trennstriche) unter der Ikone, Leiste 76 statt 56 px, Knoepfe >= 44 px. schmal/breit unveraendert.
    Gemessen 800x1280: 14 Knoepfe, alle mit sichtbarem Namen, 1-2 Zeilen, keiner gekappt, 57-71 px hoch.
(2) Planung 800x1280: MA-Chip "Paschinger" stand als "Pasch..." (63 von 80 px). In mittel bricht er
    jetzt um (Silbentrennung, sonst am Rand) - Tabelle bleibt Tabelle. Gemessen: 0 gekappt, 2 Zeilen.
(3) Mehr-Knopf mit aktivem "Monatsabrechnung" gekappt (108/112 px mittel, 117/121 px breit):
    maxWidth 9em -> 10em. Gemessen: 0 gekappt in beiden Stufen.
(4) Maengel-Zaehler: Reiter "Maengel 1", Uebersicht "0 von 2 behoben", Status-Chips summierten 1
    bei "alle 2". Ursache: Altwert status "in_arbeit" (Beispieldaten; im Bestand moeglich auch
    "erledigt"/"in_bearbeitung") - kein Chip, keine Listengruppe, kein Zaehler kannte ihn; der Mangel
    stand in der Liste GAR NICHT. Jetzt ordnet _mgStSicht (reine Anzeige, nichts wird geschrieben)
    Altwerte zu, Unbekanntes zaehlt als "offen"; _mgIstOffen ist die EINE Offen-Definition fuer
    Reiter, Projektliste und Uebersicht. Gemessen 384x752: Reiter "Maengel 2", Chips 1+1+0+0 = alle 2.

Jede Zusicherung hat eine Umkehrprobe: der alte Stand muss an derselben Pruefung scheitern.
"""
import io
import json
import os
import re
import subprocess

import pytest

from _hilfen import nur_code

WURZEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


@pytest.fixture(scope="module")
def html():
    s = io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8", newline="").read()
    assert len(s) > 3_000_000, "index.html zu klein - Datenverlust, kein gruener Fall"
    return s.replace("\r\n", "\n")


def _fn(src, name):
    i = src.index("\nfunction %s(" % name) + 1
    return src[i:src.index("\nfunction ", i + 5)]


def _node(js):
    from conftest import _find_node
    exe = _find_node()
    if not exe:
        pytest.skip("Node.js fehlt")
    r = subprocess.run([exe, "-e", js], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


# ── (4) Maengel: eine Offen-Definition, Chips summieren zu "alle" ───────────
def _helfer(src):
    teile = []
    for pat in [r"const MANGEL_ST=\[[^\]]*\];", r"const MANGEL_ST_SICHT=[^;]*;", r"const _TICKET2MANGEL_ST=\{[^}]*\};",
                r"function _mgStSicht\(s\)\{.*?\}\n", r"function _mgIstOffen\(m\)\{.*?\}\n"]:
        m = re.search(pat, src)
        assert m, pat
        teile.append(m.group(0))
    return "\n".join(teile)


def _seed(src):
    a = src.index("maengel:[\n", src.index("const [forms,setForms]="))
    b = src.index("],", a)
    return src[a + len("maengel:"):b + 1]


def _zaehle(src, offen_js):
    """Je Projekt der Beispieldaten: alle, Reiter-Zaehler, behoben, Summe der Status-Chips."""
    js = (_helfer(src) + "\nconst ms=" + _seed(src) + ";\nconst offen=" + offen_js + ";\n"
          "const r={};[...new Set(ms.map(m=>m.pid))].forEach(pid=>{const l=ms.filter(m=>m.pid===pid);"
          "r[pid]={alle:l.length,reiter:l.filter(offen).length,"
          "behoben:l.filter(m=>_mgStSicht(m.status)===\"behoben\").length,"
          "abgelehnt:l.filter(m=>_mgStSicht(m.status)===\"abgelehnt\").length,"
          "chips:MANGEL_ST_SICHT.reduce((s,st)=>s+l.filter(m=>_mgStSicht(m.status)===st).length,0),"
          "chipsAlt:MANGEL_ST_SICHT.reduce((s,st)=>s+l.filter(m=>m.status===st).length,0)};});"
          "process.stdout.write(JSON.stringify(r));")
    return _node(js)


def test_zuordnung_der_statuswerte(html):
    js = (_helfer(html) + "\nconst w=[\"offen\",\"in Behebung\",\"behoben\",\"abgelehnt\",\"in_arbeit\",\"in_bearbeitung\","
          "\"erledigt\",\"abgenommen\",\"storniert\",\"xyz\",\"\",null,undefined,\"constructor\",\"toString\"];"
          "process.stdout.write(JSON.stringify(w.map(s=>[_mgStSicht(s),_mgIstOffen({status:s})])));")
    r = _node(js)
    assert r == [["offen", True], ["in Behebung", True], ["behoben", False], ["abgelehnt", False],
                 ["in Behebung", True], ["in Behebung", True], ["behoben", False], ["behoben", False],
                 ["behoben", False], ["offen", True], ["offen", True], ["offen", True], ["offen", True],
                 ["offen", True], ["offen", True]]


def test_beispieldaten_zaehler_stimmen_ueberein(html):
    r = _zaehle(html, "_mgIstOffen")
    assert r["p1"]["alle"] == 2 and r["p1"]["reiter"] == 2 and r["p1"]["behoben"] == 0, r["p1"]
    for pid, z in r.items():
        assert z["chips"] == z["alle"], (pid, z)                      # Chips summieren zu "alle"
        assert z["reiter"] + z["behoben"] + z["abgelehnt"] == z["alle"], (pid, z)  # Reiter = alle - behoben (- abgelehnt)


def test_umkehr_alter_zaehler_waere_rot(html):
    """Der alte Reiter-Zaehler (nur "offen") und die alten Chips (roher Status) zeigen den Fund."""
    r = _zaehle(html, "m=>m.status===\"offen\"")
    assert r["p1"]["reiter"] == 1 and r["p1"]["chipsAlt"] == 1 and r["p1"]["alle"] == 2


def test_alle_zaehlstellen_ueber_die_eine_definition(html):
    pl, ps, vd, vm = (nur_code(_fn(html, n)) for n in ("ProjList", "ProjectShell", "VDash", "VMang"))
    assert "const mgOffen=(forms&&forms.maengel||[]).filter(x=>x.pid===p.id&&_mgIstOffen(x)).length;" in pl
    assert "const _pfMgOffen=(forms&&forms.maengel||[]).filter(x=>x.pid===p.id&&_mgIstOffen(x)).length;" in ps
    assert "const _projMaengelDone=_projMaengel.filter(m=>_mgStSicht(m.status)===\"behoben\").length;" in vd
    # In der Maengelansicht vergleicht keine Stelle mehr den ROHEN Status
    assert not re.findall(r"\bm\.status\s*[!=]==", vm), re.findall(r".{40}\bm\.status\s*[!=]==.{20}", vm)
    assert vm.count("_mgStSicht(m.status)") >= 9


def test_umkehr_roher_vergleich_wird_gefunden(html):
    vm = _fn(html, "VMang")
    alt = "const isCur=_mgStSicht(m.status)===ns;"
    assert vm.count(alt) == 1
    kaputt = nur_code(vm.replace(alt, "const isCur=m.status===ns;"))
    assert re.findall(r"\bm\.status\s*[!=]==", kaputt)


def test_nichts_wird_geschrieben(html):
    """_mgStSicht ist Anzeige: kein Schreibweg setzt einen Status aus der Zuordnung."""
    code = nur_code(html)
    assert code.count("_mgStSicht(") >= 12
    assert not re.search(r"status\s*:\s*_mgStSicht|status\s*=\s*_mgStSicht|updSt\([^)]*_mgStSicht", code)


# ── (1) Ikonenleiste mit sichtbarem Namen in mittel ─────────────────────────
RAIL_STIL = ('{fontSize:12,lineHeight:"14px",fontWeight:"inherit",textAlign:"center",maxWidth:"100%",display:"-webkit-box",'
             'WebkitBoxOrient:"vertical",WebkitLineClamp:2,overflow:"hidden",overflowWrap:"anywhere",hyphens:"manual"}')


WEICH = chr(0xAD)  # weicher Trennstrich


def _rail_l(src):
    m = re.search(r"const _psRailL=(\{[^}]*\});", _fn(src, "ProjectShell"))
    assert m
    return _node("process.stdout.write(JSON.stringify(" + m.group(1) + "));")


def test_leiste_traegt_namen_nur_in_mittel(html):
    ps = nur_code(_fn(html, "ProjectShell"))
    assert ps.count("_psMittel?React.createElement('span', { className: \"sb-rail-l\", 'aria-hidden': \"true\", style: "
                    + RAIL_STIL + "}, ") == 2
    assert "}, _psRailL[n.id]||n.l):null, React.createElement('span', { className: \"sb-text\"}, n.l," in ps
    # hinter dem sb-text-span, damit die Anker aelterer Riegel (v960, Scan 1045) unveraendert gelten
    assert "React.createElement('span', { className: \"sb-text\"}, \"Alle Projekte\"), _psMittel?React.createElement('span', { className: \"sb-rail-l\"" in ps
    assert "}, \"Alle Projekte\"):null" in ps
    assert ps.count('flexDirection:_psMittel?"column":"row",minHeight:_psMittel?44:undefined') == 2
    assert "'aria-label': _psMittel?n.l:undefined" in ps and "title: n.l" in ps
    css = html[html.index("<style"):html.index("</style>")]
    assert ".sidebar.sb-rail { width: 76px; }" in css


def test_leistennamen_sind_die_seitennamen(html):
    """Weiche Trennstriche entfernt = derselbe Name wie im Menue; einzige Ausnahme Zeiterfassung = Handy-Reiter "Zeiten"."""
    ps = _fn(html, "ProjectShell")
    nav = dict(re.findall(r'\{id:"(\w+)",ik:"\w+",l:"([^"]+)"', ps[ps.index("const _allNav="):]))
    reiter = dict(re.findall(r'\["(\w+)","([^"]+)"\]', ps[ps.index("const _pfReiter="):ps.index("const _pfHaupt=")]))
    rl = _rail_l(html)
    assert rl and set(rl) <= set(nav)
    for k, v in rl.items():
        ohne = v.replace(WEICH, "")
        nav_l = json.loads('"' + nav[k] + '"')
        assert ohne == nav_l or (k == "zeit" and ohne == reiter["zeit"] == "Zeiten"), (k, v, nav[k])
        assert len(v.split(WEICH)) <= 3


def test_umkehr_falscher_leistenname_waere_rot(html):
    kaputt = html.replace('dokumente:"Doku\\u00ADmente"', 'dokumente:"Doks"', 1)
    assert kaputt != html
    with pytest.raises(AssertionError):
        test_leistennamen_sind_die_seitennamen(kaputt)


def test_umkehr_alte_leiste_waere_rot(html):
    alt = html.replace(".sidebar.sb-rail { width: 76px; }", ".sidebar.sb-rail { width: 56px; }", 1)
    with pytest.raises(AssertionError):
        test_leiste_traegt_namen_nur_in_mittel(alt)


# ── (2) Planung: Name bricht in mittel um statt gekappt ─────────────────────
CHIP_MITTEL = '...(_wpStufe==="mittel"?{whiteSpace:"normal",overflowWrap:"anywhere",hyphens:"auto",textOverflow:"clip",padding:"3px 3px"}:{})}}, m.n)))'


def test_planung_chip_umbruch_nur_mittel(html):
    wp = nur_code(_fn(html, "WeekPlan"))
    assert wp.count(CHIP_MITTEL) == 1
    i = wp.index(CHIP_MITTEL)
    vorher = wp[wp.rfind("maNames.map(m=>(", 0, i):i]
    assert 'whiteSpace:"nowrap"' in vorher and 'textOverflow:"ellipsis"' in vorher  # schmal/breit wie bisher
    assert "React.createElement('table'" in wp  # bleibt Tabelle


def test_umkehr_planung_ohne_umbruch_waere_rot(html):
    with pytest.raises(AssertionError):
        test_planung_chip_umbruch_nur_mittel(html.replace(CHIP_MITTEL, "}}, m.n)))", 1))


# ── (3) Mehr-Knopf traegt "Monatsabrechnung" ganz ──────────────────────────
def test_mehr_knopf_10em(html):
    nm = nur_code(_fn(html, "NavMehr"))
    assert 'akt?React.createElement(\'span\', { style: {display:"inline-block",maxWidth:"10em",overflow:"hidden",textOverflow:"ellipsis"' in nm
    assert "'aria-label': akt?\"Weitere Bereiche, aktiv: \"+akt.l" in nm


def test_umkehr_9em_waere_rot(html):
    nm = _fn(html, "NavMehr")
    kaputt = nm.replace('maxWidth:"10em"', 'maxWidth:"9em"', 1)
    assert kaputt != nm
    with pytest.raises(AssertionError):
        test_mehr_knopf_10em(html.replace(nm, kaputt, 1))
