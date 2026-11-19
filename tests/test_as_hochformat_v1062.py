# -*- coding: utf-8 -*-
"""AS Hochformat (GF 19.11.2026): "Arbeitsscheine schaut im Hochformat das UI
komisch aus ... die Liste der AS ist so schlimm".

Gemessen am Tablet (Lenovo TB328XU hochkant, 800 CSS-px): die Liste zeigte die
Rechner-Tabelle (minWidth 1300). Die klebende Aktionen-Spalte deckte BESTAETIGT
zu, Kunde/Status/Monteur lagen ausserhalb des Bildes, elf Kacheln nahmen die
halbe Hoehe, die Dispo-Wochenleiste brach um (KW 50 allein), der Freitag der
Dispo war abgeschnitten, der Sperrknopf lag ueber einer Karte, und "Heute" sah
im Kalender wie eine zweite Auswahl aus.

Was hier gesichert wird:
1. Die Listenform haengt an EINER app-weiten Breitenstufe (_layoutStufe:
   schmal/mittel/breit, nur Breite + Lage) - mit echtem Code fuer 384, 412,
   800 hochkant, 1280 quer, 1920 ausgefuehrt; Abdeckungsriegel: die umgebauten
   Teile vergleichen keine Breite selbst.
2. Karte und Tabelle haengen an derselben Entscheidung; die Karte traegt
   dieselben Handlungen wie die Tabellenzeile, Storno unter derselben Bedingung.
3. Die Dispo-Wochen bleiben eine Reihe, die Pfeile normal hoch.
4. Der Sperrknopf hat am Touch-Geraet seinen 44-px-Streifen.
5. Heute ist eine Aktion neben den Pfeilen, die Ansicht eine Segmentgruppe.
Jeder Riegel hat eine Umkehrprobe.

Nachtrag AS Liste mittel (GF-Entscheidung 19.11.2026 nach 1065): "die Ansicht
der AS in Kacheln kann ich nicht zuordnen, vorher in der Liste konnte ich
direkt aendern, war besser". Karten gelten seitdem NUR fuer schmal (Handy).
mittel (Tablet hochkant) zeigt wieder die Tabelle - dieselben Zeilen und
dieselben Direkt-Felder wie breit -, aber die Aktionen-Spalte klebt dort
nicht mehr (sie deckte BESTAETIGT zu), die Koepfe brechen nicht um, Felder
und Knoepfe sind 44 px. Die Kacheln bleiben in mittel kompakt.
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _stufe_code(src):
    """BP_MOB + BP_BREIT/BP_QUER + _layoutStufe, so wie sie in index.html stehen."""
    mob = src[src.index("const BP_MOB=600;"):src.index("const BP_MOB=600;") + len("const BP_MOB=600;")]
    i = src.index("const BP_BREIT=")
    j = src.index("function _layoutStufe(w,h){", i)
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[i:k]


def _fn_layout(src):
    i = src.index("function _layoutStufe(w,h){")
    return src[i:src.index("function _grobZeiger(", i)]


def _stufen(node_exe, code, faelle):
    out = run_node_snippet(
        node_exe,
        "var window={innerWidth:0,innerHeight:0};\n" + code
        + "\nprocess.stdout.write(JSON.stringify(" + json.dumps(faelle)
        + ".map(function(f){return _layoutStufe(f[0],f[1]);})));")
    return json.loads(out)


# (Breite, Hoehe) -> Stufe. A55 hochkant 384/412, Tablet hochkant 800x1280,
# Tablet quer 1280x800, Rechner 1920x1080; dazu die Grenzen.
FAELLE = [([384, 832], "schmal"), ([412, 915], "schmal"), ([599, 900], "schmal"),
          ([600, 960], "mittel"), ([800, 1280], "mittel"), ([1024, 1366], "mittel"),
          ([1099, 1400], "mittel"), ([899, 600], "mittel"),
          ([900, 600], "breit"), ([1024, 768], "breit"), ([1100, 1400], "breit"),
          ([1280, 800], "breit"), ([1920, 1080], "breit")]


def test_stufe_fuer_handy_tablet_hoch_quer_und_rechner(roh, node_exe):
    r = _stufen(node_exe, _stufe_code(roh), [f for f, _ in FAELLE])
    assert r == [e for _, e in FAELLE], list(zip([f for f, _ in FAELLE], r))


def test_ohne_breite_bleibt_die_tabelle(roh, node_exe):
    """Fehlt die Breite ganz (kein Fenster), gilt der alte Zustand: breit = Tabelle."""
    r = _stufen(node_exe, _stufe_code(roh), [[0, 0], [None, None], ["x", 5]])
    assert r == ["breit"] * 3


def test_umkehr_alte_schwelle_waere_rot(roh, node_exe):
    """Mit der Handy-Schwelle als Tabellengrenze haette das Tablet hochkant wieder
    die Tabelle - genau der Befund. Der Riegel muss das sehen."""
    gut = _stufe_code(roh)
    kaputt = gut.replace("const BP_BREIT=1100;", "const BP_BREIT=600;")
    assert kaputt != gut
    assert _stufen(node_exe, kaputt, [f for f, _ in FAELLE]) != [e for _, e in FAELLE]


def test_stufe_kennt_kein_geraet(roh):
    """Nur Breite und Lage - nie userAgent, nie Geraeteerkennung."""
    f = _fn_layout(roh)
    for verboten in ("userAgent", "navigator", "platform", "maxTouchPoints", "matchMedia"):
        assert verboten not in f, verboten
    assert "userAgent" not in _fn_layout(roh.replace("navigator.userAgent", "")), "Selbstprobe"


def test_umkehr_geraeteerkennung_waere_rot(roh):
    f = _fn_layout(roh)
    kaputt = f.replace("if(n<BP_MOB)", "if(/Android/.test(navigator.userAgent)||n<BP_MOB)")
    assert kaputt != f and "userAgent" in kaputt


# ── ABDECKUNG (Paragraph 9 "Zwei Apps") ─────────────────────────────────────
# Die umgebauten Teile fragen _layoutStufe und vergleichen keine Breite selbst.
# Ausnahmen sind namentlich genannt, mit Grund:
AUSNAHMEN = {
    # Seitentitel: dasselbe Muster an 23 Stellen der App, gepinnt von
    # test_d9_seitenueberschriften_v956 und test_seitentitel_v1007 - kein Teil
    # der umgebauten Liste.
    "fontSize:window.innerWidth<BP_MOB?UI.fSeiteMob:UI.fSeite",
    # Kopf-Versatz des klebenden Dispo-Tageskopfs: haengt an der Polsterung von
    # .main-pad (CSS), nicht an der Layoutstufe. Unveraendert seit Tablet 1041.
    "top:(window.innerWidth<1200?-20:0)",
}
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|innerWidth\s*[<>]=?|matchMedia|\bww<|\bww>")


def _bereiche(src):
    a = src.index("function DispoPanel(")
    b = src.index("function ArbeitsscheinView(")
    # Druckvorlage (genAsPdf) liegt dazwischen und ist kein Bildschirm-Layout
    g0 = src.index("const genAsPdf=", b)
    g1 = src.index("const stats=_react.useMemo.call(void 0, ()=>arbeitsscheine.reduce(", g0)
    ende = src.index("\nfunction ", g1)
    return {"DispoPanel": src[a:b], "ArbeitsscheinView": src[b:g0] + src[g1:ende]}


def _fremde_breiten(src):
    funde = []
    for name, teil in _bereiche(src).items():
        code = nur_code(teil)
        for aus in AUSNAHMEN:
            code = code.replace(aus, "")
        for m in BREITEN_MUSTER.finditer(code):
            funde.append((name, code[max(0, m.start() - 50):m.end() + 30]))
    return funde


def test_abdeckung_keine_eigenen_breitenvergleiche(roh):
    funde = _fremde_breiten(roh)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(map(str, funde))


def test_abdeckung_beide_teile_fragen_die_stufe(roh):
    b = _bereiche(roh)
    assert "const _asStufe=_layoutStufe(ww," in b["ArbeitsscheinView"]
    assert "const isMob=_asStufe===\"schmal\";" in b["ArbeitsscheinView"]
    # GF 19.11. nach 1065: Karte nur noch schmal, mittel = Tabelle
    assert "const _asKarte=_asStufe===\"schmal\";const _asMittel=_asStufe===\"mittel\";" in b["ArbeitsscheinView"]
    assert "var _dpStufe=_layoutStufe();" in b["DispoPanel"]
    assert "var _dpGrob=_grobZeiger();" in b["DispoPanel"]


def test_umkehr_abdeckung_findet_einen_neuen_vergleich(roh):
    kaputt = roh.replace("const _asKarte=_asStufe===\"schmal\";", "const _asKarte=ww<600;", 1)
    assert kaputt != roh
    assert _fremde_breiten(kaputt), "Abdeckungsriegel blind"
    kaputt2 = roh.replace("var _dpGrob=_grobZeiger();", "var _dpGrob=window.matchMedia(\"(pointer: coarse)\").matches;", 1)
    assert _fremde_breiten(kaputt2), "Abdeckungsriegel blind fuer matchMedia"


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def _block(bl, pos):
    for n, (a, b) in enumerate(bl):
        if a <= pos < b:
            return n
    return None


def test_schwelle_steht_im_block_ihrer_leser(roh):
    """node_check parst nur - eine Konstante im falschen Block waere gruen und
    zur Laufzeit ein ReferenceError."""
    bl = _bloecke(roh)
    d = _block(bl, roh.index("function _layoutStufe(w,h){"))
    assert d is not None
    for leser in ("function ArbeitsscheinView(", "function DispoPanel("):
        assert _block(bl, roh.index(leser)) == d, leser


def _as_view(src):
    i = src.index("function ArbeitsscheinView(")
    return src[i:i + 260000]


KARTE = "_asKarte&&React.createElement('div', { 'data-as-karten'"
TABELLE = "!_asKarte&&React.createElement('div', { style: {...CC(),padding:0,overflow:\"hidden\"}}"


def _zweige(v):
    i = v.index(KARTE)
    j = v.index(TABELLE, i)
    k = v.index("!filtered.length&&", j)
    return v[i:j], v[j:k]


def test_karte_und_tabelle_haengen_an_derselben_entscheidung(roh):
    v = _as_view(roh)
    assert v.count(KARTE) == 1 and v.count(TABELLE) == 1
    assert ", !_asKarte&&_asRollt&&React.createElement(" in v, "Rollhinweis gehoert zur Tabelle und haengt an der gemessenen Ueberbreite"
    assert "WebkitOverflowScrolling:\"touch\"}, ref: _asRollRef" in v
    assert "..._asNrKlebt()}, onClick: ()=>_openEditGuarded(a)}, a.nummer" in v, "Nummer klebt links im Rollkasten"
    # Sortierauswahl dort, wo es keine Spaltenkoepfe gibt
    s = v.index("React.createElement('select', { value: sortCol")
    z = v.rfind(", _asKarte&&React.createElement('div', { style: {display:\"flex\",gap:6,alignItems:\"center\"}}", 0, s)
    assert z != -1 and s - z < 2500
    # Kein Zweig haengt mehr an isMob allein
    code = nur_code(v)
    assert "isMob&&React.createElement('div', { style: {display:\"flex\",flexDirection:\"column\",gap:8}}" not in code
    assert "!isMob&&React.createElement('div', { style: {...CC(),padding:0,overflow:\"hidden\"}}, React.createElement('div', { className: \"epk-as-roll\"" not in code


HANDLUNGEN = ["openEdit(a);", "genAsPdf(a);", "setAsShowQR(asShowQR===a.id?null:a.id);", "storno(a.id);"]
STORNO_BED = "!isSt&&!(isMonteurRole&&!isAdmin&&!AS_GRP_OFFEN.includes(a.scheinstatus))"


def _karte_ok(v):
    karte, tabelle = _zweige(v)
    for h in HANDLUNGEN:
        if h not in karte or h not in tabelle:
            return False
    return karte.count(STORNO_BED) == 1 and tabelle.count(STORNO_BED) == 1


def test_karte_traegt_alle_handlungen_der_zeile(roh):
    """Bearbeiten, PDF, QR, Storno - dieselben Aufrufe wie in der Tabelle, Storno
    unter derselben Bedingung (storniert: kein Storno, Monteur bei
    abgeschlossenem Schein: kein Storno)."""
    assert _karte_ok(_as_view(roh))


def test_umkehr_karte_ohne_storno_waere_rot(roh):
    v = _as_view(roh)
    karte, _ = _zweige(v)
    i = karte.index(STORNO_BED)
    kaputt = v.replace(karte, karte[:i] + "false" + karte[i + len(STORNO_BED):], 1)
    assert not _karte_ok(kaputt)


def test_karte_knoepfe_sind_tippziele_und_storniert_steht_gleich(roh):
    karte, _ = _zweige(_as_view(roh))
    assert karte.count("minHeight:44") >= 4, "jeder Kartenknopf mindestens 44 px"
    assert "justifyContent:\"flex-start\"" in karte, "Knoepfe links - storniert ohne Storno verrutscht nicht"
    assert "justifyContent:\"flex-end\",marginTop:4" not in karte
    assert "marginLeft:\"auto\"}" in karte, "Storno rechts abgesetzt"


def test_karte_nennt_beide_termine_und_den_ort(roh):
    karte, _ = _zweige(_as_view(roh))
    for t in ("\"Erf. \"", "\"Vorschl. \"+fdt(a.terminVorschlag)", "\"Best. \"+fdt(a.terminBestaetigt)",
              "a.arbeitsort||a.kundOrt", "WebkitLineClamp:2"):
        assert t in karte, t


def test_kacheln_kompakt_nur_am_tablet_hochkant(roh):
    v = _as_view(roh)
    # GF 19.11. nach 1065: mittel zeigt wieder die Tabelle, die Kacheln bleiben dort kompakt
    assert "epk-kachelband\"+(_asMittel?\" epk-kachel-kompakt\":\"\")" in v
    css = [m.group(0) for m in re.finditer(r"\.kpi-grid\.epk-leiste\.epk-kachel-kompakt[^{]*\{[^}]*\}", roh)]
    assert css, "keine Kompakt-Regel"
    for r in css:
        assert "overflow-x" not in r, "Querrollen toetet den Reiter-Wisch (v3.9.930)"
        assert "display: none" not in r


def _wochen_seg(src):
    i = src.index("/* v3.9.725 #14: KW-Tabs (Wochenplanungs-Stil)")
    return src[i:i + 6000]


def _leiste_ok(seg):
    return ("{display:\"flex\",alignItems:\"center\",gap:6,marginBottom:10,flexWrap:\"nowrap\"}}" in seg
            and "'data-kw-leiste':\"1\",style:{display:\"flex\",gap:6,flexWrap:\"nowrap\",overflowX:\"auto\"" in seg
            and "flex:\"1 0 auto\",minWidth:96" in seg)


def test_dispo_wochen_eine_reihe_pfeile_normal_hoch(roh):
    assert _leiste_ok(_wochen_seg(roh))


def test_umkehr_umbrechende_wochen_waeren_rot(roh):
    seg = _wochen_seg(roh)
    kaputt = seg.replace("style:{display:\"flex\",gap:6,flexWrap:\"nowrap\",overflowX:\"auto\"",
                         "style:{display:\"flex\",gap:6,flexWrap:\"wrap\",overflowX:\"auto\"")
    assert kaputt != seg and not _leiste_ok(kaputt)


def test_dispo_tablet_hochkant_feste_spalten(roh):
    i = roh.index("function DispoPanel(")
    p = roh[i:i + 120000]
    assert "var _dpEng=_dpStufe!==\"breit\";var _dpFix=_dpStufe===\"mittel\";" in p
    assert "_dpFix?{tableLayout:\"fixed\",minWidth:0}:{}" in p
    assert "_dpFix?{overflowWrap:\"break-word\"}:{}" in p
    assert "h('span',{style:{whiteSpace:\"nowrap\"}},t.wtag+" in p, "Datum im Tageskopf bricht nicht"
    assert "className:_dpFix?\"epk-dp-umbruch\":undefined" in p, "Monteurname bricht in der festen Aufteilung um"
    assert "td.epk-dp-umbruch { white-space: normal !important;" in roh


def test_sperrknopf_streifen_folgt_der_hausregel(roh):
    """Die CSS-Hausregel macht am Touch-Geraet jeden Knopf 44 hoch. Der Streifen
    muss dieselbe Bedingung lesen wie die Regel, sonst rechnet er mit 24."""
    css = re.search(r"@media \(pointer: coarse\), \(max-width: 768px\) \{", roh)
    assert css, "Hausregel nicht gefunden - dann misst _dpGrob gegen eine andere Bedingung"
    assert "function _grobZeiger(){try{return !!(window.matchMedia&&window.matchMedia(\"(pointer: coarse), (max-width: 768px)\").matches);" in roh
    m = re.search(r"paddingTop:_hasToggle\?\(_dpGrob\?(\d+):(\d+)\):4", roh)
    k = re.search(r"position:\"absolute\",top:(\d+),right:8,zIndex:3,.*?minHeight:_dpGrob\?(\d+):(\d+),", roh)
    assert m and k
    assert int(m.group(1)) >= int(k.group(1)) + 44 and int(k.group(2)) >= 44
    # Handy: die Mobil-Regel td,th padding 6px !important schlug den Streifen - eigene Regel stellt ihn wieder her
    assert "'data-sperrstreifen':_hasToggle?\"1\":undefined," in roh
    assert re.search(r'td\[data-dispocell\]\[data-sperrstreifen="1"\] \{ padding-top: (\d+)px !important; \}', roh)


def _kal(src):
    i = src.index("sub===\"kalender\"&&(React.createElement('div', { className: \"epk-tab-fade\", key: \"as-kal\" }")
    return src[i:i + 5000]


def _heute_ok(k):
    h = k.find("onClick: gotoToday")
    vor = k.find("onClick: ()=>navCal(1)")
    grp = k.find("role: \"group\", 'aria-label': \"Kalenderansicht\"")
    return -1 not in (h, vor, grp) and vor < h < grp and "'aria-pressed': calView===v?\"true\":\"false\"" in k


def test_heute_ist_aktion_neben_den_pfeilen(roh):
    assert _heute_ok(_kal(roh))


def test_umkehr_heute_in_der_ansichtsgruppe_waere_rot(roh):
    k = _kal(roh)
    h0 = k.index("            , React.createElement('button', { onClick: gotoToday")
    h1 = k.index("\n", h0) + 1
    zeile = k[h0:h1]
    ohne = k[:h0] + k[h1:]
    g = ohne.index("[\"tag\",\"woche\",\"monat\"].map(")
    kaputt = ohne[:g] + zeile.strip() .lstrip(", ") + "," + ohne[g:]
    assert not _heute_ok(kaputt)


# ── AS Liste mittel (GF-Entscheidung 19.11.2026 nach 1065) ──────────────────
# "die Ansicht der AS in Kacheln kann ich nicht zuordnen, vorher in der Liste
# konnte ich direkt aendern, war besser" - mittel zeigt die Tabelle.

ENTSCHEIDUNG = "const _asKarte=_asStufe===\"schmal\";const _asMittel=_asStufe===\"mittel\";"


def _form_je_stufe(node_exe, code, entscheidung):
    """Fuehrt _layoutStufe UND die Entscheidungszeile aus und liefert je Fall
    'karte' oder 'tabelle' (plus ob die Stufe mittel ist)."""
    out = run_node_snippet(
        node_exe,
        "var window={innerWidth:0,innerHeight:0};\n" + code
        + "\nprocess.stdout.write(JSON.stringify(" + json.dumps([f for f, _ in FAELLE])
        + ".map(function(f){var _asStufe=_layoutStufe(f[0],f[1]);" + entscheidung
        + "return [_asKarte?\"karte\":\"tabelle\",!!_asMittel];})));")
    return json.loads(out)


def _soll_form():
    return [["karte" if e == "schmal" else "tabelle", e == "mittel"] for _, e in FAELLE]


def test_mittel_zeigt_die_tabelle_schmal_die_karte(roh, node_exe):
    assert roh.count(ENTSCHEIDUNG) == 1
    r = _form_je_stufe(node_exe, _stufe_code(roh), ENTSCHEIDUNG)
    assert r == _soll_form(), list(zip([f for f, _ in FAELLE], r))
    # 800x1280 (Tablet hochkant) ausdruecklich
    assert r[[f for f, _ in FAELLE].index([800, 1280])] == ["tabelle", True]


def test_umkehr_karten_in_mittel_waeren_rot(roh, node_exe):
    """Die 1065-Entscheidung (Karte in schmal UND mittel) muss der Riegel sehen."""
    alt = ENTSCHEIDUNG.replace("_asStufe===\"schmal\";", "_asStufe!==\"breit\";")
    assert alt != ENTSCHEIDUNG
    assert _form_je_stufe(node_exe, _stufe_code(roh), alt) != _soll_form()


# Die Direkt-Felder der Tabellenzeile (Kennung -> Schreibweg). Sie stehen genau
# einmal im Tabellenzweig, und nichts davon haengt an der Stufe - mittel hat
# also dieselben Direkt-Aenderungen wie breit.
DIREKT = {
    "Terminvorschlag": "onChange: e=>updAs(a.id,{terminVorschlag:e.target.value})",
    "Bestaetigt": "onChange: e=>_asBestEntwurf(a,e,_bestSt,updAs), onBlur: e=>{_asBestUebernehmen(a,e,_bestSt,updAs);}",
    "Status": "_asZeileRueckfrage(a,\"scheinstatus\",_newS).then(_ok=>{if(_ok)updAs(a.id,{scheinstatus:_newS});});",
    "Prioritaet": "_asZeileRueckfrage(a,\"prioritaet\",_np).then(_ok=>{if(_ok)updAs(a.id,{prioritaet:_np});});",
    "Sachbearbeiter": "isAdmin?React.createElement('select', { className: \"epk-ruhig\", value: a.sachbearbeiter||\"\", onChange: e=>{e.stopPropagation();updAs(a.id,{sachbearbeiter:e.target.value});}",
    "Monteur": "_asZeileRueckfrage(a,\"monteur\",_nm,monteure).then(_ok=>{if(_ok)updAs(a.id,{monteur:_nm});});",
}
STUFEN_WOERTER = ("_asMittel", "_asStufe", "isMob", "_asKarte")


def _direkt_ok(v):
    _, tabelle = _zweige(v)
    zeile = tabelle[tabelle.index("React.createElement('tbody'"):]
    for name, weg in DIREKT.items():
        if zeile.count(weg) != 1:
            return False
    code = nur_code(zeile)
    # Die Zeile (Felder UND Knoepfe) haengt an keiner Stufe; die Aktionen-
    # Spalte unterscheidet sich nur im Kleben (_asAktSpalte), nicht im Inhalt.
    rest = code.replace("..._asAktSpalte()", "")
    return not any(w in rest for w in STUFEN_WOERTER)


def test_mittel_hat_dieselben_direkt_felder_wie_breit(roh):
    v = _as_view(roh)
    assert _direkt_ok(v)
    # die Tabelle selbst haengt nur an !_asKarte, also an mittel UND breit
    assert v.count(TABELLE) == 1


def test_umkehr_feld_nur_in_breit_waere_rot(roh):
    v = _as_view(roh)
    _, tabelle = _zweige(v)
    anker = "React.createElement('td', { style: {...tdSt(),padding:2}}, React.createElement('select', { className: \"epk-ruhig\", value: a.scheinstatus"
    assert tabelle.count(anker) == 1
    kaputt = v.replace(tabelle, tabelle.replace(anker, "!_asMittel&&" + anker, 1), 1)
    assert not _direkt_ok(kaputt)


def _akt_klebt(node_exe, helfer, mittel):
    out = run_node_snippet(
        node_exe,
        "var V={cd:\"#fff\"};var _asMittel=" + ("true" if mittel else "false") + ";\n"
        + helfer + "\nprocess.stdout.write(JSON.stringify(_asAktSpalte()));")
    return json.loads(out)


def _akt_helfer(src):
    i = src.index("const _asAktKlebt=()=>(")
    j = src.index(";", src.index("boxShadow:", i)) + 1
    k = src.index("const _asAktSpalte=()=>(")
    l = src.index(";", k) + 1
    return src[i:j] + "\n" + src[k:l]


def test_aktionen_kleben_nur_in_breit(roh, node_exe):
    h = _akt_helfer(roh)
    assert _akt_klebt(node_exe, h, False).get("position") == "sticky", "breit unveraendert"
    m = _akt_klebt(node_exe, h, True)
    assert "position" not in m and "right" not in m, "mittel: die Spalte deckt nichts zu"
    v = _as_view(roh)
    _, tabelle = _zweige(v)
    assert tabelle.count("..._asAktSpalte()") == 2 and "..._asAktKlebt()" not in tabelle
    assert "..._asNrKlebt()" in tabelle, "Nummer klebt weiter links"


def test_umkehr_klebende_aktionen_in_mittel_waeren_rot(roh, node_exe):
    h = _akt_helfer(roh).replace("_asMittel?{}:_asAktKlebt()", "_asAktKlebt()")
    assert _akt_klebt(node_exe, h, True).get("position") == "sticky"


def test_mittel_tabelle_koepfe_ohne_umbruch_und_tippziele(roh):
    v = _as_view(roh)
    _, tabelle = _zweige(v)
    assert "React.createElement('table', { className: _asMittel?\"epk-as-mittel\":undefined," in tabelle
    assert "table.epk-as-mittel th { white-space: nowrap; }" in roh
    assert "table.epk-as-mittel thead th:first-child { z-index: 2 !important; }" in roh, "NUMMER-Kopf liegt beim Querrollen oben"
    assert re.search(r'table\.epk-as-mittel td select, table\.epk-as-mittel td input\[type="date"\] \{ min-height: 44px; \}', roh)
    r = re.search(r"table\.epk-as-mittel td button \{([^}]*)\}", roh)
    assert r and "min-width: 44px !important" in r.group(1) and "min-height: 44px !important" in r.group(1)
    for regel in re.findall(r"table\.epk-as-mittel[^{]*\{[^}]*\}", roh):
        assert "font-size" not in regel, "Schrift bleibt bei thS/tdSt (>= 12)"
        assert "position" not in regel and "overflow" not in regel
