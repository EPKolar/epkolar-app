# -*- coding: utf-8 -*-
"""Stufe 7 Administration (GF 19.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: AdminPanel entschied selbst ueber die Breite (isMob=ww<BP_MOB). Am
Tablet hochkant (600-767 px) stand die Benutzerliste UEBER den Details
(.user-grid stapelt per CSS unter 768 px) - wer einen Benutzer antippte, sah
die Details erst nach dem Rollen ueber die ganze Liste. Login-Verlauf und
Benutzer-Status waren am Handy 500 px breite Tabellen, die quer rollten; die
Benachrichtigungs-Matrix rollte am Tablet quer und verlor dabei die
Benutzerspalte, ihre Schalter waren 24 px gross.

Jetzt (nur Darstellung):
  schmal  = Handy: Login-Verlauf und Benutzer-Status als gestapelte Zeilen mit
            Feldnamen (CSS epk-ad-karten, dieselben Zellen); Matrix bleibt
            Tabelle, Benutzerspalte klebt, Schalter >= 36 px.
  mittel  = Tablet hochkant: Liste und Details nebeneinander; Tabellen bleiben
            Tabellen (Owner-Vorgabe 1070), erste Spalte klebt, Koepfe brechen
            nicht um; Matrix wie schmal.
  breit   = quer/PC: wie bisher.

Was hier gesichert wird (jeder Riegel mit Umkehrprobe):
1. Stufe NUR ueber _layoutStufe - mit echtem Code fuer 384, 412, 800x1280,
   1280x800, 1920x1080 ausgefuehrt; Handy-Grenze identisch mit vorher.
2. mittel und breit haben dieselben Bedienelemente: _adMittel/_adStufe/_adKleb
   kommen nur in Darstellungs-Ausdruecken vor.
3. Abdeckung: keine eigene Breitenabfrage mehr ausser dem gemeinsamen,
   gepinnten Seitentitel-Ausdruck.
4. Juprowa-Reiter byte-gleich, Logik vor dem Rendern (Handler, Schreibwege,
   Abrufe) byte-gleich bis auf die Stufen-Deklaration.
5. Jede Zelle der zwei Lese-Tabellen traegt ihren Feldnamen (sonst stehen am
   Handy namenlose Werte untereinander).
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

DEKL = ('const _adStufe=_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0));'
        'const isMob=_adStufe==="schmal";const _adMittel=_adStufe==="mittel";'
        'const _adKleb=(bg,auchSchmal)=>(_adMittel||(auchSchmal&&isMob))?{position:"sticky",left:0,zIndex:1,background:bg}:{};')
KLASSE_LESE = 'isMob?"epk-ad-karten":_adMittel?"epk-ad-mittel":undefined'
KLASSE_MATRIX = '_adStufe!=="breit"?"epk-ad-matrix":undefined'
GRID = '_adMittel?{gridTemplateColumns:"minmax(0,1fr) minmax(0,1fr)"}:undefined'


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ad(src):
    a = src.index("\nfunction AdminPanel(")
    return src[a:src.index("\nfunction OfflineBanner(", a)]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


KLEBT = {"position": "sticky", "left": 0, "zIndex": 1, "background": "x"}
ZWEI = {"gridTemplateColumns": "minmax(0,1fr) minmax(0,1fr)"}
# (Breite, Hoehe) -> (Stufe, isMob, Lese-Tabellen-Klasse, Kleb, Kleb Matrix, Matrix-Klasse, user-grid)
FAELLE = [
    ([384, 832], ["schmal", True, "epk-ad-karten", {}, KLEBT, "epk-ad-matrix", None]),
    ([412, 915], ["schmal", True, "epk-ad-karten", {}, KLEBT, "epk-ad-matrix", None]),
    ([800, 1280], ["mittel", False, "epk-ad-mittel", KLEBT, KLEBT, "epk-ad-matrix", ZWEI]),
    ([1280, 800], ["breit", False, None, {}, {}, None, None]),
    ([1920, 1080], ["breit", False, None, {}, {}, None, None]),
]


def _entscheidung(node_exe, src, faelle):
    """Fuehrt die ECHTEN Ausdruecke aus AdminPanel aus (nicht abgeschrieben)."""
    v = _ad(src)
    assert v.count(DEKL) == 1
    assert v.count("className: " + KLASSE_LESE) == 2
    assert v.count("className: " + KLASSE_MATRIX) == 1
    assert v.count("style: " + GRID + "}") == 1
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;" + DEKL
          + "var r=[_adStufe,isMob," + KLASSE_LESE + ",_adKleb(\"x\"),_adKleb(\"x\",true)," + KLASSE_MATRIX
          + "," + GRID + "];return r.map(function(x){return x===undefined?null:x;});}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(faelle)
          + ".map(function(x){return f(x[0],x[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_entscheidung_fuer_fuenf_groessen(roh, node_exe):
    r = _entscheidung(node_exe, roh, [f for f, _ in FAELLE])
    assert r == [e for _, e in FAELLE], list(zip([f for f, _ in FAELLE], r))


def test_umkehr_breite_grenze_auf_handy_waere_rot(roh, node_exe):
    kaputt = roh.replace("const BP_BREIT=1100;", "const BP_BREIT=600;", 1)
    assert kaputt != roh
    assert _entscheidung(node_exe, kaputt, [f for f, _ in FAELLE]) != [e for _, e in FAELLE]


def test_dieselbe_handy_grenze_wie_vorher(roh, node_exe):
    """schmal == alte isMob (ww<BP_MOB): 599 Handy, 600 nicht."""
    r = _entscheidung(node_exe, roh, [[599, 900], [600, 900]])
    assert [x[1] for x in r] == [True, False]


# ── mittel und breit: dieselben Bedienelemente ──────────────────────────────
NUR_DARSTELLUNG = [
    re.escape(DEKL),
    re.escape("className: " + KLASSE_LESE),
    re.escape("className: " + KLASSE_MATRIX),
    re.escape("'data-ad-stufe': _adStufe, style: " + GRID),
    r"\.\.\._adKleb\((?:V\.cd|isFail\?\"linear-gradient\(rgba\(239,68,68,\.06\),rgba\(239,68,68,\.06\)\),\"\+V\.cd:V\.cd)(?:,true)?\)",
    # A55 Runde 3 (1084): Benachrichtigungs-Matrix unter breit mit eigenem Rollkasten und klebenden
    # Kopfzeilen - reine Darstellung (Hoehe, Rollen, Raender, Hintergrund, Ausrichtung), exakt gepinnt.
    # Render 1089 P3: der Rollkasten (70vh) und die deckenden Kopf-Hintergruende gelten jetzt in ALLEN Stufen
    # (Kopf klebt auch unter breit) - sie haengen an keiner Stufe mehr; uebrig bleibt nur die Hoehengrenze
    # der Tabelle selbst (unter 768 px ist sie der Rollkasten) und die Ausrichtung.
    re.escape('...(_adStufe!=="breit"?{maxHeight:"70vh",overscrollBehavior:"contain"}:{})'),
    re.escape('textAlign:_adStufe!=="breit"?"left":"center"'),
]


def _stufen_reste(v):
    for m in NUR_DARSTELLUNG:
        v = re.sub(m, "", v)
    return re.findall(r"_adMittel|_adStufe|_adKleb", nur_code(v))


def test_mittel_und_breit_unterscheiden_nur_darstellung(roh):
    assert _stufen_reste(_ad(roh)) == []
    assert _ad(roh).count("..._adKleb(") == 7


def test_umkehr_handlung_nur_breit_waere_rot(roh):
    v = _ad(roh)
    alt = "React.createElement('button', { onClick: ()=>toggleLock(selU.id),"
    assert v.count(alt) == 1
    assert _stufen_reste(v.replace(alt, "_adMittel?null:" + alt, 1))


# ── Abdeckung ───────────────────────────────────────────────────────────────
# Gepinnter gemeinsamer Seitentitel-Ausdruck (test_d9_seitenueberschriften_v956 u. a.)
AUSNAHMEN = ["fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite"]
# navigator.onLine / navigator.clipboard sind keine Breitenfragen - gesucht wird nur userAgent.
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|\(ww\|\|0\)\s*[<>]|innerWidth\s*[<>]=?|matchMedia|userAgent")


def _fremde_breiten(src):
    code = nur_code(_ad(src))
    for a in AUSNAHMEN:
        code = code.replace(a, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


def test_abdeckung_keine_eigenen_breitenvergleiche(roh):
    funde = _fremde_breiten(roh)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)
    assert _ad(roh).count(AUSNAHMEN[0]) == 1
    assert "ww<BP_MOB" not in _ad(roh)


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    assert _fremde_breiten(roh.replace('const isMob=_adStufe==="schmal";', "const isMob=ww<BP_MOB;", 1))
    v = _ad(roh)
    alt = 'gridTemplateColumns:isMob?"1fr":"1fr 1fr",gap:14,marginTop:14'
    assert v.count(alt) == 1
    assert _fremde_breiten(roh.replace(alt, alt.replace("isMob", "window.innerWidth<700"), 1))


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def test_stufe_steht_im_block_von_adminpanel(roh):
    bl = _bloecke(roh)
    p1, p2 = roh.index("function _layoutStufe(w,h){"), roh.index("function AdminPanel(")
    n1 = [n for n, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [n for n, (a, b) in enumerate(bl) if a <= p2 < b]
    assert n1 and n2 and n1[0] == n2[0]


# ── Juprowa und Logik byte-gleich ───────────────────────────────────────────
def _md5(t):
    return hashlib.md5(t.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def _juprowa(src):
    v = _ad(src)
    i = v.index('adminTab==="juprowa"&&(')
    return v[i:v.index('adminTab==="haendler"&&(', i)]


def _kopf(src):
    """Alles vor dem Rendern: Zustaende, Abrufe, Handler, Schreibwege."""
    v = _ad(src).replace("\r\n", "\n")
    return v[:v.index("\n  return (\n")]


JUPROWA_MD5 = "75f4e6af6dd8d1458b966da766143807"   # Render 1089 P3: nur Anzeige - Emoji (Verbindung/Speichern/Diagramm/Liste/Pull-Push-Sync) durch Linien-Ikonen _ikVw/_ik ersetzt; alter Wert 3ff4e8bb925e7dee0064d1fe5ee528d1 (v3.9.1076, durch Stufe 7 nicht veraendert) | Render-Funde 1096: nur Anzeige - Cyan/Orange im Worker-Mapping und Sync-Protokoll ueber _lesbar (2,20/2,43/2,80:1) - bewusst neu gehasht; der Altstand 5807fce ergibt den alten Hash 5f747f49aaa4ffde7fdf05d3f67f98fe
# 1077: Funde 1077b zaehlt Lieferanten-Artikel exakt (_saAnzahlExakt in fetchSuppliers) - bewusste Logik-Aenderung, Prüfsumme nachgezogen
# v3.9.1081 Render-Fund P3a: fetchJupConfig zeigt den Fehler ueber die Anzeige-Hilfe _fehlerText(e) statt (e&&e.message||e) -
# "Failed to fetch" wird "keine Verbindung zum Server". Einzige Abweichung im Kopf (difflib gegen origin/main 9ccd9ed gemessen),
# alter Wert 10071af7aa5791b70d724755163a5207. Schreibwege/Juprowa-Push unberuehrt.
# A55 Runde 3 (1084): ACT_LABELS (Anzeigetexte im Kopf) ohne Emoji ("🟢 Login" -> "Anmeldung") und mit
# deutschen Texten fuer juprowa_push_fail/_status_unbekannt - reine Anzeigetabelle, kein Handler/Schreibweg.
# Alter Wert d04b894788546b35a586f442795af90a.
# Render 1089 P3: die zwei fetchJupConfig-Toasts ohne Emoji ("❌ Juprowa-Config" -> "Juprowa-Konfiguration") - reine Meldungstexte,
# kein Handler/Schreibweg/Abruf geaendert. Alter Wert f2ed6cf75b4d9b3a2ca996312f9cd4d4.
KOPF_MD5_VORHER = "8a7402229c8827766fcef4d9fa53fdeb"  # v3.9.1089 mit const isMob=ww<BP_MOB;


def test_juprowa_reiter_byte_gleich(roh):
    assert _md5(_juprowa(roh)) == JUPROWA_MD5


def test_umkehr_juprowa_aenderung_waere_rot(roh):
    j = _juprowa(roh)
    assert _md5(j.replace("Juprowa Cloud", "Juprowa-Cloud", 1)) != JUPROWA_MD5


def _kopf_zurueck(src):
    k = _kopf(src)
    m = re.search(re.escape(DEKL) + r"/\*.*?\*/", k)
    assert m, "Stufen-Deklaration samt Kommentar nicht gefunden"
    return k[:m.start()] + "const isMob=ww<BP_MOB;" + k[m.end():]


def test_logik_vor_dem_rendern_unveraendert(roh):
    assert _md5(_kopf_zurueck(roh)) == KOPF_MD5_VORHER


def test_umkehr_handler_aenderung_waere_rot(roh):
    alt = "const fetchStats=async()=>{"
    assert alt in _kopf(roh)
    kaputt = roh.replace(alt, "const fetchStats=async()=>{;", 1)
    assert _md5(_kopf_zurueck(kaputt)) != KOPF_MD5_VORHER


# ── Lese-Tabellen: Feldnamen je Zelle ───────────────────────────────────────
TABELLEN_ENDE = {"logins": "/* Activity Log */", "status": "/* Activity by User */"}


def _tabelle(v, name):
    i = v.index("'data-ad-tabelle': \"%s\"" % name)
    return v[i:v.index(TABELLEN_ENDE[name], i)]


def _koepfe(t):
    kopf = t[t.index("React.createElement('thead'"):t.index("React.createElement('tbody'")]
    return re.findall(r"React\.createElement\('th', \{[^}]*\}+, \"([^\"]+)\"", kopf)


def _zellen(t):
    body = t[t.index("React.createElement('tbody'"):]
    return re.findall(r"React\.createElement\('td', \{ 'data-l': \"([^\"]+)\"", body)


@pytest.mark.parametrize("name,koepfe", [
    ("logins", ["Zeit", "Benutzer", "Status", "Anmeldeart", "Gerät"]),  # A55 Runde 3 (1084): Spaltenkopf deutsch statt "Auth"
    ("status", ["Benutzer", "Rolle", "Letzter Login", "Logins gesamt", "Aktionen (7T)", "Status"]),
])
def test_jede_zelle_traegt_ihren_feldnamen(roh, name, koepfe):
    """Die Feldnamen der Zellen sind genau die Spaltenkoepfe, in derselben Reihenfolge."""
    t = _tabelle(_ad(roh).replace("\r\n", "\n"), name)
    assert _koepfe(t) == koepfe
    z = [x.replace("\\u00e4", "\u00e4") for x in _zellen(t)]
    assert z == koepfe, z
    body = t[t.index("React.createElement('tbody'"):]
    assert body.count("React.createElement('td', {") == len(koepfe)


def test_umkehr_zelle_ohne_feldnamen_waere_rot(roh):
    v = _ad(roh).replace("\r\n", "\n")
    kaputt = v.replace("React.createElement('td', { 'data-l': \"Rolle\", ", "React.createElement('td', { ", 1)
    assert _zellen(_tabelle(kaputt, "status")) != ["Benutzer", "Rolle", "Letzter Login", "Logins gesamt", "Aktionen (7T)", "Status"]


def test_matrix_bleibt_tabelle_mit_klebender_benutzerspalte(roh):
    v = _ad(roh)
    t = v[v.index("'data-ad-tabelle': \"benachrichtigungen\""):]
    t = t[:t.index("/* Arbeitsscheine-Einstellungen */")]
    assert "epk-ad-karten" not in t
    assert t.count("..._adKleb(V.cd,true)") == 3  # zwei Kopfzellen + Benutzerzelle
    assert "React.createElement('tbody', {}, users.filter(u=>u.active).map(u=>{" in t


def _css(roh):
    a = roh.index("<style")
    return roh[a:roh.index("</style>", a)]


CSS_PFLICHT = [
    "table.epk-ad-mittel th { white-space: nowrap; }",
    "table.epk-ad-mittel thead th:first-child { z-index: 2 !important; }",
    "table.epk-ad-matrix thead th:first-child { z-index: 2 !important; }",
    "table.epk-ad-matrix td button { min-width: 36px; min-height: 36px; }",
    "table.epk-ad-karten thead { display: none; }",
    "table.epk-ad-karten td[data-l]::before { content: attr(data-l);",
]


def test_css_vorhanden_ohne_breitenabfrage(roh):
    css = _css(roh)
    for z in CSS_PFLICHT:
        assert z in css, z
    for r in re.findall(r"[^\n{}]*epk-ad-[^{]*\{[^}]*\}", css):
        assert "@media" not in r and "overflow-x" not in r, r
        for px in re.findall(r"font-size:\s*(\d+)px", r):
            assert int(px) >= 12, r


def test_umkehr_kleine_schalter_waeren_rot(roh):
    alt = "table.epk-ad-matrix td button { min-width: 36px; min-height: 36px; }"
    kaputt = _css(roh.replace(alt, alt.replace("36px", "24px"), 1))
    assert alt not in kaputt
