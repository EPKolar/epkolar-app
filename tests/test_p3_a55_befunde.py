# -*- coding: utf-8 -*-
"""P3-A55 (Samsung A55, 412 px, Admin, 16.11.2026) - Riegel je Fund, je mit Umkehrprobe.

1  Fussleiste: am Chef-Portal stand 'Home' als aktiv (Chef traegt g:0).
2  Home: Team-Kacheln und Wetter mit Emoji statt Linien-Ikonen.
3  Chef -> Arbeit -> Kritisch ueberfaellig: Zeile brach um, Tageszahl in eigener Zeile.
Gemessen (Playwright 412x915, hell+dunkel, Offline-Saat): vorher Zeilenhoehen 58/44 px,
Tageszahl 26 px unter der Nummer; nachher alle 50 px, Tageszahl auf Nummernhoehe.
"""
import re

from _hilfen import nur_code

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")


def _fn(src, name):
    i = src.index("function " + name + "(")
    j = src.find("\nfunction ", i + 10)
    return src[i:j]


def _ikon_schluessel(code):
    i = code.index("const IKON={")
    j = code.index("};function _ik(", i)
    sch = set(re.findall(r'(?:[{,]|\*/)([a-z]+):\[', code[i:j]))
    # Nachtrag hinter dem Token-Objekt (P3-A55): dasselbe Objekt, per Object.assign
    k = code.find("Object.assign(IKON,{")
    if k >= 0:
        sch |= set(re.findall(r'(?:[{,])([a-z]+):\[', code[k:code.index("});", k)]))
    return sch


# ---------- Fund 1 -------------------------------------------------------

def _fussleiste(code):
    i = code.index('className: "bottom-nav"')
    return code[i:i + 7000]


def _reiter(code):
    i = code.index("const _allTabs=[")
    j = code.index("];", i)
    return re.findall(r'perm:"([a-z_]+)",g:(\d)', code[i:j])


def _gruppe_fussleiste(code):
    """Die Gruppenregel der Fussleiste als Python - aus der Quelle abgelesen."""
    m = re.search(r'const _fussG=t=>t\.perm==="([a-z_]+)"\?(\d):t\.g;', code)
    if not m:
        return lambda perm, g: g
    sonder, ziel = m.group(1), int(m.group(2))
    return lambda perm, g: ziel if perm == sonder else g


def _aktive_slots(code, gezeigt):
    """Welche Fussleisten-Slots waeren beim gezeigten Reiter markiert?"""
    blk = _fussleiste(code)
    gruppe = _gruppe_fussleiste(code) if "_fussG(t)===gr.g" in blk else (lambda perm, g: g)
    slots = {0: "Home", 1: "Baustelle", 2: "Zeit", 3: "Fuhrpark", 4: "Mehr"}
    reiter = [(p, int(g)) for p, g in _reiter(code)]
    g_gezeigt = [gruppe(p, g) for p, g in reiter if p == gezeigt][0]
    return [slots[g_gezeigt]]


def test_fussleiste_markiert_den_gezeigten_reiter(index_html):
    code = nur_code(index_html)
    blk = _fussleiste(code)
    assert blk.count("_fussG(t)===gr.g") == 2, "Filter UND grTabs muessen dieselbe Fussleisten-Gruppe nutzen"
    # A55-2 Fund 25: ueber die Mehr-Liste geoeffnet -> Mehr markiert; sonst die Gruppe des gezeigten Reiters (safeKat)
    assert "const _viaMehr=_fussMehrKat!==null&&_fussMehrKat===safeKat;const isActive=gr.g===4?(_viaMehr||grTabs.some(t=>tabs.indexOf(t)===safeKat)):(!_viaMehr&&grTabs.some(t=>tabs.indexOf(t)===safeKat));" in blk
    assert "tabs.indexOf(t)===kat)" not in blk, "Markierung liest kat statt des gezeigten Reiters (safeKat)"
    # Am Chef-Portal ist NICHT Home markiert, sondern Mehr (wie NavMehr am Tablet)
    assert _aktive_slots(code, "_chef") == ["Mehr"]
    assert _aktive_slots(code, "_home") == ["Home"]
    nh = code[code.index("const NAV_HAUPT="):code.index("];", code.index("const NAV_HAUPT="))]
    assert '"_chef"' not in nh, "Tablet und Handy sollen Chef gleich einordnen (im Mehr)"


def test_umkehrprobe_alte_gruppierung_markiert_home_am_chef_portal(index_html):
    code = nur_code(index_html)
    kaputt = code.replace("_fussG(t)===gr.g", "t.g===gr.g")
    assert kaputt != code
    assert _aktive_slots(kaputt, "_chef") == ["Home"], "Umkehrprobe greift nicht"


# ---------- Fund 2 -------------------------------------------------------

def _wetter(hv):
    i = hv.index("dv('wetter')&&(weather&&weather.daily?(")
    j = hv.index("Lade Wetter", i)
    return hv[i:j]


def test_home_wetter_und_team_ohne_emoji(index_html):
    hv = nur_code(_fn(index_html, "HomeView"))
    wetter = _wetter(hv)
    assert not EMOJI.search(wetter), EMOJI.findall(wetter)
    assert wetter.count("_ik(_wmoIk(") == 2, "Live- und Ersatzleiste zeichnen Linien-Ikonen"
    assert '_ik("wind",12)' in wetter and '_ik("tropfen",12)' in wetter
    k = hv.index("_teamAktiv.map(m=>{")
    team = hv[k:k + 1600]
    assert not EMOJI.search(team), EMOJI.findall(team)
    assert "_ik(_teamIk(at2,m),26)" in team
    assert "at2.i" not in team


def test_jeder_neue_wetter_und_team_schluessel_hat_eine_zeichnung(index_html):
    code = nur_code(index_html)
    ikon = _ikon_schluessel(code)
    m = re.search(r"const WMO_IK=\{(.*?)\};", code)
    wmo = set(re.findall(r'\d+:"([a-z]+)"', m.group(1)))
    m2 = re.search(r"const AT_KAT_IK=\{(.*?)\};", code)
    at = set(re.findall(r':"([a-z]+)"', m2.group(1)))
    extra = {"wind", "tropfen", "person", "aktentasche", "kalender", "wolke"}
    fehlt = sorted((wmo | at | extra) - ikon)
    assert not fehlt, "Schluessel ohne Zeichnung in IKON: %r" % fehlt
    # jeder WMO-Code der Texttabelle hat eine Ikone
    codes_text = set(re.findall(r"(\d+):", re.search(r"const WMO_TEXT=\{(.*?)\};", code).group(1)))
    codes_ik = set(re.findall(r"(\d+):", m.group(1)))
    assert codes_text == codes_ik, sorted(codes_text ^ codes_ik)
    # jede Abwesenheits-Kategorie hat eine Ikone
    kats = set(re.findall(r'kat:"([a-z]+)"', code[code.index("const AT_T={"):code.index("const AT_KATS=")]))
    assert kats <= set(re.findall(r'([a-z]+):"', m2.group(1))), kats


def test_umkehrprobe_emoji_im_wetter_wird_erkannt(index_html):
    hv = nur_code(_fn(index_html, "HomeView"))
    kaputt = hv.replace('_ik("wind",12)', '"\U0001F4A8"', 1)
    assert kaputt != hv
    assert EMOJI.search(_wetter(kaputt))
    code = nur_code(index_html)
    kaputt = code.replace('{wolke:["', '{wolkx:["', 1)
    assert "wolke" not in _ikon_schluessel(kaputt)


# ---------- Fund 3 -------------------------------------------------------

def _ueberfaellig_zeile(code):
    i = code.index("'Kritisch überfällig ('")
    j = code.index("_drill('Arbeitsscheine','arbeitsscheine')", i)
    return code[i:j]


def test_ueberfaellig_zeile_bricht_nicht_um_und_tage_haben_feste_spalte(index_html):
    z = _ueberfaellig_zeile(nur_code(index_html))
    assert "flexWrap:'wrap'" not in z, "Zeile bricht wieder um - Tageszahl rutscht in eine eigene Zeile"
    assert "flexWrap:'nowrap'" in z
    m = re.search(r"React\.createElement\('span',\{style:\{([^}]*)\}\},tage\+'d'\)", z)
    assert m, "Tages-Spalte nicht gefunden"
    st = m.group(1)
    assert "whiteSpace:'nowrap'" in st and "flex:'0 0 auto'" in st
    # Name und Monteur kuerzen mit Ellipsis statt die Zeile zu sprengen
    assert z.count("textOverflow:'ellipsis',whiteSpace:'nowrap'") >= 2
    assert "{flex:1,minWidth:0,display:'flex',flexDirection:'column'}" in z


def test_umkehrprobe_umbrechende_zeile_wird_erkannt(index_html):
    code = nur_code(index_html)
    kaputt = code.replace("alignItems:'center',flexWrap:'nowrap'}}", "alignItems:'center',flexWrap:'wrap'}}", 1)
    assert kaputt != code
    z = _ueberfaellig_zeile(kaputt)
    assert "flexWrap:'wrap'" in z
