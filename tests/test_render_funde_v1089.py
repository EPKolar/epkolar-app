# -*- coding: utf-8 -*-
"""Render-Pruefung 1087 (dunkel 800x1280, PROBE_*.json) + Owner-Messung AS-Liste -> Fassung 1089.

Nur Darstellung. Jeder Riegel hat eine Umkehrprobe (der alte Zustand waere rot).

P2-1 Projekte > Listenansicht: Kopfzeile im Dunkeln hell (#FAFBFA) unter UI.grau -> 1,88.
P2-2 Kameras > Einrichtung: gesperrter Knopf sah aktiv aus -> button:disabled blass + Verbotszeiger.
P2-3 Admin > Haendler: "+ Neuer Haendler" Weiss auf #22c55e 2,28 -> EP_GREEN_DARK.
P3   Planung leere Nummern 1,40; MA-Uebersicht hart abgeschnitten; Mehr-Dreieck 3,46;
     Aktivitaet rot 4,24, Login roh "_raw: ...", leere Pille, Login-Verlauf ohne Ladezustand,
     Geraet " - Android"; Juprowa/System-Emoji; Matrix-Kopf klebt unter breit nicht.
AS   Owner-Messung (hell, breit): klebender Kopf AKTIONEN weiss neben getoentem Kopf.
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


# ── WCAG ───────────────────────────────────────────────────────────────────
def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _L(c):
    def f(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def _k(a, b):
    x, y = sorted([_L(a), _L(b)], reverse=True)
    return (x + 0.05) / (y + 0.05)


def _misch(fg, bg, op):
    return tuple(op * f + (1 - op) * b for f, b in zip(fg, bg))


def _thema(roh, name):
    m = re.search(r"\n  %s:\{(.*?)\}" % name, roh)
    assert m, name
    return dict(re.findall(r'(\w+):"(#[0-9A-Fa-f]{6})"', m.group(1)))


def _between(s, a, b):
    i = s.index(a)
    return s[i:s.index(b, i)]


def test_wcag_helfer_umkehr():
    assert _k((255, 255, 255), (34, 197, 94)) < 2.3  # gemessen 2,28
    assert round(_k((255, 255, 255), (0, 150, 64)), 2) == 3.86  # Owner-Entscheid CI-Gruen, unveraendert


# ── P2-1 ───────────────────────────────────────────────────────────────────
def test_p2_1_projliste_kopf_dunkel_lesbar(roh):
    d = _thema(roh, "dark")
    grau_dunkel = d["dm"]  # UI.grau dunkel = 179,188,182 gemessen
    assert _hex(grau_dunkel) == (179, 188, 182)
    assert 'padding:"10px 12px",background:_dark?V.sb:"#FAFBFA"' in roh
    assert _k(_hex(grau_dunkel), _hex(d["sb"])) >= 4.5
    # Umkehr: die alte helle Flaeche im Dunkeln
    assert _k(_hex(grau_dunkel), _hex("#FAFBFA")) < 2


# ── P2-2 ───────────────────────────────────────────────────────────────────
def _kamera_knopf(roh):
    i = roh.index("'aria-labelledby':'kam-freigabe-titel',disabled:!fa.aktiv,")
    return roh[i:roh.index("'Freigabe: Aus – einschalten'", i)]


def _disabled_ok(roh, knopf):
    return ("button:disabled{opacity:.5;cursor:not-allowed !important}" in roh
            and "opacity" not in knopf)


def test_p2_2_gesperrter_knopf_sieht_gesperrt_aus(roh):
    k = _kamera_knopf(roh)
    assert _disabled_ok(roh, k)
    # die Regel steht im App-Stilblock, hinter der Hover-Regel (nur :not(:disabled) hellt auf)
    i = roh.index("button:not(:disabled):hover{filter:brightness(1.08)}")
    assert roh.index("button:disabled{opacity:.5;") > i


def test_p2_2_umkehr(roh):
    k = _kamera_knopf(roh)
    assert not _disabled_ok(roh.replace("button:disabled{opacity:.5;cursor:not-allowed !important}", ""), k)
    assert not _disabled_ok(roh, k.replace("style:fa.an?bsS():bpS", "style:{...bpS,opacity:1}"))


# ── P2-3 ───────────────────────────────────────────────────────────────────
def test_p2_3_neuer_haendler_lesbar(roh):
    m = re.search(r'const EP_GREEN_DARK="(#[0-9a-fA-F]{6})"', roh)
    assert m
    assert 'background:EP_GREEN_DARK,border:"1px solid "+EP_GREEN_DARK,color:"#fff"}}' in _between(roh, "setSuppNew(true);", '"+ Neuer Händler")')
    assert _k((255, 255, 255), _hex(m.group(1))) >= 4.5
    assert "background:COLORS.SUCCESS,color:\"#fff\"}}, \"+ Neuer Händler\"" not in roh


# ── P3 Planung ─────────────────────────────────────────────────────────────
def test_p3_planung_leere_nummern(roh):
    # Render-Funde 1096: die Zeilen-Deckkraft .5 ist weg (Nummern 3,35:1, Striche 2,02:1) - die ganz leere Zeile
    # ist ueber V.mt gedaempft und muss jetzt 4,5:1 halten (strenger als die >= 3 von 1089)
    assert 'verticalAlign:"top",color:isEmpty&&!hasAnyContent?V.mt:isEmpty?V.tx:"#009640"' in roh
    assert "opacity:isEmpty&&!hasAnyContent?0.5:1" not in roh
    d, h = _thema(roh, "dark"), _thema(roh, "light")
    for bg in ((35, 39, 36), (30, 35, 32)):  # gemessene Zeilenflaechen (Zebra)
        assert _k(_hex(d["mt"]), bg) >= 4.5
        assert _k(_misch(_hex(d["mt"]), bg, .5), bg) < 4.5  # Umkehr: mit der alten Deckkraft waere es rot
        assert _k(_misch(_hex("#555555"), bg, .5), bg) < 1.5  # Umkehr: gemessen 1,40
    for bg in ((255, 255, 255), (251, 251, 251)):
        assert _k(_hex(h["mt"]), bg) >= 4.5
        assert _k(_misch(_hex(h["mt"]), bg, .5), bg) < 4.5


def test_p3_ma_uebersicht_bricht_langes_wort(roh):
    seg = _between(roh, "const pc=projColorMap[p.bvh]||\"#71717a\";", "_wpNameLesbar(p.bvh));")
    assert 'overflowWrap:"break-word",wordBreak:"normal",hyphens:"auto"' in seg and "title: p.bvh" in seg
    assert 'overflowWrap:"normal"' not in seg


# ── P3 Mehr-Dreieck ────────────────────────────────────────────────────────
def test_p3_mehr_dreieck_volle_farbe(roh):
    seg = _between(roh, "function NavMehr(", "\n}\n")
    assert "React.createElement('span', { 'aria-hidden': \"true\", style: {fontSize:UI.fMeta,marginLeft:2}}, offen?" in seg
    assert "opacity:.75" not in seg
    d = _thema(roh, "dark")
    bg = (20, 48, 31)  # UI.markeBg dunkel, gemessen
    assert _k(_hex(d["acTx"]), bg) >= 4.5
    assert _k(_misch(_hex(d["acTx"]), bg, .75), bg) < 3.5  # Umkehr: gemessen 3,46


# ── P3 Aktivitaet: Farbe ───────────────────────────────────────────────────
def _lesbar_js(roh):
    return "var _lesbarMerk={};var _dark=true;\n" + _between(roh, "function _lesbar(h,chip){", "\n")


def test_p3_aktivitaet_rot_lesbar(roh, node_exe):
    assert '_zs.ok===false?_lesbar(COLORS.ERROR)' in roh
    js = _lesbar_js(roh) + '\nprocess.stdout.write(_lesbar("#ef4444"));'
    rot = run_node_snippet(node_exe, js)
    karte = _hex(_thema(roh, "dark")["cd"])
    assert _k(_hex(rot), karte) >= 4.5, rot
    assert _k(_hex("#ef4444"), (30, 35, 32)) < 4.5  # Umkehr: gemessen 4,24


# ── P3 Aktivitaet: Zusammenfassung / Geraet / Pille (Node, echter Code) ───
def _helfer(roh):
    return _between(roh, "function _jpAntwortOk(", "/* A55 Runde 3 (1084) P2-a")


ANDROID = "gotrue v3.9.1087-supabase Mozilla/5.0 (Linux; Android 14; SM-A556B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
WIN = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"


def _lauf(node_exe, js_helfer):
    js = js_helfer + "\nvar r={};" \
        "r.z1=_actZusammenfassung('login',{_raw:'gotrue Chrome Android'},null);" \
        "r.z2=_actZusammenfassung('login',{},%s);" \
        "r.z3=_actZusammenfassung('login_failed',{reason:'wrong_password'});" \
        "r.z4=_actZusammenfassung('login_failed',{reason:'xyz'});" \
        "r.u=[_uaText('Android'),_uaText(''),_uaText(%s),_uaText(%s),_uaText('Chrome Android')];" \
        "r.p=[_actPilleSichtbar('\\u2014'),_actPilleSichtbar(''),_actPilleSichtbar(null),_actPilleSichtbar(' - '),_actPilleSichtbar('Projekte')];" \
        "process.stdout.write(JSON.stringify(r));" % (json.dumps(ANDROID), json.dumps(IPHONE), json.dumps(WIN))
    return json.loads(run_node_snippet(node_exe, js))


def test_p3_login_zusammenfassung_und_geraet(roh, node_exe):
    r = _lauf(node_exe, _helfer(roh))
    assert r["z1"] == {"text": "Anmeldung · Android · Chrome", "ok": None}
    assert r["z2"] == {"text": "Anmeldung · Android · Chrome", "ok": None}
    assert r["z3"] == {"text": "Anmeldung fehlgeschlagen – Falsches Passwort", "ok": False}
    assert r["z4"] == {"text": "Anmeldung fehlgeschlagen", "ok": False}
    assert r["u"] == ["Android", "", "Safari · iOS", "Edge · Windows", "Chrome · Android"]
    assert r["p"] == [False, False, False, False, True]
    for z in (r["z1"], r["z2"]):
        assert "_raw" not in z["text"] and "gotrue" not in z["text"]


def test_p3_umkehr_alte_verkettung_fuehrender_punkt(roh, node_exe):
    neu = 'return [u.b,u.os].filter(function(x){return !!x;}).join(" · ");'
    h = _helfer(roh)
    assert h.count(neu) == 1
    r = _lauf(node_exe, h.replace(neu, 'return (u.b+(u.os?" · "+u.os:"")).trim();', 1))
    assert r["u"][0] == "· Android"


def test_p3_feed_und_login_verlauf_verdrahtet(roh):
    assert "const _zs=_actZusammenfassung(a.action,det,a.details);" in roh
    assert 'const _roh=_actDetailText(det,4000)||(typeof a.details==="string"?_actDetailText(a.details,4000):"");' in roh
    assert "const _parseUA=(s)=>_uaText(s);" in roh
    assert "return(b+(os?\" · \"+os:\"\")).trim();" not in roh
    assert "return _actPilleSichtbar(_el)?React.createElement('span'" in roh
    # Ladezustand VOR dem Leerbild und vor der Tabelle
    i = roh.index("logins.length===0&&loadingStats?React.createElement('div', { 'data-ad-logins-laedt': \"1\"")
    j = roh.index("Noch keine Login-Daten", i)
    k = roh.index("'data-ad-tabelle': \"logins\"", i)
    assert i < j < k
    assert "logins.length===0&&!loadingStats?" not in roh


# ── P3 Emoji Juprowa / System ──────────────────────────────────────────────
EMOJI = ["🔗", "💾", "📊", "📋", "📤", "🔽", "🔄", "❌"]


def _juprowa_reiter(roh):
    return _between(roh, 'adminTab==="juprowa"&&(', 'adminTab==="haendler"&&(')


def _jup_config(roh):
    return _between(roh, "const fetchJupConfig=async()=>{", "\n")


def _emoji_in(t):
    return [e for e in EMOJI if e in t]


def test_p3_juprowa_und_system_ohne_emoji(roh):
    assert _emoji_in(_juprowa_reiter(roh)) == []
    assert _emoji_in(_jup_config(roh)) == []
    j = _juprowa_reiter(roh)
    for n in ('_ikVw("verbindung","Juprowa Cloud — Konfiguration")', '_ikVw("speichern","Speichern")',
              '_ikVw("diagramm","Sync-Status")', '_ikVw("liste","Sync-Protokoll")',
              '_ik(isPull?"download":isPush?"senden":"drehen",16)', '_ik("drehen",32)'):
        assert n in j, n
    # Schreibwege unberuehrt: der Reiter ruft weiter nur updatePassport
    assert "onClick:updatePassport" in j


def test_p3_umkehr_emoji_waere_rot(roh):
    j = _juprowa_reiter(roh)
    assert _emoji_in(j.replace('"Sync-Status"', '"📊 Sync-Status"', 1)) == ["📊"]


def test_p3_ikonen_gibt_es(roh):
    ik = roh[roh.index("const IKON="):]
    for n in ("verbindung", "speichern", "diagramm", "liste", "download", "senden", "drehen"):
        assert re.search(r"[{,]\s*%s:\[" % n, ik[:60000]), n


# ── P3 Benachrichtigungs-Matrix: Kopf klebt auch unter breit ──────────────
def _matrix_ok(roh):
    return ("'data-ad-matrix-kasten': \"1\", style: {maxHeight:\"70vh\",overflow:\"auto\",overscrollBehavior:\"contain\"}}" in roh
            and "[data-ad-matrix-kasten] > table > thead > tr:first-child > th { position: sticky; top: 0;" in roh
            and "[data-ad-matrix-kasten] > table > thead > tr:nth-child(2) > th { position: sticky; top: 40px;" in roh
            and 'style: {width:"100%",borderCollapse:"separate",borderSpacing:0,minWidth:600,' in roh)


def test_p3_matrix_kopf_klebt_in_allen_stufen(roh):
    assert _matrix_ok(roh)
    kopf = _between(roh, "'data-ad-tabelle': \"benachrichtigungen\"", "React.createElement('tbody'")
    # deckende Kopfzellen (sonst scheint die Liste durch den klebenden Kopf)
    assert kopf.count("background:V.cd") >= 4
    assert '...(_adStufe!=="breit"?{background:V.cd}:{})' not in kopf


def test_p3_umkehr_matrix_alt(roh):
    alt = roh.replace("'data-ad-matrix-kasten': \"1\", style: {maxHeight:\"70vh\",overflow:\"auto\",overscrollBehavior:\"contain\"}}",
                      "'data-ad-matrix-kasten': \"1\", style: _adStufe!==\"breit\"?{maxHeight:\"70vh\",overflow:\"auto\",overscrollBehavior:\"contain\"}:undefined}", 1)
    assert alt != roh and not _matrix_ok(alt)


# ── AS-Liste: klebende Zellen deckend aus Tokens (Owner-Messung) ──────────
WEISS = re.compile(r"#fff\b|#ffffff\b|rgb\(\s*255\s*,\s*255\s*,\s*255\s*\)|['\"]white['\"]", re.I)


def _as_helfer_zeile(roh):
    return _between(roh, "const _asAktKlebt=", "\n")


def _as_tabelle(roh):
    a = roh.index("React.createElement('table', { className: _asMittel?\"epk-as-mittel\"")
    return roh[a:roh.index("!filtered.length&&", a)]


def _ths_ton(roh, dark):
    m = re.search(r'const thS=_mkS\(\(\)=>\(\{.*?background:_dark\?"([^"]+)":"([^"]+)"', roh)
    assert m
    return m.group(1) if dark else m.group(2)


def _as_eval(node_exe, zeile, dark, mittel):
    js = ("var V={cd:'CD',bd:'BD'};var _dark=%s;var _asMittel=%s;\n" % ("true" if dark else "false", "true" if mittel else "false")
          + zeile + "\nvar T='rgba(239,68,68,.03)';process.stdout.write(JSON.stringify({"
          "kn:_asKopfKlebt(_asNrKlebt()),ka:_asKopfKlebt(_asAktSpalte()),zn:_asNrKlebt(T),za:_asAktSpalte(T),"
          "n0:_asNrKlebt(null),a0:_asAktSpalte(null),deck:_asKopfDeck()}));")
    return json.loads(run_node_snippet(node_exe, js))


def _as_ok(node_exe, roh, zeile):
    if WEISS.search(zeile):
        return False
    for dark in (False, True):
        ton = _ths_ton(roh, dark)
        kopf = "linear-gradient(%s,%s),CD" % (ton, ton)
        for mittel in (False, True):
            r = _as_eval(node_exe, zeile, dark, mittel)
            if r["kn"].get("background") != kopf:
                return False
            if not mittel and r["ka"].get("background") != kopf:
                return False
            if mittel and r["ka"] != {}:
                return False  # mittel: Aktionen kleben nicht (Owner 19.11.)
            if mittel and r["deck"].get("background") != kopf:
                return False  # derselbe Kopfton wie die nicht klebenden Koepfe in mittel
            for z in ("zn",) + (() if mittel else ("za",)):
                if r[z].get("background") != "linear-gradient(rgba(239,68,68,.03),rgba(239,68,68,.03)),CD":
                    return False
            if r["n0"].get("background") != "CD":
                return False
    return True


def test_as_klebezellen_deckend_aus_tokens(roh, node_exe):
    z = _as_helfer_zeile(roh)
    assert _as_ok(node_exe, roh, z)
    t = _as_tabelle(roh)
    # Kopf: beide klebenden Koepfe ueber _asKopfKlebt; Zeile: Toenung der stornierten Zeile
    assert t.count("..._asKopfKlebt(_asNrKlebt())") == 1 and t.count("..._asKopfKlebt(_asAktSpalte())") == 1
    assert t.count("..._asNrKlebt(isSt?_AS_ST_TON:null)") == 1 and t.count("..._asAktSpalte(isSt?_AS_ST_TON:null)") == 1
    assert "background:isSt?_AS_ST_TON:\"transparent\"" in t
    assert 'const _AS_ST_TON="rgba(239,68,68,.03)";const _asAktKlebt=' in roh
    # keine zweite Kopfzeilen-Toenung unter thS, kein hartes Weiss an klebenden Zellen
    assert "React.createElement('thead', {}, React.createElement('tr', {}/* Owner-Messung 1089" in t
    for m in re.finditer(r"style: \{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", t):
        st = m.group(1)
        if "sticky" in st or "Klebt" in st or "_asAktSpalte" in st:
            assert not WEISS.search(st), st[:120]


@pytest.mark.parametrize("alt,neu", [
    # Koeder woertlich aus dem Code: hartes Weiss / halbdurchsichtig statt Token-Komposition
    ('background:"linear-gradient("+_tn+","+_tn+"),"+V.cd', 'background:"#fff"'),
    ('background:"linear-gradient("+_tn+","+_tn+"),"+V.cd', 'background:_tn'),
    ('const _asNrKlebt=(tn)=>({position:"sticky",left:0,zIndex:1,background:tn?"linear-gradient("+tn+","+tn+"),"+V.cd:V.cd});',
     'const _asNrKlebt=(tn)=>({position:"sticky",left:0,zIndex:1,background:tn||V.cd});'),
    ('const _asNrKlebt=(tn)=>({position:"sticky",left:0,zIndex:1,background:tn?"linear-gradient("+tn+","+tn+"),"+V.cd:V.cd});',
     'const _asNrKlebt=(tn)=>({position:"sticky",left:0,zIndex:1,background:"rgb(255,255,255)"});'),
])
def test_as_umkehr_weiss_oder_halbdurchsichtig_waere_rot(roh, node_exe, alt, neu):
    z = _as_helfer_zeile(roh)
    assert z.count(alt) >= 1
    assert not _as_ok(node_exe, roh, z.replace(alt, neu))


def test_as_umkehr_alter_kopf_waere_rot(roh):
    t = _as_tabelle(roh)
    alt = t.replace("..._asKopfKlebt(_asAktSpalte())", "..._asAktSpalte()", 1)
    assert alt.count("..._asKopfKlebt(_asAktSpalte())") == 0


def test_projliste_hat_keine_klebezellen(roh):
    """Gegenprobe zur Owner-Vermutung: die Projektliste ist ein Raster ohne klebende Zellen -
    ihr Befund (P2-1) war die harte Hellflaeche, nicht die Klebelogik der AS-Liste."""
    seg = _between(roh, "/* ═══ LISTE VIEW ═══ */", "fil.map((p,idx)=>")
    assert "sticky" not in seg and "_asKopfKlebt" not in seg
