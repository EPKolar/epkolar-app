"""Backlog 1094: Reste aus der Tablet-Vollpruefung 19.11.2026 (Minor-Liste), die bei 1093 noch offen waren.

Alles nur Anzeige - keine Daten, keine Rechte, kein OFFA-Weg (VOffa ist reine Anzeige ohne Knoepfe).

 1  Chef > Kennzahlen: "Tankkosten 2026-11" stand als roher ISO-Monat -> "Tankkosten November 2026" (_monatAnz).
 2  Chef > Ressourcen: Karte hiess "Gefahrstoffe", Navigation und Seite heissen "Gefahrenstoffe".
 3  Fahrzeug > Serviceheft: "(1 Einträge)" -> "(1 Eintrag)".
 4  Projektakte > OFFA Daten: leerer Matchcode zeigte "MC:" ohne Wert -> Strich wie bei Kd-Nr.

Die Ausdruecke laufen in Node aus dem ECHTEN Quelltext. Jede Pruefung hat eine Umkehrprobe: mit dem
alten Quelltext muss sie scheitern.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn


def _zeile(src, anker):
    assert src.count(anker) == 1, anker
    i = src.index(anker)
    a = src.rfind("\n", 0, i) + 1
    e = src.index("\n", i)
    return src[a:e]


def _mo_de(src):
    m = re.search(r"const MO_DE=\[[^\]]*\];", src)
    assert m
    return m.group(0) + "\n"


# 1 ── Tankkosten-Monat ──────────────────────────────────────────────────────

def _tank_label(node_exe, src):
    z = _zeile(src, "_metric('Tankkosten '+")
    m = re.search(r"_metric\(('Tankkosten '\+[^,]*),fmt\$\(tankMTD\)", z)
    assert m, z
    expr = re.sub(r"/\*.*?\*/", "", m.group(1))
    prog = (_mo_de(src) + _extract_fn(src, "_monatAnz") + "\nvar _moNow='2026-11';\n"
            "console.log(JSON.stringify(" + expr + "));")
    return json.loads(run_node_snippet(node_exe, prog))


def _tank_ok(lbl):
    return lbl == "Tankkosten November 2026" and not re.search(r"\d{4}-\d{2}", lbl)


def test_chef_tankkosten_monat_ausgeschrieben(node_exe, index_html):
    assert _tank_ok(_tank_label(node_exe, index_html))


def test_chef_tankkosten_umkehrprobe(node_exe, index_html):
    alt = index_html.replace("'Tankkosten '+_monatAnz(_moNow)", "'Tankkosten '+_moNow", 1)
    assert alt != index_html
    lbl = _tank_label(node_exe, alt)
    assert lbl == "Tankkosten 2026-11" and not _tank_ok(lbl)


# 2 ── Gefahrenstoffe ────────────────────────────────────────────────────────

def _chef(src):
    f = _extract_fn(src, "ChefDashboard")
    assert f
    return f


def _gs_ok(src):
    c = _chef(src)
    return ("'Gefahrstoffe'" not in c and "_drill('Gefahrenstoffe','gefahrstoff')" in c
            and "'kolben','Gefahrenstoffe'" in c)


def test_chef_gefahrenstoffe_wie_navigation(index_html):
    assert '{l:"Gefahrenstoffe",ik:"kolben"' in index_html  # Navigation
    assert _gs_ok(index_html)


def test_chef_gefahrenstoffe_umkehrprobe(index_html):
    alt = index_html.replace("_drill('Gefahrenstoffe','gefahrstoff')", "_drill('Gefahrstoffe','gefahrstoff')", 1)
    assert alt != index_html and not _gs_ok(alt)


# 3 ── Serviceheft Einzahl ───────────────────────────────────────────────────

def _sh_texte(node_exe, src):
    z = _zeile(src, '"Serviceheft ("  , (selFz.serviceheft||[]).length,')
    m = re.search(r'("Serviceheft \(".*?Einträge\)"(?:/\*.*?\*/)?)\s*\)', z)
    assert m, z
    teile = re.sub(r"/\*.*?\*/", "", m.group(1))
    prog = ("function t(n){var selFz={serviceheft:new Array(n).fill({})};return [" + teile + "].join('');}\n"
            "console.log(JSON.stringify([t(1),t(2),t(0)]));")
    return json.loads(run_node_snippet(node_exe, prog))


def test_serviceheft_einzahl(node_exe, index_html):
    assert _sh_texte(node_exe, index_html) == ["Serviceheft (1 Eintrag)", "Serviceheft (2 Einträge)",
                                               "Serviceheft (0 Einträge)"]


def test_serviceheft_umkehrprobe(node_exe, index_html):
    neu = '(selFz.serviceheft||[]).length===1?" Eintrag)":" Einträge)"'
    assert neu in index_html
    alt = index_html.replace(neu, '" Einträge)"', 1)
    assert _sh_texte(node_exe, alt)[0] == "Serviceheft (1 Einträge)"


# 4 ── VOffa Matchcode ───────────────────────────────────────────────────────

def _mc_wert(node_exe, src, mc):
    f = _extract_fn(src, "VOffa")
    assert f
    m = re.search(r"\"MC:\"\), \" \" , React\.createElement\('b', \{\}, (.*?)\)\), React\.createElement", f)
    assert m, "MC-Zelle nicht gefunden"
    expr = re.sub(r"/\*.*?\*/", "", m.group(1))
    prog = "var p=" + json.dumps({"matchcode": mc}) + ";console.log(JSON.stringify(" + expr + "));"
    return json.loads(run_node_snippet(node_exe, prog))


def test_voffa_matchcode_strich(node_exe, index_html):
    assert _mc_wert(node_exe, index_html, "") == "—"
    assert _mc_wert(node_exe, index_html, None) == "—"
    assert _mc_wert(node_exe, index_html, "KOLAR") == "KOLAR"


def test_voffa_matchcode_umkehrprobe(node_exe, index_html):
    alt = re.sub(r"p\.matchcode\|\|\"—\"/\*[^*]*\*/", "p.matchcode", index_html, count=1)
    assert alt != index_html
    assert _mc_wert(node_exe, alt, "") == ""


def test_voffa_bleibt_ohne_knoepfe(index_html):
    f = _extract_fn(index_html, "VOffa")
    assert "onClick" not in f and "React.createElement('button'" not in f
