# -*- coding: utf-8 -*-
r"""Render-Funde 1086 (Render-Audit 1085, 384x752 hell).

1. P2 Projekt > Bautagebuch / Fotos / Material: bei nicht erreichbarem Server
   nur graue Kaesten ohne Text (mainTextLen 0). Jetzt: Skelett mit Satz,
   nach 4 s Hinweis "Verbindung langsam" + "Erneut laden"; ein Lesefehler ohne
   Zeilen zeigt "Keine Verbindung - Daten konnten nicht geladen werden" und
   NIE "Noch keine ...". Die Regel steht in EINER reinen Funktion
   _ladeZustand, die hier in Node ausgefuehrt wird.
2. P2 Emoji im Formular "Neues Projekt" und im Home-Toast -> Ikonen.
3. P3 Kontrast: Werte werden hier in Python nachgerechnet (WCAG 2.x), jeweils
   mit Umkehrprobe gegen den alten Wert.
4. P3 "Upload" -> "das Hochladen".

Jeder Riegel hat eine Umkehrprobe: der alte Zustand muss am selben Pruefer
rot werden.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn  # noqa: E402
from _hilfen import nur_code  # noqa: E402

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")


@pytest.fixture(scope="module")
def html():
    return (WURZEL / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def code(html):
    return nur_code(html)


# ── Kontrast-Rechnung ────────────────────────────────────────────────────────

def _rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def _blend(fg, a, bg):
    return [f * a + b * (1 - a) for f, b in zip(fg, bg)]


def _lum(c):
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _ratio(fg, bg):
    a, b = _lum(fg), _lum(bg)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


WEISS = [255, 255, 255]
CI_GRUEN = _rgb("#009640")
GRUEN_DUNKEL = _rgb("#006e30")


def test_kontrast_export_warnung():
    # hell: UI.achtungTxt auf rgba(234,179,8,.1) ueber Karte #fff
    bg = _blend([234, 179, 8], 0.1, WEISS)
    assert _ratio(_rgb("#8A3E06"), bg) >= 4.5
    # dunkel: UI.achtungTxt (dunkel) auf derselben Tönung ueber #1E2320
    bg_d = _blend([234, 179, 8], 0.1, _rgb("#1E2320"))
    assert _ratio(_rgb("#FDBA74"), bg_d) >= 4.5
    # Umkehrprobe: das alte #eab308 lag bei 1,80
    assert _ratio([234, 179, 8], bg) < 2.0


def test_kontrast_zeiten_datum():
    # Weiss auf rgba(0,0,0,.22) ueber beiden Enden des Heute-Verlaufs
    for kopf in (CI_GRUEN, GRUEN_DUNKEL, _rgb("#1e293b"), _rgb("#475569")):
        assert _ratio(WEISS, _blend([0, 0, 0], 0.22, kopf)) >= 4.5, kopf
    # Umkehrprobe: 70 % Weiss auf #009640 = 2,64
    alt = _blend(WEISS, 0.7, CI_GRUEN)
    assert _ratio(alt, CI_GRUEN) < 3.0


def test_kontrast_segmentzaehler_und_maengelzaehler():
    # Projekte-Chips ohne Opazitaet: neutralTxt auf Weiss, Weiss auf Tinte
    assert _ratio(_rgb("#414B45"), WEISS) >= 4.5
    assert _ratio(WEISS, _rgb("#141A16")) >= 4.5
    # Umkehrprobe: mit opacity .7 = 3,99
    assert _ratio(_blend(_rgb("#414B45"), 0.7, WEISS), WEISS) < 4.5
    # Maengel-Chip aktiv: Farbe EP_GREEN_DARK auf eigener 0x28-Toenung
    chip = _blend(GRUEN_DUNKEL, 0x28 / 255, WEISS)
    assert _ratio(GRUEN_DUNKEL, chip) >= 4.5
    # Umkehrprobe: mit opacity .85 (gemessen 3,60-3,84)
    assert _ratio(_blend(GRUEN_DUNKEL, 0.85, chip), chip) < 4.5


def test_kontrast_betrag_liste():
    grund = _rgb("#F2F4F2")
    assert _ratio(GRUEN_DUNKEL, grund) >= 4.5  # V.acTx hell = EP_GREEN_DARK
    assert _ratio(CI_GRUEN, grund) < 4.5       # Umkehrprobe: V.ac = 3,49


def test_ci_gruen_selbst_unveraendert(code):
    """Weiss auf #009640 (3,86) ist Markenentscheid - hier nur festgehalten."""
    assert 'EP_GREEN_DARK="#006e30"' in code
    assert round(_ratio(WEISS, CI_GRUEN), 2) == 3.86


# ── Kontrast: der Code traegt die gerechneten Farben ────────────────────────

def test_code_traegt_neue_farben(code):
    assert 'fontSize:12,color:UI.achtungTxt}}, _ikVw("warnung","Es sind noch ")' in code
    assert 'color:"#eab308"}}, _ikVw("warnung","Es sind noch ")' not in code
    assert 'background:"rgba(0,0,0,.22)",padding:"1px 6px",borderRadius:4,fontSize:UI.fMeta,marginLeft:6}},dateFmt(i))' in code
    assert 'color:"rgba(255,255,255,.7)",fontSize:UI.fMeta,marginLeft:6}},dateFmt(i))' not in code
    assert "opacity:tab===t.id?.85:.7" not in code
    assert "fontFamily:mono,opacity:.85}}, cnt" not in code
    assert "color:p.betrag>0?V.acTx:V.dm}}, p.betrag>0?fmt$(p.betrag)" in code


# ── 1. Lade-/Leer-/Fehlerzustand ────────────────────────────────────────────

FAELLE = [
    # (laedt, fehl, anzahl, erwartet)
    (True, False, 0, "laden"),
    (True, True, 3, "laden"),
    (False, False, 0, "leer"),
    (False, True, 0, "fehler"),     # Kern: Lesefehler ist NIE "leer"
    (False, True, 2, "liste"),      # Offline-Vorrat wird gezeigt
    (False, False, 5, "liste"),
    (False, True, None, "fehler"),
]


def _node_lauf(fn_src, tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node fehlt")
    js = fn_src + "\nconst F=" + json.dumps([f[:3] for f in FAELLE]) + \
        ";console.log(JSON.stringify(F.map(f=>_ladeZustand(f[0],f[1],f[2]))));\n"
    datei = tmp_path / "lz.js"
    datei.write_text(js, encoding="utf-8")
    r = subprocess.run([node, str(datei)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip())


def test_ladezustand_in_node(html, tmp_path):
    src = _extract_fn(html, "_ladeZustand")
    assert src, "_ladeZustand fehlt"
    ist = _node_lauf(src, tmp_path)
    assert ist == [f[3] for f in FAELLE]


def test_ladezustand_umkehrprobe(html, tmp_path):
    """Die alte Logik (leer sobald nichts da ist) muss am selben Pruefer rot sein."""
    alt = 'function _ladeZustand(laedt,fehl,anzahl){if(laedt)return "laden";return (+anzahl||0)>0?"liste":"leer";}'
    ist = _node_lauf(alt, tmp_path)
    assert ist != [f[3] for f in FAELLE]


def test_skelett_und_fehler_tragen_text(html):
    sk = _extract_fn(html, "_LadeSkelett")
    fe = _extract_fn(html, "_LadeFehler")
    assert sk and fe
    assert " werden geladen …" in sk and "Die Verbindung ist langsam" in sk
    assert "_Skeleton(props.rows)" in sk and "Erneut laden" in sk and "setTimeout" in sk
    assert "Keine Verbindung – Daten konnten nicht geladen werden" in fe
    assert "Erneut laden" in fe
    assert not EMOJI.search(sk + fe)


@pytest.mark.parametrize("name,neu", [("VFotos", "_setFotoNeu"), ("VBautag", "_setBtNeu"), ("VMaterial", "loadOrders")])
def test_ansichten_nutzen_skelett_mit_text(html, name, neu):
    src = _extract_fn(html, name)
    assert src, name
    body = nur_code(src)
    assert "return _Skeleton(" not in body, name + " zeigt wieder nur graue Kaesten"
    m = re.search(r"if\(loading\)return React\.createElement\(_LadeSkelett,\{[^}]*onReload:[^;]*" + re.escape(neu), body)
    assert m, name + ": Skelett ohne Erneut-laden"


def test_fotos_und_bautagebuch_unterscheiden_fehler_von_leer(html):
    fo = nur_code(_extract_fn(html, "VFotos"))
    bt = nur_code(_extract_fn(html, "VBautag"))
    assert '_ladeZustand(false,_fotoFehl,photos.length)==="fehler"' in fo
    assert "React.createElement(_LadeFehler" in fo
    assert fo.count("_setFotoFehl(true)") == 2  # Rechtefehler + Netzfehler
    assert "},[p.id,_fotoNeu]);" in fo
    assert '_ladeZustand(false,_btFehl,btEntries.length)==="fehler"' in bt
    assert '_ladeZustand(false,_btFehl,btEntries.length)==="leer"' in bt
    assert "if(!data||_rlsLeer(data))_setBtFehl(true);" in bt
    assert "},[p.id,_btNeu]);" in bt
    # Abrufwege unveraendert: je Ansicht genau der eine Leseaufruf
    assert fo.count('_sbGetOrder("photos"') == 1
    assert bt.count('_sbGet("bautagebuch"') == 1


# ── 2. Emoji ──────────────────────────────────────────────────────────────────

def test_formular_neues_projekt_ohne_emoji(code):
    assert 'editP?_ikT("stift","Projekt bearbeiten"):_ikT("helm","Neues Projekt"))' in code
    assert '_ikT("person","Kundenkontakt")' in code
    assert '_ikT("verbindung","Kundenportal")' in code
    assert '_ikVw("speichern",editP?"Aktualisieren":"Anlegen")' in code
    for alt in ("\U0001f3d7️ Neues Projekt", "\U0001f464 Kundenkontakt",
                "fontWeight:600}}, \"\U0001f517 Kundenportal\" )",  # Formular; Login-Portal (Zugang mit Code) ist eine andere Ansicht
"\U0001f4be \" , editP",
                "✏️ Projekt bearbeiten"):
        assert alt not in code, alt


def test_home_toast_ohne_emoji(code):
    assert 'window.__toast("Mitarbeiterliste konnte nicht aktualisiert werden' in code
    assert "⚠️ Mitarbeiterliste konnte" not in code


def test_emoji_umkehrprobe():
    alt = 'React.createElement(\'div\', {}, "\U0001f464 Kundenkontakt")'
    assert EMOJI.search(alt)


# ── 4. Upload ─────────────────────────────────────────────────────────────────

def test_kein_upload_in_einstellungen(code):
    assert "Bei Verbindung erfolgt das Hochladen automatisch." in code
    assert "erfolgt der Upload automatisch" not in code
