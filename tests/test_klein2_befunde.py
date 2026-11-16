# -*- coding: utf-8 -*-
"""Klein2 (16.11.2026) - fuenf gemeldete, noch nicht gebaute Funde. Je ein Riegel mit Umkehrprobe.

1  Plaene: deleteLayer loeschte eine Ebene OHNE Rueckfrage.
2  Einstellungen: sichtbare Emoji (Passwort-Auge, Teilen-Pfeil, Smoke-Ergebnis, Fotosync-Knoepfe/Status, Speichern-Sanduhr, Passwort-Meldung).
3  Material Lager/Bestellungen/Katalog: Emoji aus MATERIAL_CATS/MAT_STATUS/MAT_PRIO/SUPP_ORD_STATUS und Knopf-Emoji.
   Die Daten (.i) bleiben - die Ikone wird beim Zeichnen ueber _MAT_IK zugeordnet.
4  Home-Wetter: JEDER Abruffehler hiess orange "offline" (gemessen: open-meteo HTTP 429 bei bestehender Verbindung).
5  DATANORM 4: Verarbeitungskennzeichen A und X wurden nicht erkannt -> "A;A;..." als vereinfachtes Format gelesen.
"""
import json
import re
import subprocess

from _hilfen import nur_code
from conftest import EPK_TEST_TIMEOUT

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿]")


def _fn(src, name):
    i = src.index("function " + name + "(")
    j = src.find("\nfunction ", i + 10)
    return src[i:j]


def _sichtbare_emoji(code):
    """Emoji in String-Literalen, die NICHT Toast- oder Rueckfrage-Text sind (Toasts sind ausgenommen)."""
    aus = []
    for m in re.finditer(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', code):
        if not EMOJI.search(m.group(0)):
            continue
        vor = code[max(0, m.start() - 160):m.start()]
        if "__toast" in vor or "_confirmModal(" in vor:
            continue
        aus.append(m.group(0)[:60])
    return aus


# ---------- 1 Ebene loeschen ----------

def _delete_layer(code):
    i = code.index("const deleteLayer=")
    return code[i:code.index("\n", i)]


def _hat_rueckfrage(zeile):
    a = zeile.find("_confirmModal(")
    b = zeile.find("setLayers(")
    return a >= 0 and b > a and "if(!await _confirmModal(" in zeile and ")return;" in zeile[a:b]


def test_ebene_loeschen_fragt_vorher(index_html):
    z = _delete_layer(nur_code(index_html))
    assert _hat_rueckfrage(z), z[:300]
    # nennt Ebene und Ticketzahl, zaehlt wie die Ebenen-Liste
    assert "_dl.name" in z and "(t.gewerk||t.layer)===id" in z and "Tickets" in z
    # der Loeschweg selbst unveraendert
    assert "setLayers(prev=>{const next=prev.filter(l=>l.id!==id);_persistLayers(next);return next;})" in z


def test_umkehrprobe_alte_ebenenloeschung_ohne_rueckfrage():
    alt = "const deleteLayer=id=>setLayers(prev=>{const next=prev.filter(l=>l.id!==id);_persistLayers(next);return next;});"
    assert not _hat_rueckfrage(alt)


# ---------- 2 Einstellungen ----------

EINSTELLUNGEN = ("PwInput", "VerbindungView", "PhotoSyncStatus", "SmokeTestPanel", "SystemConfigPanel")


def test_einstellungen_ohne_sichtbare_emoji(index_html):
    code = nur_code(index_html)
    for n in EINSTELLUNGEN:
        assert not _sichtbare_emoji(_fn(code, n)), (n, _sichtbare_emoji(_fn(code, n)))
    assert '_ik(_show?"augeAus":"auge",18)' in _fn(code, "PwInput")


def test_umkehrprobe_einstellungen_emoji_wird_gefunden(index_html):
    code = _fn(nur_code(index_html), "PwInput").replace('_ik(_show?"augeAus":"auge",18)', '_show?"\U0001F648":"\U0001F441️"')
    assert _sichtbare_emoji(code)
    # Toasts bleiben ausgenommen
    assert not _sichtbare_emoji('window.__toast("\U0001F4F7 hochgeladen")')


# ---------- 3 Material ----------

def _ikon_schluessel(code):
    i = code.index("const IKON={")
    j = code.index("};function _ik(", i)
    sch = set(re.findall(r'(?:[{,]|\*/)([a-z]+):\[', code[i:j]))
    k = code.find("Object.assign(IKON,{")
    while k >= 0:
        sch |= set(re.findall(r'[{,]([A-Za-z]+):\[', code[k:code.index("});", k)]))
        k = code.find("Object.assign(IKON,{", k + 10)
    return sch


def _render(code, name):
    i = code.index("const " + name + "=()=>{")
    j = code.find("\n  const render", i + 20)
    k = code.find("\n  return React.createElement", i + 20)
    ende = min(x for x in (j, k) if x > 0)
    return code[i:ende]


def _material_teile(code):
    v = _fn(code, "VMaterial")
    teile = [_render(v, n) for n in ("renderLager", "renderSupplierOrders", "renderKatalog")]
    for badge in ("const statusBadge=", "const prioBadge=", "const suppBadge="):
        i = v.index(badge)
        teile.append(v[i:v.index("\n", i)])
    return teile


def _zeigt_daten_emoji(teil):
    return bool(re.search(r'\b(?:s|p2|mc|v)\.i\b(?!\w)|\]\.i\b|\)\.i\b', teil))


def test_material_ohne_sichtbare_emoji(index_html):
    code = nur_code(index_html)
    for t in _material_teile(code):
        assert not _sichtbare_emoji(t), _sichtbare_emoji(t)
        assert not _zeigt_daten_emoji(t), t[:200]


def test_material_ikonen_existieren_und_daten_bleiben(index_html):
    code = nur_code(index_html)
    m = re.search(r"const _MAT_IK=(\{.*?\}\});", code)
    namen = set(re.findall(r':"([a-zA-Z]+)"', m.group(1)))
    fehlt = sorted(namen - _ikon_schluessel(code))
    assert not fehlt, fehlt
    # Gewerke vollstaendig zugeordnet
    kats = set(re.findall(r"^\s*([a-z]+):\{l:", code[code.index("const MATERIAL_CATS={"):code.index("};", code.index("const MATERIAL_CATS={"))], re.M))
    assert kats == set(re.findall(r'([a-z]+):"', m.group(1).split("},status")[0]))
    # Daten unveraendert (Emoji bleiben in den Daten)
    assert 'elektro:{l:"Elektro",i:"⚡",c:"#3b82f6"}' in code


def test_umkehrprobe_material_alter_badge_wird_gefunden():
    alt = 'const statusBadge=(st)=>{const s=MAT_STATUS[st]||MAT_STATUS.angefordert;return React.createElement(\'span\', {}, s.i, " ", s.l);};'
    assert _zeigt_daten_emoji(alt)
    assert _sichtbare_emoji('React.createElement(\'button\', {}, "\U0001F6D2 Als bestellt markieren")')


# ---------- 4 Wetter ----------

def _wetter(code):
    i = code.index("dv('wetter')&&(weather&&weather.daily?(")
    return code[i:code.index("alerts.length>0&&", i)]


def _offline_nur_wenn_offline(blk):
    """'offline' (orange) darf nur im Zweig stehen, der erst NACH dem Online-Fehler-Zweig kommt."""
    g = blk.find('weatherErr&&!(typeof navigator!=="undefined"&&navigator.onLine===false)?(')
    o = blk.find('"offline"')
    n = blk.find("Wetter gerade nicht verfügbar")
    return g >= 0 and n > g and o > n


def test_wetter_offline_nur_bei_echtem_offline(index_html):
    blk = _wetter(nur_code(index_html))
    assert _offline_nur_wenn_offline(blk)
    assert "Lade Wetter" in blk, "Ladezustand muss bleiben"


def test_umkehrprobe_wetter_alter_zweig(index_html):
    blk = _wetter(nur_code(index_html))
    i = blk.index('weatherErr&&!(typeof navigator')
    j = blk.index("):weatherErr?(", i)
    alt = blk[:i] + "weatherErr?(" + blk[j + len("):weatherErr?("):]
    assert not _offline_nur_wenn_offline(alt)


# ---------- 5 DATANORM A/X ----------

NODE = r"""
const fs=require('fs');const src=fs.readFileSync(process.argv[2],'utf8');
eval(src+"\n;global._parseDatanorm=_parseDatanorm;");
const proben={
  aend:"A;A;1001;00;Kugelhahn Messing;Trinkwasser;1;0;Stk;2450;R12;\r\nA;X;1002;00;Schieber;DN50;1;0;Stk;990;R12;\r\n",
  neu:"A;N;1001;00;Kugelhahn Messing;Trinkwasser;1;0;Stk;2450;R12;\r\n",
  v5:"A;5001;;Heizkoerper;Typ 22;;Stk\r\n",
};
const aus={};for(const k in proben){const r=_parseDatanorm(proben[k],0);aus[k]={det:r.detVer,arts:r.map(a=>[a.artNr,a.name,a.preis])};}
process.stdout.write(JSON.stringify(aus));
"""


def _dn_quelle(src):
    i = src.index("\nfunction _fixCp850(")
    a = src.index("\nfunction _parseDatanorm(")
    e = src.index("\n}\n", a) + 2
    return src[i + 1:src.index("\n}\n", i) + 2] + src[a + 1:e]


def _dn_lauf(node_exe, tmp_path, quelle):
    q = tmp_path / "q.js"; q.write_text(quelle, encoding="utf-8")
    s = tmp_path / "s.js"; s.write_text(NODE, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    out = p.stdout.decode("utf-8", "replace")
    assert p.returncode == 0, out + p.stderr.decode("utf-8", "replace")
    return json.loads(out)


def test_datanorm4_kennzeichen_a_und_x(index_html, node_exe, tmp_path):
    r = _dn_lauf(node_exe, tmp_path, _dn_quelle(index_html))
    assert r["aend"]["det"] == "v4ext"
    assert [a[0] for a in r["aend"]["arts"]] == ["1001", "1002"]
    assert r["aend"]["arts"][0][1] == "Kugelhahn Messing Trinkwasser"
    assert abs(r["aend"]["arts"][0][2] - 24.5) < 1e-9
    assert r["neu"]["det"] == "v4ext" and r["v5"]["det"] == "v5"
    assert index_html.count("/^[NUDÄLAX]$/i.test(") == 3


def test_umkehrprobe_datanorm_ohne_a_x(index_html, node_exe, tmp_path):
    alt = _dn_quelle(index_html).replace("[NUDÄLAX]", "[NUDÄL]")
    r = _dn_lauf(node_exe, tmp_path, alt)
    assert r["aend"]["det"] == "v4sim"
    assert r["aend"]["arts"][0][0] == "A", "ohne Fix wird das Kennzeichen als Artikelnummer gelesen"
