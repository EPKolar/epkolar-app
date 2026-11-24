# -*- coding: utf-8 -*-
"""Stufe 10 Monatsabrechnung und Mitarbeiter (GF 20.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: StundenzettelView (2 Stellen) und MitarbeiterView (1 Stelle) entschieden
selbst ueber die Breite (ww<BP_MOB). Am Tablet hochkant (600-767 px) stand in
Mitarbeiter die Liste UEBER den Details (.user-grid stapelt per CSS unter
768 px) - wer einen Mitarbeiter antippte, sah die Details erst nach dem Rollen
ueber die ganze Liste. Im Zeitabgleich der Monatsabrechnung stand "Nach
Projekt" am Tablet mit dem Namen ganz links und den Stunden ganz rechts.

Jetzt (nur Darstellung):
  MitarbeiterView    schmal = wie bisher; mittel = Liste und Details
                     nebeneinander (gleiche Loesung wie Administration Stufe 7);
                     breit = wie bisher.
  StundenzettelView  schmal = wie bisher (Zettel-Karten, Unterabstand ueber der
                     Leiste); mittel = "Nach Projekt" zweispaltig; breit = wie
                     bisher. Zettel bleiben Karten.

Jeder Riegel mit Umkehrprobe. Keine echten Mitarbeiterdaten in diesem Test.
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
HOEHE = '(typeof window!=="undefined"?window.innerHeight:0)'

DEKL_MA = 'const _maStufe=_layoutStufe(ww,' + HOEHE + ');const isMob=_maStufe==="schmal";const _maMittel=_maStufe==="mittel";'
DEKL_SZ = ('const _szStufe=_layoutStufe(ww,' + HOEHE + ');const isMob=_szStufe==="schmal";const _szMittel=_szStufe==="mittel";'
           'const _szProjGrid=_szMittel?{display:"grid",gridTemplateColumns:"repeat(2,minmax(0,1fr))",columnGap:16}:{};'
           'const _szProjKopf=_szMittel?{gridColumn:"1 / -1"}:{};')
GRID_MA = '_maMittel?{gridTemplateColumns:"minmax(0,1fr) minmax(0,1fr)"}:undefined'
UG_ALT = "React.createElement('div', { className: \"user-grid\"}"
UG_NEU = "React.createElement('div', { className: \"user-grid\", 'data-ma-stufe': _maStufe, style: " + GRID_MA + "}"
PAD_ALT = 'padding:ww<BP_MOB?"0 0 calc('
PAD_NEU = 'padding:isMob?"0 0 calc('
PROJ_ALT = ("Object.keys(byProject).length>0&&React.createElement('div', { style: {marginBottom:10}}",
            "color:V.dm,marginBottom:4}}, \"Nach Projekt:\")")
PROJ_NEU = ("Object.keys(byProject).length>0&&React.createElement('div', { 'data-sz-stufe': _szStufe, style: {marginBottom:10,..._szProjGrid}}",
            "color:V.dm,marginBottom:4,..._szProjKopf}}, \"Nach Projekt:\")")

SPANNE = {
    "ma": ("\nfunction MitarbeiterView({", "\nfunction _dispoMinToHHMM("),
    "sz": ("\nfunction StundenzettelView({", "\nfunction PhotoSyncStatus("),
}


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read().replace("\r\n", "\n")


def _teil(src, k):
    a, b = SPANNE[k]
    i = src.index(a)
    return src[i:src.index(b, i)]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


ZWEI = {"gridTemplateColumns": "minmax(0,1fr) minmax(0,1fr)"}
PGRID = {"display": "grid", "gridTemplateColumns": "repeat(2,minmax(0,1fr))", "columnGap": 16}
PKOPF = {"gridColumn": "1 / -1"}
# (Breite, Hoehe) -> [Mitarbeiter: Stufe, isMob, user-grid | Monatsabrechnung: Stufe, isMob, Projekt-Grid, Projekt-Kopf, Handy-Unterabstand]
FAELLE = [
    ([384, 832], ["schmal", True, None, "schmal", True, {}, {}, True]),
    ([412, 915], ["schmal", True, None, "schmal", True, {}, {}, True]),
    ([800, 1280], ["mittel", False, ZWEI, "mittel", False, PGRID, PKOPF, False]),
    ([1280, 800], ["breit", False, None, "breit", False, {}, {}, False]),
    ([1920, 1080], ["breit", False, None, "breit", False, {}, {}, False]),
]


def _entscheidung(node_exe, src, faelle):
    """Fuehrt die ECHTEN Ausdruecke aus beiden Komponenten aus (nicht abgeschrieben)."""
    ma, sz = _teil(src, "ma"), _teil(src, "sz")
    assert ma.count(DEKL_MA) == 1 and ma.count(UG_NEU) == 1
    assert sz.count(DEKL_SZ) == 1 and sz.count(PAD_NEU) == 1
    assert all(sz.count(x) == 1 for x in PROJ_NEU)
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function ma(ww){" + DEKL_MA + "return [_maStufe,isMob," + GRID_MA + "];}\n"
          "function sz(ww){" + DEKL_SZ + "return [_szStufe,isMob,_szProjGrid,_szProjKopf,isMob];}\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;"
          "return ma(ww).concat(sz(ww)).map(function(x){return x===undefined?null:x;});}\n"
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
    """schmal == alte isMob (ww<BP_MOB): 599 Handy, 600 nicht - in beiden Komponenten."""
    r = _entscheidung(node_exe, roh, [[599, 900], [600, 900]])
    assert [(x[1], x[4], x[7]) for x in r] == [(True, True, True), (False, False, False)]


# ── mittel und breit: dieselben Bedienelemente ──────────────────────────────
NUR_DARSTELLUNG = {
    "ma": [re.escape(DEKL_MA), re.escape(UG_NEU)],
    "sz": [re.escape(DEKL_SZ), re.escape(PROJ_NEU[0]), re.escape(PROJ_NEU[1])],
}
NAMEN = {"ma": r"_maMittel|_maStufe", "sz": r"_szMittel|_szStufe|_szProjGrid|_szProjKopf"}


def _stufen_reste(v, k):
    for m in NUR_DARSTELLUNG[k]:
        v = re.sub(m, "", v)
    return re.findall(NAMEN[k], nur_code(v))


@pytest.mark.parametrize("k", ["ma", "sz"])
def test_mittel_und_breit_unterscheiden_nur_darstellung(roh, k):
    assert _stufen_reste(_teil(roh, k), k) == []


@pytest.mark.parametrize("k,alt,stufe", [
    ("ma", "onClick: ()=>setSel(m.id), className: \"epk-card-hover\"", "_maMittel"),
    ("sz", "onClick: ()=>setAbgeglichen(z.id,true)", "_szMittel"),
])
def test_umkehr_handlung_nur_breit_waere_rot(roh, k, alt, stufe):
    v = _teil(roh, k)
    assert v.count(alt) == 1
    neu = alt.replace("onClick: ", "onClick: " + stufe + "?null:", 1)
    assert _stufen_reste(v.replace(alt, neu, 1), k)


# ── Abdeckung ───────────────────────────────────────────────────────────────
# Gepinnter gemeinsamer Seitentitel-Ausdruck (test_d9_seitenueberschriften_v956 u. a.) und die
# Unterschriftsflaeche (Pixelbreite der Zeichenflaeche unter 400 px, keine Layout-Stufe).
AUSNAHMEN = {"ma": ["fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite"],
             "sz": ["width: ww<400?260:360"]}
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|\(ww\|\|0\)\s*[<>]|innerWidth\s*[<>]=?|matchMedia|userAgent")


def _fremde_breiten(src, k):
    code = nur_code(_teil(src, k))
    for a in AUSNAHMEN[k]:
        code = code.replace(a, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


@pytest.mark.parametrize("k", ["ma", "sz"])
def test_abdeckung_keine_eigenen_breitenvergleiche(roh, k):
    funde = _fremde_breiten(roh, k)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)
    for a in AUSNAHMEN[k]:
        assert _teil(roh, k).count(a) == 1, a
    assert "ww<BP_MOB" not in nur_code(_teil(roh, k))


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    assert _fremde_breiten(roh.replace('const isMob=_maStufe==="schmal";', "const isMob=ww<BP_MOB;", 1), "ma")
    assert _fremde_breiten(roh.replace(PAD_NEU, PAD_ALT, 1), "sz")
    assert _fremde_breiten(roh.replace('const isMob=_szStufe==="schmal";', "const isMob=window.innerWidth<700;", 1), "sz")


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


@pytest.mark.parametrize("name", ["function MitarbeiterView(", "function StundenzettelView("])
def test_stufe_steht_im_selben_block(roh, name):
    bl = _bloecke(roh)
    p1, p2 = roh.index("function _layoutStufe(w,h){"), roh.index(name)
    n1 = [n for n, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [n for n, (a, b) in enumerate(bl) if a <= p2 < b]
    assert n1 and n2 and n1[0] == n2[0]


# ── Ganze Komponente byte-gleich nach Rueckbau (origin/main v3.9.1078, d1cbd11) ──
def _md5(t):
    return hashlib.md5(t.encode("utf-8")).hexdigest()


def _zurueck(v, dekl, alt):
    m = re.search(re.escape(dekl) + r"/\*.*?\*/", v)
    assert m, "Stufen-Deklaration samt Kommentar nicht gefunden"
    return v[:m.start()] + alt + v[m.end():]


def _ersetze1(v, alt, neu):
    assert v.count(alt) == 1, alt
    return v.replace(alt, neu, 1)


def _ma_zurueck(src):
    """Ganze MitarbeiterView (Zustaende, Handler, Schreibwege, Maskierung, Rendern), zurueckgebaut."""
    v = _zurueck(_teil(src, "ma"), DEKL_MA, "const isMob=ww<BP_MOB;")
    return _ersetze1(v, UG_NEU, UG_ALT)


def _sz_zurueck(src):
    """Ganze StundenzettelView (Upload, Freigabe, Abgleich, Druck, Rendern), zurueckgebaut."""
    v = _zurueck(_teil(src, "sz"), DEKL_SZ, "const isMob=ww<BP_MOB;")
    v = _ersetze1(v, PAD_NEU, PAD_ALT)
    for a, n in zip(PROJ_NEU, PROJ_ALT):
        v = _ersetze1(v, a, n)
    return v


# A55 Runde 3 (1084), nur Darstellung - gemessen: nimmt man genau diese zwei Aenderungen zurueck, ergeben
# sich wieder die alten Werte (ma 2eac1ef87d05cb693777765ab84edd1b, sz d6ec951803b6a6041939cb42eb7c4e3d):
#   ma: Platzhalter "Mitarbeiter auswaehlen" am Handy weg (isMob ? null, wie Administration 1080)
#   sz: Monatsabrechnung MA-Filter am Handy eigene Zeile (flex:isMob?"1 1 100%":1)
MD5 = {
    "ma": "b36bd8b3ddc901d3342d79540f14bff9",  # Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen (Abwesenheits-/Stundenanzeigen) - vorher 4adbcd7687756147276f9fc1368b9ec7 |  v3.9.1104 GF 24.11. (Rollen-Sicht): SV-Nr. und Reisepass im Mitarbeiter-Detail und im Neu-Formular nur noch fuer Admin/Buero (_maPersDatenRolle), PL sieht sie maskiert - bewusst neu gehasht, Riegel+Umkehrprobe in test_rollen_sicht_v1104.py; vorher 0afaa5ff44120309a82cf3c9d5a1b555 | Render-Funde 1096: nur Anzeige - "Nicht" (Chip) ueber _lesbar(COLORS.ERROR) (dunkel 4,24:1) - bewusst neu gehasht; der Altstand 5807fce ergibt den alten Hash 240ee69acea97156c3d1970d09942a88
    "sz": "b435f4b674775bc327ffec3db8671f8a",  # Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen (FinkZeit-Abgleich/Monatsabrechnung) - vorher caf974cf6167d6c3cf3c474f23006812 |  Monatsfreigabe (GF 24.11.2026, feature/monatsfreigabe, unsichtbar ohne Datenmodell): MonatsfreigabeMonteur fuer Monteur/Helfer bei Datenmodell, Alt-Liste ohne Freigabe-Zeilen - Rueckbau ergibt den alten Hash; vorher e4dbdd9d04d1899e6184b8c3c8c0d502 | Monatsfreigabe (GF 24.11.2026, feature/monatsfreigabe): StundenzettelView zeigt MonatsfreigabeMonteur fuer Monteur/Helfer, Alt-Liste ohne Freigabe-Zeilen (_mfIstNeu) - Rueckbau dieser zwei Stellen ergibt den alten Hash; vorher 0960aebc612c8336ccb4d8f5e6905dd5 | v3.9.1107 GF 24.11. Zulage laut Stempeluhr: eigene Stempelungen laden (_myStz) und EZ-Tage aus _ezTageAusStempel, Beschriftung Projektstunden - bewusst neu gehasht; vorher c9c163d49698109c624f33a2929ad638 | v3.9.1106 Meine Stempelzeiten (GF 24.11.): Signatur +pushNotif und Abschnitt MeineStempelzeiten in der eigenen Sicht - bewusst neu gehasht; vorher 9181d7ba8929ccbf1cc8c2a4486622e7 | v3.9.1093 Zahlenfelder text statt number (ZahlEingabe/_fzZahl/_ganzZahl) - bewusst neu gehasht; Rueckbau genau dieser Ersetzungen ergibt den alten Hash 8f5c7ae1c5e2e562db679ef16bd2bcfb | Render-Funde 1096: nur Anzeige - "Datei waehlen" gesperrt als Umriss-Knopf in V.mt statt 50 % Deckkraft (2,31:1) - bewusst neu gehasht; der Altstand 5807fce ergibt den alten Hash 041fd10ccba590331841544219f0598a
}
ZURUECK = {"ma": _ma_zurueck, "sz": _sz_zurueck}


@pytest.mark.parametrize("k", ["ma", "sz"])
def test_logik_unveraendert(roh, k):
    assert _md5(ZURUECK[k](roh)) == MD5[k]


@pytest.mark.parametrize("k,alt,neu", [
    ("ma", "const updMonteur=(id,f,v)=>{if(!isAdmin)return;", "const updMonteur=(id,f,v)=>{if(!isAdmin)return;;"),
    ("sz", "const setFinkStunden=(zid,val)=>{", "const setFinkStunden=(zid,val)=>{;"),
])
def test_umkehr_handler_aenderung_waere_rot(roh, k, alt, neu):
    assert _teil(roh, k).count(alt) == 1
    assert _md5(ZURUECK[k](roh.replace(alt, neu, 1))) != MD5[k]


# ── Owner-Regel: Zettel bleiben Karten, keine neuen Tabellen/Media-Abfragen ──
def test_keine_neue_tabelle_und_kein_media(roh):
    # Monatsabrechnung: einzig die zwei Druckvorlagen (@media print) - vorbestehend, keine Breite.
    assert nur_code(_teil(roh, "ma")).count("@media") == 0
    sz = nur_code(_teil(roh, "sz"))
    assert sz.count("@media") == sz.count("@media print") == 2
    assert "React.createElement('table'" not in nur_code(_teil(roh, "ma"))
    assert "React.createElement('table'" not in nur_code(_teil(roh, "sz"))
